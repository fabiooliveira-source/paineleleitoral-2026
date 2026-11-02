"""Ajustes municipais independentes sobre pacotes por seção conciliados.
Não reconstitui flags ausentes: registra explicitamente o universo disponível.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import base64,gzip,json
from pathlib import Path
import numpy as np
from inferencia_eleitoral import fit_territory,bounds
p=Path(__file__).parent/'dados/2026'
def read(path):
 raw=path.read_bytes()
 try:o=json.loads(gzip.decompress(raw))
 except (OSError,EOFError):o=json.loads(raw)
 return json.loads(gzip.decompress(base64.b64decode(o['dados']))) if isinstance(o,dict) and 'dados' in o else o
master=read(p/'inferencia-resultados.json');origins=master['origins']
for path in sorted(p.glob('secoes-*.json.gz')):
 uf=path.name.split('-')[1].split('.')[0];data=read(path);cols=data['colunas'];idx={c:i for i,c in enumerate(cols)}
 cand=read(p/f'candidatos-secao-{uf}.json');lookup={tuple(str(int(v)) for v in row[:3]):row[3:] for row in cand['linhas']}
 nums=cand['numeros'];rows={};excluded={}
 for row in data['linhas']:
  code=str(int(row[0]));key=tuple(str(int(row[idx[k]])) for k in ['codigo_municipio_tse','zona','secao']);v=lookup.get(key)
  get=lambda k:row[idx[k]]
  if v is None:excluded[code]=excluded.get(code,0)+1;continue
  x=[get('lula_1t'),get('flavio_1t')]+[v[nums.index(n)] if n in nums else 0 for n in ['14','16','21','27','28','29','30','35','55','70','80']]+[get('brancos_1t'),get('nulos_1t'),get('abstencoes_1t')]
  y=[get(k+'_2t') for k in ['lula','flavio','brancos','nulos','abstencoes']];n=get('aptos_1t')
  if not all(isinstance(a,(int,float)) and np.isfinite(a) and a>=0 and a%1==0 for a in x+y+[n]) or n<=0 or n!=get('aptos_2t') or sum(x)!=n or sum(y)!=n or str(get('local_votacao_1t'))!=str(get('local_votacao_2t')) or any(get('situacao_dados_'+t)!='conferido' or get('comparecimento_'+t)+get('abstencoes_'+t)!=n for t in ['1t','2t']):
   excluded[code]=excluded.get(code,0)+1;continue
  rows.setdefault(code,[]).append((x,y,n))
 results={}
 for code,rr in rows.items():
  X=np.array([a for a,b,n in rr]);Y=np.array([b for a,b,n in rr]);N=np.array([n for a,b,n in rr]);active=X.sum(axis=0)>0
  try:fit=fit_territory(X,Y,N,np.full(len(N),code),origins,B=0)
  except RuntimeError as e:fit={'status':'optimization_failed','n':len(N),'error':str(e)}
  lo,hi=bounds(X,Y,N);mask=active if fit.get('rates') else np.ones(len(origins),bool)
  fit.update(origins=np.array(origins)[mask].tolist(),destinations=master['destinations'],origin_totals=X[:,mask].sum(axis=0).tolist(),destination_totals=Y.sum(axis=0).tolist(),bounds_min=lo[:,mask].sum(axis=0).tolist(),bounds_max=hi[:,mask].sum(axis=0).tolist(),grouped_bounds={},excluded_sections=excluded.get(code,0),municipal_warning='Ajuste municipal independente, sem bootstrap municipal. Pacotes não contêm flags de instalação/anulação; universo não equivale à auditoria nacional completa.')
  results['MUN:'+uf+':'+code]=fit
 out={'territories':results,'scope':'municipal_sections_available','source':'secoes-'+uf+'.json.gz + candidatos-secao-'+uf+'.json','limitation':'Sem flags de instalação/anulação nos pacotes; filtros de conciliação, cadastro e local reaplicados.'}
 (p/f'inferencia-municipios-{uf}.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print(uf,len(results),sum(bool(v.get('rates')) for v in results.values()),flush=True)
