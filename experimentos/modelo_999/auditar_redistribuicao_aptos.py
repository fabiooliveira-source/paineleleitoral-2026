#!/usr/bin/env python3
"""Verifica indícios de redistribuição de aptos: pareamento intra município e zona.
Não atribui automaticamente ao voto em trânsito."""
import json,gzip,pathlib,collections
root=pathlib.Path("dados/2026");dest=pathlib.Path("experimentos/modelo_999/resultados/redistribuicao_aptos_territorial.json")
ufs=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO","ZZ"]
levels={"zona":collections.defaultdict(int),"municipio":collections.defaultdict(int),"uf":collections.defaultdict(int)}
counts=collections.Counter();local_changes=[]
for uf in ufs:
 data=json.loads(gzip.decompress((root/f"secoes-{uf}.json.gz").read_bytes()));idx={x:i for i,x in enumerate(data["colunas"])}
 for r in data["linhas"]:
  if r[idx["situacao_dados_1t"]]!="conferido" or r[idx["situacao_dados_2t"]]!="conferido":continue
  delta=int(r[idx["aptos_2t"]])-int(r[idx["aptos_1t"]])
  if not delta:continue
  mun=str(r[idx["codigo_municipio_tse"]]);zona=str(r[idx["zona"]])
  levels["zona"][(uf,mun,zona)]+=delta;levels["municipio"][(uf,mun)]+=delta;levels["uf"][uf]+=delta
  counts["sections_changed"]+=1
  if r[idx["local_votacao_1t"]]!=r[idx["local_votacao_2t"]]:
   counts["local_changed"]+=1
   if len(local_changes)<30:local_changes.append({"uf":uf,"municipio":mun,"zona":zona,"secao":r[idx["secao"]],"delta":delta})
summary={}
for level,groups in levels.items():
 positive=sum(max(0,x) for x in groups.values());negative=sum(max(0,-x) for x in groups.values())
 summary[level]={"groups":len(groups),"net":sum(groups.values()),"positive":positive,"negative":negative,
  "balanced_groups":sum(x==0 for x in groups.values()),"unbalanced_groups":sum(x!=0 for x in groups.values()),
  "gross_unmatched":positive+negative,
  "top_unbalanced":[{"key":list(k) if isinstance(k,tuple) else k,"delta":v} for k,v in sorted(groups.items(),key=lambda kv:abs(kv[1]),reverse=True)[:30] if v]}
report={"summary":summary,"counts":dict(counts),"local_change_samples":local_changes,
"interpretation":["Compensação na mesma zona é compatível com redistribuição local, mas não identifica causa.",
"Compensação apenas entre municípios/UFs é compatível com trânsito ou outros processos, sem prova.",
"Para confirmar voto em trânsito são necessários registros oficiais de seções especiais e habilitações."]}
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"summary":summary},ensure_ascii=False)[:4000])
