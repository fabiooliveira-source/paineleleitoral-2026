#!/usr/bin/env python3
"""Backtest temporal causal: baseline nacional sem uso de resultado futuro na previsão."""
import csv,json,pathlib,datetime,collections,math
ROOT=pathlib.Path("dados/2026/backtest")
SOURCE=ROOT/"csv/acervo_2026_2/observacoes_nacional_uf.csv"
OUT=pathlib.Path("experimentos/modelo_999/resultados")
OUT.mkdir(parents=True,exist_ok=True)
def integer(x):return int(x or 0)
def stamp(s):return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
with SOURCE.open(encoding="utf-8-sig",newline="") as f:
 rows=list(csv.DictReader(f))
required={"timestamp","scope","uf","votos_13","votos_22","secoes_contabilizadas","eleitores_secoes_contabilizadas"}
assert rows and required.issubset(rows[0]),"CSV incompatível"
scopes=collections.Counter(r["scope"] for r in rows)
national=[r for r in rows if not r["uf"] and not r["municipio_tse"]]
assert national,"Não há snapshots nacionais"
national.sort(key=lambda r:stamp(r["timestamp"]))
# Verificar monotonicidade; se houver revisão, registrar em vez de ocultar.
cols=["votos_13","votos_22","secoes_contabilizadas","eleitores_secoes_contabilizadas"]
violations=[]
for prev,cur in zip(national,national[1:]):
 for col in cols:
  if integer(cur[col])<integer(prev[col]):violations.append({"timestamp":cur["timestamp"],"column":col,"before":integer(prev[col]),"after":integer(cur[col])})
final=national[-1]
final_votes=integer(final["votos_13"])+integer(final["votos_22"])
final_sections=integer(final["secoes_contabilizadas"])
assert final_votes>0 and final_sections>0
target=100*integer(final["votos_13"])/final_votes
snapshots=[]
for r in national:
 v13=integer(r["votos_13"]);v22=integer(r["votos_22"])
 votes=v13+v22; sections=integer(r["secoes_contabilizadas"])
 if votes<=0:continue
 # Somente informação disponível no instante t: proporção entre votos já contados.
 predicted=100*v13/votes
 coverage=100*sections/final_sections
 snapshots.append({"timestamp":r["timestamp"],"coverage_sections_pct":coverage,
  "observed_valid_votes":votes,"predicted_13_pct":predicted,
  "absolute_error_pp":abs(predicted-target),
  "winner_correct":(v13>v22)==(integer(final["votos_13"])>integer(final["votos_22"])) if v13!=v22 else None})
bins=[]
for start in range(5,101,5):
 eligible=[s for s in snapshots if s["coverage_sections_pct"]>=start]
 if not eligible:
  bins.append({"threshold_pct":start,"status":"NOT_REACHED"});continue
 s=eligible[0]
 bins.append({"threshold_pct":start,**s})
errors=[s["absolute_error_pp"] for s in bins if "absolute_error_pp" in s and s["threshold_pct"]<100]
summary={"status":"BACKTEST_BASELINE_EXECUTADO","model":"participacao_nos_votos_ja_apurados",
 "caveat":"Não é o modelo territorial avançado. Resultado final é usado SOMENTE como alvo de avaliação e denominador de cobertura; nunca como atributo preditivo.",
 "rows_source":len(rows),"scopes":dict(scopes),"national_snapshots":len(national),
 "first_timestamp":national[0]["timestamp"],"last_timestamp":national[-1]["timestamp"],
 "final_13_pct":target,"final_22_pct":100-target,
 "monotonicity_violations":violations[:100],"monotonicity_violations_count":len(violations),
 "thresholds":bins,"mae_pp_5_to_95":sum(errors)/len(errors) if errors else None,
 "thresholds_error_le_0_1_pp":sum(s.get("absolute_error_pp",math.inf)<=0.1 for s in bins if s["threshold_pct"]<100),
 "thresholds_evaluated":sum("absolute_error_pp" in s for s in bins if s["threshold_pct"]<100),
 "limitations":["O CSV pode conter snapshots não uniformes ou revisões.","O número de seções finais é conhecido apenas para definir marcos retrospectivos.","Uma única eleição não demonstra taxa de acerto de 99,9%.","Sem ordem de entrada por seção, não é possível validar ponderação territorial por seção.","O erro do baseline não certifica o modelo territorial."]}
(OUT/"backtest_baseline_nacional.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({k:v for k,v in summary.items() if k!="thresholds"},ensure_ascii=False,indent=2))
