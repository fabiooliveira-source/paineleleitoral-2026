"""Evaluate V6 frozen national geographic expansion (15 cities, 5 regions).

Read ONLY artifacts from frozen data-only GitHub Actions preparation run.
No training, retuning, substitution or candidate relabelling is permitted.
A success here is historical challenge performance, NOT independent review.
"""
import collections
import hashlib
import json
import pathlib
import statistics
import subprocess
from datetime import datetime
from avaliar_externos_v41_2024 import quantile
from preditor_v4_guardado import predict_guarded
from preditor_v6_guardado import predict_v6_guarded

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
PROTOCOL=ROOT/"protocolo_raio_nacional_v6_2024_v1.json"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"
PRIMARY=tuple(range(5,100,5))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def metrics(series):
    vals=[float(v) for v in series if v is not None]
    if not vals:return {"n":0,"total":len(series),"mae_pp":None,"max_abs_pp":None,"p95_abs_pp":None,"bias_pp":None}
    return {"n":len(vals),"total":len(series),
            "mae_pp":statistics.mean(map(abs,vals)),"max_abs_pp":max(map(abs,vals)),
            "p95_abs_pp":quantile([abs(v) for v in vals]),"bias_pp":statistics.mean(vals)}

def evaluate(city,lock):
    uf=city["uf"]; name=city["name"]
    meta=lock["states"][uf]
    fp=DATA/(uf+"_checkpoints_1_100.json")
    mp=DATA/(uf+"_manifest.json")
    if not fp.exists() or not mp.exists():
        raise RuntimeError("CITY_DATA_BLOCKED "+uf+" "+name)
    if digest(fp)!=meta["input_sha256"] or digest(mp)!=meta["manifest_sha256"]:
        raise RuntimeError("CITY_SOURCE_REPLACED "+uf)
    manifest=json.loads(mp.read_text())
    d=json.loads(fp.read_text())
    if (d["config"]["uf"]!=uf or d["config"]["name"]!=name or
        d["config"]["municipality"]!=manifest["tse_code"] or
        manifest["city"]!=name or
        manifest["input_sha256"]!=meta["input_sha256"] or
        d["source_sha256"]!={x["name"]:x["sha256"] for x in manifest["sources"]}):
        raise RuntimeError("CITY_IDENTITY_MISMATCH "+uf)
    if d["config"]["candidate_a"]!=manifest["candidate_a"] or d["config"]["candidate_b"]!=manifest["candidate_b"]:
        raise RuntimeError("CANDIDATE_ROSTER_CHANGED "+uf)
    assert not d["official_public_snapshot_authenticated"]
    rows=d["checkpoints"]
    if [x["threshold_pct"] for x in rows]!=list(range(1,101)):
        raise RuntimeError("INVALID_GRID "+uf)
    target=d["target_a"]; truth="a" if target>.5 else "b"
    if not(0<target<1):raise RuntimeError("bad final share")
    checkpoints=[]
    previous=None
    last_time=None
    last_sections=-1
    last_votes=(0,0)
    for frame in rows:
        curr=frame["current"]; t=datetime.fromisoformat(curr["timestamp"])
        if last_time is not None and t<last_time:raise RuntimeError("time regression")
        if frame["sections_counted"]<last_sections:raise RuntimeError("section regression")
        if frame["sections_fraction"]+1e-12<frame["threshold_pct"]/100:raise RuntimeError("early checkpoint")
        if curr["votes_a"]<last_votes[0] or curr["votes_b"]<last_votes[1]:raise RuntimeError("vote revision")
        if sum(r["votes_a"] for r in frame["ledger"])!=curr["votes_a"]:raise RuntimeError("a reconciliation fail")
        if sum(r["votes_b"] for r in frame["ledger"])!=curr["votes_b"]:raise RuntimeError("b reconciliation fail")
        if len(frame["ledger"])!=len(d["reference"]):raise RuntimeError("incomplete zones")
        if not all(datetime.fromisoformat(x["available_at"])<=t for x in frame["ledger"]):raise RuntimeError("future ledger")
        if not all(datetime.fromisoformat(x["available_at"])<=t for x in d["reference"].values()):raise RuntimeError("future reference")
        v6=predict_v6_guarded(curr,d["reference"],frame["ledger"],previous=previous)
        v4=predict_guarded(curr,d["reference"],frame["ledger"],previous=previous)
        observed=curr["votes_a"]/(curr["votes_a"]+curr["votes_b"]) if curr["votes_a"]+curr["votes_b"] else None
        e6=v6["estimate_a"];e4=v4["estimate_a"]
        if frame["threshold_pct"]==100:
            if v6["status"]!="CLOSED" or abs(e6-target)>1e-12:
                raise RuntimeError("100pct final exactness failure "+uf)
        checks=({
            "pct":frame["threshold_pct"],"time":curr["timestamp"],
            "sections_seen":frame["sections_counted"],
            "sections_share":frame["sections_fraction"],
            "electorate_share":curr["electorate_counted"]/curr["electorate_total"],
            "v6_a_pct":None if e6 is None else 100*e6,
            "v4_a_pct":None if e4 is None else 100*e4,
            "observed_a_pct":None if observed is None else 100*observed,
            "v6_error_pp":None if e6 is None else 100*(e6-target),
            "v4_error_pp":None if e4 is None else 100*(e4-target),
            "observed_error_pp":None if observed is None else 100*(observed-target),
            "v6_provisional_winner_correct":None if e6 is None or e6==0.5 else ("a" if e6>.5 else "b")==truth,
            "v4_provisional_winner_correct":None if e4 is None or e4==0.5 else ("a" if e4>.5 else "b")==truth,
            "deterministic_call_correct":None if v6["conditional_winner"] is None else v6["conditional_winner"]==truth,
            "physical_bound_contains_target":v6["lower_a"]-1e-12<=target<=v6["upper_a"]+1e-12 if v6["lower_a"] is not None else False,
            "zero_sample_first_vote_share":v6.get("zero_sample_first_vote_share"),
            "first_round_coverage":v6.get("coverage_first_valid"),
            "status":v6["status"],"reason":v6["reason"],
        })
        checkpoints.append(checks)
        if v6["status"] in ("ESTIMATED","CLOSED"):previous=curr
        last_time=t;last_sections=frame["sections_counted"]
        last_votes=(curr["votes_a"],curr["votes_b"])
    basis=[p for p in checkpoints if p["pct"] in PRIMARY]
    m6=metrics([x["v6_error_pp"] for x in basis])
    m4=metrics([x["v4_error_pp"] for x in basis])
    base=metrics([x["observed_error_pp"] for x in basis])
    rules={
        "all_19_estimates":m6["n"]==19,
        "mae_not_worse_than_raw_observed":m6["mae_pp"] is not None and m6["mae_pp"]<=base["mae_pp"]+1e-12,
        "max_abs_not_worse_than_raw_observed":m6["max_abs_pp"] is not None and m6["max_abs_pp"]<=base["max_abs_pp"]+1e-12,
        "mae_pp_at_most":m6["mae_pp"] is not None and m6["mae_pp"]<=1,
        "p95_pp_at_most":m6["p95_abs_pp"] is not None and m6["p95_abs_pp"]<=2,
        "max_pp_at_most":m6["max_abs_pp"] is not None and m6["max_abs_pp"]<=3,
        "winner_correct_at5":basis[0]["v6_provisional_winner_correct"] is True,
        "no_false_conditional_call":all(x["deterministic_call_correct"] is not False for x in basis),
        "physical_bounds_contain_truth":all(x["physical_bound_contains_target"] for x in basis)}
    assert set(rules)==set(json.loads(PROTOCOL.read_text())["primary_rules"])
    bad=[k for k,v in rules.items() if not v]
    return {"name":name,"uf":uf,"region":city["region"],
            "tse_code":manifest["tse_code"],"candidate_a":manifest["candidate_a"],
            "candidate_b":manifest["candidate_b"],
            "zones":manifest["zones"],"sections":manifest["sections"],
            "target_a_pct":100*target,
            "primary_19":{"v6":m6,"v4":m4,"raw":base},
            "first5":basis[0],"gate_passed":not bad,"failed":bad,
            "wrong_primary_v6":[z["pct"] for z in basis if z["v6_provisional_winner_correct"] is False],
            "wrong_primary_v4":[z["pct"] for z in basis if z["v4_provisional_winner_correct"] is False],
            "unique_internal_times":len({z["time"] for z in checkpoints}),
            "coverage_5pct":basis[0]["first_round_coverage"],
            "zero_sample_5pct":basis[0]["zero_sample_first_vote_share"],
            "all_checkpoints":checkpoints}

def run():
    p=json.loads(PROTOCOL.read_text())
    lock=json.loads(LOCK.read_text())
    assert p["status"]=="PREREGISTERED_NEVER_SCORED"
    assert p["v6_coverage_limit"]==0.20
    assert len(p["cities"])==15 and len(lock["states"])==15
    assert digest(PROTOCOL)==lock["protocol_sha256"]
    assert lock["data_preparation_run_id"]==41250338824
    # Exact frozen files: reject any changed version of model or inputs.
    for filename,want in (("preditor_v6_guardado.py",p["v6_model_blob_sha1"]),
                          ("preditor_v4_guardado.py",p["v4_model_blob_sha1"])):
        actual=subprocess.check_output(["git","hash-object",str(ROOT/filename)],text=True).strip()
        if actual!=want:raise RuntimeError("MODEL_FROZEN_HASH_DRIFT "+filename)
    results=[]
    for city in p["cities"]:
        c=evaluate(city,lock)
        results.append(c)
        print(json.dumps({"name":c["name"],"uf":c["uf"],"pass":c["gate_passed"],
                          "failures":c["failed"],
                          "v6":c["primary_19"]["v6"],
                          "v4":c["primary_19"]["v4"],
                          "observed":c["primary_19"]["raw"],
                          "winner_wrong":c["wrong_primary_v6"],
                          "first5":c["first5"]["v6_a_pct"]},ensure_ascii=False),flush=True)
    groups={}
    for region in sorted({x["region"] for x in results}):
        group=[x for x in results if x["region"]==region]
        groups[region]={"cities":len(group),"passed":sum(x["gate_passed"] for x in group),
                        "unweighted_city_mae_v6_pp":statistics.mean(c["primary_19"]["v6"]["mae_pp"] for c in group),
                        "unweighted_city_mae_v4_pp":statistics.mean(c["primary_19"]["v4"]["mae_pp"] for c in group)}
    passed=sum(x["gate_passed"] for x in results)
    conclusion="WIDER_HISTORICAL_HOLDOUT_PASS_NOT_CERTIFIED" if passed==15 else "WIDER_HISTORICAL_HOLDOUT_FAILED_NOT_CERTIFIED"
    output={"status":conclusion,"preregistration_commit":"4409295ed075da08c717b3880095b1de4ca8460f",
            "model":"V6 frozen 20pct","data_prep_run":lock["data_preparation_run_id"],
            "cities_total":len(results),"cities_passed":passed,
            "regions_total":len(groups),"states_total":len({c["uf"] for c in results}),
            "checkpoint_count":sum(len(c["all_checkpoints"]) for c in results),
            "primary_checkpoints":19*len(results),
            "region_metrics":groups,"cases":results,
            "integral_certification":False,"independent_reviewer":False,
            "limitations":["Historical data and city outcomes are publicly knowable; retrospective holdout not a blinded prospective assessment.",
                           "TSE internal first-totalization timestamps reconstructed from final votes are not authenticated public snapshots.",
                           "15 elections, not 1500 independent trials: checkpoints correlated.",
                           "V6 uses zones; no spatial search radius or coordinate-distance input was added.",
                           "No per-case fixes or parameter changes after analyzing previous holdout failures."]}
    target=DATA/"resultado_raio_nacional_v6_2024.json"
    target.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":conclusion,"passed":passed,"total":len(results),
                      "regions":len(groups),"primary_checkpoints":output["primary_checkpoints"],
                      "diagnostic_checkpoints":output["checkpoint_count"]},ensure_ascii=False),flush=True)
    return output
if __name__=="__main__":run()
