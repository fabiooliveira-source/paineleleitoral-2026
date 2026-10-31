"""Historical transfer check. 2020/2022 were used for V4 development; not external certification."""
import json,pathlib,statistics
from avaliar_cobertura_v6_sensibilidade import calc
ROOT=pathlib.Path(__file__).resolve().parent
def run():
 out={"status":"HISTORICAL_TRANSFER_NOT_INDEPENDENT_CERTIFICATION","cases":[]}
 for year in ("2020","2022"):
  p=ROOT/("entradas_pareadas_v4_"+year+".json")
  d=json.loads(p.read_text());target=100*d["target_a"]
  item={"year":year,"scope":d.get("scope"),"target_pct":target,"n":len(d["checkpoints"]),"thresholds":{}}
  for t in (.05,.10,.20,.30,.50):
   err=[calc(f,d["reference"],t)-target for f in d["checkpoints"]]
   item["thresholds"][str(t)]={"mae_pp":statistics.mean(map(abs,err)),"max_abs_pp":max(map(abs,err)),"winner_correct":sum(((calc(f,d["reference"],t)>50)==(target>50)) for f in d["checkpoints"])}
  out["cases"].append(item)
 (ROOT/"resultado_transferencia_v6_historico.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":run()
