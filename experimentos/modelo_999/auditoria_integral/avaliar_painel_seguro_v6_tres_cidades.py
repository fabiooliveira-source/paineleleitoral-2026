"""Retrospective UI safety verification: full estimate coverage, zero false deterministic calls.

Do not conflate mathematically conditional calls with V6 leader projections.
The tested three municipalities were seen during model development.
"""
import json
import pathlib
from preditor_v6_painel_seguro import predict_for_panel
ROOT=pathlib.Path(__file__).resolve().parent
CASES={"13897":"Fortaleza","87912":"Pelotas","17612":"Natal"}

def run():
    report={"status":"RETROSPECTIVE_UI_SAFETY_NOT_EXTERNAL_CERTIFICATION","cases":[],"failures":[]}
    for code,name in CASES.items():
        f=ROOT/"externos2024"/code/"entradas_pareadas_v4_2024.json"
        d=json.loads(f.read_text())
        truth="a" if d["target_a"]>0.5 else "b"
        output=[]
        previous=None
        for frame in d["checkpoints"]:
            p=predict_for_panel(frame["current"],d["reference"],frame["ledger"],previous)
            if p["status"]=="ESTIMATED":previous=frame["current"]
            entry={"pct":frame["threshold_pct"],
                   "prediction_a_pct":None if p["estimate_a"] is None else 100*p["estimate_a"],
                   "provisional_leader":p["provisional_leader"],
                   "provisional_leader_correct":p["provisional_leader"]==truth,
                   "winner_call":p["winner_call"],
                   "winner_call_correct":None if p["winner_call"] is None else p["winner_call"]==truth,
                   "alert":p["territorial_alert"],
                   "max_single_zone_shift_pp":p.get("single_zone_max_shift_pp"),
                   "single_zone_leader_flip":p.get("single_zone_leader_flip"),
                   "v4_v6_disagree":p.get("v4_v6_estimated_leaders_disagree"),
                   "status":p["status"]}
            if p["winner_call"] is not None and p["conditional_winner"]!=p["winner_call"]:
                report["failures"].append(name+":"+str(frame["threshold_pct"])+": unauthorized winner call")
            if p["probability"] is not None:
                report["failures"].append(name+":"+str(frame["threshold_pct"])+": invented probability")
            output.append(entry)
        report["cases"].append({
            "name":name,"code":code,"truth":truth,
            "estimates":sum(x["prediction_a_pct"] is not None for x in output),
            "total":len(output),
            "provisional_wrong_pcts":[x["pct"] for x in output if not x["provisional_leader_correct"]],
            "unsafe_provisional_winner_calls":sum(x["winner_call"] is not None and x["winner_call_correct"] is False for x in output),
            "deterministic_calls":sum(x["winner_call"] is not None for x in output),
            "stability_warnings":sum(x["alert"] not in (None,"NO_SINGLE_ZONE_ALERT") for x in output),
            "first5_provisional_correct":output[0]["provisional_leader_correct"],
            "checkpoints":output})
    good=not report["failures"] and all(c["estimates"]==19 and c["unsafe_provisional_winner_calls"]==0 for c in report["cases"])
    report["policy_gate_passed"]=good
    report["limitations"]=[
        "Mathematical conditional winner calls require no future revisions and physically accurate electorate counts.",
        "The estimate remains provisional and may temporarily imply the wrong leader: checkpoint error lists are preserved.",
        "No published UI integration or production deployment is asserted by this test.",
        "Zone sensitivity trials remove valid votes only, not exact zone turnout.",
        "These three cities are not independent external V6 holdouts."
    ]
    (ROOT/"resultado_painel_seguro_v6.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"policy_gate_passed":good,"failures":report["failures"],
                      "cases":[{k:v for k,v in c.items() if k!="checkpoints"} for c in report["cases"]]},ensure_ascii=False),flush=True)
    if not good:raise SystemExit("Safety integration gate failed")
if __name__=="__main__":run()
