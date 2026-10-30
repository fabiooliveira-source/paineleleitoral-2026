#!/usr/bin/env python3
"""Backtest de nowcast territorial por UF, causal, sem treinamento no resultado final.

É um modelo experimental: estima voto futuro por tendência de UF e estabilização
nacional. Não usa totais finais por UF, que constituiriam vazamento temporal.
"""
import csv,collections,datetime,json,pathlib,math
SRC=pathlib.Path("dados/2026/backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
OUT=pathlib.Path("experimentos/modelo_999/resultados/backtest_nowcast_uf.json")
def tm(x):return datetime.datetime.fromisoformat(x.replace("Z","+00:00"))
def num(x):return int(x or 0)
def share(r):
 a=num(r["votos_13"]);b=num(r["votos_22"])
 return a/(a+b) if a+b else None
with SRC.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
by=collections.defaultdict(list)
for r in rows:by[r["scope"]].append(r)
for k in by:by[k].sort(key=lambda r:tm(r["timestamp"]))
br=by.pop("BR");final=br[-1]
assert len(by)==28
final_sections=num(final["secoes_contabilizadas"])
target=share(final)
# Snapshot de cada UF no instante nacional: não utilizar registros posteriores.
idx={uf:0 for uf in by}
last={uf:None for uf in by}
previous={uf:None for uf in by}
evaluations=[]
for r in br:
 t=tm(r["timestamp"]);baseline=share(r)
 if baseline is None:continue
 for uf,rr in by.items():
  while idx[uf]<len(rr) and tm(rr[idx[uf]]["timestamp"])<=t:
   previous[uf]=last[uf]
   last[uf]=rr[idx[uf]]
   idx[uf]+=1
 # Sinal de tendência calculado somente com duas observações reais por UF.
 weighted_signal=weighted_den=0.0
 stale=0
 for uf,cur in last.items():
  prev=previous[uf]
  if cur is None or prev is None:continue
  age=(t-tm(cur["timestamp"])).total_seconds()
  if age>300:stale+=1;continue
  cur_share=share(cur);prev_share=share(prev)
  if cur_share is None or prev_share is None:continue
  delta_sections=num(cur["secoes_contabilizadas"])-num(prev["secoes_contabilizadas"])
  if delta_sections<=0:continue
  # Tendência local de curto prazo com peso por crescimento de seções,
  # amortecida por idade do dado. Não pressupõe cobertura final conhecida.
  weight=math.sqrt(delta_sections)*math.exp(-age/120)
  weighted_signal+=weight*(cur_share-prev_share)
  weighted_den+=weight
 trend=weighted_signal/weighted_den if weighted_den else 0.0
 # Shrinkage para evitar extrapolação excessiva. Parâmetro fixo, não ajustado
 # ao resultado final de 2026.
 forecast=max(0.0,min(1.0,baseline+0.5*trend))
 coverage=100*num(r["secoes_contabilizadas"])/final_sections
 evaluations.append({"timestamp":r["timestamp"],"coverage_pct":coverage,
 "baseline_13_pct":100*baseline,"nowcast_13_pct":100*forecast,
 "baseline_error_pp":100*abs(baseline-target),
 "nowcast_error_pp":100*abs(forecast-target),
 "fresh_state_trends":sum(1 for uf,cur in last.items() if cur is not None and previous[uf] is not None and (t-tm(cur["timestamp"])).total_seconds()<=300),
 "stale_states_with_trend":stale})
bins=[]
for pct in range(5,101,5):
 matching=[r for r in evaluations if r["coverage_pct"]>=pct]
 if matching:bins.append({"threshold_pct":pct,**matching[0]})
pre=[r for r in bins if r["threshold_pct"]<100]
mae=lambda k:sum(r[k] for r in pre)/len(pre) if pre else None
result={"status":"NOWCAST_UF_EXPERIMENTAL_NAO_CERTIFICADO",
 "description":"Tendência de UF em snapshots disponíveis até t, corrigindo baseline nacional com shrinkage fixo.",
 "target_final_13_pct":100*target,"thresholds":bins,
 "baseline_mae_pp":mae("baseline_error_pp"),"nowcast_mae_pp":mae("nowcast_error_pp"),
 "nowcast_better_thresholds":sum(r["nowcast_error_pp"]<r["baseline_error_pp"] for r in pre),
 "thresholds_evaluated":len(pre),
 "limitations":["Sem dados históricos de 1o turno por UF, não estima composição do eleitorado ainda não apurado.",
 "Uma única eleição não permite calibrar a probabilidade de 99,9%.",
 "Comparação em 2026 é retrospectiva; não foi feito treino externo nem validação cruzada.",
 "Defasagem de UF tratada por limite de 300 s e ponderação por idade; não garante ausência de viés territorial."]}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({k:v for k,v in result.items() if k!="thresholds"},ensure_ascii=False))
