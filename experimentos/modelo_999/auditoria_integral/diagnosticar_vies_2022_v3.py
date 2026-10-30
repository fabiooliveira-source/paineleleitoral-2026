"""Diagnóstico de composição intra-UF usando exclusivamente 2022.
O swing pareado é diagnóstico, não variável nova dos preditores congelados.
"""
import pathlib,json,pickle,zipfile,io,csv,collections,datetime
from preditor_causal_v2 import predict
ROOT=pathlib.Path(__file__).resolve().parent

def run():
 first={}
 with zipfile.ZipFile(ROOT/'microdados/votacao_secao_2022_BR.zip') as z,z.open('votacao_secao_2022_BR.csv') as f:
  reader=csv.reader(io.TextIOWrapper(f,encoding='latin1'),delimiter=';');h=next(reader);ix={k:h.index(k) for k in h}
  for r in reader:
   if r[ix['NR_TURNO']]!='1' or r[ix['NR_VOTAVEL']] not in ['13','22']:continue
   key=tuple(r[ix[k]] for k in ['SG_UF','CD_MUNICIPIO','NR_ZONA','NR_SECAO']);v=first.setdefault(key,[0,0]);v[0 if r[ix['NR_VOTAVEL']]=='13' else 1]+=int(r[ix['QT_VOTOS']])
 with (ROOT/'microdados/reconstrucao_cache.pkl').open('rb') as f:events,_,_,_=pickle.load(f)
 saved=json.loads((ROOT/'entradas_checkpoints_reconstruidos_2022.json').read_text());history=saved['first_round'];i=0;acc=collections.defaultdict(lambda:[0,0]);missing=0;points=[]
 for x in saved['checkpoints']:
  now=datetime.datetime.fromisoformat(x['current']['timestamp']);t=now.replace(tzinfo=None)
  while i<len(events) and events[i][0]<=t:
   _,key,v=events[i];prior=first.get(key)
   if prior is None:
    if v[0]+v[1]:missing+=1
   else:
    acc[key[0]][0]+=prior[0];acc[key[0]][1]+=prior[1]
   i+=1
  raw=paired=composition=denominator=0.;usable=0
  for r in x['territorial']:
   age=(now-datetime.datetime.fromisoformat(r['timestamp'])).total_seconds();a,b=r['votes_a'],r['votes_b'];h=history[r['scope']];ma,mb=acc[r['scope']]
   if age>300 or not a+b or not ma+mb:continue
   w=min(a+b,h['valid_votes'])*(1-age/600);observed=a/(a+b);full=h['votes_a']/(h['votes_a']+h['votes_b']);matched=ma/(ma+mb)
   raw+=w*(observed-full);paired+=w*(observed-matched);composition+=w*(matched-full);denominator+=w;usable+=1
  if denominator:
   raw/=denominator;paired/=denominator;composition/=denominator
  actual=predict(x['current'],history,x['territorial'])
  points.append({'threshold_pct':x['threshold_pct'],'raw_swing_pp':raw*100,'matched_section_swing_pp':paired*100,'composition_effect_pp':composition*100,'decomposition_residual_pp':100*(raw-paired-composition),'predictor_swing_difference_pp':100*(raw-actual['swing']),'territories_usable':usable})
 out={'year':2022,'method':'Com os mesmos pesos e idade da v2: swing bruto = swing contra 1T das secoes ja observadas + diferenca entre preferencia 1T da amostra observada e preferencia 1T da UF inteira.','paired_vote_reference_missing_sections':missing,'checkpoints':points,'mean_composition_effect_pp':sum(x['composition_effect_pp'] for x in points)/len(points),'composition_effect_negative_checkpoints':sum(x['composition_effect_pp']<0 for x in points),'max_decomposition_residual_pp':max(abs(x['decomposition_residual_pp']) for x in points),'interpretation':'Composicao intra-UF contamina o swing agregado. A decomposicao nao prova causalidade individual de voto, nem torna o swing pareado uma estimativa sem vies para secoes restantes.'}
 (ROOT/'diagnostico_vies_v2_2022.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checkpoints'},ensure_ascii=False),flush=True);print(points[:3],flush=True)
if __name__=='__main__':run()
