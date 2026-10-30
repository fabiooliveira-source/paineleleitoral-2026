"""Testes do validador de snapshots; não substituem evidência histórica."""
import json,tempfile,unittest
from pathlib import Path
from validar_snapshots_independentes import validate

SHA='a'*64
def record(t='2026-10-25T20:00:00-03:00',sections=5,total=100,lula=600,flavio=400):
 return {'captured_at':t,'source_url':'https://example.org/captura','source_sha256':SHA,'sections_counted':sections,'sections_total':total,'lula':lula,'flavio':flavio}
class SnapshotValidationTests(unittest.TestCase):
 def check(self,rows):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'snapshots.jsonl'
   p.write_text('\\n'.join(json.dumps(x) for x in rows),encoding='utf-8')
   return validate(p)
 def test_valid_sequence_not_certified(self):
  r=self.check([record(),record('2026-10-25T20:05:00-03:00',10,100,1100,900)])
  self.assertEqual(r['snapshots'],2)
  self.assertFalse(r['source_authenticity_verified'])
  self.assertFalse(r['historical_forecast_certified'])
 def test_empty_rejected(self):
  with self.assertRaisesRegex(ValueError,'Nenhum'):self.check([])
 def test_naive_timestamp_rejected(self):
  with self.assertRaisesRegex(ValueError,'fuso'):self.check([record(t='2026-10-25T20:00:00')])
 def test_missing_sha_rejected(self):
  with self.assertRaisesRegex(ValueError,'SHA256'):self.check([dict(record(),source_sha256='abc')])
 def test_negative_votes_rejected(self):
  with self.assertRaisesRegex(ValueError,'flavio'):self.check([record(flavio=-1)])
 def test_nonmonotonic_votes_rejected(self):
  with self.assertRaisesRegex(ValueError,'diminuíram'):self.check([record(),record('2026-10-25T20:05:00-03:00',10,100,599,500)])
 def test_nonmonotonic_sections_rejected(self):
  with self.assertRaisesRegex(ValueError,'Seções contabilizadas'):self.check([record(sections=10),record('2026-10-25T20:05:00-03:00',5,100,1100,900)])
 def test_changed_denominator_rejected(self):
  with self.assertRaisesRegex(ValueError,'Total de seções'):self.check([record(),record('2026-10-25T20:05:00-03:00',10,101,1100,900)])
 def test_out_of_order_rejected(self):
  with self.assertRaisesRegex(ValueError,'fora de ordem'):self.check([record('2026-10-25T20:05:00-03:00'),record('2026-10-25T20:00:00-03:00',10,100,1100,900)])
if __name__=='__main__':unittest.main()
