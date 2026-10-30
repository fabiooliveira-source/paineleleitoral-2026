import unittest,itertools,datetime
from preditor_causal_v4 import predict,deterministic_bounds
T='2022-10-30T18:00:00-03:00'
class V4Tests(unittest.TestCase):
 def setUp(self):
  self.c=dict(timestamp=T,available_at=T,votes_a=30,votes_b=40,electorate_total=300,electorate_counted=100)
  self.r={'X':dict(votes_a=100,votes_b=100,available_at='2022-10-03T00:00:00-03:00')}
  self.l=[dict(scope='X',timestamp=T,available_at=T,votes_a=30,votes_b=40,matched_first_a=20,matched_first_b=40)]
 def test_paired_ratio_control(self):
  # unseen A=(100-20)*30/20=120; B=(100-40)*40/40=60
  p=predict(self.c,self.r,self.l);self.assertAlmostEqual(p['estimate_a'],150/250)
 def test_incomplete_ledger_abstains(self):self.assertIsNone(predict(self.c,self.r,[])['estimate_a'])
 def test_delayed_ledger_abstains(self):
  self.l[0]['timestamp']=self.l[0]['available_at']='2022-10-30T17:59:00-03:00'
  self.assertEqual(predict(self.c,self.r,self.l)['reason'],'unsynchronized_ledger')
 def test_future_injection_ignored(self):
  later=dict(self.l[0],timestamp='2022-10-30T19:00:00-03:00',available_at='2022-10-30T19:00:00-03:00',votes_a=999999)
  self.assertEqual(predict(self.c,self.r,self.l),predict(self.c,self.r,self.l+[later]))
 def test_unavailable_history_abstains(self):
  self.r['X']['available_at']='2022-11-01T00:00:00-03:00';self.assertIsNone(predict(self.c,self.r,self.l)['estimate_a'])
 def test_mismatch_abstains(self):
  self.l[0]['votes_a']=31;self.assertEqual(predict(self.c,self.r,self.l)['reason'],'national_territorial_mismatch')
 def test_invalid_electorate_rejected(self):
  self.c['electorate_counted']=301
  with self.assertRaises(ValueError):predict(self.c,self.r,self.l)
 def test_first_cohort_exceeds_total_abstains(self):
  self.l[0]['matched_first_a']=101;self.assertIsNone(predict(self.c,self.r,self.l)['estimate_a'])
 def test_closed(self):
  self.c['electorate_counted']=300;self.assertAlmostEqual(predict(self.c,{},[])['estimate_a'],30/70)
 def test_conflict_abstains(self):
  conflict=dict(self.l[0],votes_a=31);self.assertIsNone(predict(self.c,self.r,self.l+[conflict])['estimate_a'])
 def test_zero_global_denominator_abstains(self):
  self.l[0]['matched_first_a']=0;self.assertEqual(predict(self.c,self.r,self.l)['reason'],'global_ratio_unidentifiable')
 def test_permutation_invariant(self):
  self.r['Y']=dict(votes_a=10,votes_b=10,available_at='2022-10-03T00:00:00-03:00');self.l.append(dict(scope='Y',timestamp=T,available_at=T,votes_a=0,votes_b=0,matched_first_a=0,matched_first_b=0))
  self.assertEqual(predict(self.c,self.r,self.l),predict(self.c,self.r,list(reversed(self.l))))
 def test_physical_cap(self):
  self.c.update(electorate_total=110,electorate_counted=100);p=predict(self.c,self.r,self.l)
  self.assertLessEqual(p['estimated_unseen_a']+p['estimated_unseen_b'],10+1e-12)
 def test_no_probability(self):self.assertIsNone(predict(self.c,self.r,self.l)['probability'])
 def test_exhaustive_bounds_and_calls(self):
  for a,b,R in itertools.product(range(8),repeat=3):
   bound=deterministic_bounds(a,b,R)
   for x in range(R+1):
    for y in range(R-x+1):
     if not a+b+x+y:continue
     truth=(a+x)/(a+b+x+y);self.assertLessEqual(bound['lower_a'],truth+1e-12);self.assertGreaterEqual(bound['upper_a'],truth-1e-12)
     if bound['conditional_winner']=='a':self.assertGreater(a+x,b+y)
     if bound['conditional_winner']=='b':self.assertGreater(b+y,a+x)
if __name__=='__main__':unittest.main()
