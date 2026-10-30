#!/usr/bin/env python3
"""Teste de robustez: contrafactuais de cobertura por UF sem usar finais do 2o turno."""
import csv,collections,datetime,json,pathlib
root=pathlib.Path("dados/2026");out=pathlib.Path("experimentos/modelo_999/resultados/stress_primeiro_turno_uf.json")
def read(p,sep=","):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f,delimiter=sep))
def n(v):return int(v or 0)
def tm(v):return datetime.datetime.fromisoformat(v.replace("Z","+00:00"))
hist=collections.defaultdict(lambda:[0,0,0])
for r in read(root/"comparacao_municipios.csv",";"):
 a=hist[r["uf"]];a[0]+=n(r["lula_1t"]);a[1]+=n(r["flavio_1t"]);a[2]+=n(r["validos_1t"])
base={u:{"share":a/(a+b),"weight":v} for u,(a,b,v) in hist.items() if a+b and v}
data=collections.defaultdict(list)
for r in read(root/"backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv"):data[r["scope"]].append(r)
for rr in data.values():rr.sort(key=lambda r:tm(r["timestamp"]))
national=data.pop("BR");assert set(base)==set(data)
target=n(national[-1]["votos_13"])/(n(national[-1]["votos_13"])+n(national[-1]["votos_22"]))
end_sections=n(national[-1]["secoes_contabilizadas"])
latest={u:None for u in base};indices={u:0 for u in base}
scenarios={"original":{"age":300,"weight_exp":1,"swing_factor":1},
 "strict_60s":{"age":60,"weight_exp":1,"swing_factor":1},
 "lenient_600s":{"age":600,"weight_exp":1,"swing_factor":1},
 "uniform_territory":{"age":300,"weight_exp":0,"swing_factor":1},
 "conservative_swing":{"age":300,"weight_exp":1,"swing_factor":0.5},
 "no_swing":{"age":300,"weight_exp":1,"swing_factor":0}}
records=[]
for r in national:
 t=tm(r["timestamp"]);a=n(r["votos_13"]);b=n(r["votos_22"])
 if a+b==0:continue
 for u,rr in data.items():
  while indices[u]<len(rr) and tm(rr[indices[u]]["timestamp"])<=t:
   latest[u]=rr[indices[u]];indices[u]+=1
 coverage=n(r["secoes_contabilizadas"])/end_sections
 entry={"coverage_pct":coverage*100,"baseline_error_pp":abs(a/(a+b)-target)*100}
 for name,config in scenarios.items():
  residual=den=0
  for u,rr in latest.items():
   if rr is None:continue
   age=(t-tm(rr["timestamp"])).total_seconds()
   if age>config["age"]:continue
   aa=n(rr["votos_13"]);bb=n(rr["votos_22"])
   if not aa+bb:continue
   weight=min(aa+bb,base[u]["weight"])*max(0,1-age/600)
   residual+=weight*(aa/(aa+bb)-base[u]["share"]);den+=weight
  swing=(residual/den if den else 0)*config["swing_factor"]
  if config["weight_exp"]==0:
   unseen=sum(max(0,min(1,x["share"]+swing)) for x in base.values())/len(base)
  else:
   total=sum(x["weight"] for x in base.values())
   unseen=sum(x["weight"]*max(0,min(1,x["share"]+swing)) for x in base.values())/total
  pred=coverage*a/(a+b)+(1-coverage)*unseen
  entry[name+"_error_pp"]=abs(pred-target)*100
 records.append(entry)
check=[next((r for r in records if r["coverage_pct"]>=p),None) for p in range(5,100,5)]
check=[r for r in check if r]
keys=["baseline_error_pp"]+[s+"_error_pp" for s in scenarios]
metrics={k:sum(r[k] for r in check)/len(check) for k in keys}
report={"status":"STRESS_TEST_EXPERIMENTAL","checkpoint_count":len(check),"mae_pp":metrics,
 "notes":["Comparações contrafactuais internas ao mesmo pleito, não validação externa.",
 "Nenhuma variável de segundo turno final é usada no preditor; final só no alvo.",
 "Testes de cobertura e ordem de chegada por UF ainda pendentes.",
 "O nome uniform_territory altera pesos territoriais, não ordem da apuração."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(report,ensure_ascii=False))
