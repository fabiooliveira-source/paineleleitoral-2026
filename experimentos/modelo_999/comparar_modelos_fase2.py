#!/usr/bin/env python3
"""Comparacao pareada dos modelos ja calculados, com testes de sensibilidade temporal."""
import json,pathlib,statistics
p=pathlib.Path("experimentos/modelo_999/resultados")
b=json.loads((p/"backtest_nowcast_uf.json").read_text())
h=json.loads((p/"backtest_primeiro_turno_uf.json").read_text())
bs={x["threshold_pct"]:x for x in b["thresholds"] if x["threshold_pct"]<100}
hs={x["threshold_pct"]:x for x in h["checkpoints"] if x["threshold_pct"]<100}
assert set(bs)==set(hs)==set(range(5,100,5))
rows=[]
for k in sorted(bs):
 x=bs[k];y=hs[k]
 assert x["timestamp"]==y["timestamp"],(k,x["timestamp"],y["timestamp"])
 rows.append({"threshold_pct":k,"baseline_error_pp":x["baseline_error_pp"],
 "territorial_trend_error_pp":x["nowcast_error_pp"],
 "first_round_weighted_error_pp":y["forecast_error_pp"],
 "improvement_pp":x["baseline_error_pp"]-y["forecast_error_pp"]})
mae=lambda s,field:statistics.mean(r[field] for r in s)
periods={}
for name,lo,hi in (("inicio_5_25",5,25),("meio_30_65",30,65),("final_70_95",70,95)):
 a=[r for r in rows if lo<=r["threshold_pct"]<=hi]
 periods[name]={"n":len(a),"baseline_mae_pp":mae(a,"baseline_error_pp"),
 "historico_mae_pp":mae(a,"first_round_weighted_error_pp"),
 "melhoria_mae_pp":mae(a,"improvement_pp")}
result={"status":"VALIDACAO_RETROSPECTIVA_PAREADA","snapshots":len(rows),
 "baseline_mae_pp":mae(rows,"baseline_error_pp"),
 "tendencia_territorial_mae_pp":mae(rows,"territorial_trend_error_pp"),
 "historico_primeiro_turno_mae_pp":mae(rows,"first_round_weighted_error_pp"),
 "melhoria_absoluta_pp":mae(rows,"improvement_pp"),
 "melhoria_relativa_pct":100*mae(rows,"improvement_pp")/mae(rows,"baseline_error_pp"),
 "snapshots_historico_melhor":sum(r["improvement_pp"]>0 for r in rows),
 "periodos":periods,"checkpoints":rows,
 "status_certificacao":"NAO_CERTIFICADO",
 "limitacoes":["O primeiro turno de 2026 e informacao anterior ao segundo, mas nao valida independencia de selecao de modelo.",
 "Os 19 checkpoints de uma unica eleicao sao temporalmente dependentes.",
 "Nao houve validacao em outras eleicoes nem teste de sensibilidade ao drift regional.",
 "Nao converter desempenho retrospectivo em probabilidade de acerto."]}
(p/"comparacao_modelos_fase2.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="checkpoints"},ensure_ascii=False))
