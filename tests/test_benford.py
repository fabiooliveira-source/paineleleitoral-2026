import importlib.util
from pathlib import Path
import unittest
import numpy as np
from scipy.stats import chisquare

spec=importlib.util.spec_from_file_location('benford',Path(__file__).parents[1]/'scripts/aplicar_benford.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

class TestBenford(unittest.TestCase):
    def test_probabilities(self):
        for digit in [1,2]: self.assertAlmostEqual(sum(b.probabilities(digit)),1,12)
        self.assertAlmostEqual(b.probabilities(1)[0],np.log10(2),12)

    def test_zero_and_digit_boundaries(self):
        values=[0,1,9,10,99,100,999]
        a=b.diagnose(values,1);c=b.diagnose(values,2)
        self.assertEqual(a['counts'],[3,0,0,0,0,0,0,0,3])
        self.assertEqual(c['counts'],[2,0,0,0,0,0,0,0,0,2])
        self.assertEqual(c['n'],4);self.assertIsNone(c['p_nominal'])
        self.assertEqual(a['zeros'],1)
        self.assertEqual(b.diagnose([],2)['n'],0)

    def test_independent_chisquare(self):
        a=b.diagnose(list(range(10,1000)),2)
        s=chisquare(a['counts'],a['expected_counts'])
        self.assertAlmostEqual(a['chi_square'],s.statistic,10)
        self.assertAlmostEqual(a['p_nominal'],s.pvalue,12)

    def test_holm(self):
        rows=[{'p_nominal':.04},{'p_nominal':None},{'p_nominal':.001},{'p_nominal':.02}]
        self.assertEqual(b.holm(rows),3)
        np.testing.assert_allclose([r['p_holm'] for r in rows if r['p_nominal'] is not None],[.04,.003,.04])

if __name__=='__main__': unittest.main()
