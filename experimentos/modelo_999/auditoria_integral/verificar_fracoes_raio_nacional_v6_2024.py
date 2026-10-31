"""Exact fractions independent V6 arithmetic cross-check for expanded frozen data.

No modification of predictive parameters or metric thresholds permitted.
"""
import hashlib
import json
import pathlib
from fractions import Fraction
from verificar_fracoes_holdout_v6 import estimate_fraction
from preditor_v6_guardado import predict_v6_guarded

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"

def run():
    lock=json.loads(LOCK.read_text())
    results=[]
    for uf,meta in lock["states"].items():
        file=DATA/(uf+"_checkpoints_1_100.json")
        digest=hashlib.sha256(file.read_bytes()).hexdigest()
        if digest!=meta["input_sha256"]:raise RuntimeError("DATA HASH MISMATCH "+uf)
        d=json.loads(file.read_text())
        comparisons=0;closed=0;abstentions=0;max_error=0.
        for x in d["checkpoints"]:
            p=predict_v6_guardado if False else predict_v6_guarded(x["current"],d["reference"],x["ledger"])
            if p["status"]=="CLOSED":
                closed+=1
                if x["threshold_pct"]!=100 or abs(p["estimate_a"]-d["target_a"])>1e-12:
                    raise RuntimeError("invalid complete point "+uf)
                continue
            if p["estimate_a"] is None:
                abstentions+=1
                # Do not drop abstentions from summary or assert model passed.
                continue
            exact=estimate_fraction(x,d["reference"])
            difference=abs(100*(p["estimate_a"]-float(exact)))
            max_error=max(max_error,difference)
            if difference>1e-9:
                raise RuntimeError("V6 exact rational mismatch "+uf+" point="+str(x["threshold_pct"]))
            comparisons+=1
        row={"uf":uf,"city":meta["city"],"independent_rational_checks":comparisons,
             "closed":closed,"abstentions":abstentions,"max_diff_pp":max_error}
        results.append(row)
        print(json.dumps(row,ensure_ascii=False),flush=True)
    output={"status":"ARITHMETIC_VERIFICATION_ONLY","passed":True,
            "states":len(results),"rational_matches":sum(x["independent_rational_checks"] for x in results),
            "cases":results,"predictive_certification":False,
            "notes":["Fractions compare only arithmetic, not model accuracy.",
                     "2024 source availability is a retrospective assumption."]}
    (DATA/"resultado_fracoes_raio_nacional_v6.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"states":len(results),"checks":output["rational_matches"],"status":output["status"]}),flush=True)

if __name__=="__main__":run()
