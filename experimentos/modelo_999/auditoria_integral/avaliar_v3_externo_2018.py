"""Teste entre eleições, condicionado à reconstrução. Não ajusta o modelo."""
import pathlib,json,pickle,collections,datetime,bisect,hashlib
from preditor_causal_v2 import predict as v2
from preditor_causal_v3 import predict as v3
ROOT=pathlib.Path(__file__).resolve().parent
TZ=datetime.timezone(datetime.timedelta(hours=-3))
SCENARIOS={'referencia':(0,set()),'atraso_5min':(300,set()),'atraso_15min':(900,set()),'atraso_30min':(1800,set()),'sem_SP':(0,{'SP'}),'sem_SP_MG_RJ':(0,{'SP','MG','RJ'}),'sem_Nordeste':(0,set('AL BA CE MA PB PE PI RN SE'.split()))}

def metrics(points):
 errors=[x['error_pp'] for x in points];correct=[x['winner_correct'] for x in points]
 stable=next((points[i]['threshold_pct'] for i in range(len(points)) if all(correct[i:])),None)
 return {'mae_pp':sum(map(abs,errors))/len(errors),'max_abs_error_pp':max(map(abs,errors)),'bias_pp':sum(errors)/len(errors),'winner_correct_checkpoints':sum(correct),'first_sampled_stable_correct_winner_pct':stable,'checkpoints':points}

def run():
 for model in ['v2','v3']:
  manifest=json.loads((ROOT/f'congelamento_{model}.json').read_text());entry=next(x for x in manifest['files'] if x['path'].endswith(f'preditor_causal_{model}.py'))
  assert hashlib.sha256((ROOT/f'preditor_causal_{model}.py').read_bytes()).hexdigest()==entry['sha256'],'Preditor congelado alterado'
 with (ROOT/'microdados2018/replay_cache.pkl').open('rb') as f:events,first,denominator,diag=pickle.load(f)
 cutoff=datetime.datetime(2018,10,29,23,59,59)
 increments=collections.defaultdict(lambda:[0,0,0]);national_increment=collections.defaultdict(lambda:[0,0,0])
 for t,key,v in events:
  for bucket in [increments[t,key[0]],national_increment[t]]:
   bucket[0]+=v[0];bucket[1]+=v[1];bucket[2]+=1
 by_uf=collections.defaultdict(list);acc=collections.defaultdict(lambda:[0,0,0])
 for (t,u),delta in sorted(increments.items()):
  state=acc[u]
  for j in range(3):state[j]+=delta[j]
  by_uf[u].append((t,*state))
 times={u:[x[0] for x in rr] for u,rr in by_uf.items()}
 national=[];state=[0,0,0]
 for t,delta in sorted(national_increment.items()):
  for j in range(3):state[j]+=delta[j]
  if t<=cutoff:national.append((t,*state))
 selected=[]
 for pct in range(5,100,5):
  found=next((row for row in national if 100*row[3]/denominator>=pct),None)
  assert found is not None,'Marco nao atingido na janela predefinida'
  selected.append((pct,found))
 history={u:{'votes_a':v[0],'votes_b':v[1],'valid_votes':v[2],'available_at':'2018-10-27T00:00:00-03:00'} for u,v in first.items()}
 assert len(history)==28
 target=diag['all_source_votes'][0]/sum(diag['all_source_votes'][:2]);results={};saved=[]
 for scenario,(delay,drop) in SCENARIOS.items():
  points={'v2':[],'v3':[],'baseline':[]}
  for pct,(t,a,b,ss) in selected:
   now=t.replace(tzinfo=TZ);iso=now.isoformat();c={'timestamp':iso,'available_at':iso,'votes_a':a,'votes_b':b,'counted_sections':ss,'total_sections':denominator};states=[]
   for u in sorted(by_uf):
    if u in drop:continue
    index=bisect.bisect_right(times[u],t-datetime.timedelta(seconds=delay))-1
    if index<0:continue
    tt,aa,bb,_=by_uf[u][index];generated=tt.replace(tzinfo=TZ)
    states.append({'scope':u,'timestamp':generated.isoformat(),'available_at':(generated+datetime.timedelta(seconds=delay)).isoformat(),'votes_a':aa,'votes_b':bb})
   for model,fn in [('v2',v2),('v3',v3),('baseline',None)]:
    prediction=fn(c,history,states) if fn else {'forecast_a':a/(a+b),'swing':0,'fresh_territories':0,'mode':'baseline'}
    pred=prediction['forecast_a'];points[model].append({'threshold_pct':pct,'timestamp':iso,'forecast_a_pct':100*pred,'error_pp':100*(pred-target),'winner_correct':(pred>.5)==(target>.5),'swing_pp':100*prediction['swing'],'fresh_territories':prediction['fresh_territories'],'mode':prediction['mode']})
   if scenario=='referencia':saved.append({'threshold_pct':pct,'current':c,'territorial':states})
  results[scenario]={model:metrics(pp) for model,pp in points.items()}
 a=results['referencia']['v2'];b=results['referencia']['v3'];worst={m:max(s[m]['max_abs_error_pp'] for s in results.values()) for m in ['v2','v3']}
 criteria={'lower_reference_mae':b['mae_pp']<a['mae_pp'],'reference_max_not_worse':b['max_abs_error_pp']<=a['max_abs_error_pp']+1e-12,'reference_abs_bias_not_worse':abs(b['bias_pp'])<=abs(a['bias_pp'])+1e-12,'worst_stress_max_not_worse':worst['v3']<=worst['v2']+1e-12}
 result={'status':'TESTE_EXTERNO_2018_RECONSTRUIDO_CONCLUIDO','predictor_v3_freeze_commit':'8fd1d1705e9d843fbf6a8209432d0fa6bcdf9ae4','parameters_changed_after_2018':False,'primary_candidate':'FERNANDO HADDAD 13','other_candidate':'JAIR BOLSONARO 17','target_a_pct':100*target,'denominator_sections_first_round':denominator,'national_reconstructed_timestamps_in_window':len(national),'criteria':criteria,'all_criteria_passed':all(criteria.values()),'decision':'PASSA_NOS_CRITERIOS_NUMERICOS_DO_REPLAY' if all(criteria.values()) else 'NAO_PROMOVER_V3_CRITERIOS_EXTERNOS_FALHARAM','worst_stress_max_pp':worst,'scenarios':results,'limitations':['Reconstrucao por votos finais, primeira totalizacao e disponibilidade simultanea assumida; nao parciais publicas originais.','Nao foi obtido historico nacional oficial2018 para confronto integral da curva como feito2022.','Referencia UF1T retrospectiva; versao contemporanea nao autenticada.','Denominador e cadastro do primeiro turno, recuperado retrospectivamente; disponibilidade previa assumida.','Eventos tardios mantidos fora da janela e incluidos apenas no alvo final de avaliacao.','Uma eleicao externa e checkpoints correlacionados nao calibram probabilidades nem certificam operacionalmente.']}
 (ROOT/'resultado_externo_v3_2018.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'entradas_externas_2018.json').write_text(json.dumps({'year':2018,'assumed_available_at':True,'first_round':history,'checkpoints':saved},ensure_ascii=False,separators=(',',':'))+'\n')
 print(json.dumps({'decision':result['decision'],'criteria':criteria,'reference':{m:{k:v for k,v in results['referencia'][m].items() if k!='checkpoints'} for m in ['baseline','v2','v3']},'worst_stress':worst},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
