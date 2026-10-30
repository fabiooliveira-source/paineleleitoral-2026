#!/usr/bin/env python3
"""Stress de disponibilidade territorial com cenarios predefinidos, sem calibrar no alvo."""
import csv,collections,datetime,json,pathlib,statistics
root=pathlib.Path("dados/2026");out=pathlib.Path("experimentos/modelo_999/resultados")
def read(p,sep=","):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f,delimiter=sep))
def n(x):return int(x or 0)
def tm(x):return datetime.datetime.fromisoformat(x.replace("Z","+00:00"))
hist=collections.defaultdict(lambda:[0,0,0])
for r in read(root/"comparacao_municipios.csv",";"):
 h=hist[r["uf"]];h[0]+=n(r["lula_1t"]);h[1]+=n(r["flavio_1t"]);h[2]+=n(r["validos_1t"])
first={u:{"share":a/(a+b),"weight":v} for u,(a,b,v) in hist.items() if a+b and v}
rows=read(root/"backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
groups=collections.defaultdict(list)
for r in rows:groups[r["scope"]].append(r)
for rr in groups.values():rr.sort(key=lambda r:tm(r["timestamp"]))
br=groups.pop("BR");assert set(groups)==set(first)
target=n(br[-1]["votos_13"])/(n(br[-1]["votos_13"])+n(br[-1]["votos_22"]))
end=n(br[-1]["secoes_contabilizadas"])
# Controle temporal: no cenario com atraso, a UF so pode contribuir com observacoes <= t-atraso.
scenarios=[("referencia",0,set()),("atraso_5min",5,set()),("atraso_15min",15,set()),
 ("atraso_30min",30,set()),("sem_SP",0,{"SP"}),("sem_SP_MG_RJ",0,{"SP","MG","RJ"}),
 ("sem_Nordeste",0,{"BA","SE","AL","PE","PB","RN","CE","PI","MA"})]
results={}
for label,delay,excluded in scenarios:
 idx={u:0 for u in first};last={u:None for u in first}
 checks={}
 for r in br:
  t=tm(r["timestamp"]);a=n(r["votos_13"]);b=n(r["votos_22"])
  if a+b==0:continue
  cutoff=t-datetime.timedelta(minutes=delay)
  for u,rr in groups.items():
   while idx[u]<len(rr) and tm(rr[idx[u]]["timestamp"])<=cutoff:
    last[u]=rr[idx[u]];idx[u]+=1
  numerator=denominator=0.;fresh=0
  for u,rr in last.items():
   if u in excluded or rr is None:continue
   age=(cutoff-tm(rr["timestamp"])).total_seconds()
   if age>300:continue
   aa=n(rr["votos_13"]);bb=n(rr["votos_22"])
   if aa+bb==0:continue
   w=min(aa+bb,first[u]["weight"])*max(0,1-age/600)
   numerator+=w*(aa/(aa+bb)-first[u]["share"]);denominator+=w;fresh+=1
  swing=numerator/denominator if denominator else 0.
  total_weight=sum(v["weight"] for u,v in first.items() if u not in excluded)
  # Sem dado de UF, mantem referencia do 1T para o territorio ausente.
  unseen=sum(v["weight"]*max(0,min(1,v["share"]+(swing if u not in excluded else 0)))
    for u,v in first.items())/sum(v["weight"] for v in first.values())
  coverage=n(r["secoes_contabilizadas"])/end
  pred=coverage*(a/(a+b))+(1-coverage)*unseen
  for k in range(5,100,5):
   if k not in checks and coverage*100>=k:
    checks[k]={"error_pp":100*abs(pred-target),"baseline_error_pp":100*abs(a/(a+b)-target),
      "fresh_ufs":fresh,"timestamp":r["timestamp"]}
 assert len(checks)==19,(label,len(checks))
 values=list(checks.values())
 results[label]={"mae_pp":statistics.mean(x["error_pp"] for x in values),
 "baseline_mae_pp":statistics.mean(x["baseline_error_pp"] for x in values),
 "mae_5_25_pp":statistics.mean(checks[k]["error_pp"] for k in range(5,26,5)),
 "melhores_que_baseline":sum(x["error_pp"]<x["baseline_error_pp"] for x in values),
 "media_ufs_frescas":statistics.mean(x["fresh_ufs"] for x in values),
 "checkpoints":checks}
ref=results["referencia"]["mae_pp"]
report={"status":"STRESS_EXECUTADO","cenarios":results,
 "referencia_mae_pp":ref,"todos_cenarios_superam_baseline":all(v["mae_pp"]<v["baseline_mae_pp"] for v in results.values()),
 "pior_cenario":max(results,key=lambda x:results[x]["mae_pp"]),
 "limitacoes":["Cenarios artificiais predefinidos sobre uma unica eleicao.",
 "Atraso reduz disponibilidade dos snapshots UF, nao modifica votos nacionais ja observados.",
 "Exclusao de UF usa share historico sem swing, mas mantem votos nacionais ja apurados.",
 "Nao e validacao independente em outra eleicao nem certificacao de probabilidade."]}
out.mkdir(parents=True,exist_ok=True)
(out/"stress_disponibilidade_uf_fase2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="cenarios"},ensure_ascii=False))
for k,v in results.items():print(k,round(v["mae_pp"],5),v["melhores_que_baseline"])
