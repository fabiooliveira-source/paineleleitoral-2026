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
 def test_geographic_concentration(self):
  d=sections(40)
  # All early reporting comes from BA; SP arrives later.
  d.loc[d.uf=='BA','time']=pd.Timestamp('2026-10-25T17:00:00Z')
  d.loc[d.uf=='SP','time']=pd.Timestamp('2026-10-25T19:00:00Z')
  r=self.execute(d,[5,50,100],32)
  self.assertEqual(r['ticks'][0]['state_coverage'],1)
  self.assertEqual(r['ticks'][-1]['state_coverage'],2)
  self.assertEqual(r['ticks'][-1]['remaining_electorate'],0)
  self.assertIn('não é garantida',r['warning'])
 def test_prior_sensitivity_reported(self):
  r=self.execute(sections(),[5,50],32)
  for t in r['ticks']:
   for model in t['models'].values():
    self.assertEqual([x['prior_pseudo_sections'] for x in model['scenarios']],[2,20,100])
    self.assertEqual(model['sensitivity_p_lula'],[min(x['p_lula'] for x in model['scenarios']),max(x['p_lula'] for x in model['scenarios'])])
 def test_monte_carlo_draws_and_seed(self):
  d=sections()
  a=self.execute(d,[5,100],16)
  b=self.execute(d,[5,100],64)
  self.assertEqual(a['draws'],16)
  self.assertEqual(b['draws'],64)
  self.assertEqual(a['ticks'][-1]['observed_lula'],b['ticks'][-1]['observed_lula'])
  self.assertEqual(a['ticks'][-1]['observed_flavio'],b['ticks'][-1]['observed_flavio'])
  self.assertEqual(a['ticks'][-1]['remaining_electorate'],0)
 def test_repeated_run_deterministic(self):
  d=sections()
  a=self.execute(d,[1,5,50,100],32)
  b=self.execute(d,[1,5,50,100],32)
  self.assertEqual(a['ticks'],b['ticks'])
 def test_empty_rejected(self):
  with self.assertRaisesRegex(ValueError,'vazia'):self.execute(sections(0))
 def test_invalid_draws_rejected(self):
  with self.assertRaisesRegex(ValueError,'draws'):self.execute(sections(),[1],0)
 def test_invalid_percent_rejected(self):
  with self.assertRaisesRegex(ValueError,'Percentual'):self.execute(sections(),[0])
if __name__=='__main__':unittest.main()
