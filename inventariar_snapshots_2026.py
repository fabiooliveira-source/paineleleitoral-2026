"""Inventory timestamped historical snapshots; reject synthetic temporal backtests."""
import pathlib,re,json,datetime
root=pathlib.Path('.')
patterns=('**/*snapshot*.json','**/*snapshot*.jsonl','**/*parcial*.json','**/*historico*.json','**/*timeline*.json')
found=set()
for pattern in patterns:
 for p in root.glob(pattern):
  if '.git' in p.parts or 'node_modules' in p.parts or 'originais_tse' in p.parts:continue
  if p.is_file() and p.stat().st_size<50_000_000:found.add(p.as_posix())
files=[]
for name in sorted(found):
 p=root/name;size=p.stat().st_size
 try:
  with p.open(encoding='utf-8') as f: sample=f.read(12000)
 except (OSError,UnicodeError):continue
 # Content must show independent observed time and data payload; naming alone insufficient.
 files.append({'path':name,'bytes':size,'has_timestamp_field':bool(re.search(r'(?:timestamp|capturad[oa]|consultad[oa]|data_hora|generated_at|coletad[oa])',sample,re.I)),'has_vote_field':bool(re.search(r'(?:votos|votes|candidatos|cand)',sample,re.I))})
eligible=[x for x in files if x['has_timestamp_field'] and x['has_vote_field']]
report={'auditoria_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidatos_a_snapshot':files,'candidatos_com_campos_minimos':eligible,'historical_backtest_approved':False,'explanation':'Arquivo com campos de horario e votos ainda requer comprovar captura contemporanea, cobertura e ausencia de vazamento. Nenhum arquivo e certificado automaticamente.','next_action':'Obter capturas contemporaneas originais do EA15/EA20 com hash e timestamp de aquisicao; validar ordem temporal e calibracao.'}
out=pathlib.Path('inventario_snapshots_2026.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('INVENTARIO_SNAPSHOTS',json.dumps(report,ensure_ascii=False))
