"""Avaliação dos casos previamente fixados, sem reajustar a V4.1."""
import pathlib,json,hashlib,datetime,copy
from preditor_v4_guardado import predict_guarded
ROOT=pathlib.Path(__file__).resolve().parent
CASES={'13897':'Fortaleza','87912':'Pelotas','17612':'Natal'}
def quantile(values,p=.95):
 s=sorted(values);position=(len(s)-1)*p;lo=int(position);return s[lo]+(position-lo)*(s[min(lo+1,len(s)-1)]-s[lo])
def criteria_for(metrics,baseline,points,estimate_count,stress):
 return {'all19_estimates':estimate_count==19,'mae_not_worse_than_baseline':metrics is not None and metrics['mae_pp']<=baseline['mae_pp']+1e-12,'maximum_not_worse_than_baseline':metrics is not None and metrics['max_abs_error_pp']<=baseline['max_abs_error_pp']+1e-12,'mae_at_most1pp':metrics is not None and metrics['mae_pp']<=1,'p95_at_most2pp':metrics is not None and metrics['p95_abs_error_pp']<=2,'maximum_at_most3pp':metrics is not None and metrics['max_abs_error_pp']<=3,'winner_correct_at5':points[0]['winner_correct'],'no_wrong_conditional_call':not any(x['conditional_call_correct'] is False for x in points),'bounds_cover_all':all(x['bounds_cover_target'] for x in points),'all95_fault_checks':stress==95}
def evaluate_case(code):
 folder=ROOT/'externos2024'/code;path=folder/'entradas_pareadas_v4_2024.json'
 if not path.exists():return {'municipality':code,'name':CASES[code],'status':'DATA_BLOCKED','reason':'No qualified inputs; do not substitute case.'}
 d=json.loads(path.read_text());target=d['target_a'];reference=d['reference'];previous=None;points=[];stress=0
 for frame in d['checkpoints']:
  c=frame['current'];ledger=frame['ledger'];p=predict_guarded(c,reference,ledger,previous=previous);prediction=p['estimate_a'];observed=c['votes_a']/(c['votes_a']+c['votes_b']);now=datetime.datetime.fromisoformat(c['timestamp'])
  assert all(datetime.datetime.fromisoformat(r['available_at'])<=now for r in reference.values())
  assert all(datetime.datetime.fromisoformat(r['timestamp'])<=now and datetime.datetime.fromisoformat(r['available_at'])<=now for r in ledger)
  assert predict_guarded(c,reference,ledger[1:],previous=previous)['estimate_a'] is None;stress+=1
  delayed=copy.deepcopy(ledger);t=(now-datetime.timedelta(minutes=5)).isoformat();delayed[0]['timestamp']=delayed[0]['available_at']=t;assert predict_guarded(c,reference,delayed,previous=previous)['estimate_a'] is None;stress+=1
  t=(now+datetime.timedelta(days=1)).isoformat();future=dict(ledger[0],timestamp=t,available_at=t,votes_a=999999999);assert predict_guarded(c,reference,ledger+[future],previous=previous)['estimate_a']==prediction;stress+=1
  assert predict_guarded(c,reference,list(reversed(ledger)),previous=previous)['estimate_a']==prediction;stress+=1
  conflict=copy.deepcopy(ledger);conflict[0]['votes_a']+=1;assert predict_guarded(c,reference,conflict,previous=previous)['estimate_a'] is None;stress+=1
  called=p['conditional_winner'];winner='a' if target>.5 else 'b';correct=prediction is not None and prediction!=.5 and (prediction>.5)==(target>.5)
  points.append({'threshold_pct':frame['threshold_pct'],'timestamp':c['timestamp'],'estimate_a_pct':None if prediction is None else 100*prediction,'error_pp':None if prediction is None else 100*(prediction-target),'baseline_a_pct':100*observed,'baseline_error_pp':100*(observed-target),'winner_correct':correct,'conditional_winner':called,'conditional_call_correct':None if called is None else called==winner,'lower_a_pct':None if p['lower_a'] is None else 100*p['lower_a'],'upper_a_pct':None if p['upper_a'] is None else 100*p['upper_a'],'bounds_cover_target':p['lower_a'] is not None and p['lower_a']-1e-12<=target<=p['upper_a']+1e-12,'status':p['status'],'reason':p['reason']})
  if p['status'] in ['ESTIMATED','CLOSED']:previous=c
 errors=[abs(x['error_pp']) for x in points if x['error_pp'] is not None];base=[abs(x['baseline_error_pp']) for x in points]
 metrics={'mae_pp':sum(errors)/len(errors),'p95_abs_error_pp':quantile(errors),'max_abs_error_pp':max(errors),'bias_pp':sum(x['error_pp'] for x in points if x['error_pp'] is not None)/len(errors)} if errors else None
 baseline={'mae_pp':sum(base)/len(base),'p95_abs_error_pp':quantile(base),'max_abs_error_pp':max(base)};criteria=criteria_for(metrics,baseline,points,len(errors),stress)
 result={'municipality':code,'name':CASES[code],'year':2024,'status':'ACCEPTED_IN_PREDEFINED_BENCHMARK' if all(criteria.values()) else 'NOT_ACCEPTED_ALL_CRITERIA','role':'external_reconstructed_municipal_challenge_case','input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'target_a_pct':100*target,'metrics':metrics,'baseline':baseline,'criteria':criteria,'winner_correct_points':sum(x['winner_correct'] for x in points),'fault_checks_passed':stress,'model_adjusted_after_2024':False,'probabilistic_certificate':False,'points':points,'limitations':['Public historical outcomes were known when choosing challenging cases; not a random representative sample.','Final section votes and internal first-totalization clocks are retrospective, not authenticated public snapshots.','Municipal cases do not constitute external national-presidential validation.']}
 (folder/'resultado_externo_v41_2024.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
def run():
 freeze=json.loads((ROOT/'congelamento_guard_v41.json').read_text());assert hashlib.sha256((ROOT/'preditor_causal_v4.py').read_bytes()).hexdigest()==freeze['core_sha256_unchanged']
 for r in freeze['files']:assert hashlib.sha256((ROOT/r['name']).read_bytes()).hexdigest()==r['sha256']
 cases=[evaluate_case(code) for code in CASES];summary={'protocol_commit':'537cc770f07855a3bef0a5febe3ac719dcb427dd','model_unchanged':True,'cases':[{k:v for k,v in c.items() if k!='points'} for c in cases],'accepted_cases':sum(c['status']=='ACCEPTED_IN_PREDEFINED_BENCHMARK' for c in cases),'evaluated_cases':sum(c['status']!='DATA_BLOCKED' for c in cases),'decision':'BENCHMARK_COMPLETED_NO_AUTOMATIC_INTEGRAL_CERTIFICATION'};(ROOT/'resumo_externo_v41_2024.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False),flush=True);return summary
if __name__=='__main__':run()
