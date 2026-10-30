"""Diagnósticos retrospectivos estáticos; adaptações de teses, sem entrevistas."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import json,gzip,base64,pathlib,zlib,hashlib
import numpy as np
from scipy.spatial import cKDTree
from spatial_validation_core import fit_predict
root=pathlib.Path('.').resolve()
def decode(path):return json.loads(gzip.decompress(base64.b64decode(json.loads(path.read_text(encoding='utf8'))['dados'])))
source=decode(root/'dados/estudos_territoriais_pacote.json');rows=[r for r in source['rows']if r['coord']and all(v is not None and np.isfinite(v)and v>0 for v in r['ibge'])];n=len(rows);coords=np.asarray([r['coord']for r in rows]);radians=np.radians(coords);vectors=np.column_stack([np.cos(radians[:,0])*np.cos(radians[:,1]),np.cos(radians[:,0])*np.sin(radians[:,1]),np.sin(radians[:,0])]);tree=cKDTree(vectors);_,near=tree.query(vectors,k=9);neighbors=np.asarray([[j for j in ids if j!=i][:8]for i,ids in enumerate(near)]);assert neighbors.shape==(n,8)
raw=np.asarray([r['ibge']for r in rows]);local=np.column_stack([np.log10(raw[:,0]),np.log10(raw[:,1]),raw[:,2],np.log10(raw[:,3])]);spatial=local[neighbors].mean(axis=1);uf=np.asarray([r['uf']for r in rows]);states=sorted(set(uf));dummies=np.column_stack([uf==s for s in states]).astype(float);cellx=np.floor(6371*np.cos(np.radians(-15))*radians[:,1]/200).astype(int);celly=np.floor(6371*radians[:,0]/200).astype(int);blocks=[f'{a}:{b}'for a,b in zip(cellx,celly)];blockfold=np.asarray([zlib.crc32((key+'|20261029').encode())%5 for key in blocks]);randomfold=np.asarray([zlib.crc32((r['key']+'|20261029').encode())%5 for r in rows]);splits={};audit={};bits=np.zeros(n,int)
for protocol in ['municipios','blocos','buffer']:
 assignments=randomfold if protocol=='municipios'else blockfold;split=[];audit[protocol]=[]
 for f in range(5):
  test=assignments==f;eligible=~test;distance,_=cKDTree(vectors[test]).query(vectors[eligible],k=1);km=2*6371*np.arcsin(np.minimum(1,distance/2));train=eligible.copy()
  if protocol=='buffer':
   rejected=np.flatnonzero(eligible)[km<100];train[rejected]=False;bits[rejected]|=1<<f
  assert not np.any(train&test);assert train.sum()>100
  selectedDistance=km[train[eligible]];mind=float(selectedDistance.min());assert protocol!='buffer'or mind>=100-1e-8
  if protocol!='municipios':assert set(np.asarray(blocks)[train]).isdisjoint(set(np.asarray(blocks)[test]))
  split.append((train,test));audit[protocol].append({'fold':f,'train':int(train.sum()),'test':int(test.sum()),'excluded_buffer':int((~(train|test)).sum()),'train_blocks':len(set(np.asarray(blocks)[train])),'test_blocks':len(set(np.asarray(blocks)[test])),'min_train_test_km':mind,'unseen_ufs':sorted(set(uf[test])-set(uf[train]))})
 splits[protocol]=split

def design_fit(features,y,w,train):
 p,c=fit_predict(features,y,w,train,dummies);c['uf_effects_pp']=dict(zip(states,c['uf_effects_pp']));return p,c
def scores(y,p,w,mask):
 a,b,c=y[mask],p[mask],w[mask]
 if len(a)==0:return None
 return {'n':len(a),'weight':int(c.sum()),'rmse_pp':float(100*np.sqrt(np.average((b-a)**2,weights=c))),'mae_pp':float(100*np.average(abs(b-a),weights=c)),'aggregate_error_pp':float(100*np.average(b-a,weights=c))}
def moran(residual):
 z=residual-residual.mean();den=(z*z).sum();return float((z*z[neighbors].mean(axis=1)).sum()/den)if den>1e-18 else None
features={'ibge_uf':local,'slx':np.column_stack([local,spatial])};tasks={}
for yearindex,year in enumerate(source['years']):
 for kind in ['vote','abst']:
  d=np.asarray([r['years'][yearindex]for r in rows]);y=d[:,0 if kind=='vote'else 4]/d[:,2 if kind=='vote'else 3];w=d[:,2 if kind=='vote'else 3];task={'year':year,'kind':kind,'protocols':{},'full':{}}
  for protocol,split in splits.items():
   predictions={name:np.full(n,np.nan)for name in ['media','ibge_uf','slx']}
   for train,test in split:
    predictions['media'][test]=np.average(y[train],weights=w[train])
    for name,x in features.items():p,_=design_fit(x,y,w,train);predictions[name][test]=p[test]
   result={}
   for name,p in predictions.items():
    assert np.isfinite(p).all();result[name]={'national':scores(y,p,w,np.ones(n,bool)),'ufs':{state:scores(y,p,w,uf==state)for state in states},'predictions_millipp':np.rint(p*100000).astype(int).tolist()}
   task['protocols'][protocol]=result
  for name,x in features.items():
   p,coeff=design_fit(x,y,w,np.ones(n,bool));task['full'][name]={'scores':scores(y,p,w,np.ones(n,bool)),'residual_moran_i':moran(p-y),'coefficients':coeff}
  task['observed_millipp']=np.rint(y*100000).astype(int).tolist();task['weights']=w.astype(int).tolist();tasks[f'{year}_{kind}']=task;print('Validação espacial',year,kind,{k:round(v['slx']['national']['rmse_pp'],3)for k,v in task['protocols'].items()},flush=True)
output={'years':source['years'],'n':n,'excluded_from_territorial':len(source['rows'])-n,'source_sha256':hashlib.sha256((root/'dados/estudos_territoriais_pacote.json').read_bytes()).hexdigest(),'feature_names':['log₁₀ população 2022','log₁₀ densidade 2022','Alfabetização 15+ 2022','log₁₀ PIB por habitante calculado 2021'],'tasks':tasks,'audit':audit,'rows':[{'key':r['key'],'name':r['name'],'uf':r['uf'],'coord':r['coord'],'block':blocks[i],'block_fold':int(blockfold[i]),'random_fold':int(randomfold[i]),'buffer_bits':int(bits[i])}for i,r in enumerate(rows)],'methods':{'models':'Regressões lineares ponderadas pelo denominador eleitoral. Base IBGE + efeitos fixos de UF; SLX acrescenta médias das quatro covariáveis nos oito vizinhos. Somente covariáveis, nunca votos vizinhos do teste. Predições limitadas a 0–100%. Penalização numérica 1e-6, intercepto não penalizado. Médias e desvios das covariáveis estimados só no treino em cada rodada.','split':'Cinco rodadas fora do ajuste: CRC32(chave|20261029) mod 5. Blocos de aproximadamente 200 km em projeção equirretangular com paralelo de referência −15°. Protocolo buffer retira treino a menos de 100 km de qualquer posição eleitoral de teste, em esfera. Posições são médias de locais de votação de 2026, não limites municipais.','limits':'Retrospectiva dentro de cada eleição, com características IBGE de 2021/2022 e geografia de 2026 fixas. Não treina só em eleições passadas nem reproduz parciais. Covariáveis dos municípios de teste e de seus vizinhos são conhecidas, mas seus resultados não entram no ajuste. Coeficientes descrevem associação, não causalidade.','prediction_precision':'Predições e observações no pacote arredondadas a 0,001 ponto percentual; métricas são calculadas antes desse arredondamento.'}}
(root/'dados/teses_espaciais_pacote.json').write_text(json.dumps({'codificacao':'gzip+base64','dados':base64.b64encode(gzip.compress(json.dumps(output,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode(),mtime=0)).decode()},separators=(',',':')),encoding='utf8');print('Base comum',n,'blocos',len(set(blocks)),'audit',audit['buffer'],flush=True)
