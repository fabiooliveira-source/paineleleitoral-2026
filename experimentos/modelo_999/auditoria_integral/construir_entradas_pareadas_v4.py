"""Constrói coortes pareadas entre turnos; não ajusta nem executa preditor.
Registros de disponibilidade são hipóteses de replay, não capturas públicas.
"""
import pathlib,zipfile,io,csv,datetime,collections,json,sys
ROOT=pathlib.Path(__file__).resolve().parent
TZ=datetime.timezone(datetime.timedelta(hours=-3))
CONFIG={
2018:dict(folder='microdados2018',detail='detalhe_votacao_secao_2018_BR.csv',votes='votacao_secao_2018_BR.csv',cargo='1',a='13',b='17',municipality=None,day='2018-10-28',cutoff='2018-10-29T23:59:59',prior='2018-10-27T00:00:00-03:00'),
2022:dict(folder='microdados',detail='detalhe_votacao_secao_2022_BRASIL.csv',votes='votacao_secao_2022_BR.csv',cargo='1',a='13',b='22',municipality=None,day='2022-10-30',cutoff='2022-10-31T23:59:59',prior='2022-10-29T00:00:00-03:00'),
2020:dict(folder='microdados2020',detail='detalhe_votacao_secao_2020_SP.csv',votes='votacao_secao_2020_SP.csv',cargo='11',a='50',b='45',municipality='71072',day='2020-11-29',cutoff='2020-11-30T23:59:59',prior='2020-11-28T00:00:00-03:00')}
def reader(archive,member):
 with zipfile.ZipFile(archive) as z,z.open(member) as f:
  r=csv.reader(io.TextIOWrapper(f,encoding='latin1'),delimiter=';');yield next(r);yield from r

def build(year):
 c=CONFIG[year];data=ROOT/c['folder'];first_keys=set();second={};counts=collections.Counter()
 def key(r,ix):return r[ix['SG_UF']],r[ix['CD_MUNICIPIO']].zfill(5),str(int(r[ix['NR_ZONA']])),str(int(r[ix['NR_SECAO']]))
 def selected(r,ix):return r[ix['CD_CARGO']]==c['cargo'] and (c['municipality'] is None or r[ix['CD_MUNICIPIO']].zfill(5)==c['municipality']) and r[ix['CD_TIPO_ELEICAO']]=='2'
 rs=reader(data/f'detalhe_votacao_secao_{year}.zip',c['detail']);h=next(rs);ix={k:h.index(k) for k in h}
 for r in rs:
  if not selected(r,ix):continue
  k=key(r,ix);turn=r[ix['NR_TURNO']];counts['detail_'+turn]+=1
  if turn=='1':
   if k in first_keys:raise ValueError('duplicate first detail')
   first_keys.add(k)
  elif turn=='2':
   if k in second:raise ValueError('duplicate second detail')
   second[k]={name:r[ix[name]] for name in ['QT_APTOS','QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS','DT_PRIM_TOT_PARCIAL_HOR_TSE']}
 first_votes=collections.defaultdict(lambda:[0,0]);second_votes=collections.defaultdict(lambda:[0,0,0,0]);seen=set()
 rs=reader(data/('votacao_secao_2020_SP.zip' if year==2020 else f'votacao_secao_{year}_BR.zip'),c['votes']);h=next(rs);ix={k:h.index(k) for k in h}
 for r in rs:
  if not selected(r,ix):continue
  k=key(r,ix);turn=r[ix['NR_TURNO']];candidate=r[ix['NR_VOTAVEL']];n=int(r[ix['QT_VOTOS']]);counts['votes_'+turn]+=1
  if turn=='1' and candidate in [c['a'],c['b']]:
   if (turn,k,candidate) in seen:raise ValueError('duplicate first candidate')
   seen.add((turn,k,candidate));first_votes[k][[c['a'],c['b']].index(candidate)]+=n
  elif turn=='2':
   if (turn,k,candidate) in seen:raise ValueError('duplicate second candidate')
   seen.add((turn,k,candidate))
   if candidate not in [c['a'],c['b'],'95','96']:
    if n:raise ValueError('unexpected second-round vote category '+candidate)
   else:second_votes[k][[c['a'],c['b'],'95','96'].index(candidate)]+=n
 print(year,'read_complete',dict(counts),flush=True)
 def scope(k):return k[2] if year==2020 else k[0]
 totals=collections.defaultdict(lambda:[0,0])
 for k in first_keys:
  a,b=first_votes.get(k,[0,0]);totals[scope(k)][0]+=a;totals[scope(k)][1]+=b
 extra_votes=set(second_votes)-set(second);assert not extra_votes,'second votes without detail'
 missing_pairs=[];missing_times=[];events=[];final=[0]*4;total_electorate=0;date_counts=collections.Counter();cutoff=datetime.datetime.fromisoformat(c['cutoff']);late=[]
 for k,d in second.items():
  v=second_votes.get(k,[0,0,0,0]);aptos=int(d['QT_APTOS']);total_electorate+=aptos
  assert [v[0]+v[1],v[2],v[3]]==[int(d[name]) for name in ['QT_VOTOS_NOMINAIS','QT_VOTOS_BRANCOS','QT_VOTOS_NULOS']],'source sum mismatch'
  assert sum(v)<=aptos,'more votes than registered electorate'
  for j in range(4):final[j]+=v[j]
  if k not in first_keys:
   missing_pairs.append({'key':k,'votes':v})
   continue
  stamp=d['DT_PRIM_TOT_PARCIAL_HOR_TSE'];date_counts[stamp[:10]]+=1
  try:t=datetime.datetime.strptime(stamp,'%d/%m/%Y %H:%M:%S')
  except ValueError:missing_times.append({'key':k,'votes':v});continue
  events.append((t,k,v,aptos,first_votes.get(k,[0,0])))
  if t>cutoff:late.append({'key':k,'timestamp':stamp,'votes':v})
 diag={'year':year,'counts':dict(counts),'first_sections':len(first_keys),'second_sections':len(second),'scopes':len(totals),'final_votes':final,'electorate_total_retrospective':total_electorate,'missing_pairs':missing_pairs,'missing_times':missing_times,'date_counts':dict(date_counts),'late_events':late,'assumptions':['References1T and registered electorate2T are retrospective; contemporaneous versions not authenticated.','Ledger availability_at equals internal totalization cutoff by replay hypothesis, not public capture.']}
 (ROOT/f'diagnostico_pareamento_v4_{year}.json').write_text(json.dumps(diag,ensure_ascii=False,indent=2)+'\n')
 assert not missing_pairs,'unmatched sections block paired model'
 assert all(not any(x['votes']) for x in missing_times),'votes without chronological timestamp'
 events.sort(key=lambda x:(x[0],x[1]));increments=collections.defaultdict(lambda:collections.defaultdict(lambda:[0]*5));national_inc=collections.defaultdict(lambda:[0,0,0,0])
 for t,k,v,aptos,prior in events:
  g=increments[t][scope(k)]
  for j,n in enumerate([v[0],v[1],prior[0],prior[1],aptos]):g[j]+=n
  n=national_inc[t];n[0]+=v[0];n[1]+=v[1];n[2]+=1;n[3]+=aptos
 evaluation_times={}
 if year==2022:
  with zipfile.ZipFile(data/'Historico_Totalizacao_Presidente_BR_2T_2022.zip') as z:
   name=next(n for n in z.namelist() if n.endswith('.csv'));rs=csv.reader(io.StringIO(z.read(name).decode('latin1')),delimiter=';');h=[x.strip() for x in next(rs)];rows=[dict(zip(h,[x.strip() for x in r])) for r in rs]
  for pct in range(5,100,5):
   r=next(r for r in rows if 100*int(r['QT_SECOES_TOT_ACUMULADO'])/int(r['QT_SECOES_TOTAL'])>=pct)
   evaluation_times[pct]=datetime.datetime.strptime(r['DT_TOTALIZACAO'],'%d/%m/%Y %H:%M:%S')
 else:
  ss=0
  for t,n in sorted(national_inc.items()):
   ss+=n[2]
   if t>cutoff:continue
   for pct in range(5,100,5):
    if pct not in evaluation_times and 100*ss/len(first_keys)>=pct:evaluation_times[pct]=t
 assert len(evaluation_times)==19,'missing coverage checkpoints'
 acc={u:[0]*5 for u in totals};national=[0]*4;idx=0;ordered=sorted(increments);checkpoints=[]
 reference={u:dict(votes_a=v[0],votes_b=v[1],available_at=c['prior']) for u,v in sorted(totals.items())}
 for pct,t in sorted(evaluation_times.items()):
  while idx<len(ordered) and ordered[idx]<=t:
   tt=ordered[idx]
   for u,delta in increments[tt].items():
    for j in range(5):acc[u][j]+=delta[j]
   for j in range(4):national[j]+=national_inc[tt][j]
   idx+=1
  iso=t.replace(tzinfo=TZ).isoformat();current=dict(timestamp=iso,available_at=iso,votes_a=national[0],votes_b=national[1],electorate_total=total_electorate,electorate_counted=national[3])
  ledger=[dict(scope=u,timestamp=iso,available_at=iso,votes_a=v[0],votes_b=v[1],matched_first_a=v[2],matched_first_b=v[3]) for u,v in sorted(acc.items())]
  checkpoints.append({'threshold_pct':pct,'current':current,'ledger':ledger})
 out={'year':year,'config':c,'reference':reference,'checkpoints':checkpoints,'target_a':final[0]/(final[0]+final[1]),'scope':'Retrospective paired-ledger replay; assumptions in diagnostic.','availability_is_assumed':True}
 (ROOT/f'entradas_pareadas_v4_{year}.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 print(year,'prepared',len(checkpoints),'scopes',len(reference),'late',len(late),flush=True)
if __name__=='__main__':build(int(sys.argv[1]))
