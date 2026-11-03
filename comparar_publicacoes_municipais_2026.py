"""Compare publication 29/10 with frozen municipal snapshot 28/10; keep all discrepancies."""
import csv,gzip,io,json,sys,zipfile,collections,pathlib
p=pathlib.Path(sys.argv[1]); oldpath=pathlib.Path('dados/2026/municipios.json.gz')
with gzip.open(oldpath,'rt',encoding='utf-8') as f:old=json.load(f)
assert isinstance(old,list),type(old)
new=collections.defaultdict(int)
with zipfile.ZipFile(p) as z:
 names=[n for n in z.namelist() if n.endswith('_BR.csv') and 'BRASIL' not in n]
 assert len(names)==1,names
 with z.open(names[0]) as raw:
  rd=csv.DictReader(io.TextIOWrapper(raw,encoding='latin-1',newline=''),delimiter=';')
  for r in rd:
   if r['CD_CARGO']!='1' or r['NR_CANDIDATO'] not in ('13','22') or r['NR_TURNO'] not in ('1','2'):continue
   k=(r['SG_UF'],r['CD_MUNICIPIO'].zfill(5),r['NR_TURNO'],r['NR_CANDIDATO'])
   new[k]+=int(r['QT_VOTOS_NOMINAIS_VALIDOS'] or 0)
previous={}
for r in old:
 for t in ('1','2'):
  for n,c in (('13','lula'),('22','flavio')):
   k=(r['uf'],str(r['codigo_municipio_tse']).zfill(5),t,n)
   if k in previous:raise ValueError('Chave antiga duplicada '+str(k))
   previous[k]=int(r[c+'_validos_'+t+'t'] or 0)
keys=set(previous)|set(new)
differences=[{'uf':k[0],'municipio':k[1],'turno':k[2],'candidato':k[3],'votos_28out':previous.get(k),'votos_29out':new.get(k),'delta':(new.get(k,0)-previous.get(k,0))} for k in sorted(keys) if previous.get(k)!=new.get(k)]
out=pathlib.Path('resultados_comparacao');out.mkdir(exist_ok=True)
with (out/'divergencias_municipais_28out_vs_29out.csv').open('w',encoding='utf-8-sig',newline='') as f:
 wr=csv.DictWriter(f,fieldnames=['uf','municipio','turno','candidato','votos_28out','votos_29out','delta'],delimiter=';');wr.writeheader();wr.writerows(differences)
summary={'referencia_antiga':'dados/2026/municipios.json.gz','referencia_atual':p.name,'chaves_antigas':len(previous),'chaves_atuais':len(new),'chaves_diferentes':len(differences),'soma_deltas':sum(x['delta'] for x in differences),'diferencas_por_uf':dict(collections.Counter(x['uf'] for x in differences)),'exemplos':differences[:30]}
(out/'resumo_comparacao.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print('RESULTADO_COMPARACAO',json.dumps(summary,ensure_ascii=False))
if differences:print('ATENCAO: divergencias registradas; consultar CSV completo')
