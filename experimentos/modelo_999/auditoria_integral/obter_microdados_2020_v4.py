"""Aquisição de dados externos 2020; não seleciona nem ajusta parâmetros."""
import urllib.request,pathlib,json,concurrent.futures,hashlib,zipfile,datetime
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'microdados2020'
SOURCES={name:f'https://cdn.tse.jus.br/estatistica/sead/odsele/{typ}/{name}' for name,typ in [('detalhe_votacao_secao_2020.zip','detalhe_votacao_secao'),('votacao_secao_2020_SP.zip','votacao_secao')]}
EXPECTED_SHA256={'detalhe_votacao_secao_2020.zip': '10a50a467763dce73d44eee9023ffeeb3ebe6279756edb6b437203eb2bc71a30', 'votacao_secao_2020_SP.zip': '79dbc252f6d6187f351ceaf1bbf2a0d3fba5043a90df1e2af9c4e8bae7244fc8'}
def get(item):
 DATA.mkdir(exist_ok=True);name,url=item;f=DATA/name;headers={}
 if not f.exists():
  with urllib.request.urlopen(url,timeout=60) as r,open(str(f)+'.part','wb') as w:
   headers=dict(r.headers)
   for b in iter(lambda:r.read(1024*1024),b''):w.write(b)
  pathlib.Path(str(f)+'.part').rename(f)
 h=hashlib.sha256()
 with f.open('rb') as r:
  for b in iter(lambda:r.read(1024*1024),b''):h.update(b)
 if name in EXPECTED_SHA256: assert h.hexdigest()==EXPECTED_SHA256[name], 'Hash da fonte alterado'
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None
  members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
 result={'name':name,'url':url,'sha256':h.hexdigest(),'bytes':f.stat().st_size,'zip_crc_ok':True,'members':members,'headers':headers,'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};print(json.dumps({'name':name,'bytes':f.stat().st_size,'sha256':h.hexdigest()}),flush=True);return result
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(2) as pool:manifest=list(pool.map(get,SOURCES.items()))
 (DATA/'manifesto2020.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
