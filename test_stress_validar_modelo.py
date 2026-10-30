"""Deterministic stress and adversarial tests of prediction validator."""
import unittest
import numpy as np
import pandas as pd
from validar_modelo import validar

def fixture(n=1000):
 rng=np.random.default_rng(20261030)
 ids=np.arange(n).astype(str)
 p=pd.DataFrame({'id':ids,'probabilidade':rng.uniform(0,1,n),'estimativa':rng.normal(100,20,n),'realizado_em':['2026-10-25T18:00:00Z']*n,'informacao_ate':['2026-10-25T17:59:00Z']*n})
 o=pd.DataFrame({'id':ids,'resultado':rng.integers(0,2,n),'valor_final':rng.normal(100,20,n)})
 return p,o
class StressValidation(unittest.TestCase):
 def test_10000_deterministic(self):
  p,o=fixture(10000)
  a=validar(p,o);b=validar(p.sample(frac=1,random_state=13),o.sample(frac=1,random_state=7))
  self.assertEqual(a['n'],10000)
  for metric in ['brier_score','mae_estimativa','rmse_estimativa','vies_medio']:
   self.assertAlmostEqual(a[metric],b[metric],places=9)
 def test_extreme_probabilities(self):
  p,o=fixture(10);p['probabilidade']=[0,1]*5
  r=validar(p,o);self.assertTrue(0<=r['brier_score']<=1)
 def test_future_information_rejected(self):
  p,o=fixture(10);p.loc[0,'informacao_ate']='2026-10-25T18:01:00Z'
  with self.assertRaisesRegex(ValueError,'Vazamento temporal'):validar(p,o)
 def test_missing_prediction_rejected(self):
  p,o=fixture(10)
  with self.assertRaises(ValueError):validar(p.iloc[:-1],o)
 def test_duplicate_ids_rejected(self):
  p,o=fixture(10);p.loc[1,'id']=p.loc[0,'id']
  with self.assertRaises(ValueError):validar(p,o)
 def test_nonfinite_rejected(self):
  p,o=fixture(10);p.loc[0,'probabilidade']=np.inf
  with self.assertRaises(ValueError):validar(p,o)
 def test_negative_probability_rejected(self):
  p,o=fixture(10);p.loc[0,'probabilidade']=-.01
  with self.assertRaises(ValueError):validar(p,o)
 def test_missing_timestamps_rejected(self):
  p,o=fixture(10);p.loc[0,'realizado_em']=None
  with self.assertRaises(ValueError):validar(p,o)
 def test_invalid_outcome_rejected(self):
  p,o=fixture(10);o.loc[0,'resultado']=2
  with self.assertRaises(ValueError):validar(p,o)
 def test_identical_time_not_proof_of_provenance(self):
  p,o=fixture(10);p['informacao_ate']=p['realizado_em']
  r=validar(p,o)
  self.assertIn('snapshots históricos',r['aviso'])
if __name__=='__main__':unittest.main()
