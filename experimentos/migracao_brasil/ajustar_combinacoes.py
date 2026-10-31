"""Ajuste exploratório por pseudoverossimilhança multinomial agregada.
Não é a verossimilhança exata de transições individuais nem acerto certificado.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='2'
os.environ['OMP_NUM_THREADS']='2'
import pathlib,json,inspect,hashlib,time
import numpy as np
import analisar_migracao_brasil as src
P=pathlib.Path(__file__).resolve().parent
source=inspect.getsource(src.analyze).split(' # Cenário')[0]
source=source.replace('def analyze(uf):','def extract(uf):')+'\n return a,b,[tuple(r[:3]) for r in s["linhas"] if all(r[cols["situacao_dados_"+t]]=="conferido" for t in ["1t","2t"])]\n'
ns=vars(src).copy();exec(source,ns);extract=ns['extract']
xs=[];ys=[];validation=[];labels=[]
for uf in src.UFS:
 a,b,keys=extract(uf);assert len(a)==len(keys)
 mask=np.array([int(hashlib.sha256((uf+':'+str(k[0])).encode()).hexdigest()[:8],16)%5==0 for k in keys])
 xs.append(a);ys.append(b);validation.extend(mask);labels.extend([uf]*len(a))
 print('loaded',uf,len(a),flush=True)
x=np.concatenate(xs);y=np.concatenate(ys);valid=np.array(validation);labels=np.array(labels);xt=x[~valid];yt=y[~valid];xv=x[valid];yv=y[valid]
assert np.max(abs(x.sum(axis=1)-y.sum(axis=1)))==0
weights=xt.sum(axis=0);s=yt.sum(axis=0);ind=np.tile(s/s.sum(),(x.shape[1],1))
initials=[('independencia',ind),('permanencia',ind.copy()),('aleatoria',np.random.default_rng(20261031).dirichlet(np.ones(6),size=x.shape[1]))]
for i,j in [(0,0),(1,1),(len(src.CODES),2),(len(src.CODES)+1,3),(len(src.CODES)+2,4),(len(src.CODES)+3,5)]:
 initials[1][1][i,:]*=.1;initials[1][1][i,j]+=.9

def metrics(xx,yy,p):
 pred=xx@p;n=yy.sum(axis=1);obs=yy/n[:,None];est=pred/n[:,None];err=abs(est[:,:2]-obs[:,:2])*100
 return {'mae_finalists_pp':float(err.mean()),'p95_finalists_pp':float(np.quantile(err,.95)),'max_finalists_pp':float(err.max()),'weighted_mae_finalists_pp':float((abs(pred[:,:2]-yy[:,:2]).sum())/(2*n.sum())*100),'national_residual_votes':(pred.sum(axis=0)-yy.sum(axis=0)).tolist()}
results=[]
for name,p0 in initials:
 p=p0.copy();old=None;converged=False;history=[]
 for step in range(1,601):
  mu=np.maximum(xt@p,1e-100);ratio=yt/mu
  p*=xt.T@ratio/np.maximum(weights[:,None],1e-100);p=np.maximum(p,1e-12);p/=p.sum(axis=1,keepdims=True)
  if step%20==0:
   mu=np.maximum(xt@p,1e-100);objective=float(-np.sum(yt*np.log(mu/yt.sum(axis=1)[:,None]))/yt.sum())
   history.append([step,objective]);print(name,step,objective,flush=True)
   if old is not None and abs(objective-old)<1e-9:converged=True;break
   old=objective
 results.append({'initialization':name,'iterations':step,'converged_numerically':converged,'objective_cross_entropy':history[-1][1],'history':history,'rates':p.tolist(),'training':metrics(xt,yt,p),'validation':metrics(xv,yv,p)})
 (P/'ajuste-combinacoes-checkpoint.json').write_text(json.dumps(results,ensure_ascii=False))
best=min(results,key=lambda r:r['objective_cross_entropy']);byp=np.array(best['rates']);origin=x.sum(axis=0);flow=origin[:,None]*byp
output={'method':'Constrained transfer mixtures fitted by aggregate multinomial pseudo-likelihood with EM. This is not the exact likelihood of ecological contingency tables.','split':'20% municipalities held out by deterministic SHA256 hash UF:municipality; no second-turn validation outcomes enter fitting','sections_total':len(x),'training_sections':int(sum(~valid)),'validation_sections':int(sum(valid)),'origins':src.ORIGINS,'codes':src.CODES,'destinations':src.DEST,'results':results,'selected_by':'minimum training cross entropy, not validation error','selected_initialization':best['initialization'],'national_origin':origin.tolist(),'national_fitted_flows':flow.tolist(),'observed_second':y.sum(axis=0).tolist(),'baseline_validation':metrics(xv,yv,ind),'limitations':['Assumes one global transfer matrix across all sections; territorial heterogeneity can bias origin rates.','No individual transfers observed, no certified percentage accuracy.','Different initializations expose sensitivity; convergence alone does not establish identification.','Source data are repository derivatives, not independently authenticated here.','Rates of small and spatially collinear candidates may be weakly identified.','Other destinations and accounting adjustment preserved; all rates are conditional on the modeled common universe.']}
(P/'ajuste-combinacoes-resultado.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print('COMPLETE',best['initialization'],best['validation'],flush=True)
