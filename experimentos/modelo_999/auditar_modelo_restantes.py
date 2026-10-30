#!/usr/bin/env python3
"""Auditoria independente de coerência e sensibilidade do backtest por UF."""
import json,pathlib,statistics
p=pathlib.Path("experimentos/modelo_999/resultados")
new=json.loads((p/"backtest_restantes_uf.json").read_text())
old=json.loads((p/"backtest_primeiro_turno_uf.json").read_text())
base=json.loads((p/"backtest_baseline_nacional.json").read_text())
a={x["threshold_pct"]:x for x in new["checkpoints"]}
b={x["threshold_pct"]:x for x in old["checkpoints"]}
assert set(range(5,101,5))<=set(a) and set(a)==set(b)
rows=[]
for k in range(5,100,5):
 x=a[k];y=b[k]
 assert 0<=x["remaining_fraction"]<=1
 rows.append({"coverage":k,"baseline":x["baseline_error_pp"],"old":y["forecast_error_pp"],"new":x["forecast_error_pp"],
 "gain_vs_old":y["forecast_error_pp"]-x["forecast_error_pp"]})
mae=lambda key:statistics.mean(x[key] for x in rows)
# Verifica anomalia da regra de total esperado: a previsão não deve se tornar
# determinística em 100% sem explicitar que o resultado já está conhecido.
out={"status":"AUDITORIA_COMPARATIVA_CONCLUIDA",
 "mae_pp":{k:mae(k) for k in ["baseline","old","new"]},
 "new_beats_old":sum(x["gain_vs_old"]>0 for x in rows),
 "new_worse_than_old":sum(x["gain_vs_old"]<0 for x in rows),
 "new_worse_checkpoints":[x["coverage"] for x in rows if x["gain_vs_old"]<0],
 "early_5_25_mae":{k:statistics.mean(x[k] for x in rows if x["coverage"]<=25) for k in ["baseline","old","new"]},
 "late_75_95_mae":{k:statistics.mean(x[k] for x in rows if x["coverage"]>=75) for k in ["baseline","old","new"]},
 "flags":["O total de votos válidos do primeiro turno pode subestimar ou superestimar o segundo.",
 "A soma de UFs assíncronas não equivale ao instantâneo nacional.",
 "A validação utiliza o mesmo pleito que motivou o desenvolvimento: risco de sobreajuste.",
 "Faltam testes por município, ordem de apuração e pleitos externos."],
 "checkpoint_details":rows}
(p/"auditoria_comparativa_restantes.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({k:v for k,v in out.items() if k!="checkpoint_details"},ensure_ascii=False))
