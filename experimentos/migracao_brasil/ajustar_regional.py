import os
os.environ['OPENBLAS_NUM_THREADS']='2'
import pathlib,json,inspect,hashlib
import numpy as np
from scipy.optimize import minimize,LinearConstraint,Bounds
import analisar_migracao_brasil as src
P=pathlib.Path(__file__).resolve().parent
source=inspect.getsource(src.analyze).split(' # Cenário')[0].replace('def analyze(uf):','def extract(uf):')+'\n return a,b,[tuple(r[:3]) for r in s["linhas"] if all(r[cols["situacao_dados_"+t]]=="conferido" for t in ["1t","2t"])]\n'
ns=vars(src).copy();exec(source,ns)
xs=[];ys=[];labels=[];splits=[]
for uf in src.UFS:
 a,b,keys=ns['extract'](uf);assert len(a)==len(keys);xs.append(a);ys.append(b);labels.extend([uf]*len(a));splits.extend([int(hashlib.sha256((uf+':'+str(k[0])).encode()).hexdigest()[:8],16)%5 for k in keys])
x=np.concatenate(xs);y=np.concatenate(ys);labels=np.array(labels);split=np.array(splits);train=split>=2;tune=split==1;test=split==0
R={u:r for r,us in {'Norte':'AC AM AP PA RO RR TO','Nordeste':'AL BA CE MA PB PE PI RN SE','Centro-Oeste':'DF GO MS MT','Sudeste':'ES MG RJ SP','Sul':'PR RS SC','Exterior':'ZZ'}.items() for u in us.split()}
regions=np.array([R[u] for u in labels]);K=x.shape[1];J=6
xx=x[train];yy=y[train];normal=yy.sum()
def objective(v):
 p=v.reshape(K,J);mu=np.maximum(xx@p,1e-100);loss=-np.sum(yy*np.log(mu/yy.sum(axis=1)[:,None]))/normal;g=-xx.T@(yy/mu)/normal;return loss,g.ravel()
start=np.tile(yy.sum(axis=0)/yy.sum(),(K,1));A=np.zeros((K,K*J))
for i in range(K):A[i,i*J:(i+1)*J]=1
opt=minimize(objective,start.ravel(),jac=True,method='SLSQP',constraints=[LinearConstraint(A,1,1)],bounds=Bounds(1e-12,1),options={'maxiter':400,'ftol':1e-12})
globalp=opt.x.reshape(K,J);grad=objective(opt.x)[1].reshape(K,J);gap=float(np.sum(globalp*grad)-np.sum(grad.min(axis=1)))
print('GLOBAL',opt.success,opt.nit,opt.fun,'gap',gap,flush=True)
def fit(a,b,prior,alpha):
 p=prior.copy();weights=a.sum(axis=0)
 for it in range(350):
  mu=np.maximum(a@p,1e-100);new=(p*(a.T@(b/mu))+alpha*prior)/(weights[:,None]+alpha);new=np.maximum(new,1e-12);new/=new.sum(axis=1,keepdims=True)
  delta=np.max(abs(new-p));p=new
  if delta<1e-7:break
 return p,it+1,delta

def metrics(mask,pred):
 yy=y[mask];mu=pred[mask];n=yy.sum(axis=1);e=abs(mu[:,:2]-yy[:,:2])/n[:,None]*100
 return {'sections':int(sum(mask)),'mae_pp':float(e.mean()),'weighted_mae_pp':float(np.sum(abs(mu[:,:2]-yy[:,:2]))/n.sum()/2*100),'p95_pp':float(np.quantile(e,.95)),'max_pp':float(e.max()),'aggregate_residual_votes':(mu.sum(axis=0)-yy.sum(axis=0)).tolist()}
basepred=x@globalp;candidates=[{'level':'nacional','alpha':None,'rates':{'BR':globalp.tolist()},'tuning':metrics(tune,basepred),'test':metrics(test,basepred),'fit_diagnostics':[]}]
predictions=[basepred]
for level,groups in [('regiao',regions),('UF',labels)]:
 for alpha in [100,1000,10000]:
  pred=np.zeros_like(y);rates={};diagnostics=[]
  for group in sorted(set(groups)):
   mask=groups==group;tm=mask&train;p,it,delta=fit(x[tm],y[tm],globalp,alpha);pred[mask]=x[mask]@p;rates[group]=p.tolist();diagnostics.append({'group':group,'iterations':it,'last_max_delta':float(delta),'training_sections':int(sum(tm))})
  rec={'level':level,'alpha':alpha,'rates':rates,'tuning':metrics(tune,pred),'test':metrics(test,pred),'fit_diagnostics':diagnostics};candidates.append(rec);predictions.append(pred);print(level,alpha,rec['tuning']['mae_pp'],rec['test']['mae_pp'],flush=True)
  (P/'regional-checkpoint.json').write_text(json.dumps(candidates,ensure_ascii=False))
selected_index=min(range(len(candidates)),key=lambda i:candidates[i]['tuning']['weighted_mae_pp']);selected=candidates[selected_index];flows=np.zeros((K,J));byuf=[]
for uf in src.UFS:
 mask=labels==uf;group='BR' if selected['level']=='nacional' else R[uf] if selected['level']=='regiao' else uf;p=np.array(selected['rates'][group]);origin=x[mask].sum(axis=0);flow=origin[:,None]*p;flows+=flow
 byuf.append({'uf':uf,'sections':int(sum(mask)),'origins':origin.tolist(),'flow':flow.tolist(),'rates':p.tolist(),'observed_second':y[mask].sum(axis=0).tolist(),'fitted_second':flow.sum(axis=0).tolist()})
spread=[]
for i,code in enumerate(src.CODES):
 shares=[]
 for c in candidates:
  f=np.zeros((K,J))
  for uf in src.UFS:
   group='BR' if c['level']=='nacional' else R[uf] if c['level']=='regiao' else uf;f+=x[labels==uf].sum(axis=0)[:,None]*np.array(c['rates'][group])
  shares.append((f[i]/x[:,i].sum()).tolist())
 spread.append({'code':code,'scenario_min':np.min(shares,axis=0).tolist(),'scenario_max':np.max(shares,axis=0).tolist()})
out={'method':'Regional ecological mixture regression under aggregate multinomial pseudo-likelihood, not exact individual-transition likelihood. Regional fits penalized toward global fit via pseudo-count alpha per origin.','split':'Municipalities hash SHA256(UF:municipality)%5: 0=test, 1=tuning, 2-4=training. Selection uses tuning weighted MAE; test held out.','counts':{'total':len(x),'train':int(sum(train)),'tuning':int(sum(tune)),'test':int(sum(test))},'origins':src.ORIGINS,'codes':src.CODES,'destinations':src.DEST,'global_optimizer':{'success':bool(opt.success),'iterations':int(opt.nit),'message':str(opt.message),'convex_objective_gap_upper_bound':gap},'candidates':candidates,'selection_index':selected_index,'selected_model':{'level':selected['level'],'alpha':selected['alpha'],'test':selected['test']},'national_origin':x.sum(axis=0).tolist(),'national_flow':flows.tolist(),'national_observed_second':y.sum(axis=0).tolist(),'by_uf':byuf,'sensitivity_not_confidence_intervals':spread,'limitations':['Transfer rates are model-dependent, not observed voter trajectories or certified accuracy.','Regional association is not individual behavior. Co-location, collinearity and turnout changes affect identifiability.','Pseudo-likelihood is an approximation to ecological table likelihood. Alpha choices and fit family are exploratory.','Global convex optimization bound applies only to the specified objective; not all possible behavioral models.','Final table uses selected training-only model on all first-turn margins; no forced match to second-turn totals.','Test metrics evaluate section outcomes, not correctness of origin-to-destination migration.','Source repository derivatives not independently authenticated here.','Sparse origins require particular caution; numerical convergence is not identification.']}
(P/'inferencia-regional-resultado.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('COMPLETE',out['selected_model'],flush=True)
