import unittest,pathlib,tempfile
from unittest.mock import patch
import avaliar_externos_v41_2024 as m
class CriteriaTests(unittest.TestCase):
 def setUp(self):
  self.a={'mae_pp':.2,'p95_abs_error_pp':.5,'max_abs_error_pp':1};self.b={'mae_pp':.3,'max_abs_error_pp':2};self.p=[{'winner_correct':True,'conditional_call_correct':None,'bounds_cover_target':True} for _ in range(19)]
 def test_quantile(self):self.assertAlmostEqual(m.quantile(list(range(19))),17.1)
 def test_wrong_winner_rejects(self):
  self.p[0]['winner_correct']=False;self.assertFalse(m.criteria_for(self.a,self.b,self.p,19,95)['winner_correct_at5'])
 def test_extreme_error_rejects(self):
  self.a['max_abs_error_pp']=3.1;self.assertFalse(m.criteria_for(self.a,self.b,self.p,19,95)['maximum_at_most3pp'])
 def test_missing_estimate_not_excluded(self):self.assertFalse(m.criteria_for(self.a,self.b,self.p,18,95)['all19_estimates'])
 def test_wrong_call_rejects(self):
  self.p[2]['conditional_call_correct']=False;self.assertFalse(m.criteria_for(self.a,self.b,self.p,19,95)['no_wrong_conditional_call'])
 def test_blocked_case_retained(self):
  with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',pathlib.Path(t)):
   r=m.evaluate_case('13897');self.assertEqual(r['status'],'DATA_BLOCKED');self.assertEqual(r['name'],'Fortaleza')
 def test_changed_core_rejects(self):
  with tempfile.TemporaryDirectory() as t,patch.object(m,'ROOT',pathlib.Path(t)):
   p=pathlib.Path(t);(p/'congelamento_guard_v41.json').write_text('{"core_sha256_unchanged":"invalid","files":[]}');(p/'preditor_causal_v4.py').write_text('changed')
   with self.assertRaises(AssertionError):m.run()
if __name__=='__main__':unittest.main()
