#!/usr/bin/env python3
"""Portao independente de qualidade: baseline vs nowcast, sem afirmar certificacao."""
import json,pathlib,statistics
base=pathlib.Path("experimentos/modelo_999/resultados")
d=json.loads((base/"backtest_nowcast_uf.json").read_text())
rows=[r for r in d["thresholds"] if r["threshold_pct"]<100]
assert len(rows)==19
assert all(rows[i]["timestamp"]<=rows[i+1]["timestamp"] for i in range(len(rows)-1))
assert all(rows[i]["coverage_pct"]<=rows[i+1]["coverage_pct"] for i in range(len(rows)-1))
delta=[r["nowcast_error_pp"]-r["baseline_error_pp"] for r in rows]
improved=sum(x<0 for x in delta)
mae_baseline=statistics.mean(r["baseline_error_pp"] for r in rows)
mae_nowcast=statistics.mean(r["nowcast_error_pp"] for r in rows)
early=[r for r in rows if r["threshold_pct"]<=25]
res={"estado":"AVALIADO","aprovado_para_substituir_baseline":mae_nowcast<mae_baseline,
"n_snapshots":len(rows),"mae_baseline_pp":mae_baseline,"mae_nowcast_pp":mae_nowcast,
"degradacao_mae_pp":mae_nowcast-mae_baseline,"snapshots_melhores":improved,
"snapshots_piores":sum(x>0 for x in delta),"maior_degradacao_pp":max(delta),
"maior_melhoria_pp":-min(delta),
"primeiros_25_pct":{"mae_baseline_pp":statistics.mean(r["baseline_error_pp"] for r in early),
"mae_nowcast_pp":statistics.mean(r["nowcast_error_pp"] for r in early)},
"criterio":"MAE estritamente inferior ao baseline nos 19 thresholds 5..95, parametros predefinidos",
"ressalvas":["Uma eleicao apenas; thresholds correlacionados, nao amostra independente.",
"Sem probabilidades calibradas e sem validacao fora da amostra.",
"Alvo final utilizado apenas na avaliacao retrospectiva."]}
(base/"portao_qualidade_nowcast.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(res,ensure_ascii=False))
