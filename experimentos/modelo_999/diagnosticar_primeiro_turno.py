#!/usr/bin/env python3
"""Extrai metadados da base municipal do primeiro turno sem ler o segundo turno como preditor."""
import csv,json,pathlib,collections
p=pathlib.Path("dados/2026/comparacao_municipios.csv")
out=pathlib.Path("experimentos/modelo_999/resultados/diagnostico_primeiro_turno.json")
with p.open(encoding="utf-8-sig",newline="") as f:
 reader=csv.DictReader(f,delimiter=";")
 fields=reader.fieldnames
 rows=list(reader)
report={"source":str(p),"source_description":"Comparação TSE por município, dois turnos; selecionar EXCLUSIVAMENTE colunas de primeiro turno na modelagem.",
 "columns":fields,"rows":len(rows),"sample_values":{k:rows[0].get(k) for k in fields} if rows else {},
 "uf_values":sorted({r.get("uf","") for r in rows}),"status":"DIAGNOSTICO_CONCLUIDO",
 "warning":"Não usar votos, comparecimento ou total de seções do segundo turno como feature de previsão."}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("Primeiro turno: colunas inspecionadas:",len(fields),"linhas:",len(rows))
