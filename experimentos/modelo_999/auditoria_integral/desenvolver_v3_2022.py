"""Grade de desenvolvimento pré-registrada: usa somente 2022."""
import pathlib,json,pickle,collections,bisect,datetime,types,hashlib
from preditor_causal_v2 import predict as v2
ROOT=pathlib.Path(__file__).resolve().parent
GRID=[0,.25,.5,.75,1]

def candidate(alpha):
 source=(ROOT/'preditor_causal_v2.py').read_text()
 source=source.replace('swing = numerator/denominator if denominator else 0.0',f'swing = {alpha!r} * (numerator/denominator if denominator else 0.0)')
 mod=types.ModuleType('candidate');exec(compile(source,'<candidate>','exec'),mod.__dict__);return mod.predict

def cases():
 saved=json.loads((ROOT/'entradas_checkpoints_reconstruidos_2022.json').read_text());history=saved['first_round']
 with (ROOT/'microdados/reconstrucao_cache.pkl').open('rb') as f:events,_,_,_=pickle.load(f)
 increments=collections.defaultdict(lambda:[0,0])
 for t,key,v in events:
  x=increments[t,key[0]];x[0]+=v[0];x[1]+=v[1]
 rows=collections.defaultdict(list);acc=collections.defaultdict(lambda:[0,0])
 for (t,u),v in sorted(increments.items()):
  x=acc[u];x[0]+=v[0];x[1]+=v[1];rows[u].append((t,x[0],x[1]))
 times={u:[x[0] for x in rr] for u,rr in rows.items()}
 scenarios={'referencia':(0,set()),'atraso_5min':(300,set()),'atraso_15min':(900,set()),'atraso_30min':(1800,set()),'sem_SP':(0,{'SP'}),'sem_SP_MG_RJ':(0,{'SP','MG','RJ'}),'sem_Nordeste':(0,set('AL BA CE MA PB PE PI RN SE'.split()))}
 out={}
 for name,(delay,drop) in scenarios.items():
  inputs=[]
  for checkpoint in saved['checkpoints']:
   c=checkpoint['current'];now=datetime.datetime.fromisoformat(c['timestamp']);t=now.replace(tzinfo=None);states=[]
   for u in sorted(rows):
    if u in drop:continue
    i=bisect.bisect_right(times[u],t-datetime.timedelta(seconds=delay))-1
    if i<0:continue
    tt,a,b=rows[u][i];generated=tt.replace(tzinfo=now.tzinfo)
    states.append({'scope':u,'timestamp':generated.isoformat(),'available_at':(generated+datetime.timedelta(seconds=delay)).isoformat(),'votes_a':a,'votes_b':b})
   inputs.append((checkpoint['threshold_pct'],c,states))
  out[name]=inputs
 return history,out

def evaluate(predict,history,inputs,target):
 out={}
 for name,items in inputs.items():
  points=[]
  for pct,c,states in items:
   p=predict(c,history,states);error=100*(p['forecast_a']-target)
   points.append({'threshold_pct':pct,'error_pp':error,'forecast_a_pct':100*p['forecast_a'],'swing_pp':100*p['swing'],'fresh_territories':p['fresh_territories']})
  errors=[x['error_pp'] for x in points]
  out[name]={'mae_pp':sum(map(abs,errors))/len(errors),'max_abs_error_pp':max(map(abs,errors)),'bias_pp':sum(errors)/len(errors),'checkpoints':points}
 return out

def run():
 history,inputs=cases();target=json.loads((ROOT/'backtest_territorial_reconstruido_2022.json').read_text())['final_lula_pct']/100
 baseline=evaluate(v2,history,inputs,target);ref=baseline['referencia'];worst=max(x['max_abs_error_pp'] for x in baseline.values());results=[]
 for alpha in GRID:
  scores=evaluate(candidate(alpha),history,inputs,target);r=scores['referencia'];w=max(x['max_abs_error_pp'] for x in scores.values())
  eligible=r['max_abs_error_pp']<=ref['max_abs_error_pp']+1e-12 and abs(r['bias_pp'])<=abs(ref['bias_pp'])+1e-12 and w<=worst+1e-12
  results.append({'swing_shrinkage':alpha,'eligible':eligible,'worst_stress_max_pp':w,'scenarios':scores})
 eligible=[x for x in results if x['eligible']]
 chosen=min(eligible,key=lambda x:(round(x['scenarios']['referencia']['mae_pp'],12),abs(x['swing_shrinkage']-1))) if eligible else None
 out={'development_election':2022,'protocol_commit':'cb7a150896c1971d2b32dc2c5fe4987a497e5161','2018_used_for_selection':False,'selected_swing_shrinkage':chosen['swing_shrinkage'] if chosen else 1,'baseline_v2':baseline,'grid':results,'warning':'Desempenho de desenvolvimento, nao validacao externa. Guardrails e grade fixados antes do calculo.'}
 (ROOT/'grade_desenvolvimento_v3_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'selected':out['selected_swing_shrinkage'],'grid':[{'alpha':x['swing_shrinkage'],'eligible':x['eligible'],'mae':x['scenarios']['referencia']['mae_pp'],'max':x['scenarios']['referencia']['max_abs_error_pp'],'worst_stress':x['worst_stress_max_pp']} for x in results]},ensure_ascii=False))
if __name__=='__main__':run()
