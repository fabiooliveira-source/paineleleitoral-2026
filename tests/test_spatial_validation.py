import pathlib,sys,numpy as np
sys.path.insert(0,str(pathlib.Path('scripts').resolve()))
from spatial_validation_core import fit_predict
rng=np.random.default_rng(51);x=rng.normal(size=(80,4));y=np.clip(.5+.05*x[:,0]-.03*x[:,2],0,1);w=rng.integers(50,600,size=80).astype(float);train=np.arange(80)<55;dummies=np.column_stack([np.arange(80)<40,np.arange(80)>=40,np.zeros(80)]).astype(float)
p,c=fit_predict(x,y,w,train,dummies);changed=y.copy();changed[~train]=rng.random((~train).sum());q,d=fit_predict(x,changed,w,train,dummies);assert np.array_equal(p,q), 'Resultado oculto alterou o treino'
w2=w.copy();w2[~train]*=10000;r,e=fit_predict(x,y,w2,train,dummies);assert np.array_equal(p,r), 'Peso de teste alterou o treino'
np.testing.assert_allclose(c['means'],x[train].mean(axis=0));np.testing.assert_allclose(c['std'],x[train].std(axis=0));assert max(abs(p-y))<1e-5;assert c['uf_effects_pp'][-1]==0
x2=np.column_stack([x[:,0],np.ones(80)]);p,c=fit_predict(x2,y,w,train,dummies);assert np.isfinite(p).all();assert c['std'][1]==1
print('Separação de alvos/pesos do teste, padronização no treino, UF ausente e covariável constante: OK')

import json
from scipy.stats import binomtest
c=json.loads(pathlib.Path('dados/cobertura_intervalos.json').read_text(encoding='utf8'))
for scenario in c['scenarios'].values():
 for row in scenario['cells']:
  for cell in row:
   if cell['valid_repetitions']:
    ci=binomtest(cell['covered'],cell['valid_repetitions']).proportion_ci(method='wilson');np.testing.assert_allclose(cell['coverage_wilson95'],[ci.low*100,ci.high*100],atol=1e-9)
print('Intervalos Wilson conferidos independentemente com SciPy: OK')
