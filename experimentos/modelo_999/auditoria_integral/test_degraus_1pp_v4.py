import unittest
from avaliar_degraus_1pp_v4 import scan,run
class StepsTests(unittest.TestCase):
 def test_exact_steps(self):
  rows=scan(0,0)['stages'];self.assertEqual([x['target_pct'] for x in rows],list(range(99,0,-1)))
 def test_no_trials_no_positive_certificate(self):self.assertIsNone(scan(0,0)['highest_supported_target_pct'])
 def test_one_success_only_five_under_binomial_assumptions(self):self.assertEqual(scan(1,1)['highest_supported_target_pct'],5)
 def test_zero_success_not_supported(self):self.assertIsNone(scan(0,10)['highest_supported_target_pct'])
 def test_existing_scope_unchanged(self):
  d=run();self.assertTrue(d['model_unchanged']);self.assertEqual(d['independent_external_presidential_trials'],0);self.assertFalse(d['certification_granted'])
if __name__=='__main__':unittest.main()
