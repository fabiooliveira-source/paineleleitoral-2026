#!/usr/bin/env python3
"""Backtest territorial por UF com treinamento somente nos snapshots disponíveis."""
import csv,json,pathlib,collections,datetime,math
SRC=pathlib.Path("dados/2026/backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
OUT=pathlib.Path("experimentos/modelo_999/resultados/backtest_territorial_uf.json")
def num(x):return int(x or 0)
def dt(x):return datetime.datetime.fromisoformat(x.replace("Z","+00:00"))
with SRC.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
national=sorted((r for r in rows if r["scope"]=="BR"),key=lambda r:dt(r["timestamp"]))
states=collections.defaultdict(list)
for r in rows:
 if len(r["scope"])==2 and r["scope"]!="BR":states[r["scope"]].append(r)
for rs in states.values():rs.sort(key=lambda r:dt(r["timestamp"]))
assert national and states
final=national[-1]
target=100*num(final["votos_13"])/(num(final["votos_13"])+num(final["votos_22"]))
final_sections=num(final["secoes_contabilizadas"])
# Atenção: UF com parcial mais recente não pode ser posterior ao timestamp de corte.
# Baseline ponderado por seções finais de cada UF seria vazamento de informações
# futuras sobre composição final; portanto esta versão usa somente eleitorado
# já contabilizado e NÃO pretende corrigir o voto faltante.
def latest_at(rs,t):
 best=None
 for r in rs:
  if dt(r["timestamp"])<=t:best=r
  else:break
 return best
out=[]
for threshold in range(5,101,5):
 candidates=[r for r in national if 100*num(r["secoes_contabilizadas"])/final_sections>=threshold]
 if not candidates:continue
 r=candidates[0];t=dt(r["timestamp"])
 observed_a=num(r["votos_13"]);observed_b=num(r["votos_22"])
 baseline=100*observed_a/(observed_a+observed_b)
 uf_rows={uf:latest_at(rs,t) for uf,rs in states.items()}
 valid={uf:v for uf,v in uf_rows.items() if v is not None}
 uf_a=sum(num(v["votos_13"]) for v in valid.values())
 uf_b=sum(num(v["votos_22"]) for v in valid.values())
 # Verificação do sincronismo UF x BR; não usar soma se os snapshots divergem.
 discrepancy=(uf_a+uf_b)-(observed_a+observed_b)
 out.append({"threshold_pct":threshold,"timestamp":r["timestamp"],
  "national_observed_13_pct":baseline,"absolute_error_pp":abs(baseline-target),
  "states_available":len(valid),"states_total":len(states),
  "state_snapshot_total_minus_national":discrepancy,
  "state_snapshots_synchronous":discrepancy==0,
  "state_snapshot_max_age_seconds":max((t-dt(v["timestamp"])).total_seconds() for v in valid.values()) if valid else None})
result={"status":"AUDITORIA_SINCRONISMO_TERRITORIAL","final_target_13_pct":target,
 "note":"Esta etapa NÃO é um modelo de correção territorial. Testa causalidade temporal e sincronismo dos dados UF antes de estimar votos faltantes.",
 "thresholds":out,"all_state_snapshots_synchronous":all(x["state_snapshots_synchronous"] for x in out)}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({"synchronous":result["all_state_snapshots_synchronous"],"thresholds":len(out)},ensure_ascii=False))
