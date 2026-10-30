"""Safety gate: no claim of historical predictive validation from final section votes."""
from pathlib import Path
import ast,json
source=Path('previsao_territorial.py').read_text(encoding='utf-8')
tree=ast.parse(source)
assert 'Votos finais atribuídos' in source
assert 'Backtest retrospectivo' in source
assert 'não certeza calibrada' in source
assert 'não usa final 2T' in source
assert 'times=d.time.to_numpy()' in source
report={'historical_forecast_certified':False,'reason':'Backtest retrospectivo atribui votos finais a tempos de primeira totalizacao; nao ha snapshots historicos observados por instante.','model':'previsao_territorial.py','tests':['Fonte marcada como retrospectiva','Aviso de probabilidade nao calibrada','Uso de tempos nao comprova disponibilidade de votos naqueles tempos'],'required':['Capturas originais TSE por instante','Reconstrucao de informacao disponivel a cada corte','Backtest sem vazamento temporal','Calibracao empirica e stress tests']}
Path('resultado_gate_previsao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('GATE_PREVISAO',json.dumps(report,ensure_ascii=False))
