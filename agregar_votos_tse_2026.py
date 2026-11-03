import csv,io,json,sys,zipfile,collections,pathlib
p=pathlib.Path(sys.argv[1]); out=pathlib.Path('resultados_agregados');out.mkdir(exist_ok=True)
totals=collections.defaultdict(int); rows=0;dates=set()
with zipfile.ZipFile(p) as z:
 members=[n for n in z.namelist() if n.endswith('_BR.csv') and 'BRASIL' not in n]
 for name in members:
  with z.open(name) as f:
   reader=csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';')
   required={'CD_CARGO','NR_TURNO','SG_UF','NR_CANDIDATO','QT_VOTOS_NOMINAIS_VALIDOS','DT_GERACAO','HH_GERACAO'}
   if not required.issubset(reader.fieldnames):raise ValueError('Colunas faltantes: '+str(required-set(reader.fieldnames)))
   for row in reader:
    if row['CD_CARGO']!='1' or row['NR_CANDIDATO'] not in ('13','22'):continue
    if row['NR_TURNO'] not in ('1','2'):continue
    key=(row['NR_TURNO'],row['SG_UF'],row['NR_CANDIDATO'])
    totals[key]+=int(row['QT_VOTOS_NOMINAIS_VALIDOS'] or 0)
    dates.add(row['DT_GERACAO']+' '+row['HH_GERACAO']);rows+=1
report={'arquivo':p.name,'membros':members,'linhas_presidenciais_13_22':rows,'geracoes':sorted(dates),'votos_por_turno_uf_candidato':[{'turno':k[0],'uf':k[1],'candidato':k[2],'votos':v} for k,v in sorted(totals.items())],'totais_nacionais':[{'turno':t,'candidato':c,'votos':sum(v for (tt,uf,cc),v in totals.items() if tt==t and cc==c)} for t in ('1','2') for c in ('13','22')]}
target=out/(p.name+'.json');target.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'arquivo':p.name,'linhas':rows,'geracoes':sorted(dates),'totais_nacionais':report['totais_nacionais']},ensure_ascii=False))
