"""Conferência aritmética separada e testes de informação futura nas entradas externas."""
import pathlib,json,datetime,math
ROOT=pathlib.Path(__file__).resolve().parent

def run():
 d=json.loads((ROOT/'resultado_externo_v3_2018.json').read_text());inputs=json.loads((ROOT/'entradas_externas_2018.json').read_text());first=inputs['first_round'];diffs={m:[] for m in ['v2','v3']};future_tests=0
 for item in inputs['checkpoints']:
  c=item['current'];now=datetime.datetime.fromisoformat(c['timestamp']);terms=[];weights=[]
  assert all(datetime.datetime.fromisoformat(x['available_at'])<=now for x in first.values())
  for r in item['territorial']:
   t=datetime.datetime.fromisoformat(r['timestamp']);available=datetime.datetime.fromisoformat(r['available_at']);assert t<=now and available<=now
   age=(now-t).total_seconds();n=r['votes_a']+r['votes_b'];h=first[r['scope']]
   if age<=300 and n:
    w=min(n,h['valid_votes'])*(1-age/600);weights.append(w);terms.append(w*(r['votes_a']/n-h['votes_a']/(h['votes_a']+h['votes_b'])))
  raw=math.fsum(terms)/math.fsum(weights) if weights else 0
  for model,alpha in [('v2',1),('v3',.25)]:
   prior=math.fsum(h['valid_votes']*min(1,max(0,h['votes_a']/(h['votes_a']+h['votes_b'])+alpha*raw)) for h in first.values())/sum(h['valid_votes'] for h in first.values())
   coverage=c['counted_sections']/c['total_sections'];forecast=coverage*c['votes_a']/(c['votes_a']+c['votes_b'])+(1-coverage)*prior
   out=next(x for x in d['scenarios']['referencia'][model]['checkpoints'] if x['threshold_pct']==item['threshold_pct']);delta=abs(100*forecast-out['forecast_a_pct']);assert delta<1e-10;diffs[model].append(delta)
   module=__import__('preditor_causal_'+model);pred=module.predict(c,first,item['territorial'])
   later=(now+datetime.timedelta(days=1)).isoformat();row={'scope':next(iter(first)),'timestamp':later,'available_at':later,'votes_a':999999999,'votes_b':1}
   assert module.predict(c,first,item['territorial']+[row])==pred;future_tests+=1
 for scenario in d['scenarios'].values():
  for scores in scenario.values():
   rows=scores['checkpoints'];errors=[x['forecast_a_pct']-d['target_a_pct'] for x in rows];assert len(rows)==19
   assert max(abs(e-x['error_pp']) for e,x in zip(errors,rows))<1e-10
   assert abs(scores['mae_pp']-math.fsum(map(abs,errors))/19)<1e-10
   assert abs(scores['max_abs_error_pp']-max(map(abs,errors)))<1e-10
   assert abs(scores['bias_pp']-math.fsum(errors)/19)<1e-10
 result={'reference_points_recomputed_per_model':19,'models_recomputed':['v2','v3'],'max_difference_pp':{k:max(v) for k,v in diffs.items()},'future_injection_tests_passed':future_tests,'scenario_model_metrics_checked':21,'scope':'Aritmetica e filtros das entradas reconstruidas; nao autentica horarios publicos nem equivale a revisao humana independente.'}
 (ROOT/'verificacao_externa_2018_v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':run()
