"""Experimental V6 adaptive shrinkage; development-only, not certified."""
import json, pathlib, statistics
ROOT=pathlib.Path(__file__).resolve().parent
def forecast(frame,ref,mode):
 c=frame["current"];rows=frame["ledger"];obs=[c["votes_a"],c["votes_b"]]
 matched=[sum(r["matched_first_"+k] for r in rows) for k in ("a","b")]
 if not all(matched):raise ValueError("no global ratios")
 global_rates=[obs[i]/matched[i] for i in range(2)]
 common=sum(obs)/sum(matched)
 unseen=[0.,0.]
 for r in rows:
  rr=ref[r["scope"]]
  for i,k in enumerate(("a","b")):
   m=r["matched_first_"+k];v=r["votes_"+k]
   rate=v/m if m else global_rates[i]
   if mode=="v5" and not(r["matched_first_a"]+r["matched_first_b"]):rate=common
   if mode=="v6" and not(r["matched_first_a"]+r["matched_first_b"]):
    # Shrink global candidate-specific rates toward common rate as
    # total observed paired sample grows; no election outcome used.
    coverage=sum(matched)/sum(z["votes_a"]+z["votes_b"] for z in ref.values())
    alpha=min(1.,max(0.,coverage/0.20))
    rate=alpha*global_rates[i]+(1-alpha)*common
   unseen[i]+=(rr["votes_"+k]-m)*rate
 rem=c["electorate_total"]-c["electorate_counted"]
 scale=min(1.,rem/sum(unseen)) if sum(unseen)>0 else 1.
 return 100*(obs[0]+scale*unseen[0])/(sum(obs)+scale*sum(unseen))
def run():
 output={"status":"DEVELOPMENT_ONLY","rule":"V6: alpha=clip(paired_1T_votes / total_1T_valid_votes / 0.20,0,1); rate=alpha*global_candidate_rate+(1-alpha)*common_rate on zones with zero paired sample.","cities":[]}
 for city in ("87912","17612"):
  d=json.loads((ROOT/"externos2024"/city/"entradas_pareadas_v4_2024.json").read_text());target=100*d["target_a"]
  pts=[]
  for f in d["checkpoints"]:
   x={m:forecast(f,d["reference"],m) for m in ("v4","v5","v6")}
   x["pct"]=f["threshold_pct"];pts.append(x)
  metrics={}
  for mode in ("v4","v5","v6"):
   errors=[p[mode]-target for p in pts]
   metrics[mode]={"mae_pp":statistics.mean(map(abs,errors)),"max_abs_error_pp":max(map(abs,errors)),"bias_pp":statistics.mean(errors),"winner_correct":sum((p[mode]>50)==(target>50) for p in pts)}
  output["cities"].append({"code":city,"target":target,"metrics":metrics,"points":pts})
 (ROOT/"resultado_cobertura_v6_desenvolvimento.json").write_text(json.dumps(output,indent=2)+"\n")
 print(json.dumps({"status":output["status"],"cities":[{"code":c["code"],"metrics":c["metrics"]} for c in output["cities"]]}))
if __name__=="__main__":run()
