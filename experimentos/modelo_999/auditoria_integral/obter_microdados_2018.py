"""Aquisição de dados externos 2018; não seleciona nem ajusta parâmetros."""
import urllib.request,pathlib,json,concurrent.futures,hashlib,zipfile,datetime
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'microdados2018'
SOURCES={name:f'https://cdn.tse.jus.br/estatistica/sead/odsele/{typ}/{name}' for name,typ in [('detalhe_votacao_secao_2018.zip','detalhe_votacao_secao'),('votacao_secao_2018_BR.zip','votacao_secao')]}
EXPECTED_SHA256={'detalhe_votacao_secao_2018.zip': 'de35b08db427ee0c3089d88317e6166ea5dea33630f5b1dabdccf3304de48f70', 'votacao_secao_2018_BR.zip': 'dde2250058a7efa3b7ee336520556905456cb75d7debf99ea4badfc4d598a48c'}
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
 assert h.hexdigest()==EXPECTED_SHA256[name], 'Hash da fonte alterado'
 with zipfile.ZipFile(f) as z:
  assert z.testzip() is None
  members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
 result={'name':name,'url':url,'sha256':h.hexdigest(),'bytes':f.stat().st_size,'zip_crc_ok':True,'members':members,'headers':headers,'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};print(json.dumps({'name':name,'bytes':f.stat().st_size,'sha256':h.hexdigest()}),flush=True);return result
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(2) as pool:manifest=list(pool.map(get,SOURCES.items()))
 (DATA/'manifesto2018.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
