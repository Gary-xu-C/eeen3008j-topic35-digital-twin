"""Analytic and protocol checks. Run: python -m unittest discover -s experiments -v"""
import unittest
from dataclasses import replace
from simulator import Config, Sample, POLICIES, adopt, predict, make_trajectory, make_channel, simulate


class BaselineChecks(unittest.TestCase):
    def ideal(self, **kw):
        return Config(rate_bps=None, delay=0, ack_delay=0, **kw)

    def run_case(self, c, policy="periodic", scenario="constant", **kw):
        return simulate(c, policy, make_trajectory(c, scenario, **kw), make_channel(c))

    def test_constant_motion_exact_for_all_policies(self):
        c = Config(loss=0.3, jitter=0.1)
        for policy in POLICIES:
            self.assertLess(self.run_case(c, policy)["metrics"]["rmse_m"], 1e-12)

    def test_ideal_periodic_equals_age(self):
        c = self.ideal()
        p, a = [self.run_case(c, q, "maneuver") for q in ("periodic", "age")]
        self.assertEqual(p["trace"], a["trace"])
        self.assertEqual(p["events"], a["events"])

    def test_single_delayed_update_extrapolates_and_aoi_not_zero(self):
        c = Config(duration=2)
        r = self.run_case(c)
        received = next(x for x in r["events"] if x["event"] == "data_received")
        row = r["trace"][received["slot"]]
        self.assertAlmostEqual(row["estimate_m"], row["position_m"])
        self.assertAlmostEqual(row["aoi_s"], 0.13)
        self.assertEqual(r["metrics"]["attempts"], 1)

    def test_total_loss_does_not_refresh_mirror_or_receiver(self):
        c = Config(loss=1)
        r = self.run_case(c, "error_age", "maneuver")
        self.assertEqual(r["metrics"]["delivered"], 0)
        self.assertEqual(r["metrics"]["ack_bytes"], 0)
        self.assertAlmostEqual(r["trace"][-1]["aoi_s"], 9.99)
        self.assertTrue(all(x["aoi_s"] == x["sender_age_s"] for x in r["trace"]))
        sends = [x["slot"] for x in r["events"] if x["event"] == "send"]
        self.assertTrue(all(b-a >= 20 for a,b in zip(sends, sends[1:])))

    def test_maneuver_no_updates_matches_closed_form(self):
        c = self.ideal(period=20, max_age=20)
        r = self.run_case(c, scenario="maneuver", change_time=4.3, jump=2)
        for row in r["trace"]:
            self.assertAlmostEqual(row["error_m"], 2*max(0, row["time_s"]-4.3))

    def test_error_threshold_strict_and_age_inclusive(self):
        c = self.ideal(dt=0.1, duration=3, period=10, max_age=10, error_threshold=0.5)
        r = self.run_case(c, "error_age", "maneuver", change_time=1, jump=1)
        send = next(x for x in r["events"] if x["event"] == "send")
        self.assertAlmostEqual(send["time_s"], 1.6)
        a = self.run_case(replace(c, max_age=1), "age")
        self.assertAlmostEqual(a["events"][0]["time_s"], 1.0)

    def test_ack_delay_creates_observable_mirror_mismatch(self):
        c = Config(ack_delay=0.2, error_threshold=0.05)
        r = self.run_case(c, "error_age", "maneuver")
        mismatch = [x for x in r["trace"] if abs(x["estimate_m"]-x["sender_estimate_m"]) > 1e-6]
        self.assertTrue(mismatch)
        self.assertTrue(all(x["busy_before_decision"] == 1 for x in mismatch))

    def test_acceleration_closed_form(self):
        c = self.ideal(period=20, max_age=20)
        r = self.run_case(c, scenario="acceleration", jump=0.5)
        for x in r["trace"]:
            self.assertAlmostEqual(x["error_m"], 0.25*x["time_s"]**2)

    def test_old_packet_rejected(self):
        current = Sample(10, 2, 3)
        self.assertEqual(adopt(current, Sample(9, 100, 100)), current)
        self.assertEqual(adopt(current, Sample(10, 100, 100)), current)
        self.assertEqual(predict(current, 20, 0.1), 5)

    def test_counts_and_bytes_at_horizon(self):
        c = Config(duration=1.1, delay=1, loss=0)
        m = self.run_case(c)["metrics"]
        self.assertEqual(m["attempts"], 1)
        self.assertEqual(m["data_inflight"], 1)
        self.assertEqual(m["total_bytes"], 32)
        for seed in range(10):
            c = Config(seed=seed, loss=0.4, jitter=0.2)
            for q in POLICIES:
                m = self.run_case(c, q, "random_maneuver")["metrics"]
                self.assertEqual(m["attempts"], m["delivered"]+m["lost"]+m["data_inflight"])
                self.assertEqual(m["total_bytes"], 32*m["attempts"]+16*m["ack_generated"])
                self.assertEqual(m["ack_generated"], m["ack_delivered"]+m["ack_inflight"])

    def test_trace_reuse_and_reproducibility(self):
        c = Config(seed=42, loss=0.3, jitter=0.1)
        trajectory, channel = make_trajectory(c, "random_maneuver"), make_channel(c)
        self.assertEqual(trajectory, make_trajectory(c, "random_maneuver"))
        self.assertEqual(channel, make_channel(c))
        a = simulate(c, "error_age", trajectory, channel)
        self.assertEqual(a, simulate(c, "error_age", trajectory, channel))
        self.assertEqual(channel, make_channel(c))

    def test_bad_configuration_rejected(self):
        for kw in ({"dt":0}, {"loss":1.1}, {"duration":1.005}, {"rate_bps":-1}):
            with self.assertRaises(ValueError):
                Config(**kw)


if __name__ == "__main__":
    unittest.main()
