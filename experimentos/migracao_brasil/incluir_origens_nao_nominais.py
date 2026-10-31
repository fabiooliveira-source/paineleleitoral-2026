"""Conciliação contábil posterior; não altera o ajuste nem valida transferências."""
import pathlib,json,numpy as np
P=pathlib.Path(__file__).resolve().parent;p=P/'inferencia-espacial-resultado.json';d=json.loads(p.read_text());diagnostics=[]
for s in d['by_uf']:
 a=np.array(s['origin']);b=np.array(s['observed_second']);m=np.array(s['flow']);assert abs(a.sum()-b.sum())<1e-6
 target=m.copy();target=np.maximum(target,1e-100);target[a==0,:]=0;target[:,b==0]=0
 for iteration in range(1,10001):
  target*=np.divide(b,target.sum(axis=0),out=np.zeros_like(b),where=target.sum(axis=0)>0)[None,:]
  target*=np.divide(a,target.sum(axis=1),out=np.zeros_like(a),where=target.sum(axis=1)>0)[:,None]
  err=max(abs(target.sum(axis=1)-a).max(),abs(target.sum(axis=0)-b).max())
  if err<1e-6:break
 assert err<1e-5 and np.all(target>=0)
 s['calibrated_flow']=target.tolist();diagnostics.append({'uf':s['uf'],'iterations':iteration,'maximum_margin_residual_votes':float(err)})
d['postfit_reconciliation']={'method':'Iterative proportional fitting by UF: positive fitted flows raked to first-turn origin totals and all known second-turn destination totals.','purpose':'Accounting reconciliation only; uses the known second-turn totals after fitting, not out-of-sample prediction or validated migration accuracy.','original_flow_preserved':True,'diagnostics':diagnostics}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print('IPF margins passed in all',len(diagnostics),'territories; max',max(r['maximum_margin_residual_votes'] for r in diagnostics))
