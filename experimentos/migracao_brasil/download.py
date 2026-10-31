import urllib.request,pathlib,concurrent.futures,gzip,json,base64,time
P=pathlib.Path('/tmp/migracao-serrinha');ufs='AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ'.split()
def get(pair):
 uf,kind=pair;name=('secoes-'+uf+'.json.gz') if kind=='s' else 'candidatos-secao-'+uf+'.json';path=P/name
 if path.exists() and kind=='c':return
 for attempt in range(3):
  try:
   b=urllib.request.urlopen('https://raw.githubusercontent.com/fabiooliveira-source/paineleleitoral-2026/experimento/modelo-territorial-999/dados/2026/'+name,timeout=90).read()
   if kind=='s':d=json.loads(gzip.decompress(b));path.with_suffix('').write_text(json.dumps(d,ensure_ascii=False))
   else:
    d=json.loads(b);path.write_text(gzip.decompress(base64.b64decode(d['dados'])).decode())
   print(name,'ok',flush=True);return
  except Exception:
   if attempt==2:raise
with concurrent.futures.ThreadPoolExecutor(12) as pool:list(pool.map(get,[(u,k) for u in ufs for k in ['s','c']]))
