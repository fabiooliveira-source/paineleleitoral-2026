"""Downloads oficiais2024 com hashes fixados antes da reprodução."""
import pathlib,urllib.request,hashlib,zipfile,json,concurrent.futures,datetime
ROOT=pathlib.Path(__file__).resolve().parent;DATA=ROOT/'microdados2024'
PINS={'detalhe_votacao_secao_2024.zip':'ae879eb09d1ceca9ca05c1b9759a7646800b4efe57ca3d5d7f33f91287bcca3e','votacao_secao_2024_CE.zip':'14f96957ca6eff35b327665f781c5a839f7b3de7a98c02a9526ed911d320a08e','votacao_secao_2024_RS.zip':'a0fb26360917e32c7d18f806e3b6f3b8ac97378ce3127e1fecb6a2bfe0581a05','votacao_secao_2024_RN.zip':'b95f8d1c40ef6e4ac3fd077988f67b80cc4c75b74c0c306aec150cf03d086f63'}
def download(name):
 DATA.mkdir(exist_ok=True);typ='detalhe_votacao_secao' if name.startswith('detalhe') else 'votacao_secao';url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/{typ}/{name}';p=DATA/name
 if not p.exists():
  tmp=DATA/(name+'.part')
  with urllib.request.urlopen(url,timeout=60) as r,tmp.open('wb') as w:
   for b in iter(lambda:r.read(1024*1024),b''):w.write(b)
  tmp.rename(p)
 h=hashlib.sha256()
 with p.open('rb') as r:
  for b in iter(lambda:r.read(1024*1024),b''):h.update(b)
 assert h.hexdigest()==PINS[name],'Source hash changed: '+name
 with zipfile.ZipFile(p) as z:
  assert z.testzip() is None
  members=[{'name':x.filename,'bytes':x.file_size} for x in z.infolist()]
 out={'name':name,'url':url,'sha256':h.hexdigest(),'bytes':p.stat().st_size,'crc_ok':True,'members':members,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};print(name,'validated',flush=True);return out
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(4) as pool:rows=list(pool.map(download,PINS))
 (DATA/'manifesto_fontes_2024.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
