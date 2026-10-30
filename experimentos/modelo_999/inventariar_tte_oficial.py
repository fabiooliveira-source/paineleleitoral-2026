#!/usr/bin/env python3
"""Inventariar TTE 2026 oficial, conferir hash e colunas; não presumir vínculo causal."""
import urllib.request,zipfile,hashlib,io,json,pathlib,csv
url="https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_comparecimento_abstencao_eleitor_tte/perfil_comparecimento_abstencao_eleitor_tte_2026.zip"
out=pathlib.Path("experimentos/modelo_999/resultados/inventario_tte_oficial.json");out.parent.mkdir(parents=True,exist_ok=True)
result={"url":url,"status":"PENDENTE","files":[]}
try:
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
 with urllib.request.urlopen(req,timeout=90) as r: raw=r.read(300_000_000+1)
 if len(raw)>300_000_000:raise ValueError("ZIP excede 300 MB; exige download em streaming")
 result["sha256"]=hashlib.sha256(raw).hexdigest();result["bytes"]=len(raw)
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  bad=z.testzip()
  if bad:raise ValueError("CRC inválido: "+bad)
  for info in z.infolist():
   item={"name":info.filename,"bytes":info.file_size}
   if info.filename.lower().endswith(".csv"):
    with z.open(info) as fp:
     sample=fp.read(65536).decode("utf-8-sig",errors="replace").splitlines()
     if sample:
      item["header"]=sample[0][:2000]
      item["sample_rows"]=sample[1:3]
   result["files"].append(item)
 result["status"]="ZIP_VALIDADO_INVENTARIADO"
except Exception as e:result["error"]=str(e);result["status"]="FALHA_OBTENCAO_OU_VALIDACAO"
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":result["status"],"files":result["files"][:5],"error":result.get("error")},ensure_ascii=False)[:4000])
