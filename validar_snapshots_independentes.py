"""Validação conservadora de snapshots parciais independentes (JSONL).
Não confundir registros retrospectivos com observações contemporâneas.
Formato por linha: captured_at, source_url, source_sha256, sections_counted,
sections_total, lula, flavio. Evidência precisa ser obtida externamente e
auditada; este script valida formato/consistência, não autenticidade da fonte.
"""
import argparse,datetime as dt,hashlib,json
from pathlib import Path

FIELDS=('captured_at','source_url','source_sha256','sections_counted','sections_total','lula','flavio')
def validate(path):
 p=Path(path)
 if not p.is_file():raise ValueError('Arquivo de snapshots inexistente')
 records=[]
 for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip():continue
  try:r=json.loads(line)
  except json.JSONDecodeError as e:raise ValueError(f'Linha {i}: JSON inválido') from e
  if any(k not in r for k in FIELDS):raise ValueError(f'Linha {i}: campos obrigatórios ausentes')
  try:
   timestamp=dt.datetime.fromisoformat(r['captured_at'].replace('Z','+00:00'))
  except (ValueError,AttributeError) as e:raise ValueError(f'Linha {i}: horário inválido') from e
  if timestamp.tzinfo is None:raise ValueError(f'Linha {i}: horário sem fuso')
  if not isinstance(r['source_url'],str) or not r['source_url'].startswith('https://'):raise ValueError(f'Linha {i}: URL de origem inválida')
  if not isinstance(r['source_sha256'],str) or len(r['source_sha256'])!=64 or any(c not in '0123456789abcdef' for c in r['source_sha256'].lower()):raise ValueError(f'Linha {i}: SHA256 inválido')
  for k in ('sections_counted','sections_total','lula','flavio'):
   if type(r[k]) is not int or r[k]<0:raise ValueError(f'Linha {i}: {k} inválido')
  if r['sections_total']<1 or r['sections_counted']>r['sections_total']:raise ValueError(f'Linha {i}: seções inconsistentes')
  if r['lula']+r['flavio']<1:raise ValueError(f'Linha {i}: votos ausentes')
  records.append((timestamp,r))
 if not records:raise ValueError('Nenhum snapshot')
 for (a,x),(b,y) in zip(records,records[1:]):
  if b<=a:raise ValueError('Capturas fora de ordem temporal')
  if y['sections_counted']<x['sections_counted']:raise ValueError('Seções contabilizadas diminuíram')
  if y['lula']<x['lula'] or y['flavio']<x['flavio']:raise ValueError('Votos acumulados diminuíram')
 return {'snapshots':len(records),'first':records[0][0].isoformat(),'last':records[-1][0].isoformat(),'min_coverage':records[0][1]['sections_counted']/records[0][1]['sections_total'],'max_coverage':records[-1][1]['sections_counted']/records[-1][1]['sections_total'],'format_valid':True,'source_authenticity_verified':False,'historical_forecast_certified':False}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('file');x=a.parse_args()
 print(json.dumps(validate(x.file),ensure_ascii=False,indent=2))
