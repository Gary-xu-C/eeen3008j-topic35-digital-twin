import unittest
from dataclasses import replace
import simulator as old
import simulator_v02 as new
from scan_v02 import points, point_id

class V02Checks(unittest.TestCase):
    def test_E_constant_zero_cost(self):
        c=new.Config(loss=.3,ack_delay=.8)
        m=new.simulate(c,'error',new.make_trajectory(c),new.make_channel(c))['metrics']
        self.assertEqual(m['attempts'],0); self.assertEqual(m['total_bytes'],0)
        self.assertLess(m['rmse_m'],1e-12)

    def test_original_metrics_preserved_and_record_modes_identical(self):
        for seed in range(3):
            c=old.Config(seed=seed,loss=.3,ack_delay=.8)
            for policy in old.POLICIES:
                tr=old.make_trajectory(c,'random_maneuver'); ch=old.make_channel(c)
                a=old.simulate(c,policy,tr,ch)['metrics']
                b=new.simulate(c,policy,tr,ch)['metrics']
                for key in a: self.assertEqual(a[key],b[key])
                self.assertEqual(b,new.simulate(c,policy,tr,ch,False)['metrics'])

    def test_all_eligible_points_consistent_and_charged(self):
        for loss in (0,.3,1):
            for ack in (.02,.2,.8):
                c=new.Config(loss=loss,ack_delay=ack)
                for policy in new.POLICIES:
                    r=new.simulate(c,policy,new.make_trajectory(c,'maneuver'),new.make_channel(c))
                    m=r['metrics']; self.assertEqual(m['decision_mismatches'],0)
                    self.assertEqual(m['total_bytes'],32*m['attempts']+16*m['ack_generated'])
                    for row in r['trace']:
                        if not row['busy_before_decision']:
                            self.assertAlmostEqual(row['sender_estimate_m'],row['estimate_m'])

    def test_E_ignores_age_and_sweep_unique(self):
        c=new.Config(max_age=.1,error_threshold=.2)
        tr=new.make_trajectory(c,'maneuver'); ch=new.make_channel(c)
        a=new.simulate(c,'error',tr,ch)['metrics']
        b=new.simulate(replace(c,max_age=4),'error',tr,ch)['metrics']
        self.assertEqual(a,b)
        self.assertEqual(len(points()),40); self.assertEqual(len({point_id(p) for p in points()}),40)

if __name__=='__main__': unittest.main()
