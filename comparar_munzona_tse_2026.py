import csv,io,json,sys,zipfile,collections,pathlib
p=pathlib.Path(sys.argv[1]); out=pathlib.Path('resultados_agregados');out.mkdir(exist_ok=True)
totals=collections.defaultdict(int); rows=0;dates=set(); keys=set();duplicates=0
with zipfile.ZipFile(p) as z:
 members=[n for n in z.namelist() if n.endswith('_BR.csv') and 'BRASIL' not in n]
 for name in members:
  with z.open(name) as f:
   reader=csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';')
   required={'CD_CARGO','NR_TURNO','SG_UF','CD_MUNICIPIO','NR_ZONA','NR_CANDIDATO','QT_VOTOS_NOMINAIS_VALIDOS','DT_GERACAO','HH_GERACAO'}
   if not required.issubset(reader.fieldnames):raise ValueError('Colunas faltantes: '+str(required-set(reader.fieldnames)))
   for row in reader:
    if row['CD_CARGO']!='1' or row['NR_CANDIDATO'] not in ('13','22') or row['NR_TURNO'] not in ('1','2'):continue
    k=(row['NR_TURNO'],row['SG_UF'],row['CD_MUNICIPIO'],row['NR_ZONA'],row['NR_CANDIDATO'],row.get('ST_VOTO_EM_TRANSITO',''))
    if k in keys:duplicates+=1
    keys.add(k)
    totals[k]+=int(row['QT_VOTOS_NOMINAIS_VALIDOS'] or 0)
    dates.add(row['DT_GERACAO']+' '+row['HH_GERACAO']);rows+=1
national=[{'turno':t,'candidato':c,'votos':sum(v for k,v in totals.items() if k[0]==t and k[4]==c)} for t in ('1','2') for c in ('13','22')]
ufs=[{'turno':t,'uf':uf,'candidato':c,'votos':sum(v for k,v in totals.items() if k[0]==t and k[1]==uf and k[4]==c)} for uf in sorted({k[1] for k in totals}) for t in ('1','2') for c in ('13','22')]
report={'arquivo':p.name,'linhas':rows,'duplicatas_chave':duplicates,'geracoes':sorted(dates),'totais_nacionais':national,'totais_uf':ufs,'totais_munzona':[{'turno':k[0],'uf':k[1],'municipio':k[2],'zona':k[3],'candidato':k[4],'voto_transito':k[5],'votos':v} for k,v in sorted(totals.items())]}
target=out/'comparacao_munzona_2026.json';target.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')))
baseline=json.loads(pathlib.Path('dados/2026/validacao.json').read_text(encoding='utf-8'))
diff=[]
for rec in national:
 b=baseline['totais_municipais_por_turno'][rec['turno']]['lula' if rec['candidato']=='13' else 'flavio']
 if b!=rec['votos']:diff.append({'turno':rec['turno'],'candidato':rec['candidato'],'anterior':b,'atual':rec['votos'],'diferenca':rec['votos']-b})
print(json.dumps({'arquivo':p.name,'linhas':rows,'duplicatas_chave':duplicates,'geracoes':sorted(dates),'totais_nacionais':national,'divergencias_nacionais':diff,'municipios_zonas':len(totals)},ensure_ascii=False))
if duplicates or diff:raise SystemExit('FALHA: divergencias ou chaves duplicadas')
