#!/usr/bin/env python3
"""Backtest temporal SEM vazamento: baseline de proporção observada; não certifica inferência ecológica."""
import csv,json,math,pathlib,statistics,datetime,collections
P=pathlib.Path("dados/2026/backtest/csv/acervo_2026_2/observacoes_nacional_uf.csv")
OUT=pathlib.Path("dados/2026/backtest/backtest_temporal_baseline.json")
FIELDS=["secoes_contabilizadas","eleitores_secoes_contabilizadas","comparecimento","brancos","nulos","votos_13","votos_22"]
def dt(x):return datetime.datetime.fromisoformat(x.replace("Z","+00:00"))
rows=[]
with P.open(encoding="utf-8-sig",newline="") as f:
 for r in csv.DictReader(f):
  if r["scope"]!="BR" or r["uf"] or r["municipio_tse"]:continue
  try:
   t=dt(r["timestamp"]); nums={k:int(r[k]) for k in FIELDS}
  except (ValueError,KeyError,TypeError):continue
  if min(nums.values())<0:raise ValueError("Contagem negativa")
  if nums["votos_13"]+nums["votos_22"]+nums["brancos"]+nums["nulos"]>nums["comparecimento"]:raise ValueError("Votos excedem comparecimento")
  rows.append((t,nums))
rows.sort(key=lambda z:z[0])
if len(rows)<5:raise ValueError("Poucas observações nacionais")
if len({t for t,_ in rows})!=len(rows):raise ValueError("Timestamps nacionais duplicados; requer política explícita")
for (_,prev),(_,cur) in zip(rows,rows[1:]):
 for k in FIELDS:
  if cur[k]<prev[k]:raise ValueError("Acumulado decrescente: "+k)
final=rows[-1][1]
if final["secoes_contabilizadas"]<=0 or final["votos_13"]+final["votos_22"]<=0:raise ValueError("Final inválido")
final_share=final["votos_13"]/(final["votos_13"]+final["votos_22"])
records=[]
for i,(t,r) in enumerate(rows[:-1]):
 progress=r["secoes_contabilizadas"]/final["secoes_contabilizadas"]
 # Final serve EXCLUSIVAMENTE para avaliação ex post e seleção dos cortes no relatório.
 # Predição usa apenas votos acumulados no instante t; sem parâmetros aprendidos com dados futuros.
 den=r["votos_13"]+r["votos_22"]
 if not den:continue
 pred=r["votos_13"]/den
 records.append({"timestamp":t.isoformat(),"secoes_contabilizadas":r["secoes_contabilizadas"],"progresso_avaliado_ex_post":round(progress,6),"previsao_share_13":round(pred,8),"erro_pp":round(100*(pred-final_share),6)})
bins=[(0.01,0.05),(0.05,0.1),(0.1,0.25),(0.25,0.5),(0.5,0.75),(0.75,0.9),(0.9,0.99)]
summary=[]
for lo,hi in bins:
 sample=[r for r in records if lo<=r["progresso_avaliado_ex_post"]<hi]
 summary.append({"faixa_progresso":[lo,hi],"n":len(sample),"mae_pp":round(statistics.mean(abs(x["erro_pp"]) for x in sample),6) if sample else None,"vies_pp":round(statistics.mean(x["erro_pp"] for x in sample),6) if sample else None,"erro_max_pp":round(max(abs(x["erro_pp"]) for x in sample),6) if sample else None})
report={"status":"BASELINE_TEMPORAL_EXECUTADO_NAO_CERTIFICADO","metodo":"proporcao_acumulada_sem_ajuste","parametros_congelados":{"versao":"1.0","formula":"votos_13(t)/(votos_13(t)+votos_22(t))","treino":"nenhum","corte_temporal":"timestamp<=t"},"n_observacoes":len(rows),"n_previsoes":len(records),"alvo_final_apenas_avaliacao":{"share_13":round(final_share,8),"secoes":final["secoes_contabilizadas"]},"metricas_por_progresso":summary,"limites":["Progresso ex post usa denominador final somente para agrupamento e não participa da previsão.","Não valida imputação por seção nem inferência de transferência individual.","Não mede intervalos calibrados, falhas de rede ou robustez a mudanças territoriais.","Comparação externa com dados primários e testes do modelo principal ainda pendentes."]}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
