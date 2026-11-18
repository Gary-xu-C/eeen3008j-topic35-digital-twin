"""Topic 35 v0.2: slotted stop-and-wait telemetry; Python standard library only."""
from dataclasses import dataclass, asdict
import math
import random

VERSION = "0.2"
POLICIES = ("periodic", "age", "error", "error_age")


@dataclass(frozen=True)
class Config:
    dt: float = 0.01
    duration: float = 10.0
    period: float = 1.0
    max_age: float = 1.0
    error_threshold: float = 0.2
    tolerance: float = 0.5
    rate_bps: float | None = 3200.0  # None = ideal, zero service time (unit checks)
    data_bytes: int = 32
    ack_bytes: int = 16
    delay: float = 0.05
    jitter: float = 0.0
    ack_delay: float = 0.02
    loss: float = 0.0
    seed: int = 0

    def __post_init__(self):
        for name in ("dt", "duration", "period", "max_age"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(name)
        for name in ("duration", "period", "max_age"):
            n = getattr(self, name) / self.dt
            if not math.isclose(n, round(n), abs_tol=1e-9):
                raise ValueError(name + " must be a whole number of slots")
        if not 0 <= self.loss <= 1:
            raise ValueError("loss")
        if any(not math.isfinite(x) or x < 0 for x in
               (self.delay, self.jitter, self.ack_delay, self.error_threshold, self.tolerance)):
            raise ValueError("negative/nonfinite parameter")
        if self.rate_bps is not None and (not math.isfinite(self.rate_bps) or self.rate_bps <= 0):
            raise ValueError("rate_bps")
        if any(not isinstance(x, int) or x <= 0 for x in (self.data_bytes, self.ack_bytes)):
            raise ValueError("packet size")


@dataclass(frozen=True)
class Sample:
    generation: int
    position: float
    velocity: float


def predict(sample, k, dt):
    return sample.position + sample.velocity * (k - sample.generation) * dt


def adopt(current, incoming):
    """Reject duplicate/old generation timestamps."""
    return incoming if incoming.generation > current.generation else current


def slots(seconds, dt):
    return max(0, math.ceil(seconds / dt - 1e-12))


def make_trajectory(c, scenario="constant", change_time=4.3, jump=2.0):
    """Analytic, continuous position; velocity is right-continuous at a jump."""
    n = round(c.duration / c.dt)
    if scenario not in ("constant", "maneuver", "acceleration", "random_maneuver"):
        raise ValueError(scenario)
    rng = random.Random(c.seed + 1000003)
    changes = []
    if scenario == "maneuver":
        changes = [(change_time, jump)]
    if scenario == "random_maneuver":
        # One random signed velocity increment in each 2 s interval, away from boundaries.
        for start in range(2, math.ceil(c.duration), 2):
            t = round((start + rng.uniform(0.1, 1.8)) / c.dt) * c.dt
            changes.append((t, rng.choice((-jump, jump))))
    positions, velocities = [], []
    for k in range(n):
        t = k * c.dt
        p, v = t, 1.0
        if scenario == "acceleration":
            p, v = t + 0.5 * jump * t*t, 1 + jump*t
        else:
            for when, dv in changes:
                p += dv * max(0.0, t - when)
                if t + 1e-12 >= when:
                    v += dv
        positions.append(p)
        velocities.append(v)
    return positions, velocities


def make_channel(c):
    """Exogenous per-time-slot trace, independent of policy and number of sends."""
    rng_loss, rng_delay = random.Random(c.seed), random.Random(c.seed + 2000003)
    return [(rng_loss.random() < c.loss,
             slots(c.delay + rng_delay.random() * c.jitter, c.dt))
            for _ in range(round(c.duration / c.dt))]


def simulate(c, policy, trajectory, channel, record=True):
    if policy not in POLICIES:
        raise ValueError(policy)
    positions, velocities = trajectory
    n = round(c.duration / c.dt)
    if len(positions) != n or len(velocities) != n or len(channel) != n:
        raise ValueError("trace length")
    rx = mirror = Sample(0, positions[0], velocities[0])
    data_service = 0 if c.rate_bps is None else slots(8*c.data_bytes/c.rate_bps, c.dt)
    ack_service = 0 if c.rate_bps is None else slots(8*c.ack_bytes/c.rate_bps, c.dt)
    ack_prop = slots(c.ack_delay, c.dt)
    timeout_span = data_service + slots(c.delay+c.jitter, c.dt) + ack_service + ack_prop + 1
    pending = None
    events, trace = [], []
    counts = dict(attempts=0, delivered=0, accepted=0, stale=0, lost=0,
                  ack_generated=0, ack_delivered=0, timeouts=0)

    def log(k, kind, **info):
        if record:
            events.append(dict(slot=k, time_s=k*c.dt, event=kind, **info))

    def process(k):
        nonlocal pending, rx, mirror
        if pending is None:
            return
        s = pending["sample"]
        if not pending["arrived"] and pending["arrival"] <= k:
            pending["arrived"] = True
            if pending["lost"]:
                counts["lost"] += 1
                log(k, "data_lost", generation_slot=s.generation)
            else:
                counts["delivered"] += 1
                newer = s.generation > rx.generation
                rx = adopt(rx, s)
                counts["accepted" if newer else "stale"] += 1
                counts["ack_generated"] += 1
                pending["ack_at"] = k + ack_service + ack_prop
                log(k, "data_received", generation_slot=s.generation, accepted=newer)
                log(k, "ack_generated", generation_slot=s.generation, bytes=c.ack_bytes)
        if pending["ack_at"] is not None and pending["ack_at"] <= k:
            mirror = adopt(mirror, s)  # cached payload indexed by ACK sequence
            counts["ack_delivered"] += 1
            log(k, "ack_received", generation_slot=s.generation)
            pending = None
        elif pending["timeout"] <= k:
            counts["timeouts"] += 1
            log(k, "timeout", generation_slot=s.generation)
            pending = None

    error2 = aoi_sum = max_aoi = 0.0
    over = eligible = 0
    period_slots = round(c.period/c.dt)
    for k in range(n):
        process(k)
        mirror_p = predict(mirror, k, c.dt)
        trigger_error = abs(positions[k] - mirror_p)
        sender_age = (k-mirror.generation)*c.dt
        busy = pending is not None
        if not busy:
            eligible += 1
            # Validation-only invariant; trigger still uses the ACK mirror alone.
            assert rx == mirror, "receiver/mirror differ at eligible decision"
        if policy == "periodic":
            due = k % period_slots == 0
        elif policy == "age":
            due = sender_age + 1e-12 >= c.max_age
        elif policy == "error":
            due = trigger_error > c.error_threshold + 1e-12
        else:
            due = trigger_error > c.error_threshold + 1e-12 or sender_age + 1e-12 >= c.max_age
        # k=0 is a shared, exact initial state, not a free recurring update.
        if k > 0 and due and not busy:
            s = Sample(k, positions[k], velocities[k])
            failed, delay_slots = channel[k]  # hidden network state, never used by trigger
            pending = dict(sample=s, lost=failed, arrival=k+data_service+delay_slots,
                           arrived=False, ack_at=None, timeout=k+timeout_span)
            counts["attempts"] += 1
            log(k, "send", generation_slot=k, bytes=c.data_bytes,
                trigger_error_m=trigger_error, sender_age_s=sender_age)
            process(k)  # permits the analytic zero-service/zero-delay case
        estimate = predict(rx, k, c.dt)
        error = abs(positions[k]-estimate)
        aoi = (k-rx.generation)*c.dt
        error2 += error*error
        aoi_sum += aoi
        max_aoi = max(max_aoi, aoi)
        over += error > c.tolerance + 1e-12
        if record:
            trace.append(dict(time_s=k*c.dt, position_m=positions[k], velocity_m_s=velocities[k],
                              estimate_m=estimate, error_m=abs(positions[k]-estimate),
                              aoi_s=(k-rx.generation)*c.dt,
                              sender_estimate_m=predict(mirror, k, c.dt),
                              sender_age_s=(k-mirror.generation)*c.dt,
                              decision_error_m=trigger_error, busy_before_decision=int(busy)))
    counts["data_inflight"] = int(pending is not None and not pending["arrived"])
    counts["ack_inflight"] = counts["ack_generated"] - counts["ack_delivered"]
    assert counts["attempts"] == counts["lost"] + counts["delivered"] + counts["data_inflight"]
    assert counts["delivered"] == counts["accepted"] + counts["stale"]
    data_bytes = counts["attempts"] * c.data_bytes
    ack_bytes = counts["ack_generated"] * c.ack_bytes
    metrics = dict(policy=policy, eligible_decisions=eligible, decision_mismatches=0, **counts, rmse_m=math.sqrt(error2/n),
                   over_tolerance_s=over*c.dt, over_tolerance_fraction=over/n,
                   mean_aoi_s=aoi_sum/n,
                   max_aoi_s=max_aoi,
                   data_bytes=data_bytes, ack_bytes=ack_bytes, total_bytes=data_bytes+ack_bytes,
                   bytes_per_s=(data_bytes+ack_bytes)/c.duration,
                   reserved_service_s=(counts["attempts"]*data_service + counts["ack_generated"]*ack_service)*c.dt)
    return dict(metrics=metrics, trace=trace, events=events, config=asdict(c), version=VERSION)
