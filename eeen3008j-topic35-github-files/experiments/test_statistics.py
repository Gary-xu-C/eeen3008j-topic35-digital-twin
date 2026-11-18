import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'.deps'))
try:
    from analyze_results import choose,bootstrap
    import numpy as np
except ImportError:
    choose=None

@unittest.skipIf(choose is None,'install analysis dependencies first')
class StatisticalChecks(unittest.TestCase):
    def test_tuning_budget_and_no_feasible(self):
        rows=[dict(point_id='a',bytes_per_s=10,rmse_m=2),dict(point_id='b',bytes_per_s=20,rmse_m=1)]
        self.assertEqual(choose(rows,15),'a');self.assertEqual(choose(rows,25),'b')
        self.assertIsNone(choose(rows,5))
    def test_bootstrap_constant_and_paired_difference(self):
        idx=np.random.default_rng(3).integers(0,30,(10000,30))
        self.assertEqual(bootstrap([2]*30,idx),(2,2,2))
        a=np.arange(30);b=a+1
        self.assertEqual(bootstrap(b-a,idx),(1,1,1))

if __name__=='__main__':unittest.main()
