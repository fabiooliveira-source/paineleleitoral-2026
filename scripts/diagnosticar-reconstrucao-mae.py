import gzip,json,base64,pathlib
root=pathlib.Path("dados/2026")
s=json.load(gzip.open(root/"secoes-AC.json.gz","rt"))
g=json.loads(gzip.decompress(base64.b64decode(json.loads((root/"locais-geograficos-AC-0.json").read_text())["parte"])))
out={"section_columns":s["colunas"],"section_first_rows":s["linhas"][:3],"geo_keys":list(g),"geo_metadata_first":g["metadata"][:3],"geo_turn_first":{k:list(v.items())[:1] for k,v in g["turns"].items()}}
pathlib.Path("dados/2026/diagnostico-esquemas-reconstrucao.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
