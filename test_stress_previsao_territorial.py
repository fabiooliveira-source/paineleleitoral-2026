"""Synthetic projection stress tests; NOT historical forecast validation."""
import json,tempfile,unittest
from pathlib import Path
import numpy as np,pandas as pd
from previsao_territorial import run
def sections(n=40):
 rows=[]
 for i in range(n):
  rows.append(dict(time=pd.Timestamp('2026-10-25T17:00:00Z')+pd.Timedelta(minutes=i//4),uf=['BA','SP'][i%2],codigo_municipio_tse=str(i%8).zfill(5),aptos_2t=200,lula_1t=60,flavio_1t=50,nominais_1t=150,nominais_2t=160,lula_2t=85 if i%2==0 else 70,flavio_2t=75 if i%2==0 else 90))
 return pd.DataFrame(rows)
class ProjectionStress(unittest.TestCase):
 def execute(self,d,targets=[1,5,10,50,90,100],draws=16):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.pkl';out=Path(t)/'result.json';d.to_pickle(p);run(p,out,draws,targets)
   return json.loads(out.read_text())
 def test_all_phases_finite_probabilities(self):
  r=self.execute(sections())
  self.assertEqual([x['target'] for x in r['ticks']],[1,5,10,50,90,100])
  for tick in r['ticks']:
   for mode in tick['models'].values():
    for s in mode['scenarios']:
     self.assertTrue(np.isfinite(s['share_lula_median']))
     self.assertAlmostEqual(s['p_lula']+s['p_flavio']+s['p_tie'],1)
 def test_final_100_exact_counts(self):
  d=sections();r=self.execute(d,[100])
  t=r['ticks'][0]
  self.assertEqual(t['observed_lula'],int(d.lula_2t.sum()))
  self.assertEqual(t['observed_flavio'],int(d.flavio_2t.sum()))
  self.assertEqual(t['remaining_electorate'],0)
  for mode in t['models'].values():
   for s in mode['scenarios']:
    self.assertEqual(s['projected_lula_median'],int(d.lula_2t.sum()))
    self.assertEqual(s['projected_flavio_median'],int(d.flavio_2t.sum()))
 def test_simultaneous_time_order_invariance(self):
  d=sections();r1=self.execute(d,[1,5,50,100]);r2=self.execute(d.sample(frac=1,random_state=8),[1,5,50,100])
  for a,b in zip(r1['ticks'],r2['ticks']):
   self.assertEqual(a['observed_lula'],b['observed_lula'])
   self.assertEqual(a['observed_flavio'],b['observed_flavio'])
   self.assertEqual(a['remaining_electorate'],b['remaining_electorate'])
 def test_empty_rejected(self):
  with self.assertRaisesRegex(ValueError,'vazia'):self.execute(sections(0))
 def test_invalid_draws_rejected(self):
  with self.assertRaisesRegex(ValueError,'draws'):self.execute(sections(),[1],0)
 def test_invalid_percent_rejected(self):
  with self.assertRaisesRegex(ValueError,'Percentual'):self.execute(sections(),[0])
if __name__=='__main__':unittest.main()
