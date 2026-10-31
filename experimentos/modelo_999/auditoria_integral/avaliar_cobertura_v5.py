"""Experimental v5 coverage diagnostic. No modification of frozen v4/v4.1."""
import json, pathlib, statistics
ROOT=pathlib.Path(__file__).resolve().parent
def project(frame, reference, neutral=False):
 c=frame["current"]; rows=frame["ledger"]
 obs=[c["votes_a"],c["votes_b"]]
 paired=[sum(z["matched_first_"+k] for z in rows) for k in ("a","b")]
 if not all(paired): raise ValueError("unidentifiable")
 ratios=[obs[k]/paired[k] for k in range(2)]
 common=sum(obs)/sum(paired)
 unseen=[0.,0.]
 for z in rows:
  r=reference[z["scope"]]
  for k,key in enumerate(("a","b")):
   den=z["matched_first_"+key]
   local=z["votes_"+key]/den if den else ratios[k]
   if neutral and z["matched_first_a"]+z["matched_first_b"]==0:
    local=common
   unseen[k]+=(r["votes_"+key]-den)*local
 remaining=c["electorate_total"]-c["electorate_counted"]
 scale=min(1.,remaining/sum(unseen)) if sum(unseen)>0 else 1.
 unseen=[v*scale for v in unseen]
 return 100*(obs[0]+unseen[0])/(sum(obs)+sum(unseen))
def metrics(err):
 return {"mae_pp":sum(map(abs,err))/len(err),"max_abs_error_pp":max(map(abs,err)),"bias_pp":statistics.mean(err)}
def run():
 result={"status":"DEVELOPMENT_ONLY_NOT_EXTERNAL_CERTIFICATION","cases":[]}
 for code in ("87912","17612"):
  d=json.loads((ROOT/"externos2024"/code/"entradas_pareadas_v4_2024.json").read_text())
  target=100*d["target_a"]; v4=[];v5=[];base=[];points=[]
  for f in d["checkpoints"]:
   a=project(f,d["reference"]);b=project(f,d["reference"],True)
   c=f["current"];raw=100*c["votes_a"]/(c["votes_a"]+c["votes_b"])
   v4.append(a-target);v5.append(b-target);base.append(raw-target)
   points.append({"checkpoint_pct":f["threshold_pct"],"v4_pct":a,"v5_pct":b,"baseline_pct":raw,"target_pct":target,"v4_winner_correct":(a>50)==(target>50),"v5_winner_correct":(b>50)==(target>50)})
  result["cases"].append({"code":code,"target_pct":target,"v4":metrics(v4),"v5":metrics(v5),"baseline":metrics(base),"v4_winner_correct":sum(x["v4_winner_correct"] for x in points),"v5_winner_correct":sum(x["v5_winner_correct"] for x in points),"points":points})
 path=ROOT/"resultado_cobertura_v5_desenvolvimento.json"
 path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print(json.dumps({"status":result["status"],"cases":[{k:v for k,v in x.items() if k!="points"} for x in result["cases"]]},ensure_ascii=False))
if __name__=="__main__":run()
