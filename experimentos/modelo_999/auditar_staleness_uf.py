#!/usr/bin/env python3
"""Auditoria de staleness e reconciliação de UF, sem dados futuros."""
import csv,collections,datetime,json,pathlib
p=pathlib.Path("dados/2026/backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
out=pathlib.Path("experimentos/modelo_999/resultados/auditoria_staleness_uf.json")
def ts(s):return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
def n(s):return int(s or 0)
with p.open(encoding="utf-8-sig",newline="") as f: data=list(csv.DictReader(f))
by=collections.defaultdict(list)
for row in data:by[row["scope"]].append(row)
for k in by:by[k].sort(key=lambda x:ts(x["timestamp"]))
br=by["BR"];uf={k:v for k,v in by.items() if k!="BR"}
assert len(uf)==28,"Esperadas 27 UFs e exterior ZZ"
thresholds=[0,60,120,300,600,1800]
snapshots=[]
for row in br:
 t=ts(row["timestamp"]);bv=n(row["votos_13"])+n(row["votos_22"])
 current={}
 for state,records in uf.items():
  candidates=[r for r in records if ts(r["timestamp"])<=t]
  if candidates:current[state]=candidates[-1]
 summary={"timestamp":row["timestamp"],"national_votes":bv}
 for seconds in thresholds:
  valid=[r for r in current.values() if (t-ts(r["timestamp"])).total_seconds()<=seconds]
  votes=sum(n(r["votos_13"])+n(r["votos_22"]) for r in valid)
  summary["max_age_"+str(seconds)+"s"]={"territories":len(valid),"votes":votes,"difference_vs_national":votes-bv}
 snapshots.append(summary)
report={"status":"AUDITORIA_STALENESS_CONCLUIDA","territories":sorted(uf),
 "note":"Somas filtradas por idade não devem ser tratadas como estimativas nacionais. Nenhum resultado futuro é utilizado.",
 "snapshots":snapshots}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("Auditoria temporal concluída:",len(snapshots),"snapshots; territórios:",len(uf))
