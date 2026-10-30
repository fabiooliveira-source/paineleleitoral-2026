#!/usr/bin/env python3
"""Matriz de limites de transição por seção, incluindo todos os candidatos do 1T.
Apenas identificação parcial: voto individual não é observável.
"""
import csv,collections,json,pathlib
src=pathlib.Path("dados/2026/secoes_com_zero.csv")
dst=pathlib.Path("experimentos/modelo_999/resultados/matriz_transferencias_categorias.json")
with src.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f,delimiter=";"))
def n(r,k):return int(r.get(k) or 0)
source=["lula_1t","flavio_1t","demais_candidatos_1t","brancos_1t","nulos_1t","abstencoes_1t"]
target=["lula_2t","flavio_2t","brancos_2t","nulos_2t","abstencoes_2t"]
bounds={a:{b:{"min":0,"max":0} for b in target} for a in source}
excluded=collections.Counter();valid=0;totals=collections.Counter()
for r in rows:
 if r["situacao_dados_1t"]!="conferido" or r["situacao_dados_2t"]!="conferido":
  excluded["dados_nao_conferidos"]+=1;continue
 N=n(r,"aptos_1t")
 if not N or N!=n(r,"aptos_2t"):
  excluded["aptos_diferentes"]+=1;continue
 a={k:n(r,k) for k in source if k!="demais_candidatos_1t"}
 a["demais_candidatos_1t"]=n(r,"nominais_1t")-a["lula_1t"]-a["flavio_1t"]
 b={k:n(r,k) for k in target}
 if min(a.values())<0 or sum(a.values())!=N or sum(b.values())!=N:
  excluded["margens_inconsistentes"]+=1;continue
 valid+=1
 for s in source:
  totals[s]+=a[s]
  for t in target:
   bounds[s][t]["min"]+=max(0,a[s]+b[t]-N)
   bounds[s][t]["max"]+=min(a[s],b[t])
 for t in target:totals[t]+=b[t]
report={"status":"MATRIZ_LIMITES_CATEGORIAS_CONCLUIDA","sections_source":len(rows),
 "sections_eligible":valid,"excluded":dict(excluded),
 "first_round_categories":source,"second_round_categories":target,
 "matrix":bounds,"margins":dict(totals),
 "method":"Limites de Fréchet para cada célula, agregados por seção.",
 "warnings":["Mínimos e máximos de células diferentes não são simultaneamente realizáveis.",
 "Demais candidatos estão agrupados: o arquivo de seções com zero não discrimina cada candidato do 1T.",
 "Mesmo número de aptos não garante que sejam os mesmos eleitores nos dois turnos.",
 "O sigilo do voto impede identificar transferências individuais.",
 "Resultado representa somente o subconjunto de seções com zero, não o país inteiro."]}
dst.parent.mkdir(parents=True,exist_ok=True)
dst.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print(json.dumps({"status":report["status"],"sections_eligible":valid,"excluded":dict(excluded)},ensure_ascii=False))
