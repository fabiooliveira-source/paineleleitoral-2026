"""Evaluate previously frozen V7 on 18 2020 municipal elections.

Data and code hash locks MUST predate this run. All missing cases are
blocking failures; do not tune model or discard any unsuccessful city.
A historical temporal holdout is NOT real-time public-snapshot certification.
"""
import hashlib,json,pathlib,statistics,subprocess
from datetime import datetime
from preditor_v7_experimental import predict_v7
from preditor_v6_guardado import predict_v6_guarded
from preditor_v4_guardado import predict_guarded
from avaliar_externos_v41_2024 import quantile
ROOT=pathlib.Path(__file__).resolve().parent
PROTOCOL=ROOT/"protocolo_v7_holdout_temporal_2020_v1.json"
LOCK=ROOT/"congelamento_v7_holdout_temporal_2020.json"
DATA=ROOT/"raio_temporal_v7_2020"
PRIMARY=set(range(5,100,5))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def measure(values):
    vals=[v for v in values if v is not None]
    if not vals:return {"n":0,"total":len(values),"mae_pp":None,"max_abs_pp":None,"p95_abs_pp":None,"bias_pp":None}
    return {"n":len(vals),"total":len(values),"mae_pp":statistics.mean(abs(z) for z in vals),
            "max_abs_pp":max(abs(z) for z in vals),
            "p95_abs_pp":quantile([abs(z) for z in vals]),
            "bias_pp":statistics.mean(vals)}
def verify():
    p=json.loads(PROTOCOL.read_text())
    lock=json.loads(LOCK.read_text())
    assert p["model_parameter_tuning_prohibited"] and len(p["cases"])==18
    assert lock["status"]=="FROZEN_PRE_V7_2020_HOLDOUT_SCORE"
    assert lock["protocol_sha256"]==h(PROTOCOL)
    assert lock["model_git_blob_sha1"]==p["model_git_blob_sha1"]
    assert lock["data_only_run_id"]==41252574828
    assert len(lock["states"])==18
    for filename,expected in ((p["model_path"],p["model_git_blob_sha1"]),
                              ("preditor_v6_guardado.py",p["baseline_v6_sha1"]),
                              ("preditor_v4_guardado.py",p["baseline_v4_sha1"])):
        actual=subprocess.check_output(["git","hash-object",str(ROOT/filename)],text=True).strip()
        if actual!=expected:raise RuntimeError("FROZEN_MODEL_HASH_CHANGED: "+filename)
    return p,lock
def score_one(target,expected,meta):
    uf=expected["uf"];name=expected["city"]
    input_path=DATA/(uf+"_checkpoints_1_100.json")
    manifest_path=DATA/(uf+"_manifest.json")
    if not(input_path.is_file() and manifest_path.is_file()):
        raise RuntimeError("MISSING_PREREGISTERED_CASE: "+uf)
    if h(input_path)!=meta["input_sha256"] or h(manifest_path)!=meta["manifest_sha256"]:
        raise RuntimeError("HOLDOUT_INPUT_HASH_CHANGED: "+uf)
    m=json.loads(manifest_path.read_text())
    d=json.loads(input_path.read_text())
    if (m["city"]!=name or m["uf"]!=uf or d["config"]["municipality"]!=m["tse_code"] or
        d["config"]["candidate_a"]!=m["candidate_a"] or d["config"]["candidate_b"]!=m["candidate_b"]):
        raise RuntimeError("CASE_IDENTITY_ERROR "+uf)
    if len(d["checkpoints"])!=100 or not d["availability_is_assumed"] or d["official_public_snapshot_authenticated"]:
        raise RuntimeError("INVALID_RECONSTRUCTED_TIMELINE "+uf)
    truth=d["target_a"]
    actual_winner="a" if truth>.5 else "b"
    previous=None;last_ts=None;last_sect=-1
    rows=[]
    for f in d["checkpoints"]:
        pct=f["threshold_pct"];c=f["current"];ledger=f["ledger"];ref=d["reference"]
        assert pct==len(rows)+1
        now=datetime.fromisoformat(c["timestamp"])
        if last_ts is not None and now<last_ts:raise RuntimeError("OUT_OF_ORDER "+uf)
        if f["sections_counted"]<last_sect:raise RuntimeError("SECTION_COUNT_DECREASE "+uf)
        if f["sections_fraction"]+1e-12<pct/100:raise RuntimeError("MISLABELED_CHECKPOINT "+uf)
        if any(datetime.fromisoformat(x["available_at"])>now for x in ref.values()):
            raise RuntimeError("FUTURE_FIRST_ROUND "+uf)
        if any(datetime.fromisoformat(x["available_at"])>now for x in ledger):
            raise RuntimeError("FUTURE_SECOND_ROUND "+uf)
        v7=predict_v7(c,ref,ledger,previous)
        v6=predict_v6_guarded(c,ref,ledger,previous)
        v4=predict_guarded(c,ref,ledger,previous)
        assert v7["probability"] is None
        if pct==100 and (v7["status"]!="CLOSED" or v7["estimate_a"] is None or abs(v7["estimate_a"]-truth)>1e-12):
            raise RuntimeError("100_PERCENT_INCONSISTENCY "+uf)
        a,b=c["votes_a"],c["votes_b"]
        base=a/(a+b) if a+b else None
        preds={"v7":v7["estimate_a"],"v6":v6["estimate_a"],
               "v4":v4["estimate_a"],"raw":base}
        entry={"pct":pct,"timestamp":c["timestamp"],"sections_seen":f["sections_counted"],
               "electorate_coverage":c["electorate_counted"]/c["electorate_total"],
               "estimate_pct":{key:None if val is None else 100*val for key,val in preds.items()},
               "errors_pp":{key:None if val is None else 100*(val-truth) for key,val in preds.items()},
               "leader_correct":{key:None if val is None or val==.5 else
                                 ("a" if val>.5 else "b")==actual_winner for key,val in preds.items()},
               "status":{"v7":v7["status"],"v6":v6["status"],"v4":v4["status"]},
               "v7_zones_weak":v7.get("zone_count_weak"),
               "v7_reference_coverage":v7.get("first_round_coverage"),
               "mathematical_conditional_call":v7.get("conditional_winner"),
               "mathematical_winner_correct":None if v7.get("conditional_winner") is None else
                                              v7["conditional_winner"]==actual_winner,
               "physical_bounds_cover_truth":v7["lower_a"] is not None and
                     v7["lower_a"]-1e-12<=truth<=v7["upper_a"]+1e-12}
        rows.append(entry)
        if v7["status"] in ("ESTIMATED","CLOSED"):previous=c
        last_ts=now;last_sect=f["sections_counted"]
    focus=[x for x in rows if x["pct"] in PRIMARY]
    assert len(focus)==19
    scores={name:measure([x["errors_pp"][name] for x in focus]) for name in ("v7","v6","v4","raw")}
    v7m=scores["v7"];raw=scores["raw"]
    criteria=target["primary_case_criteria"]
    gates={
        "all_19_estimates":v7m["n"]==19,
        "mae_less_than_or_equal_to_observed":v7m["mae_pp"] is not None and v7m["mae_pp"]<=raw["mae_pp"]+1e-12,
        "max_error_less_than_or_equal_to_observed":v7m["max_abs_pp"] is not None and v7m["max_abs_pp"]<=raw["max_abs_pp"]+1e-12,
        "mae_at_most_1pp":v7m["mae_pp"] is not None and v7m["mae_pp"]<=1.,
        "p95_at_most_2pp":v7m["p95_abs_pp"] is not None and v7m["p95_abs_pp"]<=2.,
        "max_at_most_3pp":v7m["max_abs_pp"] is not None and v7m["max_abs_pp"]<=3.,
        "provisional_winner_correct_at_5":focus[0]["leader_correct"]["v7"] is True,
        "no_false_mathematical_winner_call":all(x["mathematical_winner_correct"] is not False for x in focus),
        "physical_bounds_cover_final":all(x["physical_bounds_cover_truth"] for x in focus)}
    if set(gates)!=set(criteria):raise RuntimeError("PROTOCOL_GATE_DRIFT")
    return {
       "uf":uf,"city":name,"region":expected["region"],
       "municipality_code":m["tse_code"],"sections":m["sections"],
       "zones":m["zones"],"actual_final_share_a":truth,
       "metrics":scores,"gates":gates,"passed_all":all(gates.values()),
       "failed_criteria":[k for k,v in gates.items() if not v],
       "wrong_v7_leaders":[x["pct"] for x in focus if x["leader_correct"]["v7"] is False],
       "wrong_v6_leaders":[x["pct"] for x in focus if x["leader_correct"]["v6"] is False],
       "first5_v7_pct":focus[0]["estimate_pct"]["v7"],
       "all_checkpoints":rows}
def run():
    p,lock=verify()
    results=[]
    for case in p["cases"]:
        r=score_one(p,case,lock["states"][case["uf"]])
        results.append(r)
        print(json.dumps({"city":r["city"],"uf":r["uf"],"pass":r["passed_all"],
            "failed":r["failed_criteria"],"v7":r["metrics"]["v7"],
            "v6":r["metrics"]["v6"],"raw":r["metrics"]["raw"],
            "wrong_v7_leaders":r["wrong_v7_leaders"]},ensure_ascii=False),flush=True)
    passed=sum(z["passed_all"] for z in results)
    out={"status":"V7_2020_HISTORICAL_TEMPORAL_CHALLENGE_ONLY",
         "model_git_sha1":p["model_git_blob_sha1"],"data_preparation_run":lock["data_only_run_id"],
         "cases_total":len(results),"cases_passed":passed,
         "primary_checkpoints":19*len(results),
         "diagnostic_checkpoints":100*len(results),
         "strict_all_cases_gate_passed":passed==p["required_passed_cases"],
         "independent_blinded_prospective_validation":False,
         "integral_certification":False,"cases":results,
         "limitations":["All 2020 timelines were retrospectively reconstructed from final section results.",
                        "First totalization clock cannot authenticate actual public snapshot availability.",
                        "2020 municipals are temporally separate from 2024 development, but not a randomly sampled blind audit.",
                        "Candidate model is not calibrated for win probabilities.",
                        "The same team selects, codes and runs the holdout."]}
    dest=DATA/"resultado_v7_holdout_temporal_2020.json"
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="cases"},ensure_ascii=False),flush=True)
if __name__=="__main__":run()
