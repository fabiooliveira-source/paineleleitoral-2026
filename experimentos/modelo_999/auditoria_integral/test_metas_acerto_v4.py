import unittest,math
from avaliar_taxa_acerto_v4 import lower_exact,min_all_success_trials,evaluate
class AccuracyPolicyTests(unittest.TestCase):
 def test_no_evidence_is_not_zero_or_certified(self):self.assertIsNone(lower_exact(0,0))
 def test_all_success_one_is_not_ninetyfive(self):self.assertAlmostEqual(lower_exact(1,1),.05)
 def test_all_success_two(self):self.assertAlmostEqual(lower_exact(2,2),math.sqrt(.05))
 def test_one_of_two(self):self.assertAlmostEqual(lower_exact(1,2),1-math.sqrt(.95))
 def test_no_success(self):self.assertEqual(lower_exact(0,10),0)
 def test_minimum_zero_failure_samples(self):
  for target,expected in [(.99,299),(.98,149),(.97,99),(.96,74),(.95,59)]:
   self.assertEqual(min_all_success_trials(target),expected);self.assertGreaterEqual(lower_exact(expected,expected),target);self.assertLess(lower_exact(expected-1,expected-1),target)
 def test_invalid_counts(self):
  with self.assertRaises(ValueError):lower_exact(2,1)
 def test_no_reclassification_of_development_or_municipality(self):
  r=evaluate();self.assertEqual(r['eligible_external_presidential_elections'],0);self.assertEqual(r['targets_evaluated_pct'],[99,98,97,96,95]);self.assertIsNone(r['selected_supported_target_pct']);self.assertFalse(r['integral_certification_granted'])
if __name__=='__main__':unittest.main()
