#!/usr/bin/env python3
"""Reconciliação hierárquica de margens eleitorais observadas por seção.
NÃO estima migrações individuais; identifica limites e lacunas dos dados.
"""
import csv,json,pathlib,collections
src=pathlib.Path("dados/2026/secoes_com_zero.csv")
out=pathlib.Path("experimentos/modelo_999/resultados/reconciliacao_hierarquica_secoes.json")
def n(r,k):return int(r.get(k) or 0)
fields=["lula_1t","flavio_1t","demais_1t","brancos_1t","nulos_1t","abstencoes_1t",
        "lula_2t","flavio_2t","brancos_2t","nulos_2t","abstencoes_2t"]
totals=collections.defaultdict(collections.Counter);rejected=collections.Counter();seen=set();count=0
with src.open(encoding="utf-8-sig",newline="") as f:
 for r in csv.DictReader(f,delimiter=";"):
  key=(r["uf"],r["codigo_municipio_tse"],r["zona"],r["secao"])
  if key in seen:rejected["duplicate_section"]+=1;continue
  seen.add(key)
  if r["situacao_dados_1t"]!="conferido" or r["situacao_dados_2t"]!="conferido":
   rejected["not_verified"]+=1;continue
  a=n(r,"aptos_1t");b=n(r,"aptos_2t")
  if not a or a!=b:rejected["different_electorate"]+=1;continue
  row={k:n(r,k) for k in fields if k!="demais_1t"}
  row["demais_1t"]=n(r,"nominais_1t")-row["lula_1t"]-row["flavio_1t"]
  if min(row.values())<0 or sum(row[k] for k in fields if k.endswith("_1t"))!=a or sum(row[k] for k in fields if k.endswith("_2t"))!=b:
   rejected["inconsistent_margins"]+=1;continue
  count+=1
  uf,mun,zone,section=key
  for group in ("BR","UF:"+uf,"MUN:"+uf+":"+mun,"SEC:"+":".join(key)):
   totals[group].update(row)
def total(prefix):
 x=collections.Counter()
 for k,v in totals.items():
  if k.startswith(prefix):x.update(v)
 return dict(x)
assert dict(totals["BR"])==total("UF:")==total("MUN:")==total("SEC:")
report={"status":"RECONCILIACAO_EXATA_SUBCONJUNTO","source":str(src),"sections_valid":count,
 "sections_rejected":dict(rejected),"national_subsample":dict(totals["BR"]),
 "ufs":{k[3:]:dict(v) for k,v in totals.items() if k.startswith("UF:")},
 "municipalities":{k[4:]:dict(v) for k,v in totals.items() if k.startswith("MUN:")},
 "checks":{"section_to_municipality":True,"municipality_to_uf":True,"uf_to_national":True},
 "warnings":["Conciliação do subconjunto de seções com zero, NÃO do Brasil completo.",
 "A matriz de transição ainda não é identificada pelas margens observadas.",
 "Não se pode inferir origem individual de voto pelo resultado agregado."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":report["status"],"sections_valid":count,"sections_rejected":dict(rejected)},ensure_ascii=False))
