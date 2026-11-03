"""Diff municipal electoral metrics against frozen 28/10 snapshot."""
import csv,gzip,io,json,zipfile,collections,pathlib,sys
p=pathlib.Path(sys.argv[1])
with gzip.open('dados/2026/municipios.json.gz','rt',encoding='utf-8') as f:old=json.load(f)
fields={'aptos':'QT_APTOS','comparecimento':'QT_COMPARECIMENTO','abstencoes':'QT_ABSTENCOES','validos':'QT_TOTAL_VOTOS_VALIDOS','brancos':'QT_VOTOS_BRANCOS','nulos':'QT_TOTAL_VOTOS_NULOS'}
current=collections.defaultdict(lambda:collections.defaultdict(int)); counts=collections.Counter()
with zipfile.ZipFile(p) as z:
 members=[n for n in z.namelist() if n.endswith('_BR.csv') and 'BRASIL' not in n];assert len(members)==1,members
 with z.open(members[0]) as f:
  for row in csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';'):
   if row['CD_CARGO']!='1' or row['NR_TURNO'] not in ('1','2'):continue
   k=(row['SG_UF'],row['CD_MUNICIPIO'].zfill(5),row['NR_TURNO']);counts[k]+=1
   for metric,column in fields.items():current[k][metric]+=int(row[column] or 0)
previous={}
for row in old:
 for t in ('1','2'):
  k=(row['uf'],str(row['codigo_municipio_tse']).zfill(5),t)
  assert k not in previous,k
  previous[k]={m:int(row[m+'_'+t+'t'] or 0) for m in fields}
diff=[]
for k in sorted(set(previous)|set(current)):
 for m in fields:
  a=previous.get(k,{}).get(m);b=current.get(k,{}).get(m)
  if a!=b:diff.append({'uf':k[0],'municipio':k[1],'turno':k[2],'indicador':m,'anterior':a,'atual':b,'delta':None if a is None or b is None else b-a})
out=pathlib.Path('resultados_metricas');out.mkdir(exist_ok=True)
import csv as csvmod
with (out/'diferencas_indicadores_municipais.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csvmod.DictWriter(f,fieldnames=['uf','municipio','turno','indicador','anterior','atual','delta'],delimiter=';');w.writeheader();w.writerows(diff)
report={'chaves_antigas':len(previous),'chaves_atuais':len(current),'linhas_detalhe':sum(counts.values()),'chaves_com_multiplas_linhas':sum(v>1 for v in counts.values()),'divergencias':len(diff),'divergencias_por_indicador':dict(collections.Counter(d['indicador'] for d in diff)),'exemplos':diff[:30]}
(out/'resumo_metricas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('AUDITORIA_INDICADORES',json.dumps(report,ensure_ascii=False))
