"""Inferência ecológica exploratória + campos de coeficientes, IDW2 e KO local.
Krigagem interpola coeficientes ecológicos estimados, não votos individuais observados.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import numpy as np,json,pathlib,inspect,hashlib,collections
from scipy.spatial import cKDTree,distance
from scipy.optimize import least_squares
import analisar_migracao_brasil as src
P=pathlib.Path(__file__).resolve().parent
protocol={'block_degrees':.5,'split':'SHA256(latitude_cell:longitude_cell)%5:0 test,1 tuning,2..4 train; same cell never split','models':['UF regularized baseline','IDW power2 log-ratio coefficients','local ordinary kriging log-ratio coefficients'],'neighbors':[8,16],'variogram':'spherical, fitted using training blocks only; standardized coefficient residual field across origins/destinations','selection':'lowest tuning weighted MAE; held-out test reported once, not selected','alpha_origin':1000,'global_EM_iterations':600,'local_EM_iterations':250,'coefficient_coordinate':'five additive log-ratios to sixth destination, clipping p>=1e-8 before transform','locations':'first-turn geographical file, no fabricated geocoding; unmapped and exterior use UF fallback'}
(P/'protocolo-espacial.json').write_text(json.dumps(protocol,indent=2)+'\n')
source=inspect.getsource(src.analyze).split(' # Cenário')[0].replace('def analyze(uf):','def extract(uf):')+'\n return a,b,[tuple(r[:3]) for r in s["linhas"] if all(r[cols["situacao_dados_"+t]]=="conferido" for t in ["1t","2t"])]\n';ns=vars(src).copy();exec(source,ns)
xs=[];ys=[];ufs=[];coords=[]
for uf in src.UFS:
 a,b,keys=ns['extract'](uf);mapping={}
 if uf!='ZZ':
  geo=json.loads((P/f'geo-{uf}.json').read_text())
  for city,locations in geo['turns']['1'].items():
   for idx,sections in locations:
    m=geo['metadata'][idx];lat,lon=m[5:7]
    if lat is None or lon is None or not (-34<=lat<=6 and -74<=lon<=-28):continue
    for row in sections:mapping[(str(city),str(m[1]),str(row[0]))]=(float(lat),float(lon))
 xs.append(a);ys.append(b);ufs.extend([uf]*len(a));coords.extend([mapping.get(tuple(map(str,k)),(np.nan,np.nan)) for k in keys]);print('geographic join',uf,len(a),sum(tuple(map(str,k)) in mapping for k in keys),flush=True)
x=np.concatenate(xs);y=np.concatenate(ys);ufs=np.array(ufs);coords=np.array(coords);mapped=np.isfinite(coords).all(axis=1)
cell=np.full(len(x),'unmapped',dtype=object)
for i in np.flatnonzero(mapped):cell[i]=str(int(np.floor(coords[i,0]/.5)))+':'+str(int(np.floor(coords[i,1]/.5)))
unique=sorted(set(cell[mapped]));cellindex={c:i for i,c in enumerate(unique)};ci=np.array([cellindex.get(c,-1) for c in cell]);splitmap={c:int(hashlib.sha256(c.encode()).hexdigest()[:8],16)%5 for c in unique};split=np.array([splitmap.get(c,-1) for c in cell]);train=split>=2;tune=split==1;test=split==0
K=x.shape[1];J=6

def fit(a,b,prior,alpha,steps):
 p=prior.copy();weights=a.sum(axis=0)
 for it in range(steps):
  mu=np.maximum(a@p,1e-100);new=(p*(a.T@(b/mu))+alpha*prior)/np.maximum(weights[:,None]+alpha,1e-100);new=np.maximum(new,1e-12);new/=new.sum(axis=1,keepdims=True);delta=float(np.max(abs(new-p)));p=new
  if delta<1e-7:break
 return p,{'iterations':it+1,'last_max_delta':delta,'converged_step_1e7':delta<1e-7}
prior=np.tile(y[train].sum(axis=0)/y[train].sum(),(K,1));globalp,gd=fit(x[train],y[train],prior,0,600);ufp={};diag={};base=np.zeros_like(y)
for uf in src.UFS:
 mask=(ufs==uf)&train
 if mask.any():p,d=fit(x[mask],y[mask],globalp,1000,250)
 else:p,d=globalp.copy(),{'fallback':'global training only; no mapped training sections in UF'}
 ufp[uf]=p;diag[uf]=d;mask=ufs==uf;base[mask]=x[mask]@p

def alr(p):
 p=np.maximum(p,1e-8);return np.log(p[:,:5]/p[:,5,None])
def inverse(z):
 z=np.column_stack([z,np.zeros(len(z))]);z-=z.max(axis=1,keepdims=True);p=np.exp(z);return p/p.sum(axis=1,keepdims=True)
def xyz(ll):
 ll=np.deg2rad(ll);return 6371*np.column_stack([np.cos(ll[:,0])*np.cos(ll[:,1]),np.cos(ll[:,0])*np.sin(ll[:,1]),np.sin(ll[:,0])])
# Each block field uses training outcomes only. Geometry uses coordinates, no outcomes.
blockcoords=np.array([np.mean(coords[ci==i],axis=0) for i in range(len(unique))]);pos=xyz(blockcoords);fields={};fieldUF={};variograms={};models={}
for uf in src.UFS:
 blockids=sorted(set(ci[(ufs==uf)&train]));blockids=[i for i in blockids if i>=0];values=[];validids=[]
 for i in blockids:
  mask=(ufs==uf)&(ci==i)&train
  p,d=fit(x[mask],y[mask],ufp[uf],1000,250);values.append((alr(p)-alr(ufp[uf])).ravel());validids.append(i)
 fields[uf]=(np.array(validids),np.array(values));print('local fields',uf,len(validids),flush=True)
 if len(values)<4:variograms[uf]={'fallback':'fewer than four training blocks'};continue
 vv=np.array(values);std=np.std(vv,axis=0);active=std>.03
 if not active.any():variograms[uf]={'fallback':'no variable coefficient field'};continue
 z=vv[:,active]/std[active];dist=distance.pdist(pos[validids]);sem=distance.pdist(z,metric='sqeuclidean')/(2*z.shape[1]);edges=np.linspace(0,min(600,float(dist.max())),13);bins=[]
 for lo,hi in zip(edges[:-1],edges[1:]):
  mask=(dist>lo)&(dist<=hi)
  if sum(mask)>=3:bins.append([float(np.mean(dist[mask])),float(np.mean(sem[mask])),int(sum(mask))])
 if len(bins)<3:variograms[uf]={'fallback':'insufficient variogram bins'};continue
 arr=np.array(bins)
 def gamma(h,p):
  nug,sill,r=p;t=np.minimum(h/r,1);return nug+sill*(1.5*t-.5*t**3)
 def fun(p):return (gamma(arr[:,0],p)-arr[:,1])*np.sqrt(arr[:,2]/arr[:,2].max())
 fitv=least_squares(fun,[.2,.8,150],bounds=([.001,.001,10],[3,5,1500]));variograms[uf]={'nugget':float(fitv.x[0]),'partial_sill':float(fitv.x[1]),'range_km_chord':float(fitv.x[2]),'bins':bins,'active_coefficient_fields':int(sum(active)),'fit_cost':float(fitv.cost),'fit_success':bool(fitv.success)};models[uf]=fitv.x

def covariance(ds,p):
 nug,sill,r=p;t=np.minimum(ds/r,1);return sill*(1-1.5*t+.5*t**3)
def metrics(mask,pred):
 yy=y[mask];mu=pred[mask];n=yy.sum(axis=1);e=abs(mu[:,:2]-yy[:,:2])/n[:,None]*100
 return {'sections':int(sum(mask)),'mae_pp':float(e.mean()),'weighted_mae_pp':float(abs(mu[:,:2]-yy[:,:2]).sum()/n.sum()/2*100),'p95_pp':float(np.quantile(e,.95)),'max_pp':float(e.max()),'aggregate_residual_votes':(mu.sum(axis=0)-yy.sum(axis=0)).tolist()}
results=[{'method':'UF','k':None,'tuning':metrics(tune,base),'test':metrics(test,base)}];predictions=[base];ratebanks=[ufp];krigdiag=[]
for method in ['IDW2','KO']:
 for k in [8,16]:
  pred=base.copy();rates={};variances=[];fallback=collections.Counter();maxweightsumerr=0
  for uf in src.UFS:
   ids,vv=fields[uf];targetids=sorted(set(ci[(ufs==uf)&mapped]));targetids=[i for i in targetids if i>=0]
   if len(ids)<4 or method=='KO' and uf not in models:fallback[uf]+=len(targetids);continue
   tree=cKDTree(pos[ids]);kk=min(k,len(ids));dd,nn=tree.query(pos[targetids],k=kk)
   for block,dists,neighbors in zip(targetids,dd,nn):
    if method=='IDW2':
     exact=dists<1e-6
     if exact.any():weights=exact/exact.sum()
     else:weights=1/np.maximum(dists,1e-6)**2;weights/=weights.sum()
    else:
     pp=models[uf];C=covariance(distance.cdist(pos[ids[neighbors]],pos[ids[neighbors]]),pp);C.flat[::kk+1]+=pp[0]+1e-9;rhs=covariance(dists,pp);A=np.block([[C,np.ones((kk,1))],[np.ones((1,kk)),np.zeros((1,1))]])
     sol=np.linalg.solve(A,np.r_[rhs,1]);weights=sol[:kk];variance=float(pp[0]+pp[1]-weights@rhs-sol[-1]);assert variance>=-1e-6;variances.append(max(0,variance));maxweightsumerr=max(maxweightsumerr,abs(weights.sum()-1))
    p=inverse(alr(ufp[uf])+(weights@vv[neighbors]).reshape(K,5));assert np.all(p>=0) and np.max(abs(p.sum(axis=1)-1))<1e-12;mask=(ufs==uf)&(ci==block);pred[mask]=x[mask]@p;rates[uf+':'+str(block)]=p
  rec={'method':method,'k':k,'tuning':metrics(tune,pred),'test':metrics(test,pred),'fallback_blocks_by_uf':dict(fallback),'maximum_kriging_weight_sum_error':maxweightsumerr,'conditional_kriging_variance_standardized_field_quantiles':np.quantile(variances,[0,.5,.95,1]).tolist() if variances else None};results.append(rec);predictions.append(pred);ratebanks.append(rates);print('SPATIAL',method,k,rec['tuning'],rec['test'],flush=True)
  (P/'espacial-checkpoint.json').write_text(json.dumps(results,ensure_ascii=False))
selected=min(range(len(results)),key=lambda i:results[i]['tuning']['weighted_mae_pp']);flows=np.zeros((K,J));byuf=[];bank=ratebanks[selected]
for uf in src.UFS:
 f=np.zeros((K,J));mask=ufs==uf
 for block in sorted(set(ci[mask])):
  mm=mask&(ci==block);p=ufp[uf] if selected==0 else bank.get(uf+':'+str(block),ufp[uf]);f+=x[mm].sum(axis=0)[:,None]*p
 flows+=f;byuf.append({'uf':uf,'sections':int(sum(mask)),'mapped_sections':int(sum(mask&mapped)),'origin':x[mask].sum(axis=0).tolist(),'flow':f.tolist(),'observed_second':y[mask].sum(axis=0).tolist()})
assert np.max(abs(flows.sum(axis=1)-x.sum(axis=0)))<1e-5

# Additional outputs only: unchanged protocol and fitting; test remains unselected.
model_flows=[]
for model_index,bank_i in enumerate(ratebanks):
 total=np.zeros((K,J))
 for uf in src.UFS:
  mask=ufs==uf
  for block in sorted(set(ci[mask])):
   mm=mask&(ci==block);pr=ufp[uf] if model_index==0 else bank_i.get(uf+':'+str(block),ufp[uf]);total+=x[mm].sum(axis=0)[:,None]*pr
 model_flows.append(total.tolist())
for rec in byuf:
 uf=rec['uf'];mask=ufs==uf;hist={c:[{'urnas':[0]*20,'votos_origem':[0]*20} for _ in range(2)] for c in src.CODES}
 for block in sorted(set(ci[mask])):
  mm=mask&(ci==block);pr=ufp[uf] if selected==0 else bank.get(uf+':'+str(block),ufp[uf])
  for i,c in enumerate(src.CODES):
   nonzero=x[mm,i]>0;ns=int(sum(nonzero));nv=int(sum(x[mm,i]))
   for j in [0,1]:
    bin_index=min(19,max(0,int(np.floor(pr[i,j]*20+1e-10))));hist[c][j]['urnas'][bin_index]+=ns;hist[c][j]['votos_origem'][bin_index]+=nv
 for i,c in enumerate(src.CODES):
  for j in [0,1]:assert sum(hist[c][j]['votos_origem'])==round(rec['origin'][i])
 rec['histograms']=hist

# Synthetic check of ordinary kriging: unit sum and constant reproduction.
C=np.array([[1,.3],[.3,1]]);A=np.block([[C,np.ones((2,1))],[np.ones((1,2)),np.zeros((1,1))]]);sol=np.linalg.solve(A,[.5,.4,1]);assert abs(sol[:2].sum()-1)<1e-12 and abs(sol[:2]@np.array([7.,7.])-7)<1e-12
out={'protocol':protocol,'source_reference':'repository derivatives, commit104b8adbecbee2261b9b4883eb46ef6352996dd4; no independent official authentication in this phase','counts':{'sections':len(x),'geocoded':int(sum(mapped)),'unmapped_including_exterior':int(sum(~mapped)),'train':int(sum(train)),'tuning':int(sum(tune)),'test':int(sum(test)),'geographical_cells':len(unique)},'codes':src.CODES,'origins':src.ORIGINS,'destinations':src.DEST,'global_fit_diagnostic':gd,'UF_fit_diagnostics':diag,'models':results,'national_flows_all_models':model_flows,'selected_index':selected,'selected':results[selected],'variograms':variograms,'national_origin':x.sum(axis=0).tolist(),'national_fitted_flow':flows.tolist(),'national_observed_second':y.sum(axis=0).tolist(),'by_uf':byuf,'tests':{'ordinary_weights_unit_sum':True,'ordinary_constant_reproduction':True,'simplex_rates':True,'origin_margin_conservation':True},'limitations':['Ordinary kriging of latent log-ratio coefficients estimated by ecological regression, not measured individual migration.','Variogram uses standardized pooled coefficient fields and an isotropic spherical approximation per UF; no demonstration of full stationarity or anisotropy.','Block centroids are averages of first-turn voting-site coordinates; model uses 0.5 degree blocks, not point kriging of every section.','Chord distances in km on Earth sphere; grid cells vary in physical size with latitude.','Spatial split has no buffer; adjacent train and test cells can be close. This is geographic holdout, not proof of independence.','Kriging variance is conditional on fitted variogram; it omits uncertainty in latent ecological coefficients and is not migration accuracy.','Missing coordinates and exterior use training-only regional fallback and are not part of spatial test.','No candidate-specific transfer ground truth; predictive error of final totals does not validate migration origin.','No proven global maximum or comprehensive enumeration: finite iterative fits with convergence diagnostics.','No forced reconciliation of destination totals; residuals are reported.']}
(P/'inferencia-espacial-resultado.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('COMPLETE',out['counts'],out['selected'],flush=True)
