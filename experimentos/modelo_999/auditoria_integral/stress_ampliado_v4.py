"""Stress V4: falhas de contrato e ordem artificial de blocos historicos.
Nao e validacao externa nova; nao altera o preditor nem a regua apos o teste.
"""
import pathlib,json,copy,datetime,random,pickle,collections,math,time,sys,hashlib
from preditor_causal_v4 import predict as original
ROOT=pathlib.Path(__file__).resolve().parent

def checked_call(fn,c,r,l,previous=None):
 try:
  return fn(c,r,l,previous=previous) if fn is not original else fn(c,r,l)
 except (ValueError,TypeError,AttributeError,KeyError,OverflowError):return {'estimate_a':None,'status':'ERROR','reason':'invalid_input','conditional_winner':None}

def fault_suite(fn):
 outcomes=[];latencies=[]
 for year in [2018,2022,2020]:
  d=json.loads((ROOT/f'entradas_pareadas_v4_{year}.json').read_text());ref=d['reference']
  for frame in d['checkpoints']:
   c=frame['current'];l=frame['ledger'];pct=frame['threshold_pct'];now=datetime.datetime.fromisoformat(c['timestamp']);before=time.perf_counter();base=checked_call(fn,c,ref,l);latencies.append(time.perf_counter()-before)
   variants=[]
   def add(name,cc,rr,ll,expected,prev=None):variants.append((name,cc,rr,ll,expected,prev))
   for seed in range(10):
    ll=copy.deepcopy(l);random.Random(seed).shuffle(ll);add('permutation_'+str(seed),c,ref,ll,'same')
   add('duplicate_identical',c,ref,l+[dict(l[0])],'same')
   for fraction in [1/len(l),.1,.5,1]:add('missing_'+str(fraction),c,ref,l[max(1,math.ceil(len(l)*fraction)):],'abstain')
   for minutes in [1,5,15,30]:
    ll=copy.deepcopy(l);t=(now-datetime.timedelta(minutes=minutes)).isoformat();ll[0]['timestamp']=ll[0]['available_at']=t;add('delay_'+str(minutes),c,ref,ll,'abstain')
   future=(now+datetime.timedelta(days=1)).isoformat();ll=copy.deepcopy(l);ll.append(dict(ll[0],timestamp=future,available_at=future,votes_a=999999999));add('future_known_scope',c,ref,ll,'same')
   ll=copy.deepcopy(l);ll[0]['votes_a']+=1;add('aggregate_mismatch',c,ref,ll,'abstain')
   ll=copy.deepcopy(l);ll.append(dict(ll[0],votes_a=ll[0]['votes_a']+1));add('conflicting_duplicate',c,ref,ll,'abstain')
   for field,value in [('votes_a',-1),('votes_a',True),('votes_a',1.5),('electorate_counted',c['electorate_total']+1)]:
    cc=dict(c);cc[field]=value;add('invalid_'+field+'_'+str(value),cc,ref,l,'abstain')
   rr=copy.deepcopy(ref);rr[next(iter(rr))]['available_at']=future;add('future_reference',c,rr,l,'abstain')
   ll=copy.deepcopy(l);u=ll[0]['scope'];ll[0]['matched_first_a']=ref[u]['votes_a']+1;add('inflated_reference',c,ref,ll,'abstain')
   cc=dict(c,generated_at=c['timestamp'],available_at=(now-datetime.timedelta(seconds=1)).isoformat());add('national_received_before_generation',cc,ref,l,'abstain')
   previous=dict(c,timestamp=(now-datetime.timedelta(seconds=1)).isoformat(),available_at=(now-datetime.timedelta(seconds=1)).isoformat(),votes_a=c['votes_a']+1);add('revision_decreasing_votes',c,ref,l,'abstain',previous)
   for name,cc,rr,ll,expected,prev in variants:
    out=checked_call(fn,cc,rr,ll,prev);ok=out.get('estimate_a') is None if expected=='abstain' else out.get('estimate_a')==base.get('estimate_a')
    outcomes.append({'year':year,'checkpoint':pct,'scenario':name,'passed':ok,'status':out.get('status'),'reason':out.get('reason')})
 return {'checks':len(outcomes),'passed':sum(x['passed'] for x in outcomes),'failed':sum(not x['passed'] for x in outcomes),'failures':[x for x in outcomes if not x['passed']],'latency_p95_seconds':sorted(latencies)[int(.95*(len(latencies)-1))]},outcomes

def blocks(year):
 stored=ROOT/f'blocos_stress_v4_{year}.json'
 if stored.exists():
  manifest=json.loads((ROOT/'manifesto_blocos_stress_v4.json').read_text());row=next(x for x in manifest['files'] if x['name']==stored.name)
  assert hashlib.sha256(stored.read_bytes()).hexdigest()==row['sha256'],'Changed cohort blocks'
  source=ROOT/row['reference_inputs'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['reference_sha256'],'Changed paired inputs'
  payload=json.loads(stored.read_text());return json.loads(source.read_text()),payload['cohorts'],payload['final_totals']
 d=json.loads((ROOT/f'entradas_pareadas_v4_{year}.json').read_text());ref=d['reference'];totals=collections.defaultdict(lambda:[0,0])
 cache=ROOT/('microdados/reconstrucao_cache.pkl' if year==2022 else 'microdados2018/replay_cache.pkl')
 with cache.open('rb') as f:events=pickle.load(f)[0]
 for t,k,v in events:totals[k[0]][0]+=v[0];totals[k[0]][1]+=v[1]
 previous={u:[0]*4 for u in ref};out=[]
 for index,frame in enumerate(d['checkpoints']):
  for row in frame['ledger']:
   u=row['scope'];v=[row[k] for k in ['votes_a','votes_b','matched_first_a','matched_first_b']];delta=[v[j]-previous[u][j] for j in range(4)];assert min(delta)>=0
   if any(delta):out.append({'scope':u,'stage':index, 'values':delta})
   previous[u]=v
 for u,h in ref.items():
  end=[totals[u][0],totals[u][1],h['votes_a'],h['votes_b']];delta=[end[j]-previous[u][j] for j in range(4)];assert min(delta)>=0
  if any(delta):out.append({'scope':u,'stage':19,'values':delta})
 return d,out,totals

def order_suite(fn):
 results=[];all_points=[]
 for year in [2018,2022]:
  d,cohorts,totals=blocks(year);ref=d['reference'];final_a=sum(x[0] for x in totals.values());final_b=sum(x[1] for x in totals.values());target=final_a/(final_a+final_b);mass=sum(x['votes_a']+x['votes_b'] for x in ref.values());electorate=d['checkpoints'][0]['current']['electorate_total'];northeast=set('AL BA CE MA PB PE PI RN SE'.split())
  orders={}
  for seed in range(10):ll=copy.deepcopy(cohorts);random.Random(seed).shuffle(ll);orders['random_'+str(seed)]=ll
  orders['uf_ascending']=sorted(cohorts,key=lambda b:(b['scope'],b['stage']))
  orders['uf_descending']=sorted(cohorts,key=lambda b:(b['scope'],b['stage']),reverse=True)
  orders['northeast_first']=sorted(cohorts,key=lambda b:(b['scope'] not in northeast,b['stage'],b['scope']))
  orders['northeast_last']=sorted(cohorts,key=lambda b:(b['scope'] in northeast,b['stage'],b['scope']))
  ratio=lambda b:b['values'][2]/sum(b['values'][2:]) if sum(b['values'][2:]) else 0
  orders['first_round_a_low_first']=sorted(cohorts,key=ratio)
  orders['first_round_a_high_first']=sorted(cohorts,key=ratio,reverse=True)
  orders['historical_cohort_order']=sorted(cohorts,key=lambda b:(b['stage'],b['scope']))
  orders['reversed_cohort_order']=sorted(cohorts,key=lambda b:(b['stage'],b['scope']),reverse=True)
  for name,ordered in orders.items():
   acc={u:[0]*4 for u in ref};i=0;seen_mass=0;points=[]
   for pct in range(5,100,5):
    while i<len(ordered) and seen_mass/mass<pct/100:
     block=ordered[i];v=block['values'];u=block['scope']
     for j in range(4):acc[u][j]+=v[j]
     seen_mass+=sum(v[2:]);i+=1
    a=sum(v[0] for v in acc.values());b=sum(v[1] for v in acc.values());now=datetime.datetime.fromisoformat(d['checkpoints'][0]['current']['timestamp'])+datetime.timedelta(seconds=i);iso=now.isoformat()
    c=dict(timestamp=iso,available_at=iso,votes_a=a,votes_b=b,electorate_total=electorate,electorate_counted=a+b)
    ledger=[dict(scope=u,timestamp=iso,available_at=iso,votes_a=v[0],votes_b=v[1],matched_first_a=v[2],matched_first_b=v[3]) for u,v in sorted(acc.items())]
    out=checked_call(fn,c,ref,ledger);prediction=out.get('estimate_a');p={'year':year,'scenario':name,'reference_mass_covered_pct':pct,'error_pp':None if prediction is None else 100*(prediction-target),'baseline_error_pp':100*(a/(a+b)-target),'bounds_cover':out.get('lower_a',0)-1e-12<=target<=out.get('upper_a',1)+1e-12,'conditional_winner':out.get('conditional_winner'),'wrong_conditional_call':out.get('conditional_winner') not in [None,'a' if target>.5 else 'b'],'status':out.get('status')};points.append(p)
   errors=[abs(x['error_pp']) for x in points if x['error_pp'] is not None];base=[abs(x['baseline_error_pp']) for x in points];mae=sum(errors)/len(errors) if errors else None;maximum=max(errors) if errors else None
   passed=len(errors)==19 and mae<=sum(base)/19+1e-12 and maximum<=max(base)+1e-12 and all(x['bounds_cover'] and not x['wrong_conditional_call'] for x in points)
   results.append({'year':year,'scenario':name,'estimates':len(errors),'mae_pp':mae,'max_abs_error_pp':maximum,'baseline_mae_pp':sum(base)/19,'baseline_max_pp':max(base),'passed':passed});all_points.extend(points)
 return {'scenarios':len(results),'passed':sum(x['passed'] for x in results),'failed':sum(not x['passed'] for x in results),'results':results,'scope':'Artificial reordering of cohort blocks, not authentic alternate totalization. Checkpoints use covered first-round two-finalist vote mass, not section count. Counted electorate is synthetic valid observed votes;R is conservative.'},all_points

def run(version='v4'):
 if version=='v4':fn=original
 else:
  from preditor_v4_guardado import predict_guarded
  fn=predict_guarded
 safety,details=fault_suite(fn);order,points=order_suite(fn)
 report={'version':version,'protocol_commit':'feeae17ed7a4a6777c923c5c321945bd330896c0','safety':safety,'synthetic_order':order,'decision':'ACCEPTED_WITHIN_DECLARED_STRESS_SCOPE' if safety['failed']==0 and order['failed']==0 else 'NOT_ACCEPTED_ALL_PREDEFINED_CRITERIA','probabilistic_certification':False}
 (ROOT/f'stress_ampliado_{version}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(ROOT/f'stress_detalhes_{version}.json').write_text(json.dumps({'fault_cases':details,'synthetic_points':points},ensure_ascii=False,separators=(',',':'))+'\n')
 print(json.dumps({'version':version,'safety':safety,'order_summary':{k:v for k,v in order.items() if k!='results'},'order_failures':[x for x in order['results'] if not x['passed']],'decision':report['decision']},ensure_ascii=False),flush=True);return report
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'v4')
