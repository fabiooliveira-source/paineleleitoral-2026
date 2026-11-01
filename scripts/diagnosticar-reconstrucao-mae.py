import gzip,json,base64,pathlib
root=pathlib.Path("dados/2026")
def shape(x):
 if isinstance(x,dict):return {k:shape(v) for k,v in list(x.items())[:25]}
 if isinstance(x,list):return {"length":len(x),"sample":shape(x[0]) if x else None}
 return str(x)[:130]
out={}
for name in ["secoes-AC.json.gz","locais-geograficos-AC-0.json","comportamento_rateios_pacote.json"]:
 p=root/name
 if name.endswith(".gz"): obj=json.load(gzip.open(p,"rt"))
 else:
  obj=json.loads(p.read_text())
  if "parte" in obj:
   try:obj=json.loads(gzip.decompress(base64.b64decode(obj["parte"])))
   except Exception as e:out[name+"_decode_error"]=str(e)
  elif "dados" in obj:obj=json.loads(gzip.decompress(base64.b64decode(obj["dados"])))
 out[name]=shape(obj)
pathlib.Path("dados/2026/diagnostico-esquemas-reconstrucao.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
