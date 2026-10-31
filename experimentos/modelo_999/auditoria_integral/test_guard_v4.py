import unittest,pathlib,json,copy,datetime
from preditor_v4_guardado import predict_guarded
from preditor_causal_v4 import predict
ROOT=pathlib.Path(__file__).resolve().parent
class GuardTests(unittest.TestCase):
 def setUp(self):
  d=json.loads((ROOT/'entradas_pareadas_v4_2022.json').read_text());self.r=d['reference'];x=d['checkpoints'][0];self.c=x['current'];self.l=x['ledger'];t=datetime.datetime.fromisoformat(self.c['timestamp'])-datetime.timedelta(seconds=1);self.prev=dict(self.c,timestamp=t.isoformat(),available_at=t.isoformat())
 def test_all_57_original_forecasts_unchanged(self):
  for year in [2018,2022,2020]:
   d=json.loads((ROOT/f'entradas_pareadas_v4_{year}.json').read_text())
   for x in d['checkpoints']:self.assertEqual(predict(x['current'],d['reference'],x['ledger'])['estimate_a'],predict_guarded(x['current'],d['reference'],x['ledger'])['estimate_a'])
 def test_invalid_national_clock(self):
  self.c['generated_at']=self.c['timestamp'];self.c['available_at']=self.prev['timestamp'];self.assertIsNone(predict_guarded(self.c,self.r,self.l)['estimate_a'])
 def test_older_valid_receipt_is_not_generation_error(self):
  self.c['available_at']=self.prev['timestamp'];self.c['generated_at']=self.prev['timestamp'];self.assertIsNotNone(predict_guarded(self.c,self.r,self.l)['estimate_a'])
 def test_decreasing_votes_clear_call(self):
  self.prev['votes_a']+=1;p=predict_guarded(self.c,self.r,self.l,self.prev);self.assertEqual(p['reason'],'observed_counts_revised');self.assertIsNone(p['conditional_winner']);self.assertTrue(p['clear_prior_forecast'])
 def test_decreasing_counted_electorate(self):
  self.prev['electorate_counted']+=1;self.assertEqual(predict_guarded(self.c,self.r,self.l,self.prev)['reason'],'observed_counts_revised')
 def test_registry_change(self):
  self.prev['electorate_total']+=1;self.assertEqual(predict_guarded(self.c,self.r,self.l,self.prev)['reason'],'electorate_registry_changed')
 def test_stale_national_snapshot(self):
  t=datetime.datetime.fromisoformat(self.c['timestamp'])+datetime.timedelta(seconds=1);self.prev.update(timestamp=t.isoformat(),available_at=t.isoformat());self.assertEqual(predict_guarded(self.c,self.r,self.l,self.prev)['reason'],'out_of_order_national_snapshot')
 def test_same_instant_conflict(self):
  self.prev=dict(self.c,votes_a=self.c['votes_a']+1);self.assertEqual(predict_guarded(self.c,self.r,self.l,self.prev)['reason'],'conflicting_national_snapshot')
 def test_monotone_previous_accepted(self):self.assertEqual(predict_guarded(self.c,self.r,self.l,self.prev)['estimate_a'],predict(self.c,self.r,self.l)['estimate_a'])
 def test_invalid_timestamp_is_safe(self):
  self.c['timestamp']=None;self.assertIsNone(predict_guarded(self.c,self.r,self.l)['estimate_a'])
 def test_future_injection_preserves_forecast(self):
  t=datetime.datetime.fromisoformat(self.c['timestamp'])+datetime.timedelta(days=1);row=dict(self.l[0],timestamp=t.isoformat(),available_at=t.isoformat(),votes_a=999999);self.assertEqual(predict_guarded(self.c,self.r,self.l)['estimate_a'],predict_guarded(self.c,self.r,self.l+[row])['estimate_a'])
if __name__=='__main__':unittest.main()
