#!/usr/bin/env python3
"""Diagnóstico das diferenças de aptos, sem presumir alteração real de eleitorado."""
import collections,gzip,json,pathlib
root=pathlib.Path("dados/2026");out=pathlib.Path("experimentos/modelo_999/resultados/investigacao_aptos_divergentes.json")
ufs=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO","ZZ"]
total=collections.Counter();per_uf={};examples=[];by_abs_delta=collections.Counter()
for uf in ufs:
 data=json.loads(gzip.decompress((root/f"secoes-{uf}.json.gz").read_bytes()))
 ix={k:i for i,k in enumerate(data["colunas"])};ct=collections.Counter()
 for r in data["linhas"]:
  def v(k):return int(r[ix[k]])
  if r[ix["situacao_dados_1t"]]!="conferido" or r[ix["situacao_dados_2t"]]!="conferido":ct["unverified"]+=1;continue
  a=v("aptos_1t");b=v("aptos_2t");d=b-a
  ct["verified"]+=1
  if d==0:ct["same_aptos"]+=1;continue
  ct["changed_aptos"]+=1;ct["delta_aptos_sum"]+=d;ct["delta_aptos_abs_sum"]+=abs(d)
  ct["delta_positive" if d>0 else "delta_negative"]+=1
  ct["delta_positive_sum" if d>0 else "delta_negative_sum"]+=d
  if abs(d)<=1:ct["abs_delta_le_1"]+=1
  if abs(d)<=5:ct["abs_delta_le_5"]+=1
  if abs(d)<=10:ct["abs_delta_le_10"]+=1
  if abs(d)>50:ct["abs_delta_gt_50"]+=1
  if abs(d)>100:ct["abs_delta_gt_100"]+=1
  if a==0 or b==0:ct["zero_aptos_either_round"]+=1
  if r[ix["local_votacao_1t"]]!=r[ix["local_votacao_2t"]]:ct["local_changed"]+=1
  for turn in ("1t","2t"):
   if v("comparecimento_"+turn)+v("abstencoes_"+turn)!=v("aptos_"+turn):ct["invalid_turnout_identity_"+turn]+=1
   if v("nominais_"+turn)+v("brancos_"+turn)+v("nulos_"+turn)!=v("comparecimento_"+turn):ct["invalid_vote_identity_"+turn]+=1
  by_abs_delta[str(min(abs(d),1001))]+=1
  if len(examples)<60 or abs(d)>abs(examples[-1]["delta_aptos"]):
   entry={"uf":uf,"municipio":r[ix["codigo_municipio_tse"]],"zona":r[ix["zona"]],"secao":r[ix["secao"]],"aptos_1t":a,"aptos_2t":b,"delta_aptos":d,"local_1t":r[ix["local_votacao_1t"]],"local_2t":r[ix["local_votacao_2t"]],"situacao_1t":r[ix["situacao_dados_1t"]],"situacao_2t":r[ix["situacao_dados_2t"]]}
   examples.append(entry);examples.sort(key=lambda x:abs(x["delta_aptos"]),reverse=True);examples=examples[:60]
 per_uf[uf]=dict(ct);total.update(ct)
report={"total":dict(total),"by_uf":per_uf,"top_60_absolute_differences":examples,"absolute_delta_histogram":dict(sorted(by_abs_delta.items(),key=lambda kv:int(kv[0]))),
"interpretation":["Mudança de aptos pode resultar de alterações cadastrais, remanejamento de seções ou integração de bases; nenhuma causa foi comprovada.","Não excluir automaticamente: auditar margens e modelar entradas/saídas do universo sem atribuir voto individual.","Uma diferença numérica de aptos não prova que os eleitores individuais mudaram."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"total":dict(total),"top_5":examples[:5]},ensure_ascii=False))
