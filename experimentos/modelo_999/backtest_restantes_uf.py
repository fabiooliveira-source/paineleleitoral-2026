#!/usr/bin/env python3
"""Backtest experimental: ponderação por votos esperados restantes em cada UF.
Usa somente primeiro turno e snapshots conhecidos até cada instante.
"""
import csv,collections,datetime,json,pathlib
root=pathlib.Path("dados/2026");out=pathlib.Path("experimentos/modelo_999/resultados/backtest_restantes_uf.json")
def read(p,sep=","):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f,delimiter=sep))
def n(v):return int(v or 0)
def tm(v):return datetime.datetime.fromisoformat(v.replace("Z","+00:00"))
hist=collections.defaultdict(lambda:[0,0,0,0])
for r in read(root/"comparacao_municipios.csv",";"):
 h=hist[r["uf"]];h[0]+=n(r["lula_1t"]);h[1]+=n(r["flavio_1t"]);h[2]+=n(r["validos_1t"]);h[3]+=n(r["comparecimento_1t"])
base={u:{"share":a/(a+b),"weight":v,"turnout":turn} for u,(a,b,v,turn) in hist.items() if a+b and v}
data=collections.defaultdict(list)
for r in read(root/"backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv"):data[r["scope"]].append(r)
for rr in data.values():rr.sort(key=lambda r:tm(r["timestamp"]))
national=data.pop("BR");assert set(base)==set(data)
final=national[-1];target=n(final["votos_13"])/(n(final["votos_13"])+n(final["votos_22"]))
total_first=sum(x["weight"] for x in base.values());end_sections=n(final["secoes_contabilizadas"])
idx={u:0 for u in base};latest={u:None for u in base}
results=[]
for r in national:
 t=tm(r["timestamp"]);a=n(r["votos_13"]);b=n(r["votos_22"])
 if not a+b:continue
 for u,rr in data.items():
  while idx[u]<len(rr) and tm(rr[idx[u]]["timestamp"])<=t:
   latest[u]=rr[idx[u]];idx[u]+=1
 coverage=n(r["secoes_contabilizadas"])/end_sections
 residual=den=0
 for u,rr in latest.items():
  if rr is None:continue
  age=(t-tm(rr["timestamp"])).total_seconds()
  if age>300:continue
  aa=n(rr["votos_13"]);bb=n(rr["votos_22"])
  if not aa+bb:continue
  w=min(aa+bb,base[u]["weight"])*max(0,1-age/600)
  residual+=w*(aa/(aa+bb)-base[u]["share"]);den+=w
 swing=residual/den if den else 0
 # Total de votos válidos projetado é ancorado no total do primeiro turno.
 # Ajuste global de comparecimento somente por informação parcial observada,
 # jamais pelo total final do segundo turno.
 known=sum(n(rr["votos_13"])+n(rr["votos_22"]) for rr in latest.values() if rr)
 # Estimador conservador: não deixa total previsto menor que votos já apurados.
 expected_total=max(total_first, a+b, known)
 unseen={}
 for u,x in base.items():
  rr=latest[u]
  counted=n(rr["votos_13"])+n(rr["votos_22"]) if rr else 0
  expected=x["weight"]*expected_total/total_first
  unseen[u]=max(0,expected-counted)
 unseen_sum=sum(unseen.values())
 predicted_unseen=sum(unseen[u]*max(0,min(1,base[u]["share"]+swing)) for u in base)/unseen_sum if unseen_sum else a/(a+b)
 # Importante: snapshots estaduais são assíncronos, portanto usar a
 # participação nacional observada para os votos já contados.
 remaining=unseen_sum/(unseen_sum+a+b) if unseen_sum else 0
 prediction=(1-remaining)*a/(a+b)+remaining*predicted_unseen
 results.append({"coverage_pct":coverage*100,"baseline_error_pp":abs(a/(a+b)-target)*100,
 "forecast_error_pp":abs(prediction-target)*100,"prediction_13_pct":prediction*100,
 "remaining_fraction":remaining,"swing_pp":swing*100})
check=[next((x for x in results if x["coverage_pct"]>=p),None) for p in range(5,101,5)]
check=[dict(threshold_pct=p,**x) for p,x in zip(range(5,101,5),check) if x]
pre=[x for x in check if x["threshold_pct"]<100]
mae=lambda key:sum(x[key] for x in pre)/len(pre)
report={"status":"BACKTEST_RESTANTES_UF_EXPERIMENTAL","baseline_mae_pp":mae("baseline_error_pp"),
 "remaining_uf_mae_pp":mae("forecast_error_pp"),"improved_checkpoints":sum(x["forecast_error_pp"]<x["baseline_error_pp"] for x in pre),
 "checkpoints":check,"caveats":["Pesos são votos válidos de 1T, não eleitorado de 2T.",
 "UF assíncronas podem gerar soma de votos contados incompatível com BR.",
 "Total esperado de votos é hipótese histórica e não estimativa calibrada.",
 "Comparação em um pleito não certifica precisão futura."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="checkpoints"},ensure_ascii=False))
