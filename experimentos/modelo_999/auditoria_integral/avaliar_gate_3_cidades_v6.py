"""Retrospective three-city V6 benchmark under original V4.1 acceptance criteria.

Passing this previously examined benchmark is NOT independent validation.
The criteria were originally registered for V4.1 (pre-V6), but V6 was devised
while the 2024 data/outcomes were already known.
"""
import hashlib
import json
import pathlib
from avaliar_externos_v41_2024 import criteria_for, quantile
from preditor_v6_guardado import predict_v6_guarded

ROOT = pathlib.Path(__file__).resolve().parent
CASES = {"13897":"Fortaleza","87912":"Pelotas","17612":"Natal"}

def run():
    cases=[]
    for code,name in CASES.items():
        path=ROOT/"externos2024"/code/"entradas_pareadas_v4_2024.json"
        d=json.loads(path.read_text())
        target=d["target_a"]
        points=[]
        previous=None
        for frame in d["checkpoints"]:
            curr=frame["current"]
            p=predict_v6_guarded(curr,d["reference"],frame["ledger"],previous)
            estimate=p["estimate_a"]
            observed=curr["votes_a"]/(curr["votes_a"]+curr["votes_b"])
            winner="a" if target>0.5 else "b"
            call=p.get("conditional_winner")
            points.append({
                "threshold_pct":frame["threshold_pct"],
                "estimate_a_pct":100*estimate if estimate is not None else None,
                "observed_baseline_a_pct":100*observed,
                "error_pp":100*(estimate-target) if estimate is not None else None,
                "baseline_error_pp":100*(observed-target),
                "winner_correct":estimate is not None and estimate!=0.5 and (estimate>0.5)==(target>0.5),
                "conditional_call_correct":None if call is None else call==winner,
                "bounds_cover_target":p["lower_a"] is not None and p["lower_a"]-1e-12<=target<=p["upper_a"]+1e-12,
                "status":p["status"],
                "reason":p["reason"],
                "zero_sample_first_vote_share":p.get("zero_sample_first_vote_share"),
                "coverage_first_valid":p.get("coverage_first_valid"),
                "model_vs_v4_pp":100*(estimate-p["comparison_v4_estimate_a"]) if estimate is not None else None,
            })
            if p["status"] in ("ESTIMATED","CLOSED"):
                previous=curr
        errors=[x["error_pp"] for x in points if x["error_pp"] is not None]
        base=[x["baseline_error_pp"] for x in points]
        metrics={
            "mae_pp":sum(map(abs,errors))/len(errors),
            "p95_abs_error_pp":quantile([abs(x) for x in errors]),
            "max_abs_error_pp":max(map(abs,errors)),
            "bias_pp":sum(errors)/len(errors),
        } if errors else None
        baseline={
            "mae_pp":sum(map(abs,base))/len(base),
            "p95_abs_error_pp":quantile([abs(x) for x in base]),
            "max_abs_error_pp":max(map(abs,base)),
        }
        criteria=criteria_for(metrics,baseline,points,len(errors),95)
        # Audited external V4.1 had 95 fault checks per municipality, but
        # that historical number must NOT be asserted as a new V6 test run.
        # The 95 here is an explicit compatibility input to the old criteria.
        # An independent V6 adversarial CI is separately required below.
        cases.append({
            "name":name,"municipality":code,"target_a_pct":100*target,
            "input_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "criteria":criteria,
            "accepted_existing_benchmark":all(criteria.values()),
            "metrics_v6":metrics,
            "observed_baseline":baseline,
            "wrong_winner_checkpoints":[x["threshold_pct"] for x in points if not x["winner_correct"]],
            "first_checkpoint":points[0],
            "checkpoints":points,
        })
    accepted=sum(x["accepted_existing_benchmark"] for x in cases)
    output={
        "model":"V6 original fixed 20%, temporal/territorial guard V4.1",
        "benchmark":"Original 2024 external V4.1 criteria reused for V6 retrospective development evaluation",
        "status":"RETROSPECTIVE_DEVELOPMENT_BENCHMARK_ONLY",
        "protocol":"protocolo_externo_v41_2024.json",
        "protocol_not_independent_for_v6":True,
        "new_external_holdout_count":0,
        "accepted_cases":accepted,
        "evaluated_cases":len(cases),
        "all_three_existing_criteria_met":accepted==3,
        "scientific_external_certification":False,
        "notes":[
          "The V6 was modified after its developers saw these cities, making this a development benchmark.",
          "The 95 original V4.1 fault checks are reused only as a fixed benchmark criterion; new V6 checks are independently in the adversarial workflow.",
          "An actual formal external certification requires holdout cities and authentic data availability timelines.",
          "Every municipal checkpoint is correlated with checkpoints from the same election.",
          "A winner estimate at a checkpoint is NOT a probabilistic election call."
        ],
        "cases":cases
    }
    (ROOT/"resultado_gate_3_cidades_v6.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "status":output["status"],"passed":accepted,"total":len(cases),
        "cases":[{"name":x["name"],"accepted":x["accepted_existing_benchmark"],
                  "v6":x["metrics_v6"],"baseline":x["observed_baseline"],
                  "failed":[k for k,v in x["criteria"].items() if not v],
                  "wrong_winner_checkpoints":x["wrong_winner_checkpoints"],
                  "first_checkpoint_estimate":x["first_checkpoint"]["estimate_a_pct"]}
                 for x in cases]
    },ensure_ascii=False),flush=True)
    if accepted!=3:
        raise SystemExit("V6 retrospective three-city gate NOT passed")
if __name__=="__main__":
    run()
