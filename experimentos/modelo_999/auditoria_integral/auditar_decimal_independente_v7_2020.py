"""Independent high-precision Decimal replay for V7: 18 frozen 2020 cases.

Checks implementation equivalence on every checkpoint. This tests
arithmetic, NOT predictive reliability nor independent THIRD-PARTY review.
"""
import decimal
import hashlib
import json
import pathlib
from decimal import Decimal as D
from preditor_v7_experimental import predict_v7

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_temporal_v7_2020"
LOCK=ROOT/"congelamento_v7_holdout_temporal_2020.json"
PROTOCOL=ROOT/"protocolo_v7_holdout_temporal_2020_v1.json"
decimal.getcontext().prec=48
HALF=D("0.5")
ONE=D(1)
THOUSAND=D(1000)
CLAMP=D(4).ln()

def odds(a,b):
    return ((D(a)+HALF)/(D(b)+HALF)).ln()

def logistic(z):
    if z>=0:
        return ONE/(ONE+(-z).exp())
    e=z.exp()
    return e/(ONE+e)

def independently_calculate(frame,reference):
    c=frame["current"]
    a=c["votes_a"];b=c["votes_b"]
    matched_a=sum(r["matched_first_a"] for r in frame["ledger"])
    matched_b=sum(r["matched_first_b"] for r in frame["ledger"])
    if min(matched_a,matched_b)<=0:raise ValueError("unidentified global support")
    swing=odds(a,b)-odds(matched_a,matched_b)
    convert=D(a+b)/D(matched_a+matched_b)
    by_scope={str(r["scope"]):r for r in frame["ledger"]}
    unseen_a=D(0)
    unseen_b=D(0)
    for scope in sorted(reference):
        row=by_scope[scope]
        ref=reference[scope]
        left_a=ref["votes_a"]-row["matched_first_a"]
        left_b=ref["votes_b"]-row["matched_first_b"]
        left=left_a+left_b
        if left==0:continue
        valid=row["votes_a"]+row["votes_b"]
        ma=row["matched_first_a"];mb=row["matched_first_b"]
        if ma==0 or mb==0 or valid==0:
            local=swing
            weight=D(0)
        else:
            local=odds(row["votes_a"],row["votes_b"])-odds(ma,mb)
            weight=D(valid)/(D(valid)+THOUSAND)
        shift=max(-CLAMP,min(CLAMP,local-swing))
        posterior=swing+weight*shift
        share=logistic(odds(left_a,left_b)+posterior)
        expected=D(left)*convert
        unseen_a+=expected*share
        unseen_b+=expected*(ONE-share)
    rem=D(c["electorate_total"]-c["electorate_counted"])
    if unseen_a+unseen_b>rem and unseen_a+unseen_b>0:
        scale=rem/(unseen_a+unseen_b)
        unseen_a*=scale;unseen_b*=scale
    denominator=D(a+b)+unseen_a+unseen_b
    if not denominator:return None
    return (D(a)+unseen_a)/denominator

def run():
    protocol=json.loads(PROTOCOL.read_text())
    lock=json.loads(LOCK.read_text())
    assert len(lock["states"])==18 and len(protocol["cases"])==18
    by_uf={z["uf"]:z for z in protocol["cases"]}
    findings=[]
    failed=[]
    for uf,rec in lock["states"].items():
        file=DATA/(uf+"_checkpoints_1_100.json")
        if hashlib.sha256(file.read_bytes()).hexdigest()!=rec["input_sha256"]:
            raise RuntimeError("input hash mismatch "+uf)
        data=json.loads(file.read_text())
        assert data["config"]["name"]==by_uf[uf]["city"]
        compared=0;closed=0;abstentions=0;max_delta=D(0)
        for f in data["checkpoints"]:
            p=predict_v7(f["current"],data["reference"],f["ledger"])
            if p["status"]=="CLOSED":
                closed+=1
                if p["estimate_a"] is None or abs(p["estimate_a"]-data["target_a"])>1e-12:
                    failed.append(f"{uf}: CLOSED inconsistency at {f['threshold_pct']}")
                continue
            if p["estimate_a"] is None:
                abstentions+=1
                try:independently_calculate(f,data["reference"])
                except (ValueError,ZeroDivisionError):pass
                else:failed.append(f"{uf}: guarded abstention despite identified denominator {f['threshold_pct']}")
                continue
            exact=independently_calculate(f,data["reference"])
            delta=abs(D(str(p["estimate_a"]))-exact)*100
            if delta>max_delta:max_delta=delta
            if delta>D("0.000000001"):
                failed.append(f"{uf}: arithmetic drift {f['threshold_pct']} delta_pp={delta}")
            compared+=1
        findings.append({"uf":uf,"city":rec["city"],"compared":compared,
                         "closed":closed,"abstained":abstentions,
                         "max_abs_delta_pp":str(max_delta)})
        print(json.dumps(findings[-1],ensure_ascii=False),flush=True)
    report={"status":"ARITHMETIC_AUDIT_PASS_NOT_PREDICTIVE_CERTIFICATION" if not failed else "ARITHMETIC_AUDIT_FAIL",
            "implementation":"High-precision Decimal 48-digit replay separate from V7 float math",
            "cases":len(findings),
            "compared":sum(z["compared"] for z in findings),
            "closed":sum(z["closed"] for z in findings),
            "abstentions":sum(z["abstained"] for z in findings),
            "failure_count":len(failed),
            "failures":failed,
            "detail":findings,
            "mathematical_equivalence_not_independent_external_review":True}
    (DATA/"resultado_auditoria_decimal_v7_2020.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("detail","failures")},ensure_ascii=False),flush=True)
    if failed:raise SystemExit("Independent Decimal arithmetic V7 discrepancies")
if __name__=="__main__":run()
