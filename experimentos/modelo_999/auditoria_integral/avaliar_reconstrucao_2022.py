"""Backtest condicionado à reconstrução oficial, não captura operacional de parciais.
Preditor audit-v2 inalterado. Protocolo: protocolo_reconstrucao_2022_v1.json.
"""
import pathlib,pickle,json,datetime,collections,bisect,hashlib,csv,zipfile,io
from preditor_causal_v2 import predict
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'microdados'
TZ=datetime.timezone(datetime.timedelta(hours=-3))
def run():
 manifest=json.loads((ROOT/'congelamento_v2.json').read_text())
 entry=next(x for x in manifest['files'] if x['path'].endswith('/preditor_causal_v2.py'))
 actual=hashlib.sha256((ROOT/'preditor_causal_v2.py').read_bytes()).hexdigest()
 assert actual==entry['sha256'],'preditor alterado apos congelamento'
 diag=json.loads((ROOT/'reconstrucao_diagnostico_2022.json').read_text())
 assert diag['national_curve_comparison']['all_fields_exact'],'Reconstrucao diverge do controle nacional'
 assert not diag['missing_detail_count'] and not diag['bad_sums_count'],'Falha de integracao'
 with (DATA/'reconstrucao_cache.pkl').open('rb') as f:events,first,official,aligned=pickle.load(f)
 with zipfile.ZipFile(DATA/'Historico_Totalizacao_Presidente_BR_1T_2022.zip') as z:
  name=next(n for n in z.namelist() if n.endswith('.csv'))
  r=csv.reader(io.StringIO(z.read(name).decode('latin1')),delimiter=';');h=[x.strip() for x in next(r)];last=list(r)[-1];control=dict(zip(h,[x.strip() for x in last]))
 totals=[sum(v[j] for v in first.values()) for j in range(3)]
 expected=[int(control[k]) for k in ['LULA_QT_VOTOS_TOT_ACUMULADO','JAIR_BOLSONARO_QT_VOTOS_TOT_ACUMULADO','QT_VOTOS_CONCORRENTES_ACUMULADO']]
 assert totals==expected,(totals,expected)
 # Cenário explícito: referência 1T disponível no instante do último controle BR.
 # Correspondência nacional não autentica a versão UF disponível naquela data.
 assumed_first_availability=datetime.datetime.strptime(control['DT_TOTALIZACAO'],'%d/%m/%Y %H:%M:%S').replace(tzinfo=TZ).isoformat()
 history={u:{'votes_a':v[0],'votes_b':v[1],'valid_votes':v[2],'available_at':assumed_first_availability} for u,v in first.items()}
 assert len(history)==28
 by_uf=collections.defaultdict(list)
 acc=collections.defaultdict(lambda:[0,0,0])
 # Agregar simultâneos por UF: um único estado cumulativo por timestamp.
 increments=collections.defaultdict(lambda:[0,0,0])
 for t,key,v in events:
  x=increments[t,key[0]];x[0]+=v[0];x[1]+=v[1];x[2]+=1
 for (t,uf),delta in sorted(increments.items()):
  x=acc[uf]
  for j in range(3):x[j]+=delta[j]
  by_uf[uf].append((t,*x))
 times={u:[x[0] for x in rr] for u,rr in by_uf.items()}
 A='LULA_QT_VOTOS_TOT_ACUMULADO';B='JAIR_BOLSONARO_QT_VOTOS_TOT_ACUMULADO'
 target=int(official[-1][A])/(int(official[-1][A])+int(official[-1][B]))
 scenarios={'referencia':(0,set()),'atraso_5min':(300,set()),'atraso_15min':(900,set()),'atraso_30min':(1800,set()),'sem_SP':(0,{'SP'}),'sem_SP_MG_RJ':(0,{'SP','MG','RJ'}),'sem_Nordeste':(0,set('AL BA CE MA PB PE PI RN SE'.split()))}
 results={};inputs=[]
 for scenario,(delay,drop) in scenarios.items():
  points=[]
  for pct in range(5,100,5):
   r=next(r for r in official if int(r['QT_SECOES_TOT_ACUMULADO'])/int(r['QT_SECOES_TOTAL'])*100>=pct)
   t=datetime.datetime.strptime(r['DT_TOTALIZACAO'],'%d/%m/%Y %H:%M:%S');iso=t.replace(tzinfo=TZ).isoformat()
   current={'timestamp':iso,'available_at':iso,'votes_a':int(r[A]),'votes_b':int(r[B]),'counted_sections':int(r['QT_SECOES_TOT_ACUMULADO']),'total_sections':int(r['QT_SECOES_TOTAL'])}
   states=[]
   for uf in sorted(by_uf):
    if uf in drop:continue
    idx=bisect.bisect_right(times[uf],t-datetime.timedelta(seconds=delay))-1
    if idx<0:continue
    tt,aa,bb,ss=by_uf[uf][idx]
    states.append({'scope':uf,'timestamp':tt.replace(tzinfo=TZ).isoformat(),'available_at':(tt+datetime.timedelta(seconds=delay)).replace(tzinfo=TZ).isoformat(),'votes_a':aa,'votes_b':bb})
   forecast=predict(current,history,states)
   points.append({'threshold_pct':pct,'timestamp':iso,'forecast_a_pct':100*forecast['forecast_a'],'baseline_a_pct':100*forecast['baseline_a'],'error_pp':100*(forecast['forecast_a']-target),'baseline_error_pp':100*(forecast['baseline_a']-target),'fresh_territories':forecast['fresh_territories'],'mode':forecast['mode']})
   if scenario=='referencia':inputs.append({'threshold_pct':pct,'current':current,'first_round':history,'territorial':states})
  errors=[p['error_pp'] for p in points];base=[p['baseline_error_pp'] for p in points]
  results[scenario]={'mae_pp':sum(map(abs,errors))/len(errors),'max_abs_error_pp':max(map(abs,errors)),'bias_pp':sum(errors)/len(errors),'baseline_mae_pp':sum(map(abs,base))/len(base),'improved_checkpoints':sum(abs(p['error_pp'])<abs(p['baseline_error_pp']) for p in points),'checkpoints':points}
 out={'status':'TESTE_TERRITORIAL_RECONSTRUIDO_CONDICIONAL_EXECUTADO_NAO_CERTIFICADO','predictor_commit':'419593081c7178a9b4e293cb0b13befe1808fe1a','predictor_sha256':actual,'protocol_commit':'43d355d5b22a869ecd5e02b9487784ebd45e7030','history_territories':len(history),'first_round_national_totals_match':totals==expected,'first_round_reference_availability_assumption':assumed_first_availability,'national_curve_comparison':diag['national_curve_comparison'],'final_lula_pct':target*100,'scenarios':results,'limitations':['Reconstrucao por votos finais e primeira totalizacao; nao captura original de parciais UF.','Igualdade nacional em todos os snapshots nao prova igualdade UF em todos os instantes: compensacoes entre UFs sao possiveis.','Disponibilidade simultanea a totalizacao e hipotese de cenario, nao fato observado de publicacao.','Primeiro turno UF usa versao retrospectiva; comparacao nacional nao autentica sua versao disponivel na data assumida.','Idade UF usa ultima mudanca reconstruida; nao recupera republicacoes sem alteracao ou cache real do coletor.','Atrasos e exclusoes mudam disponibilidade UF; votos BR continuam os oficiais, sem simular nova ordem nacional.','Os 19 marcos sao dependentes; nao inferir probabilidade de acerto ou certificacao integral.']}
 (ROOT/'backtest_territorial_reconstruido_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'entradas_checkpoints_reconstruidos_2022.json').write_text(json.dumps({'provenance':'Reconstrucao condicional; veja protocolo e limitacoes.','assumed_available_at':True,'first_round':history,'checkpoints':[{k:v for k,v in x.items() if k!='first_round'} for x in inputs]},ensure_ascii=False,separators=(',',':'))+'\n')
 print(json.dumps({'status':out['status'],'scenarios':{k:{kk:vv for kk,vv in v.items() if kk!='checkpoints'} for k,v in results.items()}},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
