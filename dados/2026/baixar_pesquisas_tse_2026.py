#!/usr/bin/env python3
import hashlib,json,urllib.request,zipfile
from pathlib import Path
base='https://cdn.tse.jus.br/estatistica/sead/odsele/pesquisa_eleitoral/'
names=['pesquisa_eleitoral_2026.zip','questionario_pesquisa_2026.zip','bairro_municipio_2026.zip']
folder=Path('dados/2026/pesquisas_originais');folder.mkdir(parents=True,exist_ok=True)
results=[]
for name in names:
 url=base+name;out=folder/name;part=folder/(name+'.part')
 try:
  start=part.stat().st_size if part.exists() else 0
  headers={'User-Agent':'Mozilla/5.0'}
  if start:headers['Range']=f'bytes={start}-'
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=120) as response:
   if start and response.status!=206:start=0
   with part.open('ab' if start else 'wb') as dest:
    while True:
     chunk=response.read(1024*1024)
     if not chunk:break
     dest.write(chunk)
  part.replace(out)
  sha=hashlib.sha256()
  with out.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''):sha.update(chunk)
  with zipfile.ZipFile(out) as z:
   bad=z.testzip();members=len(z.namelist())
  results.append(dict(nome=name,url=url,status='OK' if bad is None else 'CRC_FALHOU',bytes=out.stat().st_size,sha256=sha.hexdigest(),membros=members,erro_crc=bad))
 except Exception as exc:results.append(dict(nome=name,url=url,status='ERRO',erro=str(exc)))
 print(name,results[-1]['status'],flush=True)
(folder/'manifesto_download.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
if any(x['status']!='OK' for x in results):raise SystemExit('Um ou mais downloads falharam; ver manifesto_download.json')
