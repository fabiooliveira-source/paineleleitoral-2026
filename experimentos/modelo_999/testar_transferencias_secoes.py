#!/usr/bin/env python3
"""Limites ecológicos de transferências em seções com zero voto.
Não identifica votos individuais. Usa limites de Fréchet com eleitorado igual.
"""
import csv,json,pathlib,collections
p=pathlib.Path("dados/2026/secoes_com_zero.csv")
out=pathlib.Path("experimentos/modelo_999/resultados/limites_transferencias_secoes_zero.json")
with p.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f,delimiter=";"))
def n(row,k):return int(row.get(k) or 0)
tot=collections.Counter();samples=[];issues=collections.Counter()
for r in rows:
 if r.get("situacao_dados_1t")!="conferido" or r.get("situacao_dados_2t")!="conferido":
  issues["situacao_nao_conferida"]+=1;continue
 N=n(r,"aptos_1t")
 if N!=n(r,"aptos_2t") or N==0:
  issues["eleitorado_diferente"]+=1;continue
 L1=n(r,"lula_1t");F1=n(r,"flavio_1t");L2=n(r,"lula_2t");F2=n(r,"flavio_2t")
 # Primeiro turno: terceiros = votos nominais exceto os dois finalistas.
 other=max(0,n(r,"nominais_1t")-L1-F1)
 if L1+F1+other> N or L2+F2>N:
  issues["margens_inconsistentes"]+=1;continue
 # Fréchet: max(0, grupo_1 + grupo_2 - eleitorado) <= interseção <= min(grupos).
 bounds={}
 for label,target in [("outros_para_lula",L2),("outros_para_flavio",F2),
                      ("lula_para_flavio",F2),("flavio_para_lula",L2)]:
  src=other if label.startswith("outros") else (L1 if label.startswith("lula") else F1)
  lo=max(0,src+target-N);hi=min(src,target)
  bounds[label]={"min":lo,"max":hi}
  tot[label+"_min"]+=lo;tot[label+"_max"]+=hi
 tot["secoes_validas"]+=1;tot["eleitorado"]+=N;tot["votos_outros_1t"]+=other
 if len(samples)<12:samples.append({"uf":r["uf"],"municipio_tse":r["codigo_municipio_tse"],"zona":r["zona"],"secao":r["secao"],"limites":bounds})
report={"status":"LIMITES_ECOLOGICOS_SUBCONJUNTO_ZERO","subset":"Apenas seções em secoes_com_zero.csv, não universo completo de urnas.",
 "total_rows":len(rows),"valid_sections":tot["secoes_validas"],"excluded":dict(issues),
 "aggregate_bounds":dict(tot),"examples":samples,
 "interpretation":"Limites de identificação parcial por seção, NÃO transferências observadas. A soma de limites é válida para o subconjunto de seções.",
 "caveats":["Mudanças de eleitorado excluídas, evitando supor mesmo conjunto de pessoas.",
 "Mesmo com aptos iguais, eleitores podem mudar; os limites são condicionais à estabilidade do universo de votantes elegíveis.",
 "Não há vínculo individual entre votos do primeiro e segundo turno devido ao sigilo do voto.",
 "Para análise nacional urna a urna, é necessário obter o comparacao_secoes.csv integral, ausente no repositório atual."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="examples"},ensure_ascii=False))
