import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from rateio_inclusivo import balance
class RateioTests(unittest.TestCase):
    def test_entries_exits_and_zero_categories(self):
        x=np.array([[10,0,3],[0,4,0],[2,3,0],[0,0,0]],float)
        y=np.array([[8,5],[0,4],[4,1],[0,0]],float)
        m,_=balance(x,y,np.array([[0.,1.],[1.,0.],[.5,.5]]))
        np.testing.assert_allclose(m.sum(2),x,atol=1e-7)
        np.testing.assert_allclose(m.sum(1),y,atol=1e-7)
        self.assertTrue((m>=0).all())
    def test_random_sections(self):
        rng=np.random.default_rng(7)
        truth=rng.integers(0,100,(100,7,6)).astype(float)
        x,y=truth.sum(2),truth.sum(1)
        m,_=balance(x,y,rng.random((7,6)))
        np.testing.assert_allclose(m.sum(2),x,atol=1e-7)
        np.testing.assert_allclose(m.sum(1),y,atol=1e-7)
    def test_reject_mismatched_universe(self):
        with self.assertRaises(ValueError):balance(np.array([[1.]]),np.array([[2.]]),np.ones((1,1)))
if __name__=='__main__':unittest.main()
