import csv,hashlib,json,pathlib,collections
root=pathlib.Path("dados/2026/backtest")
data=root/"json/acervo_2026_2"
manifest=json.loads((data/"manifest.json").read_text())
original=json.loads((data/"integridade.json").read_text())
extracted=json.loads((root/"manifesto_extracao.json").read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
assert digest(data/"manifest.json")==json.loads((data/"validacao.json").read_text())["manifest_sha256"]
assert len(original)==len(manifest["files"])==36
failures=[]
for record in original:
 p=data/"raw"/record["file"]
 if not p.exists(): failures.append("missing "+str(p));continue
 actual=digest(p)
 if actual!=record["expected"] or actual!=record["actual"] or actual!=manifest["files"][record["file"]]:failures.append("hash mismatch "+str(p))
assert not failures,failures
for record in extracted["files"]:
 p=pathlib.Path(record["path"])
 assert p.exists() and digest(p)==record["sha256"],str(p)
csv_info={}
for name in ("observacoes_nacional_uf.csv","observacoes_municipais.csv"):
 p=root/"csv/acervo_2026_2"/name
 with p.open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  count=0;nulls=collections.Counter()
  for row in reader:
   count+=1
   for key,value in row.items():
    if value is None or value=="":nulls[key]+=1
  csv_info[name]={"rows":count,"columns":reader.fieldnames,"empty_cells":dict(nulls)}
assert csv_info["observacoes_nacional_uf.csv"]["rows"]==4892
assert csv_info["observacoes_municipais.csv"]["rows"]==47139
v=json.loads((data/"validacao.json").read_text())
assert all(x==0 for x in v["uf_sum_minus_national"])
report={"status":"PASSOU_AUDITORIA_DE_INTEGRIDADE","files_verified":36,"extracted_files_verified":len(extracted["files"]),"csv":csv_info,"national_final":v["national_final"],"uf_sum_minus_national":v["uf_sum_minus_national"],"limits":["Hashes confirmam consistencia com manifesto do acervo, nao autenticidade independente do TSE.","Backtest preditivo temporal ainda nao executado.","Necessario avaliar vazamento temporal, granularidade, cobertura e erros de previsao."]}
(root/"auditoria_independente.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False,indent=2))
