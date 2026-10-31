"""Conservative territorial perturbation benchmark across 15 completed holdout cities.

One/two/three observed zone removals. Removes votes of finalists from current
national total and uses these votes as LOWER BOUND on removed turnout.
This is a synthetic stress, not a real-time reconstructed sequence.
"""
import copy,hashlib,json,pathlib,random,statistics
from preditor_v6_guardado import predict_v6_guarded
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
SEED=20261031
SAMPLE=(1,2,3,4,5,10,15,20,25,30,50,75,90,95)

def remove(frame,zones):
    f=copy.deepcopy(frame)
    removed_valid=0
    for row in f["ledger"]:
        if row["scope"] in zones:
            removed_valid+=row["votes_a"]+row["votes_b"]
            f["current"]["votes_a"]-=row["votes_a"]
            f["current"]["votes_b"]-=row["votes_b"]
            for k in ("votes_a","votes_b","matched_first_a","matched_first_b"):
                row[k]=0
    f["current"]["electorate_counted"]-=removed_valid
    return f

def analyze():
    lock=json.loads((ROOT/"congelamento_raio_nacional_v6_2024.json").read_text())
    rng=random.Random(SEED)
    rows=[];total_checks=0
    for uf,meta in lock["states"].items():
        file=DATA/(uf+"_checkpoints_1_100.json")
        assert hashlib.sha256(file.read_bytes()).hexdigest()==meta["input_sha256"]
        d=json.loads(file.read_text())
        notes=[]
        for point in d["checkpoints"]:
            pct=point["threshold_pct"]
            if pct not in SAMPLE:continue
            baseline=predict_v6_guarded(point["current"],d["reference"],point["ledger"])
            if baseline["estimate_a"] is None:
                raise AssertionError("baseline absent "+uf+" "+str(pct))
            existing=[r for r in point["ledger"] if r["votes_a"]+r["votes_b"]]
            by_size=sorted(existing,key=lambda x:x["votes_a"]+x["votes_b"],reverse=True)
            by_1t=sorted(existing,key=lambda x:d["reference"][x["scope"]]["votes_a"]+
                                                d["reference"][x["scope"]]["votes_b"],reverse=True)
            candidates={}
            for zone in existing:
                candidates[("single",str(zone["scope"]))]=(zone["scope"],)
            if len(existing)>1:
                candidates[("top2_valid","largest_2_valid")]=tuple(r["scope"] for r in by_size[:2])
                candidates[("top2_prior","largest_2_prior")]=tuple(r["scope"] for r in by_1t[:2])
                candidates[("random2","seeded_random2")]=tuple(r["scope"] for r in rng.sample(existing,2))
            if len(existing)>2:
                candidates[("top3_valid","largest_3_valid")]=tuple(r["scope"] for r in by_size[:3])
                candidates[("random3","seeded_random3")]=tuple(r["scope"] for r in rng.sample(existing,3))
            trials=[]
            for (kind,label),zone_names in candidates.items():
                f=remove(point,set(zone_names))
                result=predict_v6_guarded(f["current"],d["reference"],f["ledger"])
                total_checks+=1
                outcome={
                    "mode":kind,"label":label,"zones":zone_names,
                    "synthetic_removed_valid":sum(
                        z["votes_a"]+z["votes_b"] for z in existing if z["scope"] in zone_names),
                    "status":result["status"],"reason":result.get("reason"),
                    "shift_pp":None if result["estimate_a"] is None else 100*(result["estimate_a"]-baseline["estimate_a"]),
                    "leader_flip":None if result["estimate_a"] is None else
                        ((result["estimate_a"]>.5)!=(baseline["estimate_a"]>.5)),
                    "vote_share_error_pp":None if result["estimate_a"] is None else
                        100*(result["estimate_a"]-d["target_a"])
                }
                trials.append(outcome)
            single=[t for t in trials if t["mode"]=="single" and t["shift_pp"] is not None]
            accepted=[t for t in trials if t["shift_pp"] is not None]
            notes.append({
                "pct":pct,"baseline_estimate_pct":100*baseline["estimate_a"],
                "baseline_error_pp":100*(baseline["estimate_a"]-d["target_a"]),
                "trials_count":len(trials),
                "abstentions":sum(t["shift_pp"] is None for t in trials),
                "max_shift_single_pp":max((abs(t["shift_pp"]) for t in single),default=None),
                "max_shift_all_scenarios_pp":max((abs(t["shift_pp"]) for t in accepted),default=None),
                "leader_flips_single":sum(t["leader_flip"] is True for t in single),
                "leader_flips_all":sum(t["leader_flip"] is True for t in accepted),
                "max_shift_case":max(accepted,key=lambda x:abs(x["shift_pp"])) if accepted else None,
                "trials":trials,
            })
        row={
            "uf":uf,"city":meta["city"],"zones":meta["zones"],
            "checkpoint_count":len(notes),
            "scenario_checks":sum(x["trials_count"] for x in notes),
            "abstentions":sum(x["abstentions"] for x in notes),
            "max_single_shift_pp":max((x["max_shift_single_pp"] or 0) for x in notes),
            "max_multizone_shift_pp":max((x["max_shift_all_scenarios_pp"] or 0) for x in notes),
            "single_zone_flip_count":sum(x["leader_flips_single"] for x in notes),
            "all_scenarios_flip_count":sum(x["leader_flips_all"] for x in notes),
            "at_5pct":next(x for x in notes if x["pct"]==5),
            "checkpoints":notes,
        }
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in ("checkpoints","at_5pct")} |
                          {"at_5pct":{"max_shift_single_pp":row["at_5pct"]["max_shift_single_pp"],
                                      "max_shift_all_scenarios_pp":row["at_5pct"]["max_shift_all_scenarios_pp"],
                                      "single_flips":row["at_5pct"]["leader_flips_single"],
                                      "abstentions":row["at_5pct"]["abstentions"]}},
                         ensure_ascii=False),flush=True)
    result={
        "status":"POST_HOLDOUT_SYNTHETIC_STRESS_NOT_CERTIFICATION",
        "seed":SEED,"cities":len(rows),"total_scenarios":total_checks,
        "max_shift_pp":max(x["max_multizone_shift_pp"] for x in rows),
        "total_abstentions":sum(x["abstentions"] for x in rows),
        "total_single_zone_leader_flips":sum(x["single_zone_flip_count"] for x in rows),
        "city_diagnostics":rows,
        "caveats":[
            "All stress trials synthetically subtract valid candidate votes, not actual local comparecimento.",
            "Unavailable official zone-level turnout means these scenarios are NOT causal TSE totalization replays.",
            "True winner is known historically and used only for error reporting.",
            "No V6 formula or initial holdout decision was modified.",
            "Snapshots are retrospective and not contemporaneous public TSE captures."]
    }
    dest=DATA/"stress_zonas_v6_15_cidades.json"
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"decision":result["status"],"cities":result["cities"],
                      "total_scenarios":total_checks,
                      "maximum_change_pp":result["max_shift_pp"],
                      "abstentions":result["total_abstentions"],
                      "provisional_winner_flips":result["total_single_zone_leader_flips"]},ensure_ascii=False),flush=True)
if __name__=="__main__":analyze()
