#!/usr/bin/env python3
"""Backtest de projeção UF com pesos e preferência do primeiro turno (sem dados futuros).
Modelo de pesquisa; nenhuma calibração foi realizada com o resultado final.
"""
import csv,collections,datetime,json,pathlib,bisect
root=pathlib.Path("dados/2026")
out=pathlib.Path("experimentos/modelo_999/resultados/backtest_primeiro_turno_uf.json")
def read(p,sep=","):
 with p.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f,delimiter=sep))
def n(x):return int(x or 0)
def tm(x):return datetime.datetime.fromisoformat(x.replace("Z","+00:00"))
hist=collections.defaultdict(lambda:[0,0,0])
for r in read(root/"comparacao_municipios.csv",";"):
 u=r["uf"];hist[u][0]+=n(r["lula_1t"]);hist[u][1]+=n(r["flavio_1t"]);hist[u][2]+=n(r["validos_1t"])
assert len(hist)==28
# O denominador de votos válidos inclui terceiros; para o modelo de 2 candidatos
# usa-se apenas os votos Lula+Flávio, com participação territorial de válidos.
first={u:{"share":a/(a+b),"weight":v} for u,(a,b,v) in hist.items() if a+b and v}
assert len(first)==28
rows=read(root/"backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
groups=collections.defaultdict(list)
for r in rows:groups[r["scope"]].append(r)
for g in groups.values():g.sort(key=lambda r:tm(r["timestamp"]))
br=groups.pop("BR");assert set(groups)==set(first)
final=br[-1];target=n(final["votos_13"])/(n(final["votos_13"])+n(final["votos_22"]))
total_first=sum(x["weight"] for x in first.values())
first_national=sum(hist[u][0] for u in hist)/sum(hist[u][0]+hist[u][1] for u in hist)
indices={u:0 for u in first};latest={u:None for u in first}
series=[]
for r in br:
 t=tm(r["timestamp"]);a=n(r["votos_13"]);b=n(r["votos_22"])
 if a+b==0:continue
 for u,rr in groups.items():
  while indices[u]<len(rr) and tm(rr[indices[u]]["timestamp"])<=t:
   latest[u]=rr[indices[u]];indices[u]+=1
 coverage=n(r["secoes_contabilizadas"])/n(final["secoes_contabilizadas"])
 # Modelo de balanço territorial: a fração não apurada é estimada pela
 # cobertura NACIONAL de seções, não por dados futuros das UFs.
 # O swing nacional é estimado usando os votos observados e a composição
 # de referência das UFs. Cada UF contribui com diferença de sua votação
 # observada em relação à preferência do primeiro turno.
 residual_num=residual_den=0.0;fresh=0
 for u,rr in latest.items():
  if rr is None:continue
  age=(t-tm(rr["timestamp"])).total_seconds()
  if age>300:continue
  aa=n(rr["votos_13"]);bb=n(rr["votos_22"])
  if aa+bb==0:continue
  # Shrinkage do swing observado para evitar UFs de baixa cobertura.
  weight=min(aa+bb,first[u]["weight"])*max(0,1-age/600)
  residual_num+=weight*(aa/(aa+bb)-first[u]["share"])
  residual_den+=weight;fresh+=1
 swing=residual_num/residual_den if residual_den else 0.0
 # Estimativa de votos ainda não apurados baseada no peso do primeiro turno.
 # Em 100%, a previsão é o resultado observado (não usa alvo como feature).
 remaining=max(0.0,1-coverage)
 expected_unseen_13=0.0
 for u,x in first.items():
  estimate=max(0,min(1,x["share"]+swing))
  expected_unseen_13+=x["weight"]/total_first*estimate
 forecast=(1-remaining)*(a/(a+b))+remaining*expected_unseen_13
 series.append({"timestamp":r["timestamp"],"coverage_pct":coverage*100,
 "baseline_error_pp":abs(a/(a+b)-target)*100,
 "forecast_error_pp":abs(forecast-target)*100,
 "forecast_13_pct":forecast*100,"baseline_13_pct":a/(a+b)*100,
 "swing_pp":swing*100,"fresh_territories":fresh})
check=[]
for pct in range(5,101,5):
 m=next((x for x in series if x["coverage_pct"]>=pct),None)
 if m:check.append({"threshold_pct":pct,**m})
pre=[x for x in check if x["threshold_pct"]<100]
mae=lambda key:sum(x[key] for x in pre)/len(pre)
result={"status":"BACKTEST_HISTORICO_UF_EXPERIMENTAL","first_round_territories":len(first),
 "first_round_valid_votes":total_first,"first_round_two_candidate_share_13_pct":100*first_national,
 "final_13_pct":target*100,"baseline_mae_pp":mae("baseline_error_pp"),
 "historical_mae_pp":mae("forecast_error_pp"),
 "improved_checkpoints":sum(x["forecast_error_pp"]<x["baseline_error_pp"] for x in pre),
 "evaluated_checkpoints":len(pre),"checkpoints":check,
 "method":"Ponderação UF pelos votos válidos do primeiro turno; swing entre participação observada de cada UF e voto dos dois candidatos no primeiro turno; correção por cobertura nacional de seções.",
 "limitations":["A cobertura nacional de seções não equivale à cobertura de votos em cada UF.",
 "O swing por UF pode sofrer viés de ordem de apuração interna.",
 "O peso do primeiro turno não prevê mudança de comparecimento.",
 "Nenhum dado do segundo turno final é usado para projetar; ele é usado apenas na avaliação retrospectiva.",
 "A base histórica municipal agrega primeiro e segundo turno; o código lê exclusivamente colunas sufixadas _1t."]}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps({k:v for k,v in result.items() if k!="checkpoints"},ensure_ascii=False))
