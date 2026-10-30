#!/usr/bin/env python3
"""Diagnosticar perdas de Lula/Flávio por seção: limites de destino, NÃO rastreio individual."""
import json,gzip,pathlib,collections
root=pathlib.Path("dados/2026");dest=pathlib.Path("experimentos/modelo_999/resultados/diagnostico_perdas_finalistas.json")
ufs=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO","ZZ"]
summary={p:collections.Counter() for p in ("lula","flavio")}
byuf={};examples={p:[] for p in summary};excluded=collections.Counter()
for uf in ufs:
 obj=json.loads(gzip.decompress((root/f"secoes-{uf}.json.gz").read_bytes()))
 ix={k:i for i,k in enumerate(obj["colunas"])}
 u={p:collections.Counter() for p in summary}
 for row in obj["linhas"]:
  def v(k):return int(row[ix[k]])
  if row[ix["situacao_dados_1t"]]!="conferido" or row[ix["situacao_dados_2t"]]!="conferido":
   excluded["not_verified"]+=1;continue
  N=v("aptos_1t")
  if N<=0 or N!=v("aptos_2t"):
   excluded["different_electorate"]+=1;continue
  src={"lula":v("lula_1t"),"flavio":v("flavio_1t")}
  dst={"lula":v("lula_2t"),"flavio":v("flavio_2t"),
       "branco":v("brancos_2t"),"nulo":v("nulos_2t"),"abstencao":v("abstencoes_2t")}
  if sum(dst.values())!=N or v("nominais_1t")+v("brancos_1t")+v("nulos_1t")+v("abstencoes_1t")!=N:
   excluded["inconsistent_margins"]+=1;continue
  for p in summary:
   s=src[p];t=dst[p]
   if s>=t: pass
   else:continue
   if s==t:continue
   loss=s-t
   u[p]["sections_with_net_loss"]+=1;u[p]["net_losses_in_those_sections"]+=loss
   # Minimum exits from p to ANY other destination is s - min(s,t) = s-t.
   # Frechet bounds per destination, cannot be added as if simultaneous.
   for dest_name,target in dst.items():
    if dest_name==p:continue
    lo=max(0,s+target-N);hi=min(s,target)
    u[p][dest_name+"_min"]+=lo;u[p][dest_name+"_max"]+=hi
   if len(examples[p])<15:
    examples[p].append({"uf":uf,"municipio_tse":str(row[ix["codigo_municipio_tse"]]),"zona":str(row[ix["zona"]]),"secao":str(row[ix["secao"]]),"net_loss":loss,
      "destinations":{d:{"min":max(0,s+x-N),"max":min(s,x)} for d,x in dst.items() if d!=p}})
 for p in summary:summary[p].update(u[p])
 byuf[uf]={p:dict(u[p]) for p in summary}
report={"status":"DIAGNOSTICO_LIMITES_PERDAS","scope":"Seções com aptos idênticos, ambos turnos conferidos",
 "total":{p:dict(v) for p,v in summary.items()},"by_uf":byuf,"examples":examples,"excluded":dict(excluded),
 "warnings":["Perda líquida não equivale a fluxo individual: retenções e entradas podem coexistir.",
 "Limites por destino são marginais; seus máximos não podem ser somados.",
 "Mesmo eleitorado numérico não prova identidade dos eleitores.",
 "Sem dados individuais, não é possível determinar quem mudou de voto.",
 "Seções com alteração de aptos foram excluídas desta análise."]}
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":report["status"],"total":report["total"],"excluded":dict(excluded)},ensure_ascii=False))
