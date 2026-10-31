"""Adversarial integrity gate for fixed V7 on known development cases.

This verifies input safety and chronology, NOT predictive reliability.
It does not tune constants, read targets to improve predictions or
change V7/V6 model files.
"""
import copy,hashlib,json,pathlib,random
from datetime import datetime,timedelta
from preditor_v7_experimental import predict_v7
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"
rng=random.Random(20261031)
def run():
    lock=json.loads(LOCK.read_text())
    checks=0;errors=[];samples=0
    for uf,meta in lock["states"].items():
        path=DATA/(uf+"_checkpoints_1_100.json")
        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta["input_sha256"]:
            raise RuntimeError("input changed "+uf)
        d=json.loads(path.read_text())
        ref=d["reference"]
        for f in d["checkpoints"]:
            if f["threshold_pct"]%5!=0 or f["threshold_pct"]==100:
                continue
            c=f["current"];ledger=f["ledger"]
            p=predict_v7(c,ref,ledger)
            if p["status"]!="ESTIMATED" or p["estimate_a"] is None:
                raise AssertionError("V7 baseline invalid "+uf+" "+str(f["threshold_pct"]))
            samples+=1
            assert p["lower_a"]-1e-12<=p["estimate_a"]<=p["upper_a"]+1e-12
            assert p["probability"] is None
            variants=[]
            x=copy.deepcopy(ledger);rng.shuffle(x)
            variants.append(("SHUFFLE_NOT_EQ",c,ref,x,False))
            x=copy.deepcopy(ledger);x.append(copy.deepcopy(x[0]))
            variants.append(("IDENTICAL_DUPLICATE_NOT_EQ",c,ref,x,False))
            x=copy.deepcopy(ledger);extra=copy.deepcopy(x[0])
            future=(datetime.fromisoformat(c["timestamp"])+timedelta(days=1)).isoformat()
            extra["timestamp"]=future;extra["available_at"]=future
            extra["votes_a"]=123456789;x.append(extra)
            variants.append(("FUTURE_ROW_LEAK",c,ref,x,False))
            x=copy.deepcopy(c);x["votes_a"]+=1
            variants.append(("MISMATCH_NOT_BLOCKED",x,ref,ledger,True))
            x=copy.deepcopy(c);x["available_at"]=future
            variants.append(("FUTURE_AGG_NOT_BLOCKED",x,ref,ledger,True))
            x=copy.deepcopy(ledger)[1:]
            variants.append(("INCOMPLETE_SCOPE_NOT_BLOCKED",c,ref,x,True))
            x=copy.deepcopy(ledger);x[0]["available_at"]=future
            variants.append(("FUTURE_SCOPE_NOT_BLOCKED",c,ref,x,True))
            x=copy.deepcopy(ref);x[sorted(x)[0]]["available_at"]=future
            variants.append(("FUTURE_REFERENCE_NOT_BLOCKED",c,x,ledger,True))
            x=copy.deepcopy(ledger);scope=x[0]["scope"]
            x[0]["matched_first_a"]=ref[scope]["votes_a"]+1
            variants.append(("EXCESSIVE_REFERENCE_NOT_BLOCKED",c,ref,x,True))
            for label,cc,rr,ll,must_abstain in variants:
                z=predict_v7(cc,rr,ll)
                checks+=1
                if must_abstain:
                    if z["status"]!="ABSTAIN" or z["estimate_a"] is not None or not z.get("clear_prior_forecast"):
                        errors.append(uf+":"+str(f["threshold_pct"])+":"+label)
                else:
                    if z["status"]!="ESTIMATED" or z["estimate_a"] is None or abs(z["estimate_a"]-p["estimate_a"])>1e-12:
                        errors.append(uf+":"+str(f["threshold_pct"])+":"+label)
    report={"status":"V7_SOFTWARE_INVARIANTS_PASS" if not errors else "V7_SOFTWARE_INVARIANTS_FAIL",
            "cities":len(lock["states"]),"reference_checkpoints":samples,
            "checked_assertions":checks,"errors":errors,
            "model_parameters_changed":False,"external_predictive_certification":False}
    (DATA/"auditoria_invariantes_v7.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="errors"}),flush=True)
    if errors:
        print(json.dumps({"errors":errors[:30]},ensure_ascii=False),flush=True)
        raise SystemExit("V7 fail-open or determinism regression")
if __name__=="__main__":run()
