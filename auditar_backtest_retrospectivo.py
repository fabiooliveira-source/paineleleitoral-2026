"""Auditável: compara projeções retrospectivas ao resultado final SEM certificá-las."""
import argparse,json
from pathlib import Path
def audit(source):
 d=json.loads(Path(source).read_text(encoding='utf-8'))
 if 'Votos finais atribuídos' not in d.get('source',''):
  raise ValueError('Fonte desconhecida: classificação manual necessária')
 ticks=d['ticks']
 final=ticks[-1]
 if final['target']!=100 or final['remaining_electorate']!=0:
  raise ValueError('Resultado final não está fechado')
 total=final['observed_lula']+final['observed_flavio']
 if not total:raise ValueError('Votos finais ausentes')
 true_share=final['observed_lula']/total
 rows=[]
 for t in ticks:
  models={}
  for name,model in t['models'].items():
   scenarios=[]
   for s in model['scenarios']:
    err=100*(s['share_lula_median']-true_share)
    scenarios.append({'prior':s['prior_pseudo_sections'],'estimated_lula_pct':100*s['share_lula_median'],'error_pp':err,'absolute_error_pp':abs(err),'p_lula':s['p_lula']})
   models[name]={'scenarios':scenarios,'max_absolute_error_pp':max(x['absolute_error_pp'] for x in scenarios)}
  rows.append({'target':t['target'],'time':t['time'],'sections_share':t['sections_share'],'models':models})
 return {'classification':'RETROSPECTIVO_COM_RISCO_DE_VAZAMENTO_TEMPORAL','historical_forecast_certified':False,'source':d['source'],'final_lula':final['observed_lula'],'final_flavio':final['observed_flavio'],'final_lula_pct':100*true_share,'rows':rows,'limitation':'Horários atribuídos a votos finais não comprovam que esses votos estavam disponíveis na ocasião. Não estimar taxa histórica de acerto nem calibrar probabilidades.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',default='dados/2026/previsao-territorial.json');p.add_argument('--output',default='dados/2026/backtest_retrospectivo_auditavel.json');a=p.parse_args()
 result=audit(a.input)
 Path(a.output).parent.mkdir(parents=True,exist_ok=True)
 Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('BACKTEST_RETROSPECTIVO',len(result['rows']),'marcos; certificacao:',result['historical_forecast_certified'])
