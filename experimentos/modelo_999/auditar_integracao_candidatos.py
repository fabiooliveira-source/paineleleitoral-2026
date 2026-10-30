#!/usr/bin/env python3
"""Auditoria de cobertura e reconciliação dos candidatos por seção, 28 territórios."""
import json,gzip,base64,pathlib,collections
root=pathlib.Path("dados/2026");dest=pathlib.Path("experimentos/modelo_999/resultados/auditoria_integracao_candidatos.json")
territories=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO","ZZ"]
report={"ufs":{},"total":collections.Counter(),"issues":[]}
for uf in territories:
 sec=json.loads(gzip.decompress((root/f"secoes-{uf}.json.gz").read_bytes()))
 cand=json.loads((root/f"candidatos-secao-{uf}.json").read_text())
 if cand.get("codificacao")=="gzip+base64":cand=json.loads(gzip.decompress(base64.b64decode(cand["dados"])))
 cols=sec["colunas"];idx={k:i for i,k in enumerate(cols)}
 codes=list(cand["numeros"]);names=cand["nomes"];expected_len=3+len(codes)
 candmap={};dups=0;badwidth=0
 for row in cand["linhas"]:
  if len(row)!=expected_len:badwidth+=1;continue
  key=tuple(str(v).zfill(5 if i==0 else 1) for i,v in enumerate(row[:3]))
  if key in candmap:dups+=1
  candmap[key]=row[3:]
 counts=collections.Counter();sum_candidates=collections.Counter();missing_samples=[];discrepancies=[]
 for row in sec["linhas"]:
  counts["sections"]+=1
  key=tuple(str(row[idx[k]]).zfill(5 if k=="codigo_municipio_tse" else 1) for k in ("codigo_municipio_tse","zona","secao"))
  v=candmap.get(key)
  if v is None:
   counts["missing_candidate_section"]+=1
   if len(missing_samples)<3:missing_samples.append(key)
   continue
  counts["matched"]+=1
  if row[idx["situacao_dados_1t"]]!="conferido":
   counts["unverified"]+=1;continue
  actual=sum(int(x) for x in v)
  expected=int(row[idx["nominais_1t"]])-int(row[idx["lula_1t"]])-int(row[idx["flavio_1t"]])
  if actual!=expected:
   counts["candidate_sum_discrepancy"]+=1
   if len(discrepancies)<3:discrepancies.append({"key":key,"actual":actual,"expected":expected})
  else:counts["verified_sum"]+=1
  for code,val in zip(codes,v):sum_candidates[code]+=int(val)
 report["ufs"][uf]={"counts":dict(counts),"candidate_names":names,"candidate_totals":dict(sum_candidates),"duplicate_keys":dups,"bad_width":badwidth,"missing_samples":missing_samples,"discrepancy_samples":discrepancies}
 report["total"].update(counts);report["total"]["duplicate_keys"]+=dups;report["total"]["bad_width"]+=badwidth
report["total"]=dict(report["total"])
report["status"]="AUDITADO" if report["total"].get("candidate_sum_discrepancy",0)==0 and report["total"].get("missing_candidate_section",0)==0 and report["total"]["duplicate_keys"]==0 and report["total"]["bad_width"]==0 else "PENDENCIAS_DE_INTEGRACAO"
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":report["status"],"totals":report["total"],"territories":len(report["ufs"])},ensure_ascii=False))
