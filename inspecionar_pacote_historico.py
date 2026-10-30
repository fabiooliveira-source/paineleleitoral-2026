"""Inspect gzip+base64 historical package without treating inferred times as captures."""
import base64,gzip,json,pathlib,collections,re,datetime
p=pathlib.Path('dados/comparativo_historico_pacote.json')
wrapper=json.loads(p.read_text(encoding='utf-8'))
assert wrapper.get('codificacao')=='gzip+base64','Formato nao esperado'
payload=base64.b64decode(wrapper['dados'],validate=True)
raw=gzip.decompress(payload)
assert len(raw)<200_000_000,'Pacote excessivamente grande'
data=json.loads(raw)
def walk(x,depth=0):
 if depth>4:return {'tipo':type(x).__name__}
 if isinstance(x,dict):
  return {'tipo':'objeto','chaves':list(x)[:80],'amostras':{k:walk(v,depth+1) for k,v in list(x.items())[:6]}}
 if isinstance(x,list):
  return {'tipo':'lista','tamanho':len(x),'primeiro':walk(x[0],depth+1) if x else None}
 return {'tipo':type(x).__name__,'exemplo':str(x)[:120]}
def scan(x,path='$',depth=0):
 if depth>7:return []
 out=[]
 if isinstance(x,dict):
  keys=list(x)
  time=[k for k in keys if re.search(r'(timestamp|captur|consult|colet|horario|data_hora|generated_at|time)',k,re.I)]
  votes=[k for k in keys if re.search(r'(voto|vote|candidate|candidato|apurad|secoes)',k,re.I)]
  if time and votes:out.append({'path':path,'campos_temporais':time[:10],'campos_votos':votes[:10]})
  for k,v in list(x.items())[:100]:out+=scan(v,path+'.'+str(k),depth+1)
 elif isinstance(x,list):
  for i,v in enumerate(x[:12]):out+=scan(v,path+'['+str(i)+']',depth+1)
 return out[:100]
report={'pacote':str(p),'bytes_comprimidos':len(payload),'bytes_descompactados':len(raw),'estrutura':walk(data),'estruturas_com_tempo_e_votos':scan(data),'capturas_historicas_certificadas':False,'ressalva':'A existencia de horario e votos no mesmo objeto nao prova captura contemporanea nem ausencia de dados futuros.'}
pathlib.Path('inspecao_pacote_historico.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PACOTE_HISTORICO',json.dumps({k:v for k,v in report.items() if k!='estrutura'},ensure_ascii=False))
print('ESTRUTURA_PACOTE',json.dumps(report['estrutura'],ensure_ascii=False)[:9000])
