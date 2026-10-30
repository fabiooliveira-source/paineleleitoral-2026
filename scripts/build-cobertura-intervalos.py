"""Cobertura experimental de intervalos bootstrap do estimador existente (16×5)."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import pathlib,sys,json,gzip,base64,time,hashlib
import numpy as np
root=pathlib.Path('.').resolve();sys.path.insert(0,str(root));from inferencia_eleitoral import solve
raw=json.loads(gzip.decompress((root.parent/'model-input.json.gz').read_bytes()));allX=np.asarray(raw['X16'],float);clusters=np.asarray(raw['C']);del raw
ids,inv=np.unique(clusters,return_inverse=True);counts=np.bincount(inv);eligible=np.flatnonzero((counts>=8)&np.asarray([not s.startswith('ZZ:')for s in ids]));rng=np.random.default_rng(20261029);chosen=rng.choice(eligible,150,replace=False);indices=[]
for c in chosen:
 idx=np.flatnonzero(inv==c);indices.extend(rng.choice(idx,8,replace=False).tolist())
X=allX[indices];selectedClusters=clusters[indices];del allX,clusters
ids,clusterIndex=np.unique(selectedClusters,return_inverse=True);M=len(ids);N=X.sum(axis=1);Gcluster=np.zeros((M,16,16));clusterN=np.bincount(clusterIndex,weights=N);Gi=X[:,:,None]*X[:,None,:]/N[:,None,None];np.add.at(Gcluster,clusterIndex,Gi);origin=X.sum(axis=0);assert (origin>0).all()
pkg=json.loads((root/'dados/2026/inferencia-resultados.json').read_text(encoding='utf8'));published=json.loads(gzip.decompress(base64.b64decode(pkg['dados'])))['territories']['BR'];P0=.8*np.asarray(published['rates'])+.2/5;assert np.max(abs(P0.sum(axis=1)-1))<1e-6
composition=X[:,0]/N;marker=(composition-composition.mean())/composition.std();marker=np.clip(marker,-1.5,1.5);direction=np.array([1,-1,.15,-.1,.05]);scenarios={};R=100;B=100;started=time.time()
def fit(G,H,start=None):
 active=np.diag(G)>0;result=np.full((16,5),np.nan);result[active]=solve(G[active][:,active],H[active],start=start[active]if start is not None else None);return result
for scenario in ['homogeneo','heterogeneo']:
 P=np.broadcast_to(P0,(len(X),16,5)).copy()
 if scenario=='heterogeneo':
  logits=np.log(P)+.8*marker[:,None,None]*direction[None,None,:];P=np.exp(logits-logits.max(axis=2,keepdims=True));P/=P.sum(axis=2,keepdims=True)
 truth=(X[:,:,None]*P).sum(axis=0)/origin[:,None];covered=np.zeros((16,5),int);valid=np.zeros((16,5),int);width=np.zeros((16,5));bias=np.zeros((16,5));repCoverage=[];bootFailures=0;pointFailures=0;validBootCounts=[];generator=np.random.default_rng(20261029+(0 if scenario=='homogeneo'else 10000))
 for rep in range(R):
  Y=np.zeros((len(X),5))
  for r in range(16):Y+=np.asarray([generator.multinomial(int(n),p)for n,p in zip(X[:,r],P[:,r])])
  assert np.array_equal(Y.sum(axis=1),N);Hcluster=np.zeros((M,16,5));Hi=X[:,:,None]*Y[:,None,:]/N[:,None,None];np.add.at(Hcluster,clusterIndex,Hi);G=Gcluster.sum(axis=0)/N.sum();H=Hcluster.sum(axis=0)/N.sum()
  try:point=fit(G,H)
  except RuntimeError:pointFailures+=1;continue
  boot=[]
  for b in range(B):
   multiplicities=generator.multinomial(M,np.full(M,1/M));total=multiplicities@clusterN;g=np.einsum('m,mij->ij',multiplicities,Gcluster)/total;h=np.einsum('m,mij->ij',multiplicities,Hcluster)/total
   try:boot.append(fit(g,h,start=point))
   except RuntimeError:bootFailures+=1
  validBootCounts.append(len(boot))
  if len(boot)<80:continue
  sample=np.asarray(boot);enough=np.isfinite(sample).sum(axis=0)>=80;low,high=np.nanquantile(sample,[.025,.975],axis=0);hits=(low<=truth)&(truth<=high)&enough;covered+=hits;valid+=enough;width+=np.where(enough,100*(high-low),0);bias+=np.where(enough,100*(point-truth),0);repCoverage.append(float(hits.sum()/enough.sum()))
  if (rep+1)%10==0:print(scenario,rep+1,'/',R,'cobertura',round(100*covered.sum()/max(1,valid.sum()),2),'tempo',round(time.time()-started,1),flush=True)
 cells=[]
 for i,name in enumerate(published['origins']):
  row=[]
  for j,dest in enumerate(published['destinations']):
   n=int(valid[i,j]);h=int(covered[i,j]);p=h/n if n else None
   if n:
    z=1.959963984540054;center=(p+z*z/(2*n))/(1+z*z/n);half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n);interval=[100*max(0,center-half),100*min(1,center+half)]
   else:interval=None
   row.append({'covered':h,'valid_repetitions':n,'coverage_pct':100*p if p is not None else None,'coverage_wilson95':interval,'mean_width_pp':float(width[i,j]/n)if n else None,'bias_pp':float(bias[i,j]/n)if n else None,'generating_rate_pct':float(100*truth[i,j])})
  cells.append(row)
 scenarios[scenario]={'cells':cells,'macro_coverage_pct':float(100*covered.sum()/valid.sum()),'macro_mc_se_pp':float(100*np.std(repCoverage,ddof=1)/np.sqrt(len(repCoverage))),'valid_cell_intervals':int(valid.sum()),'planned_cell_intervals':R*16*5,'point_fit_failures':pointFailures,'bootstrap_fit_failures':bootFailures,'min_successful_bootstraps':min(validBootCounts)if validBootCounts else 0,'mean_successful_bootstraps':float(np.mean(validBootCounts))if validBootCounts else 0,'replicate_coverage_pct':[100*v for v in repCoverage]}
output={'source_rates_sha256':hashlib.sha256((root/'dados/2026/inferencia-resultados.json').read_bytes()).hexdigest(),'source_compositions_sha256':hashlib.sha256(gzip.decompress((root.parent/'model-input.json.gz').read_bytes())).hexdigest(),'repetitions':R,'bootstrap_repetitions':B,'nominal_pct':95,'sections':len(X),'municipalities':M,'origins':published['origins'],'destinations':published['destinations'],'origin_totals':origin.astype(int).tolist(),'sample_municipalities':ids.tolist(),'sample_sha256':hashlib.sha256(json.dumps(indices,separators=(',',':')).encode()).hexdigest(),'scenarios':scenarios,'method':'Estimador WLS restrito 16×5 de inferencia_eleitoral.py, sem ridge, mesmo núcleo e bootstrap municipal por percentis 2,5/97,5. Amostra fixa: 150 municípios com pelo menos oito seções elegíveis, oito seções sorteadas por município; semente 20261029. Em cada cenário, 100 conjuntos de destinos multinomiais sintéticos e 100 reamostragens de municípios por conjunto. Células precisam de pelo menos 80 ajustes bootstrap finitos. Taxa verdadeira é a taxa geradora média ponderada pelos totais da própria origem, não o fluxo realizado aleatório.','scenario_definitions':{'homogeneo':'Taxas constantes em todas as seções. Matriz publicada suavizada: 80% da taxa WLS integral + 20% de distribuição uniforme. É uma escolha artificial para o experimento, sem afirmar novas transferências reais.','heterogeneo':'Taxas artificiais variam com a composição inicial das seções: log-taxas recebem 0,8 × marcador padronizado/truncado da participação inicial de Lula nos aptos × vetor [1; −1; 0,15; −0,1; 0,05], e são renormalizadas por origem. Viola a hipótese de taxas homogêneas. Não é um efeito causal estimado do perfil eleitoral.'},'limits':'A cobertura mede desempenho neste desenho simulado com composições estáticas reais. Não calibra automaticamente os intervalos publicados para o Brasil completo, não identifica transferências reais e não fornece probabilidade de vitória. Wilson 95% refere-se à incerteza Monte Carlo da cobertura por célula, não à taxa de transferência. Erro Monte Carlo macro é calculado entre repetições, respeitando a dependência entre células.'}
(root/'dados/cobertura_intervalos.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf8');print('Cobertura concluída',{k:v['macro_coverage_pct']for k,v in scenarios.items()},'segundos',time.time()-started,flush=True)
