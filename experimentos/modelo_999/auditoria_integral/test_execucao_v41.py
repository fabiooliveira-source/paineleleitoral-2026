import pathlib,json,tempfile,unittest,copy,datetime
from executar_v41 import main,build
ROOT=pathlib.Path(__file__).resolve().parent
class StatefulTests(unittest.TestCase):
 def setUp(self):
  d=json.loads((ROOT/'entradas_pareadas_v4_2022.json').read_text());x=d['checkpoints'][0];self.doc={'current':x['current'],'reference':d['reference'],'ledger':x['ledger']}
 def test_single_snapshot_requires_state(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);(p/'input.json').write_text(json.dumps(self.doc));self.assertEqual(main(['--input',str(p/'input.json'),'--output',str(p/'out.json')]),2)
 def test_revision_clears_forecast_and_preserves_state(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'input.json';out=p/'out.json';state=p/'state.json';src.write_text(json.dumps(self.doc));argv=['--input',str(src),'--output',str(out),'--state',str(state)]
   self.assertEqual(main(argv),0);before=state.read_text();revised=copy.deepcopy(self.doc);stamp=(datetime.datetime.fromisoformat(revised['current']['timestamp'])+datetime.timedelta(seconds=1)).isoformat();revised['current'].update(timestamp=stamp,available_at=stamp);revised['current']['votes_a']-=1
   for row in revised['ledger']:row.update(timestamp=stamp,available_at=stamp)
   next(r for r in revised['ledger'] if r['votes_a']>0)['votes_a']-=1;src.write_text(json.dumps(revised));self.assertEqual(main(argv),0);d=json.loads(out.read_text());self.assertEqual(d['status'],'ABSTAIN');self.assertIsNone(d['projection']['share_a_pct']);self.assertIsNone(d['conditional_bounds']['conditional_winner']);self.assertEqual(before,state.read_text())
 def test_state_cannot_overwrite_input(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);src=p/'input.json';src.write_text(json.dumps(self.doc))
   with self.assertRaises(SystemExit):main(['--input',str(src),'--output',str(p/'out.json'),'--state',str(src)])
 def test_regular_prediction_unchanged(self):
  from executar_v4 import build as old
  self.assertEqual(build(self.doc)['projection'],old(self.doc)['projection'])
if __name__=='__main__':unittest.main()
