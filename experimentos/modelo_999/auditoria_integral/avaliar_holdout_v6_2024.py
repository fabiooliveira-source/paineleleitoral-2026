"""Frozen V6 evaluation on five new municipalities, 100 reconstructed checkpoints each.

Primary gate uses ONLY preregistered 5..95 step 5; the 1..100 grid
is a SECONDARY diagnostic. No model selection or parameter tuning.
"""
import hashlib
import json
import math
import pathlib
import statistics
from collections import Counter
from datetime import datetime
from preditor_v4_guardado import predict_guarded
from preditor_v6_guardado import predict_v6_guarded
from avaliar_externos_v41_2024 import quantile

ROOT=pathlib.Path(__file__).resolve().parent
PROTOCOL=ROOT/"protocolo_holdout_v6_2024_v1.json"
DATA=ROOT/"holdout_v6_2024"
PRIMARY=set(range(5,100,5))
SEGMENTS={
    "early_1_4":range(1,5),
    "primary_5_25":range(5,26),
    "mid_30_70":range(30,71),
    "late_75_95":range(75,96),
    "near_complete_97_99":range(97,100),
    "full_100":[100]
}

def numbers(points,key):
    available=[p for p in points if p[key] is not None]
    errors=[p[key] for p in available]
    if not errors:
        return {"n":0,"total":len(points),"abstentions":len(points),"mae_pp":None,
                "max_abs_error_pp":None,"p95_abs_error_pp":None,"bias_pp":None}
    abs_err=[abs(x) for x in errors]
    return {"n":len(errors),"total":len(points),"abstentions":len(points)-len(errors),
            "mae_pp":statistics.mean(abs_err),"max_abs_error_pp":max(abs_err),
            "p95_abs_error_pp":quantile(abs_err),"bias_pp":statistics.mean(errors)}

def evaluate(name,code,protocol):
    file=DATA/(code+"_checkpoints_1_100.json")
    d=json.loads(file.read_text())
    expected=next(x for x in protocol["external_cases"] if x["code"]==code)
    assert d["config"]==expected,"case config changed"
    assert d["availability_is_assumed"] and not d["official_public_snapshot_authenticated"]
    frames=d["checkpoints"]
    assert [x["threshold_pct"] for x in frames]==list(range(1,101))
    ref=d["reference"]
    target=d["target_a"]
    assert 0<target<1
    truth="a" if target>.5 else "b"
    latest=None
    previous_sections=-1
    previous_time=None
    points=[]
    for frame in frames:
        pct=frame["threshold_pct"]
        curr=frame["current"]
        now=datetime.fromisoformat(curr["timestamp"])
        section_count=frame["sections_counted"]
        assert section_count>=previous_sections and frame["sections_fraction"]>=pct/100-1e-12
        assert previous_time is None or now>=previous_time
        assert all(datetime.fromisoformat(x["available_at"])<=now for x in ref.values())
        assert all(datetime.fromisoformat(x["available_at"])<=now and datetime.fromisoformat(x["timestamp"])<=now for x in frame["ledger"])
        assert len(frame["ledger"])==len(ref)
        assert sum(r["votes_a"] for r in frame["ledger"])==curr["votes_a"]
        assert sum(r["votes_b"] for r in frame["ledger"])==curr["votes_b"]
        assert curr["votes_a"]+curr["votes_b"]<=curr["electorate_counted"]<=curr["electorate_total"]
        p=predict_v6_guarded(curr,ref,frame["ledger"],previous=latest)
        v4=predict_guarded(curr,ref,frame["ledger"],previous=latest)
        if pct==100:
            assert p["status"]=="CLOSED"
            assert abs(p["estimate_a"]-target)<1e-12,"terminal projection mismatch"
        observed=curr["votes_a"]/(curr["votes_a"]+curr["votes_b"]) if curr["votes_a"]+curr["votes_b"] else None
        v6=p.get("estimate_a")
        base=v4.get("estimate_a")
        conditional=p.get("conditional_winner")
        points.append({
            "pct":pct,"time":curr["timestamp"],
            "sections_counted":section_count,"sections_total":frame["sections_total"],
            "sections_fraction":frame["sections_fraction"],
            "electorate_fraction":curr["electorate_counted"]/curr["electorate_total"],
            "v6_status":p["status"],"v6_reason":p.get("reason"),
            "v6_estimate_pct":None if v6 is None else 100*v6,
            "v4_estimate_pct":None if base is None else 100*base,
            "raw_observed_pct":None if observed is None else 100*observed,
            "v6_error_pp":None if v6 is None else 100*(v6-target),
            "v4_error_pp":None if base is None else 100*(base-target),
            "observed_error_pp":None if observed is None else 100*(observed-target),
            "v6_winner_correct":None if v6 is None or v6==.5 else ("a" if v6>.5 else "b")==truth,
            "v4_winner_correct":None if base is None or base==.5 else ("a" if base>.5 else "b")==truth,
            "conditional_winner":conditional,
            "conditional_call_correct":None if conditional is None else conditional==truth,
            "physical_bounds_cover_truth":p["lower_a"] is not None and
                p["lower_a"]-1e-12<=target<=p["upper_a"]+1e-12,
            "zero_sample_first_vote_share":p.get("zero_sample_first_vote_share"),
            "first_round_coverage":p.get("coverage_first_valid"),
            "prior_sample_magnitude":sum(r["matched_first_a"]+r["matched_first_b"] for r in frame["ledger"]),
        })
        latest=curr if p["status"] in ("ESTIMATED","CLOSED") else latest
        previous_sections=section_count
        previous_time=now
    assert len(points)==100
    primary=[x for x in points if x["pct"] in PRIMARY]
    assert len(primary)==19
    m6=numbers(primary,"v6_error_pp")
    m4=numbers(primary,"v4_error_pp")
    observed=numbers(primary,"observed_error_pp")
    criteria=protocol["primary_case_criteria"]
    gate={
        "all_19_estimates":m6["n"]==19,
        "mae_not_worse_than_observed_share":m6["mae_pp"] is not None and m6["mae_pp"]<=observed["mae_pp"]+1e-12,
        "maximum_not_worse_than_observed_share":m6["max_abs_error_pp"] is not None and m6["max_abs_error_pp"]<=observed["max_abs_error_pp"]+1e-12,
        "mae_at_most_pp":m6["mae_pp"] is not None and m6["mae_pp"]<=criteria["mae_at_most_pp"],
        "p95_abs_at_most_pp":m6["p95_abs_error_pp"] is not None and m6["p95_abs_error_pp"]<=criteria["p95_abs_at_most_pp"],
        "max_abs_at_most_pp":m6["max_abs_error_pp"] is not None and m6["max_abs_error_pp"]<=criteria["max_abs_at_most_pp"],
        "winner_correct_at_5pct":primary[0]["v6_winner_correct"] is True,
        "no_wrong_deterministic_winner_call":all(x["conditional_call_correct"] is not False for x in primary),
        "conditional_physical_bounds_cover_truth":all(x["physical_bounds_cover_truth"] for x in primary),
        "coverage_uncertainty_reported":all(x["first_round_coverage"] is not None for x in primary),
        "source_integrity_passed":True,
    }
    assert set(gate)==set(criteria),"gate criteria drift"
    broken=[k for k,v in gate.items() if not v]
    wrong6=[x["pct"] for x in primary if x["v6_winner_correct"] is False]
    wrong4=[x["pct"] for x in primary if x["v4_winner_correct"] is False]
    wrongstreak=0;streak=0
    for p in primary:
        streak=streak+1 if p["v6_winner_correct"] is False else 0
        wrongstreak=max(wrongstreak,streak)
    breakdown={segment:{
        "v6":numbers([p for p in points if p["pct"] in values],"v6_error_pp"),
        "v4":numbers([p for p in points if p["pct"] in values],"v4_error_pp"),
        "observed":numbers([p for p in points if p["pct"] in values],"observed_error_pp")
        } for segment,values in SEGMENTS.items()}
    return {
        "name":name,"municipality":code,"uf":d["config"]["uf"],
        "file_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
        "sections_total":frames[0]["sections_total"],
        "zones":len(ref),"target_a_pct":100*target,
        "truth_winner":truth,"final_votes":d["final_votes"],
        "primary_n":len(primary),"primary_metrics_v6":m6,
        "primary_metrics_v4":m4,"primary_metrics_raw_observed":observed,
        "gate":gate,"gate_passed":not broken,"failed_criteria":broken,
        "winner_wrong_checkpoints_v6":wrong6,
        "winner_wrong_checkpoints_v4":wrong4,
        "longest_wrong_v6_streak_at_5pct_steps":wrongstreak,
        "v6_first5pct_a":primary[0]["v6_estimate_pct"],
        "v6_first5pct_correct":primary[0]["v6_winner_correct"],
        "first_percent_with_estimate":next((p["pct"] for p in points if p["v6_estimate_pct"] is not None),None),
        "full_grid_count":len(points),
        "secondary_segments":breakdown,
        "checkpoints":points,
    }

def run():
    protocol=json.loads(PROTOCOL.read_text())
    manifest=json.loads((DATA/"manifesto_reconstrucao.json").read_text())
    assert manifest["status"]=="FIVE_CASES_PREPARED_WITH_ASSUMED_AVAILABILITY"
    assert len(protocol["external_cases"])==5
    assert len(manifest["cases"])==5
    out={"status":"FROZEN_HISTORICAL_EXTERNAL_HOLDOUT_WITH_RETROSPECTIVE_AVAILABILITY",
         "protocol_version":protocol["protocol_version"],
         "protocol_file_sha256":hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
         "external_validation_is_prospective":False,
         "available_at_authenticated_public_snapshots":False,
         "criteria_preregistered_prior_to_new_case_prediction":True,
         "initial_frozen_v6_20pct":True,
         "independent_review":False,
         "cases":[]}
    for entry in protocol["external_cases"]:
        c=evaluate(entry["name"],entry["code"],protocol)
        out["cases"].append(c)
        print(json.dumps({
            "status":"CASE_SCORED","case":entry["name"],"code":entry["code"],
            "gate_passed":c["gate_passed"],"failed":c["failed_criteria"],
            "v6":c["primary_metrics_v6"],"v4":c["primary_metrics_v4"],
            "baseline":c["primary_metrics_raw_observed"],
            "v6_wrong_winner_pct":c["winner_wrong_checkpoints_v6"]
        },ensure_ascii=False),flush=True)
    passed=sum(c["gate_passed"] for c in out["cases"])
    out["evaluated_cases"]=len(out["cases"])
    out["passed_cases"]=passed
    out["full_original_gate_passed"]=passed==5
    out["integral_certification"]=False
    out["decision"]="HISTORICAL_HOLDOUT_GATE_PASSED_NOT_CERTIFIED" if passed==5 else "HISTORICAL_HOLDOUT_GATE_FAILED_NOT_CERTIFIED"
    out["limitations"]=[
        "Outcomes publicly knowable and cities manually selected; not blinded prospective.",
        "Model, protocol and code produced by same team; no independent external audit.",
        "Section first-totalization clocks reconstructed from final published section data; not authenticated public incremental snapshots.",
        "Repeated checkpoints within one election are dependent, no 500-election sample claim.",
        "All municipalities are from only two states and one 2024 election cycle.",
        "The predictions do not yield calibrated winner probabilities."]
    dest=DATA/"resultado_holdout_v6_2024.json"
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"decision":out["decision"],"passed":passed,"cases":len(out["cases"]),
                      "file":str(dest),"primary_checkpoints":19*len(out["cases"]),
                      "diagnostic_checkpoints":100*len(out["cases"])},ensure_ascii=False),flush=True)
    return out

if __name__=="__main__":
    run()
