"""Preparação do teste externo 2018, sem alterar preditores ou hiperparâmetros."""
import pathlib,zipfile,csv,io,json,collections,datetime,pickle
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/'microdados2018'
KEYS=['SG_UF','CD_MUNICIPIO','NR_ZONA','NR_SECAO']
def rows(archive,member):
 with zipfile.ZipFile(DATA/archive) as z,z.open(member) as f:
  r=csv.reader(io.TextIOWrapper(f,encoding='latin1'),delimiter=';');yield next(r);yield from r

def run():
 detail={};first_sections=set();counts=collections.Counter();detail_totals=collections.defaultdict(lambda:[0,0,0]);votes={};first=collections.defaultdict(lambda:[0,0,0]);candidate_totals=collections.Counter()
 r=rows('detalhe_votacao_secao_2018.zip','detalhe_votacao_secao_2018_BR.csv');h=next(r);ix={k:h.index(k) for k in h}
 for row in r:
  if row[ix['CD_CARGO']]!='1':continue
  turn=int(row[ix['NR_TURNO']]);key=tuple(row[ix[k]] for k in KEYS);counts[f'detail_rows_{turn}']+=1
  if turn==1:
   if key in first_sections:raise ValueError('duplicate 1T section')
   first_sections.add(key)
  elif turn==2:
   if key in detail:raise ValueError('duplicate 2T section')
   d={k:row[ix[k]] for k in ['QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS','QT_VOTOS_ANULADOS_APU_SEP','QT_APTOS','QT_COMPARECIMENTO','QT_ABSTENCOES','DT_PRIM_TOT_PARCIAL_HOR_TSE','DT_RECEBIMENTO_BU_HOR_TSE']};detail[key]=d
   for j,k in enumerate(['QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS']):detail_totals[key[0]][j]+=int(d[k])
 print('detail',dict(counts),flush=True)
 r=rows('votacao_secao_2018_BR.zip','votacao_secao_2018_BR.csv');h=next(r);ix={k:h.index(k) for k in h};seen=set()
 for row in r:
  if row[ix['CD_CARGO']]!='1':continue
  turn=int(row[ix['NR_TURNO']]);key=tuple(row[ix[k]] for k in KEYS);uf=key[0];c=row[ix['NR_VOTAVEL']];n=int(row[ix['QT_VOTOS']]);counts[f'vote_rows_{turn}']+=1
  if turn==1:
   if c=='13':first[uf][0]+=n
   if c=='17':first[uf][1]+=n
   if c not in ['95','96','97','98','99']:first[uf][2]+=n
  elif turn==2:
   unique=(key,c)
   if unique in seen:raise ValueError('duplicate section-candidate')
   seen.add(unique);candidate_totals[c]+=n;v=votes.setdefault(key,[0,0,0,0])
   if c in ['13','17','95','96']:v[['13','17','95','96'].index(c)]+=n
   elif n:raise ValueError('Unexpected vote category '+c)
 print('votes',dict(counts),dict(candidate_totals),flush=True)
 events=[];missing_times=[];late=[];bad_sums=[];dates=collections.Counter();cutoff=datetime.datetime(2018,10,29,23,59,59)
 for key,row in detail.items():
  v=votes.get(key,[0,0,0,0])
  if v[0]+v[1]!=int(row['QT_VOTOS_NOMINAIS']) or v[2]!=int(row['QT_VOTOS_BRANCOS']) or v[3]!=int(row['QT_VOTOS_NULOS']):bad_sums.append({'key':key,'votes':v,'detail':[row[k] for k in ['QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS']]})
  stamp=row['DT_PRIM_TOT_PARCIAL_HOR_TSE'];dates[stamp[:10]]+=1
  try:t=datetime.datetime.strptime(stamp,'%d/%m/%Y %H:%M:%S')
  except ValueError:
   missing_times.append({'key':key,'votes':v,'aptos':int(row['QT_APTOS'])});continue
  events.append((t,key,v))
  if t>cutoff:late.append({'timestamp':stamp,'key':key,'votes':v})
 events.sort(key=lambda x:(x[0],x[1]));missing_detail=list(set(votes)-set(detail));missing_votes=list(set(detail)-set(votes))
 by_uf=collections.defaultdict(lambda:[0,0,0,0])
 for key,v in votes.items():
  for j,n in enumerate(v):by_uf[key[0]][j]+=n
 uf_mismatch={u:{'votes':v,'detail':detail_totals[u]} for u,v in by_uf.items() if [v[0]+v[1],v[2],v[3]]!=detail_totals[u]}
 diag={'year':2018,'counts':dict(counts),'first_round_sections':len(first_sections),'second_round_sections':len(detail),'vote_sections':len(votes),'first_round_uf':dict(first),'candidate_totals':dict(candidate_totals),'missing_detail_count':len(missing_detail),'missing_votes_count':len(missing_votes),'bad_sums_count':len(bad_sums),'bad_sums_sample':bad_sums[:20],'missing_times':missing_times,'timestamp_dates':dict(dates),'late_events_after_2018_10_29':late,'uf_final_sum_mismatches':uf_mismatch,'national_official_curve_available':False,'section_keys_only_second_round':len(set(detail)-first_sections),'section_keys_only_first_round':len(first_sections-set(detail)),'late_votes_total':[sum(x['votes'][j] for x in late) for j in range(4)],'all_source_votes':[sum(v[j] for v in votes.values()) for j in range(4)],'initial_period_votes':[sum(v[j] for t,k,v in events if t<=cutoff) for j in range(4)]}
 (ROOT/'diagnostico_dados_2018.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2)+'\n')
 assert not missing_detail and not bad_sums and not uf_mismatch,'integracao falhou'
 assert all(not any(x['votes']) for x in missing_times),'Votos sem timestamp: teste cronologico bloqueado'
 with (DATA/'replay_cache.pkl').open('wb') as f:pickle.dump((events,dict(first),len(first_sections),diag),f)
 print(json.dumps({k:v for k,v in diag.items() if k not in ['first_round_uf','missing_times','late_events_after_2018_10_29','bad_sums_sample']},ensure_ascii=False),flush=True)
if __name__=='__main__':run()
