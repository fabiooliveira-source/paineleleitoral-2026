"""Avalia preditor congelado, sem ajuste. Limites físicos != probabilidade."""
import pathlib,json,hashlib,datetime,sys,math
from preditor_causal_v4 import predict
ROOT=pathlib.Path(__file__).resolve().parent

def run(year):
 manifest=json.loads((ROOT/'congelamento_v4.json').read_text());entry=next(x for x in manifest['files'] if x['path'].endswith('/preditor_causal_v4.py'))
 assert hashlib.sha256((ROOT/'preditor_causal_v4.py').read_bytes()).hexdigest()==entry['sha256'],'Frozen predictor changed'
 source=ROOT/f'entradas_pareadas_v4_{year}.json';d=json.loads(source.read_text());reference=d['reference'];target=d['target_a'];points=[];stress=0
 for x in d['checkpoints']:
  c=x['current'];ledger=x['ledger'];p=predict(c,reference,ledger);observed=c['votes_a']/(c['votes_a']+c['votes_b']);winner='a' if target>.5 else 'b'
  now=datetime.datetime.fromisoformat(c['timestamp'])
  assert all(datetime.datetime.fromisoformat(r['available_at'])<=now for r in reference.values())
  assert all(datetime.datetime.fromisoformat(r['timestamp'])<=now and datetime.datetime.fromisoformat(r['available_at'])<=now for r in ledger)
  missing=predict(c,reference,ledger[1:]);assert missing['estimate_a'] is None;stress+=1
  delayed=[dict(r) for r in ledger];delayed[0]['timestamp']=delayed[0]['available_at']=(now-datetime.timedelta(seconds=60)).isoformat();assert predict(c,reference,delayed)['estimate_a'] is None;stress+=1
  later=(now+datetime.timedelta(days=1)).isoformat();future=dict(ledger[0],timestamp=later,available_at=later,votes_a=999999999);assert predict(c,reference,ledger+[future])==p;stress+=1
  assert predict(c,reference,list(reversed(ledger)))==p;stress+=1
  inconsistent=[dict(r) for r in ledger];inconsistent[0]['votes_a']+=1;assert predict(c,reference,inconsistent)['estimate_a'] is None;stress+=1
  point={'threshold_pct':x['threshold_pct'],'timestamp':c['timestamp'],'baseline_a_pct':100*observed,'baseline_error_pp':100*(observed-target),'estimate_a_pct':None if p['estimate_a'] is None else 100*p['estimate_a'],'error_pp':None if p['estimate_a'] is None else 100*(p['estimate_a']-target),'lower_a_pct':100*p['lower_a'],'upper_a_pct':100*p['upper_a'],'target_within_conditional_bounds':p['lower_a']-1e-12<=target<=p['upper_a']+1e-12,'conditional_winner':p['conditional_winner'],'conditional_call_correct':None if p['conditional_winner'] is None else p['conditional_winner']==winner,'status':p['status'],'reason':p['reason']};points.append(point)
 errors=[x['error_pp'] for x in points if x['error_pp'] is not None];base=[x['baseline_error_pp'] for x in points]
 def metrics(e):return {'mae_pp':sum(map(abs,e))/len(e),'max_abs_error_pp':max(map(abs,e)),'bias_pp':sum(e)/len(e)} if e else None
 model=metrics(errors);baseline=metrics(base)
 criteria={'all_19_estimates_available':len(errors)==19,'lower_mae_than_baseline':bool(model and model['mae_pp']<baseline['mae_pp']),'maximum_not_worse_than_baseline':bool(model and model['max_abs_error_pp']<=baseline['max_abs_error_pp']),'conditional_bounds_cover_all_targets':all(x['target_within_conditional_bounds'] for x in points),'no_wrong_conditional_call':not any(x['conditional_call_correct'] is False for x in points),'all_95_stress_checks_passed':stress==95}
 result={'model':'audit-v4-paired-ratio','year':year,'role':'external_reconstructed_municipal_test' if year==2020 else 'development_reconstructed_presidential','predictor_freeze_commit':'04ea90abb8c535f8ee17eeb26fa781b246e03e88','source_inputs_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'parameters_fitted':False,'model_metrics':model,'baseline_metrics':baseline,'estimates_available':len(errors),'criteria':criteria,'all_numerical_criteria_passed':all(criteria.values()),'stress_checks_passed':stress,'first_conditional_call_pct':next((x['threshold_pct'] for x in points if x['conditional_winner'] is not None),None),'conditional_calls':sum(x['conditional_winner'] is not None for x in points),'checkpoints':points,'certification_integral':False,'scope_limit':'Bounds are deterministic conditional on no future revision and valid electorate upper bound. Pairing and availability are reconstructed, not authenticated live public snapshots. External municipal case does not certify national operational transfer.'}
 (ROOT/f'resultado_v4_{year}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='checkpoints'},ensure_ascii=False),flush=True)
 return result
if __name__=='__main__':run(int(sys.argv[1]))
