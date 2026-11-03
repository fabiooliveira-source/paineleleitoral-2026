import csv,io,json,sys,zipfile,pathlib,collections
p=pathlib.Path(sys.argv[1]);out=pathlib.Path('resultados_inspecao');out.mkdir(exist_ok=True)
with zipfile.ZipFile(p) as z:
 names=[n for n in z.namelist() if n.endswith('_BR.csv')]
 if not names:raise SystemExit('Membro _BR.csv ausente')
 results=[]
 for name in names:
  with z.open(name) as raw:
   txt=io.TextIOWrapper(raw,encoding='latin-1',newline='')
   reader=csv.DictReader(txt,delimiter=';')
   cols=reader.fieldnames
   sample=[]
   for _,row in zip(range(5),reader):sample.append(row)
   results.append({'membro':name,'colunas':cols,'amostra':sample})
 dest=out/(p.name+'.esquema.json')
 dest.write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print('ESQUEMA',p.name,json.dumps(results,ensure_ascii=False)[:12000])
