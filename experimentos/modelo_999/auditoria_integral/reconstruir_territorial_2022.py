"""Reconstrução explícita por primeira totalização, sem inferir divulgação pública.
Saídas NÃO são snapshots originais. Não alterar o preditor congelado.
"""
import csv,io,zipfile,pathlib,json,collections,datetime,bisect,pickle,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'microdados'
KEYS=['SG_UF','CD_MUNICIPIO','NR_ZONA','NR_SECAO']
def rows(archive,member):
 with zipfile.ZipFile(DATA/archive) as z, z.open(member) as raw:
  reader=csv.reader(io.TextIOWrapper(raw,encoding='latin1'),delimiter=';');header=next(reader)
  yield header
  yield from reader

def build():
 d={};counts=collections.Counter();first=collections.defaultdict(lambda:[0,0,0]);votes={};candidates=collections.Counter()
 rs=rows('detalhe_votacao_secao_2022.zip','detalhe_votacao_secao_2022_BRASIL.csv');h=next(rs);ix={k:h.index(k) for k in h}
 for r in rs:
  if r[ix['CD_CARGO']]!='1':continue
  turn=int(r[ix['NR_TURNO']]);counts[f'detail_{turn}']+=1
  if turn!=2:continue
  key=tuple(r[ix[k]] for k in KEYS)
  if key in d:raise ValueError('duplicate detail key '+str(key))
  d[key]={k:r[ix[k]] for k in ['DT_PRIM_TOT_PARCIAL_HOR_TSE','DT_RECEBIMENTO_BU_HOR_TSE','QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS','QT_APTOS','QT_COMPARECIMENTO','ST_SECAO_INSTALADA','ST_SECAO_ANULADA','DS_ORIGEM_VOTO']}
 print('detail',dict(counts),'sections',len(d),flush=True)
 rs=rows('votacao_secao_2022_BR.zip','votacao_secao_2022_BR.csv');h=next(rs);ix={k:h.index(k) for k in h}
 seen=set()
 for r in rs:
  if r[ix['CD_CARGO']]!='1':continue
  turn=int(r[ix['NR_TURNO']]);uf=r[ix['SG_UF']];candidate=r[ix['NR_VOTAVEL']];n=int(r[ix['QT_VOTOS']]);counts[f'vote_rows_{turn}']+=1
  if turn==1:
   if candidate=='13':first[uf][0]+=n
   if candidate=='22':first[uf][1]+=n
   if candidate not in ['95','96','97','98','99']:first[uf][2]+=n
  elif turn==2:
   key=tuple(r[ix[k]] for k in KEYS);duplicate=(key,candidate)
   if duplicate in seen:raise ValueError('duplicate candidate section')
   seen.add(duplicate);v=votes.setdefault(key,[0,0,0,0]);candidates[candidate]+=n
   if candidate in ['13','22','95','96']:v[['13','22','95','96'].index(candidate)]+=n
   elif n:raise ValueError('unexpected second round vote '+candidate)
 print('votes',dict(counts),'candidate_totals',dict(candidates),flush=True)
 missing_detail=sorted(set(votes)-set(d));missing_votes=sorted(set(d)-set(votes))
 events=[];excluded=[];bad_sums=[];timestamps=collections.Counter()
 for key,row in d.items():
  v=votes.get(key,[0,0,0,0]);date=row['DT_PRIM_TOT_PARCIAL_HOR_TSE'];timestamps[date[:10]]+=1
  if v[0]+v[1]!=int(row['QT_VOTOS_NOMINAIS']):bad_sums.append([key,'nominal',v[:2],row['QT_VOTOS_NOMINAIS']])
  if v[2]!=int(row['QT_VOTOS_BRANCOS']) or v[3]!=int(row['QT_VOTOS_NULOS']):bad_sums.append([key,'blank_null',v[2:]])
  try:t=datetime.datetime.strptime(date,'%d/%m/%Y %H:%M:%S')
  except ValueError:excluded.append({'key':key,'timestamp':date,'votes':v,'installed':row['ST_SECAO_INSTALADA']});continue
  events.append((t,key,v))
 events.sort(key=lambda x:(x[0],x[1]))
 diag={'counts':dict(counts),'candidate_totals':dict(candidates),'first_round_uf':dict(first),'detail_sections':len(d),'vote_sections':len(votes),'missing_detail_count':len(missing_detail),'missing_votes_count':len(missing_votes),'missing_detail_sample':missing_detail[:20],'missing_votes_sample':missing_votes[:60],'timestamp_dates':dict(timestamps),'bad_sums_count':len(bad_sums),'bad_sums_sample':bad_sums[:20],'excluded_missing_timestamp':excluded,'events':len(events)}
 return events,dict(first),diag

def compare(events,diag):
 rs=rows('Historico_Totalizacao_Presidente_BR_2T_2022.zip','Historico_Totalizacao_Presidente_BR_2T_2022.csv');h=[s.strip() for s in next(rs)];official=[dict(zip(h,[s.strip() for s in r])) for r in rs]
 acc=[0]*5;i=0;diffs=[];aligned=[]
 fields=['LULA_QT_VOTOS_TOT_ACUMULADO','JAIR_BOLSONARO_QT_VOTOS_TOT_ACUMULADO','BRANCO_QT_VOTOS_TOT_ACUMULADO','NULO_QT_VOTOS_TOT_ACUMULADO','QT_SECOES_TOT_ACUMULADO']
 maxima=[0]*5;exact=[0]*5
 for r in official:
  t=datetime.datetime.strptime(r['DT_TOTALIZACAO'],'%d/%m/%Y %H:%M:%S')
  while i<len(events) and events[i][0]<=t:
   _,key,v=events[i]
   for j in range(4):acc[j]+=v[j]
   acc[4]+=1;i+=1
  delta=[acc[j]-int(r[k]) for j,k in enumerate(fields)]
  for j in range(5):maxima[j]=max(maxima[j],abs(delta[j]));exact[j]+=delta[j]==0
  if any(delta) and len(diffs)<30:diffs.append({'timestamp':r['DT_TOTALIZACAO'],'delta':dict(zip(fields,delta))})
  aligned.append({'timestamp':r['DT_TOTALIZACAO'],'delta':delta})
 diag['national_curve_comparison']={'official_snapshots':len(official),'fields':fields,'exact_counts':dict(zip(fields,exact)),'max_abs_difference':dict(zip(fields,maxima)),'all_fields_exact':not any(maxima),'discrepancy_sample':diffs,'last_official':{k:official[-1][k] for k in fields},'last_reconstructed':dict(zip(fields,acc))}
 return official,aligned

if __name__=='__main__':
 events,first,diag=build();official,aligned=compare(events,diag)
 (ROOT/'reconstrucao_diagnostico_2022.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2)+'\n')
 with (DATA/'reconstrucao_cache.pkl').open('wb') as f:pickle.dump((events,first,official,aligned),f)
 print(json.dumps(diag['national_curve_comparison'],ensure_ascii=False),flush=True)
