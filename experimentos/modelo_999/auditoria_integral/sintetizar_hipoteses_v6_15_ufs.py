"""Summarize completed forensic / temporal / territorial audits without retuning V6.

This is an evidence synthesis, not a new holdout or proof of causation.
"""
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"

def load(filename):
    p=DATA/filename
    return json.loads(p.read_text())

def round4(x):
    return round(x,4) if x is not None else None

def run():
    original=load("resultado_raio_nacional_v6_2024.json")
    forensic=load("diagnostico_causas_v6_15_cidades.json")
    stress=load("stress_zonas_v6_15_cidades.json")
    clock=load("relogio_auditoria_15_ufs.json")
    assert original["cities_passed"]==5 and original["cities_total"]==15
    assert forensic["cities"]==stress["cities"]==len(clock["cities"])==15
    assert clock["total_sections"]==sum(x["sections"] for x in original["cases"])
    by_case={c["uf"]:c for c in forensic["per_city_diagnostics"]}
    by_stress={c["uf"]:c for c in stress["city_diagnostics"]}
    table=[]
    for k in by_case:
        c=by_case[k]
        f=c["summary"]["first5"]
        if f is None:raise ValueError("5 pct diagnostic missing "+k)
        s=by_stress[k]
        row={
            "uf":k,"city":c["city"],"passed_frozen_gate":c["passed_original_gate"],
            "mae_v6":round4(c["error_v6_mae_pp"]),
            "mae_v4":round4(c["error_v4_mae_pp"]),
            "mae_raw":round4(c["error_raw_mae_pp"]),
            "v6_minus_v4_mae":round4(c["v6_minus_v4_mae_pp"]),
            "first5_error_v6":round4(f["v6_error_pp"]),
            "first5_error_v4":round4(f["v4_error_pp"]),
            "first5_shift_v6_minus_v4":round4(f["v6_minus_v4_pp"]),
            "first5_unobserved_prior_percent":round4(100*f["zero_sample_reference_fraction"]),
            "first5_unobserved_future_valid_percent":round4(100*f["zero_sample_actual_future_valid_share"]),
            "first5_alpha_shrinkage":round4(f["alpha_shrinkage"]),
            "first5_oracle_mix_error_pp":round4(f["oracle_mixture_error_pp"]),
            "first5_oracle_volume_error_pp":round4(f["oracle_volume_component_pp"]),
            "first5_estimated_remaining_valid":round4(f["predicted_remaining_valid_after_cap"]),
            "first5_true_remaining_valid":f["actual_remaining_valid"],
            "first5_predicted_to_real_remaining":round4(f["predicted_remaining_valid_after_cap"]/f["actual_remaining_valid"]) if f["actual_remaining_valid"] else None,
            "first5_largest_zone_oracle":f["top_three_zones_oracle_impact"][:2],
            "first5_zone_ablation_max_shift_pp":round4(s["at_5pct"]["max_shift_single_pp"]),
            "all_checkpoints_single_zone_ablation_max_shift_pp":round4(s["max_single_shift_pp"]),
            "all_checkpoint_cap_cases":c["summary"]["cap_applied_checkpoint_count"],
            "checkpoints_v6_differs_v4":c["summary"]["count_v6_differs_from_v4"],
            "checkpoints_v6_worse_raw":c["summary"]["count_v6_worse_than_raw"],
            "checkpoint_count":c["summary"]["core_n"],
            "zones":c["zones"],"sections":c["total_sections"],
        }
        table.append(row)
        print(json.dumps({"diagnosed":row},ensure_ascii=False),flush=True)
    no_zero_at5=[r for r in table if r["first5_unobserved_prior_percent"]<1e-10]
    zero_at5=[r for r in table if r["first5_unobserved_prior_percent"]>1e-10]
    false_all=sum(r["all_checkpoint_cap_cases"] for r in table)
    gaps=[r for r in table if abs(r["first5_shift_v6_minus_v4"])>1]
    clocks=[r["first_minus_BU_received_median_seconds"] for r in clock["cities"]
            if r["first_minus_BU_received_median_seconds"] is not None]
    result={
        "status":"FORENSIC_HYPOTHESES_EVIDENCE_POST_HOLDOUT_NOT_CERTIFICATION",
        "models_frozen":True,"national_holdout_passed":False,
        "n_cities":15,"n_failed_cities":10,
        "passed_original_gate":5,
        "source_temporal_sections":clock["total_sections"],
        "clock_last_totalization_fields_absent_all":all(not c["has_last_totalization"] for c in clock["cities"]),
        "median_city_median_BU_to_first_totalization_seconds":statistics.median(clocks),
        "cities_with_no_unseen_zone_at5":len(no_zero_at5),
        "cities_with_unseen_zone_at5":len(zero_at5),
        "cities_no_zero_at5": [r["city"] for r in no_zero_at5],
        "cities_with_first5_v6_v4_shift_over1pp":[r["city"] for r in gaps],
        "city_primary_cap_applied_total":false_all,
        "city_v6_mae_worse_than_v4":forensic["v6_worse_city_mae_than_v4"],
        "city_v6_mae_better_than_v4":forensic["v6_improves_city_mae_over_v4"],
        "city_v6_mae_equal_to_v4":forensic["v6_equals_city_mae_v4"],
        "city_v6_mae_worse_than_raw":forensic["v6_worse_city_mae_than_raw"],
        "bootstrap_v6_minus_v4":forensic["bootstrap_city_mae_v6_minus_v4"],
        "bootstrap_v6_minus_raw":forensic["bootstrap_city_mae_v6_minus_raw"],
        "synthetic_zone_stress":{
            "scenarios":stress["total_scenarios"],
            "abstentions":stress["total_abstentions"],
            "winner_flips_single":stress["total_single_zone_leader_flips"],
            "max_multi_zone_shift_pp":stress["max_shift_pp"]},
        "cases":table,
        "hypotheses":{
            "H1_missing_zone_shrinkage":"Supported for some high first5 errors, especially MG with large absent-zone 1T reference. Not universal cause: city errors persist without missing zones.",
            "H2_candidate_transfer_between_rounds":"Potential bias because rates per first-round finalist extrapolate into 2T despite territorial differences in third-party transfers and turnout. Future zone-vote decomposition reports contribution but does not uniquely identify individual voter transfer.",
            "H3_counted_cap":"Ruled out as observed explanation for national 19-step primary failures: no cases where extrapolation hit physical cap.",
            "H4_geographic_sample_order":"Zone/section arrival order matters under assumed internal clock; synthetic zone-removal stress can shift estimates materially.",
            "H5_public_snapshots":"Not validated. Official section first totalization timestamps exist, but public timestamp and intermediate corrections were not archived.",
            "H6_V6_improves_V4":"Not demonstrated. 4 cities worse, 5 better and 6 identical by election-level MAE."
        },
        "cautions":[
            "Post hoc explanatory associations must not be repurposed as externally validated V7 thresholds.",
            "The 'oracle' uses all final votes, explicitly future information; only for forensic root cause.",
            "Time-to-available/publication and true per-zone turnout were not authenticated.",
            "The clock CSV has no explicit last-partial-totalization field, so historical revisions cannot be ruled out.",
            "Bootstrap resamples a purposively selected roster of historical cities; not a calibrated probability.",
            "For V7, freeze a new design before evaluating entirely unused municipalities and cycles."
        ]
    }
    dest=DATA/"sintese_forense_v6_15_cidades.json"
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("cases","hypotheses","cautions")},
                     ensure_ascii=False),flush=True)
if __name__=="__main__":run()
