"""Post-holdout failure analysis: secondary only. DO NOT calibrate V6 with it.

Replays official historical checkpoint artifacts; maintains model/protocol
frozen. Measures geography and lost-zone sensitivity, not predictive fixes.
"""
import copy
import json
import pathlib
from preditor_v6_guardado import predict_v6_guarded

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"holdout_v6_2024"
KEY=(1,2,3,4,5,10,15,20,25,30,40,50,60,70,80,90,95,97,99,100)

def analyse():
    summary=json.loads((DATA/"resultado_holdout_v6_2024.json").read_text())
    entries=[]
    for case in summary["cases"]:
        code=case["municipality"]
        d=json.loads((DATA/(code+"_checkpoints_1_100.json")).read_text())
        checkpoints=d["checkpoints"];point_by_pct={z["threshold_pct"]:z for z in checkpoints}
        scores={p["pct"]:p for p in case["checkpoints"]}
        primary=range(5,100,5)
        zone_stress=[]
        for pct in primary:
            point=point_by_pct[pct]
            original=predict_v6_guarded(point["current"],d["reference"],point["ledger"])
            assert original["estimate_a"] is not None
            outcome={"checkpoint":pct,"zone_trials":0,"abstains":0,"largest_shift_pp":0.0,
                     "leader_flips":0,"worst_zone":None,"worst_zone_observed_votes":0}
            for row in point["ledger"]:
                valid=row["votes_a"]+row["votes_b"]
                if not valid:continue
                new=copy.deepcopy(point)
                z=next(x for x in new["ledger"] if x["scope"]==row["scope"])
                for key in ("votes_a","votes_b","matched_first_a","matched_first_b"):z[key]=0
                new["current"]["votes_a"]-=row["votes_a"]
                new["current"]["votes_b"]-=row["votes_b"]
                new["current"]["electorate_counted"]-=valid
                q=predict_v6_guarded(new["current"],d["reference"],new["ledger"])
                outcome["zone_trials"]+=1
                if q["estimate_a"] is None:
                    outcome["abstains"]+=1
                    continue
                shift=100*(q["estimate_a"]-original["estimate_a"])
                leader_flip=(q["estimate_a"]>.5)!=(original["estimate_a"]>.5)
                if leader_flip:outcome["leader_flips"]+=1
                if abs(shift)>outcome["largest_shift_pp"]:
                    outcome["largest_shift_pp"]=abs(shift)
                    outcome["worst_zone"]=row["scope"]
                    outcome["worst_zone_observed_votes"]=valid
            zone_stress.append(outcome)
        stamps=[r["totalization_time"] for r in checkpoints]
        fifth=scores[5]
        diagnostics={
            "name":case["name"],"municipality":code,
            "gate_passed":case["gate_passed"],"gate_failures":case["failed_criteria"],
            "final_winner":case["truth_winner"],
            "first_5_pct":{
                "model_pct":fifth["v6_estimate_pct"],
                "v4_pct":fifth["v4_estimate_pct"],
                "observed_pct":fifth["raw_observed_pct"],
                "final_pct":case["target_a_pct"],
                "v6_error_pp":fifth["v6_error_pp"],
                "v4_error_pp":fifth["v4_error_pp"],
                "v6_winner_correct":fifth["v6_winner_correct"],
                "v4_winner_correct":fifth["v4_winner_correct"],
                "first_vote_sample_coverage":fifth["first_round_coverage"],
                "zero_sample_zone_first_vote_share":fifth["zero_sample_first_vote_share"],
                "actual_sections_fraction":fifth["sections_fraction"],
                "actual_electorate_fraction":fifth["electorate_fraction"],
                "timestamp":fifth["time"],
            },
            "v6_mae_pp":case["primary_metrics_v6"]["mae_pp"],
            "v4_mae_pp":case["primary_metrics_v4"]["mae_pp"],
            "v6_improves_mae_over_v4":case["primary_metrics_v6"]["mae_pp"]<case["primary_metrics_v4"]["mae_pp"]-1e-12,
            "v6_winner_wrong_primary":case["winner_wrong_checkpoints_v6"],
            "v4_winner_wrong_primary":case["winner_wrong_checkpoints_v4"],
            "time_resolution":{
                "100_thresholds":len(checkpoints),
                "unique_first_totalization_times":len(set(stamps)),
                "thresholds_reusing_time":len(stamps)-len(set(stamps)),
                "first_time":stamps[0],"last_time":stamps[-1]
            },
            "secondary_grid":{str(pct):{
                "v6_error_pp":scores[pct]["v6_error_pp"],
                "v4_error_pp":scores[pct]["v4_error_pp"],
                "raw_observed_error_pp":scores[pct]["observed_error_pp"],
                "v6_winner_correct":scores[pct]["v6_winner_correct"]
            } for pct in KEY},
            "stage_metrics":case["secondary_segments"],
            "one_zone_stress":zone_stress,
            "max_single_zone_shift_pp":max(r["largest_shift_pp"] for r in zone_stress),
            "zone_stress_leader_flips":sum(r["leader_flips"] for r in zone_stress),
            "zone_stress_abstains":sum(r["abstains"] for r in zone_stress),
        }
        entries.append(diagnostics)
        print(json.dumps({"city":case["name"],"first5":diagnostics["first_5_pct"],
                          "v6_wrong":diagnostics["v6_winner_wrong_primary"],
                          "v4_wrong":diagnostics["v4_winner_wrong_primary"],
                          "max_zone_shift_pp":diagnostics["max_single_zone_shift_pp"],
                          "zone_flips":diagnostics["zone_stress_leader_flips"],
                          "unique_timestamps":diagnostics["time_resolution"]["unique_first_totalization_times"]
                          },ensure_ascii=False),flush=True)
    out={"status":"POST_HOLDOUT_DIAGNOSTIC_NO_RETRAINING",
         "evaluation_protocol_unchanged":True,
         "cases":entries,
         "warnings":[
            "The new five cities are no longer untouched holdouts after this analysis.",
            "These secondary metrics are exploratory and cannot be used to lower preregistered criteria.",
            "A failed checkpoint does not establish causation from a missing geographic zone.",
            "Zone-removal subtracts valid votes, not exact observed turnout; it is a synthetic test.",
            "Thresholds 1..100 are correlated. Number of unique timestamps is reported.",
            "Do not optimize model parameters on these five and call them independent external validation."]
         }
    (DATA/"diagnostico_holdout_v6_2024.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"cases":len(entries),"status":out["status"]}),flush=True)
if __name__=="__main__":analyse()
