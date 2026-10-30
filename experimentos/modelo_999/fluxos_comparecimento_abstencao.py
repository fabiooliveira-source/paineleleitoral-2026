#!/usr/bin/env python3
"""Limites identificáveis para fluxos comparecimento <-> abstenção por seção."""
import json,gzip,pathlib,collections
root=pathlib.Path("dados/2026");out=pathlib.Path("experimentos/modelo_999/resultados/fluxos_comparecimento_abstencao.json")
ufs=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO","ZZ"]
total=collections.Counter();per_uf={};examples=[]
for uf in ufs:
 data=json.loads(gzip.decompress((root/f"secoes-{uf}.json.gz").read_bytes()))
 ix={c:i for i,c in enumerate(data["colunas"])};ct=collections.Counter()
 for r in data["linhas"]:
  def v(k):return int(r[ix[k]])
  if r[ix["situacao_dados_1t"]]!="conferido" or r[ix["situacao_dados_2t"]]!="conferido":ct["unverified"]+=1;continue
  n=v("aptos_1t")
  if n<=0 or n!=v("aptos_2t"):ct["electorate_changed"]+=1;continue
  a=v("comparecimento_1t");b=v("comparecimento_2t")
  if a+v("abstencoes_1t")!=n or b+v("abstencoes_2t")!=n:ct["invalid_margins"]+=1;continue
  # X = attended first, abstained second. Y = abstained first, attended second.
  xlo=max(0,a-b);xhi=min(a,n-b)
  ylo=max(0,b-a);yhi=min(n-a,b)
  ct["sections_valid"]+=1
  ct["attended_then_abstained_min"]+=xlo;ct["attended_then_abstained_max"]+=xhi
  ct["abstained_then_attended_min"]+=ylo;ct["abstained_then_attended_max"]+=yhi
  ct["net_change_abstention"]+=a-b
  if a!=b:ct["sections_turnout_changed"]+=1
  if len(examples)<15 and xlo>0:
   examples.append({"uf":uf,"municipio":r[ix["codigo_municipio_tse"]],"zona":r[ix["zona"]],"secao":r[ix["secao"]],"comparecimento_1t":a,"comparecimento_2t":b,"voto_para_abstencao_min":xlo,"voto_para_abstencao_max":xhi,"abstencao_para_voto_min":ylo,"abstencao_para_voto_max":yhi})
 per_uf[uf]=dict(ct);total.update(ct)
assert total["attended_then_abstained_min"]-total["abstained_then_attended_min"]==total["net_change_abstention"],"inconsistent net flow"
report={"scope":"secoes com aptos iguais e ambos turnos conferidos","total":dict(total),"by_uf":per_uf,"examples":examples,
"method":"Limites de Fréchet exatos para tabela binária comparecimento/abstenção. Cada seção pode ter fluxos simultâneos nos dois sentidos.",
"caveats":["Intervalos identificados não são probabilidades nem migração individual comprovada.","Aptos iguais não assegura mesmos indivíduos.","Seções com mudança de aptos foram excluídas."]}
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"total":dict(total)},ensure_ascii=False))
