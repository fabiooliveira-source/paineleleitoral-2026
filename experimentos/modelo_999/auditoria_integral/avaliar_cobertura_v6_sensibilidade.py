"""Frozen V6 robustness sweep: diagnostic only, not model selection."""
import json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parent
def calc(f,refs,threshold):
 c=f["current"];rows=f["ledger"];o=[c["votes_a"],c["votes_b"]]
 paired=[sum(z["matched_first_"+k] for z in rows) for k in ("a","b")]
 g=[o[i]/paired[i] for i in range(2)]
 common=sum(o)/sum(paired)
 coverage=sum(paired)/sum(v["votes_a"]+v["votes_b"] for v in refs.values())
 alpha=min(1.,coverage/threshold)
 unseen=[0.,0.]
 for z in rows:
  r=refs[z["scope"]]
  for i,k in enumerate(("a","b")):
   m=z["matched_first_"+k]
   rate=z["votes_"+k]/m if m else g[i]
   if not(z["matched_first_a"]+z["matched_first_b"]):rate=alpha*g[i]+(1-alpha)*common
   unseen[i]+=(r["votes_"+k]-m)*rate
 rem=c["electorate_total"]-c["electorate_counted"]
 scale=min(1.,rem/sum(unseen)) if sum(unseen)>0 else 1.
 return 100*(o[0]+scale*unseen[0])/(sum(o)+scale*sum(unseen))
def run():
 result={"status":"EXPLORATORY_PARAMETER_SENSITIVITY_NOT_CERTIFICATION","thresholds":[0.05,0.10,0.20,0.30,0.50],"cities":[]}
 for code in ("87912","17612"):
  d=json.loads((ROOT/"externos2024"/code/"entradas_pareadas_v4_2024.json").read_text());target=100*d["target_a"]
  summary={}
  for threshold in result["thresholds"]:
   pred=[calc(f,d["reference"],threshold) for f in d["checkpoints"]]
   errors=[p-target for p in pred]
   summary[str(threshold)]={"mae_pp":statistics.mean(map(abs,errors)),"max_error_pp":max(map(abs,errors)),"winner_correct":sum((p>50)==(target>50) for p in pred)}
  result["cities"].append({"code":code,"summary":summary})
 (ROOT/"resultado_v6_sensibilidade.json").write_text(json.dumps(result,indent=2)+"\n")
 print(json.dumps(result))
if __name__=="__main__":run()
