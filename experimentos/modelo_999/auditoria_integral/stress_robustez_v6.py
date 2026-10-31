"""Deterministic stress test for experimental V6. No fitted parameters, no certification."""
import json,pathlib,random,statistics
from avaliar_cobertura_v6_sensibilidade import calc
ROOT=pathlib.Path(__file__).resolve().parent
SEED=20261031
def perturb(f,mode,rng):
 d=json.loads(json.dumps(f))
 rows=d["ledger"]
 if mode=="shuffle":
  rng.shuffle(rows)
 elif mode=="delay_one_zone":
  zone=rng.choice(rows)
  # Entire zone is absent from observed stream. Matched 1T removed with its 2T votes.
  d["current"]["votes_a"]-=zone["votes_a"];d["current"]["votes_b"]-=zone["votes_b"]
  d["current"]["electorate_counted"]-=zone.get("electorate_counted",0)
  zone["votes_a"]=zone["votes_b"]=zone["matched_first_a"]=zone["matched_first_b"]=0
 elif mode=="delay_largest_zone":
  zone=max(rows,key=lambda z:z["votes_a"]+z["votes_b"])
  d["current"]["votes_a"]-=zone["votes_a"];d["current"]["votes_b"]-=zone["votes_b"]
  d["current"]["electorate_counted"]-=zone.get("electorate_counted",0)
  zone["votes_a"]=zone["votes_b"]=zone["matched_first_a"]=zone["matched_first_b"]=0
 elif mode=="duplicate_rows":
  d["ledger"]=rows+json.loads(json.dumps(rows))
 return d
def run():
 rng=random.Random(SEED)
 out={"seed":SEED,"status":"ROBUSTNESS_STRESS_DIAGNOSTIC_NOT_CERTIFICATION","cases":[]}
 for code in ("87912","17612"):
  d=json.loads((ROOT/"externos2024"/code/"entradas_pareadas_v4_2024.json").read_text())
  cases={}
  for threshold in (.05,.10,.20,.30,.50):
   per={}
   for mode in ("original","shuffle","delay_one_zone","delay_largest_zone"):
    errors=[];fails=0;differences=[]
    for f in d["checkpoints"]:
     original=calc(f,d["reference"],threshold)
     for repeat in range(20 if mode=="delay_one_zone" else 1):
      g=f if mode=="original" else perturb(f,mode,rng)
      try:
       pred=calc(g,d["reference"],threshold)
       errors.append(pred-100*d["target_a"])
       differences.append(pred-original)
      except (ValueError,ZeroDivisionError):fails+=1
    per[mode]={"n":len(errors),"failures":fails,"mae_pp":statistics.mean(map(abs,errors)) if errors else None,"max_abs_error_pp":max(map(abs,errors)) if errors else None,"max_shift_pp":max(map(abs,differences)) if differences else None}
   cases[str(threshold)]=per
  out["cases"].append({"code":code,"thresholds":cases})
 (ROOT/"resultado_stress_robustez_v6.json").write_text(json.dumps(out,indent=2)+"\n")
 print(json.dumps(out))
if __name__=="__main__":run()
