"""Verificação aritmética separada: não importa nem chama o preditor."""
import json,pathlib,datetime,math
ROOT=pathlib.Path(__file__).resolve().parent

def run():
 d=json.loads((ROOT/'backtest_territorial_reconstruido_2022.json').read_text())
 inputs=json.loads((ROOT/'entradas_checkpoints_reconstruidos_2022.json').read_text())
 history=inputs['first_round'];checks=[];future=0
 for item,output in zip(inputs['checkpoints'],d['scenarios']['referencia']['checkpoints']):
  c=item['current'];now=datetime.datetime.fromisoformat(c['timestamp']);terms=[];weights=[]
  assert item['threshold_pct']==output['threshold_pct']
  for row in history.values():assert datetime.datetime.fromisoformat(row['available_at'])<=now
  for r in item['territorial']:
   t=datetime.datetime.fromisoformat(r['timestamp']);arrival=datetime.datetime.fromisoformat(r['available_at']);future+=int(arrival>now or t>now)
   assert arrival<=now and t<=now
   age=(now-t).total_seconds();v=r['votes_a']+r['votes_b'];h=history[r['scope']]
   if age<=300 and v:
    w=min(v,h['valid_votes'])*(1-age/600);terms.append(w*(r['votes_a']/v-h['votes_a']/(h['votes_a']+h['votes_b'])));weights.append(w)
  swing=math.fsum(terms)/math.fsum(weights) if weights else 0
  prior=math.fsum(h['valid_votes']*min(1,max(0,h['votes_a']/(h['votes_a']+h['votes_b'])+swing)) for h in history.values())/sum(h['valid_votes'] for h in history.values())
  coverage=c['counted_sections']/c['total_sections'];forecast=coverage*(c['votes_a']/(c['votes_a']+c['votes_b']))+(1-coverage)*prior
  difference=abs(100*forecast-output['forecast_a_pct']);assert difference<1e-10;checks.append(difference)
 assert len(checks)==19
 for scenario in d['scenarios'].values():
  points=scenario['checkpoints'];errors=[x['forecast_a_pct']-d['final_lula_pct'] for x in points]
  assert len(points)==19
  assert all(abs(e-x['error_pp'])<1e-10 for e,x in zip(errors,points))
  assert abs(sum(map(abs,errors))/19-scenario['mae_pp'])<1e-10
  assert abs(max(map(abs,errors))-scenario['max_abs_error_pp'])<1e-10
  assert abs(sum(errors)/19-scenario['bias_pp'])<1e-10
 out={'checked_points':len(checks),'checked_scenarios':len(d['scenarios']),'max_forecast_difference_pp':max(checks),'future_records_in_reference_inputs':future,'method':'Calculo separado com math.fsum, sem chamar predict; conferencia de metricas em sete cenarios. Nao autentica disponibilidade publica e nao constitui revisao humana independente.'}
 (ROOT/'verificacao_aritmetica_reconstrucao_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':run()
