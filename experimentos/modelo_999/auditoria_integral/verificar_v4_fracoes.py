"""Conferência com Fraction, sem importar o preditor."""
from fractions import Fraction as F
import pathlib,json,sys
ROOT=pathlib.Path(__file__).resolve().parent

def run(year):
 d=json.loads((ROOT/f'entradas_pareadas_v4_{year}.json').read_text());out=json.loads((ROOT/f'resultado_v4_{year}.json').read_text());differences=[]
 for case,published in zip(d['checkpoints'],out['checkpoints']):
  assert case['threshold_pct']==published['threshold_pct'];c=case['current'];a,b=c['votes_a'],c['votes_b'];R=c['electorate_total']-c['electorate_counted'];ref=d['reference'];rows={r['scope']:r for r in case['ledger']};assert set(rows)==set(ref)
  pa=sum(r['matched_first_a'] for r in rows.values());pb=sum(r['matched_first_b'] for r in rows.values());global_a=F(a,pa);global_b=F(b,pb);ea=F(0);eb=F(0)
  for u,h in ref.items():
   r=rows[u];ga=F(r['votes_a'],r['matched_first_a']) if r['matched_first_a'] else global_a;gb=F(r['votes_b'],r['matched_first_b']) if r['matched_first_b'] else global_b
   ea+=(h['votes_a']-r['matched_first_a'])*ga;eb+=(h['votes_b']-r['matched_first_b'])*gb
  if ea+eb>R:scale=F(R)/(ea+eb);ea*=scale;eb*=scale
  point=(a+ea)/(a+b+ea+eb);delta=abs(100*float(point)-published['estimate_a_pct']);assert delta<1e-9;differences.append(delta)
  lower=F(a,a+b+R);upper=F(a+R,a+b+R);assert abs(100*float(lower)-published['lower_a_pct'])<1e-10;assert abs(100*float(upper)-published['upper_a_pct'])<1e-10
  winner='a' if a>b+R else ('b' if b>a+R else None);assert winner==published['conditional_winner']
 result={'year':year,'points_recomputed':len(differences),'max_difference_pp':max(differences),'method':'Fraction rational arithmetic, separate implementation, no predictor imported. Does not authenticate the retrospective availability assumptions.'}
 (ROOT/f'verificacao_fracoes_v4_{year}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False));return result
if __name__=='__main__':run(int(sys.argv[1]))
