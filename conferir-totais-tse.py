import io,urllib.request,zipfile,json,csv,gzip,collections,concurrent.futures,hashlib
from pathlib import Path
class Remote(io.RawIOBase):
 def __init__(self,url,size):
  self.url=url;self.pos=0
  with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=30) as r:self.size=int(r.headers['Content-Length'])
 def seekable(self):return True
 def seek(self,offset,whence=0):self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset;return self.pos
 def tell(self):return self.pos
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  if not n:return b''
  req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{min(self.size-1,self.pos+n-1)}'})
  with urllib.request.urlopen(req,timeout=45) as r:
   if r.status!=206:raise RuntimeError('Servidor ignorou Range: '+str(r.status))
   b=r.read()
  self.pos+=len(b);return b
base=Path(__file__).resolve().parent/'dados/2026';rows=json.load(gzip.open(base/'municipios.json.gz','rt'));by={(r['uf'],str(int(r['codigo_municipio_tse']))):r for r in rows}
def check(meta):
 url=meta['url'];stem=url.rsplit('/',1)[-1][:-4];print('Lendo',stem,flush=True)
 with zipfile.ZipFile(Remote(url,meta['bytes'])) as z:
  name=stem+'_BR.csv';raw=z.read(name)
 Path('/tmp/'+name).write_bytes(raw);print('Extraído',name,len(raw),flush=True)
 reader=csv.DictReader(io.StringIO(raw.decode('latin-1')),delimiter=';');agg=collections.defaultdict(lambda:collections.Counter());fields={}
 candidate=stem.startswith('votacao_candidato')
 if not candidate:fields={'QT_APTOS':'aptos','QT_COMPARECIMENTO':'comparecimento','QT_ABSTENCOES':'abstencoes','QT_VOTOS_BRANCOS':'brancos','QT_TOTAL_VOTOS_NULOS':'nulos','QT_TOTAL_VOTOS_VALIDOS':'validos'}
 for r in reader:
  if r['CD_CARGO']!='1' or r['NR_TURNO'] not in ['1','2']:continue
  key=(r['SG_UF'],str(int(r['CD_MUNICIPIO'])));t=r['NR_TURNO']+'t'
  if candidate:
   if r['NR_CANDIDATO'] not in ['13','22']:continue
   name='lula' if r['NR_CANDIDATO']=='13' else 'flavio';agg[key][name+'_'+t]+=int(r['QT_VOTOS_NOMINAIS'])
  else:
   for f,n in fields.items():agg[key][n+'_'+t]+=int(r[f])
 mismatches=[]
 for key,values in agg.items():
  for f,v in values.items():
   stored=by.get(key,{}).get(f)
   if stored!=v:mismatches.append({'key':key,'field':f,'tse':v,'base':stored})
 return {'url':url,'member':stem+'_BR.csv','sha256_csv':hashlib.sha256(raw).hexdigest(),'territories':len(agg),'comparisons':sum(len(v) for v in agg.values()),'mismatches':mismatches}
metas=json.load(open(base/'downloads.json'));selected=[m for m in metas if 'candidato_munzona' in m['url'] or 'detalhe_votacao_munzona' in m['url']]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(check,selected))
Path('/tmp/reconciliacao-tse.json').write_text(json.dumps(result,ensure_ascii=False));print(json.dumps(result,ensure_ascii=False)[:4000],flush=True)
if any(r['mismatches'] for r in result):raise SystemExit('Divergências detectadas com o TSE')
