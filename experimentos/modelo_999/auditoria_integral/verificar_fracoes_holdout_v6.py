"""Independent exact-rational reimplementation of frozen V6 for new cities.

Uses Fraction independently of existing V4/V6 math modules. No use of
target_a or final votes in projections; those serve evaluation only.
"""
import hashlib
import json
import pathlib
from datetime import datetime
from fractions import Fraction
from preditor_v6_guardado import predict_v6_guarded

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"holdout_v6_2024"
PROTOCOL=ROOT/"protocolo_holdout_v6_2024_v1.json"

def estimate_fraction(frame,refs):
    curr=frame["current"]
    a=curr["votes_a"];b=curr["votes_b"]
    if not a+b:raise ValueError("no observed valid")
    matched=[sum(row["matched_first_"+k] for row in frame["ledger"])
             for k in ("a","b")]
    if min(matched)<=0:raise ValueError("no global denominator")
    total_first=sum(ref["votes_a"]+ref["votes_b"] for ref in refs.values())
    if total_first<=0:raise ValueError("no historic reference")
    coverage=Fraction(sum(matched),total_first)
    alpha=min(Fraction(1),coverage/Fraction(1,5))
    global_rates=(Fraction(a,matched[0]),Fraction(b,matched[1]))
    common=Fraction(a+b,sum(matched))
    unseen=[Fraction(0),Fraction(0)]
    for row in frame["ledger"]:
        scope=str(row["scope"]);ref=refs[scope]
        empty=row["matched_first_a"]+row["matched_first_b"]==0
        for i,k in enumerate(("a","b")):
            m=row["matched_first_"+k]
            local=Fraction(row["votes_"+k],m) if m else global_rates[i]
            if empty:local=alpha*global_rates[i]+(1-alpha)*common
            unseen[i]+=(ref["votes_"+k]-m)*local
    total_unseen=sum(unseen)
    rem=curr["electorate_total"]-curr["electorate_counted"]
    if total_unseen>rem:
        factor=Fraction(rem,1)/total_unseen
        unseen=[x*factor for x in unseen]
    numerator=a+unseen[0];den=a+b+sum(unseen)
    if den==0:raise ValueError("zero share denominator")
    return numerator/den

def run():
    protocol=json.loads(PROTOCOL.read_text())
    manifest=json.loads((DATA/"manifesto_reconstrucao.json").read_text())
    pinned={c["municipality"]:c["sha256"] for c in manifest["cases"]}
    results=[];unexpected=[]
    for case in protocol["external_cases"]:
        code=case["code"];name=case["name"]
        path=DATA/(code+"_checkpoints_1_100.json")
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=pinned[code]:
            raise RuntimeError("reconstructed input hash mismatch for "+name)
        data=json.loads(path.read_text())
        tested=0;closed=0;abstained=0;max_abs_pp=0.
        for point in data["checkpoints"]:
            pct=point["threshold_pct"]
            now=datetime.fromisoformat(point["current"]["timestamp"])
            if not all(datetime.fromisoformat(z["available_at"])<=now for z in data["reference"].values()):
                raise RuntimeError("future first round reference")
            if not all(datetime.fromisoformat(z["available_at"])<=now for z in point["ledger"]):
                raise RuntimeError("future partial votes")
            model=predict_v6_guarded(point["current"],data["reference"],point["ledger"])
            if model["status"]=="CLOSED":
                closed+=1
                assert pct==100
                continue
            if model["estimate_a"] is None:
                abstained+=1
                try:estimate_fraction(point,data["reference"])
                except (ValueError,ZeroDivisionError):pass
                else:unexpected.append(name+" "+str(pct)+"%: unexpected guarded abstention")
                continue
            exact=estimate_fraction(point,data["reference"])
            delta=abs(100*(model["estimate_a"]-float(exact)))
            max_abs_pp=max(max_abs_pp,delta)
            if delta>1e-9:
                unexpected.append(name+" "+str(pct)+"%: exact rational mismatch "+str(delta))
            tested+=1
        results.append({"name":name,"code":code,"checkpoints":100,"rational_matches":tested,
                        "closed":closed,"abstained":abstained,"largest_diff_pp":max_abs_pp,
                        "input_sha256":digest})
        print(json.dumps({"case":name,"rational_matches":tested,
                          "abstained":abstained,"largest_diff_pp":max_abs_pp}),flush=True)
    out={"status":"INDEPENDENT_ARITHMETIC_VERIFICATION_NOT_EXTERNAL_CERTIFICATION",
         "checks":sum(x["rational_matches"] for x in results),
         "cities":results,"exceptions":unexpected,"pass":not unexpected,
         "limitations":["Model mathematical equivalence does not prove future accuracy.",
                        "Source availability remains a retrospective assumption.",
                        "All five cities are manually selected and from 2024."]}
    (DATA/"verificacao_fracoes_v6_holdout.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    if unexpected:raise SystemExit("Exact Fraction independent audit failed")
    print(json.dumps({"rational_audit_passed":True,"cases":len(results),
                      "checks":out["checks"]}),flush=True)
if __name__=="__main__":
    run()
