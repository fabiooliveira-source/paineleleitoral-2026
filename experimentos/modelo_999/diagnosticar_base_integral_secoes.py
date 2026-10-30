import gzip,json,pathlib,base64
p=pathlib.Path("dados/2026")
out={}
for name in ["secoes-AC.json.gz","candidatos-secao-AC.json"]:
 f=p/name
 try:
  if name.endswith(".gz"): obj=json.loads(gzip.decompress(f.read_bytes()))
  else:
   obj=json.loads(f.read_text())
   if isinstance(obj,dict) and obj.get("codificacao")=="gzip+base64":obj=json.loads(gzip.decompress(base64.b64decode(obj["dados"])))
  def shape(x):
   if isinstance(x,dict):return {"type":"dict","keys":list(x)[:35],"first":shape(next(iter(x.values()))) if x else None}
   if isinstance(x,list):return {"type":"list","length":len(x),"first":shape(x[0]) if x else None}
   return str(x)[:120]
  out[name]=shape(obj)
 except Exception as e:out[name]={"error":str(e)}
dst=pathlib.Path("experimentos/modelo_999/resultados/schema_secoes_diagnostico.json");dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False))
