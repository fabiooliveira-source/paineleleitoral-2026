import unittest,pathlib,json,tempfile,copy
from executar_v4 import build,main
ROOT=pathlib.Path(__file__).resolve().parent
class IntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.replay=json.loads((ROOT/'entradas_pareadas_v4_2020.json').read_text())
 def test_explicit_checkpoint_required(self):
  with self.assertRaises(ValueError):build(self.replay)
 def test_output_matches_qualified_checkpoint(self):
  out=build(self.replay,5);expected=json.loads((ROOT/'resultado_v4_2020.json').read_text())['checkpoints'][0]
  self.assertAlmostEqual(out['projection']['share_a_pct'],expected['estimate_a_pct']);self.assertFalse(out['operational_approved']);self.assertIsNone(out['projection']['probability_a'])
 def test_future_checkpoints_do_not_change_forecast(self):
  changed=copy.deepcopy(self.replay)
  for x in changed['checkpoints'][1:]:x['current']['votes_a']=9999999999
  self.assertEqual(build(changed,5)['projection'],build(self.replay,5)['projection'])
 def test_duplicate_checkpoint_rejected(self):
  d=copy.deepcopy(self.replay);d['checkpoints'].append(d['checkpoints'][0])
  with self.assertRaises(ValueError):build(d,5)
 def test_incomplete_ledger_exports_no_projection(self):
  d=copy.deepcopy(self.replay);d['checkpoints'][0]['ledger'].pop();out=build(d,5)
  self.assertEqual(out['status'],'ABSTAIN');self.assertIsNone(out['projection']['share_a_pct'])
 def test_cli_success(self):
  with tempfile.TemporaryDirectory() as folder:
   src=pathlib.Path(folder)/'input.json';dst=pathlib.Path(folder)/'output.json';src.write_text(json.dumps(self.replay))
   self.assertEqual(main(['--input',str(src),'--output',str(dst),'--checkpoint','5']),0);self.assertEqual(json.loads(dst.read_text())['status'],'ESTIMATED')
 def test_error_replaces_stale_projection(self):
  with tempfile.TemporaryDirectory() as folder:
   src=pathlib.Path(folder)/'bad.json';dst=pathlib.Path(folder)/'output.json';src.write_text('{');dst.write_text('{"projection":{"share_a_pct":99}}')
   self.assertEqual(main(['--input',str(src),'--output',str(dst)]),2);result=json.loads(dst.read_text());self.assertEqual(result['status'],'ERROR');self.assertIsNone(result['projection']['share_a_pct'])
 def test_invalid_timestamp_clears_output(self):
  with tempfile.TemporaryDirectory() as folder:
   src=pathlib.Path(folder)/'input.json';dst=pathlib.Path(folder)/'output.json';d=copy.deepcopy(self.replay);d['checkpoints'][0]['current']['timestamp']=None;src.write_text(json.dumps(d));dst.write_text('{"projection":{"share_a_pct":99}}')
   self.assertEqual(main(['--input',str(src),'--output',str(dst),'--checkpoint','5']),2);self.assertIsNone(json.loads(dst.read_text())['projection']['share_a_pct'])
 def test_cannot_overwrite_input(self):
  with tempfile.TemporaryDirectory() as folder:
   src=pathlib.Path(folder)/'input.json';src.write_text('{}')
   with self.assertRaises(SystemExit):main(['--input',str(src),'--output',str(src)])
   self.assertEqual(src.read_text(),'{}')
if __name__=='__main__':unittest.main()
