"""Recalcula projeções com aritmética racional independente do preditor."""
from fractions import Fraction as F
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
out=[]
for code in ['13897','87912','17612']:
 folder=ROOT/'externos2024'/code
 d=json.loads((folder/'entradas_pareadas_v4_2024.json').read_text());r=json.loads((folder/'resultado_externo_v41_2024.json').read_text());diffs=[];errors=[]
 for frame,point in zip(d['checkpoints'],r['points']):
  c=frame['current'];a,b=c['votes_a'],c['votes_b'];remaining=c['electorate_total']-c['electorate_counted'];rows=frame['ledger'];unseen=[F(0),F(0)]
  for j,key in enumerate(['a','b']):
   observed=sum(x['matched_first_'+key] for x in rows);global_ratio=F([a,b][j],observed)
   for row in rows:
    matched=row['matched_first_'+key];ratio=F(row['votes_'+key],matched) if matched else global_ratio
    unseen[j]+=(d['reference'][row['scope']]['votes_'+key]-matched)*ratio
  if sum(unseen)>remaining:unseen=[x*remaining/sum(unseen) for x in unseen]
  estimate=F(a+unseen[0],a+b+sum(unseen));delta=abs(100*float(estimate)-point['estimate_a_pct']);assert delta<1e-9;diffs.append(delta)
  assert abs(float(F(a,a+b+remaining))*100-point['lower_a_pct'])<1e-9
  assert abs(float(F(a+remaining,a+b+remaining))*100-point['upper_a_pct'])<1e-9
  winner='a' if a>b+remaining else ('b' if b>a+remaining else None);assert winner==point['conditional_winner']
  errors.append(abs(100*(float(estimate)-d['target_a'])))
 assert len(diffs)==19
 assert abs(sum(errors)/19-r['metrics']['mae_pp'])<1e-9
 s=sorted(errors);assert abs(.9*s[17]+.1*s[18]-r['metrics']['p95_abs_error_pp'])<1e-9
 out.append(dict(municipality=code,points=19,max_difference_pp=max(diffs)))
result=dict(method='independent exact rational projection, deterministic bounds and conditional calls',cases=out,passed=True)
(ROOT/'verificacao_externos2024_fracoes.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
