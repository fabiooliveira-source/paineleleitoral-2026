"""Forensic diagnosis of frozen V6 on 15 *already disclosed* held-out elections.

READ-ONLY analysis of historical outcomes. All 'oracle' calculations use
final 2T votes and therefore are DIAGNOSTIC, NEVER predictors or validation.
The frozen V6 formula / initial holdout gates are not changed here.
"""
from __future__ import annotations
import hashlib,json,math,pathlib,random,statistics
from collections import defaultdict
from datetime import datetime
from preditor_v6_guardado import predict_v6_guarded
from preditor_v4_guardado import predict_guarded

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"
ORIGINAL=DATA/"resultado_raio_nacional_v6_2024.json"
CHECKPOINTS=set(range(5,100,5)) | {1,2,3,4,6,7,8,9,98,99}
PRIMARY=set(range(5,100,5))
SEED=20261031

def value(x):
    return float(x) if x is not None else None
def h(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def metric(x):
    if not x:return None
    return {"n":len(x),"mean":statistics.mean(x),"min":min(x),"max":max(x)}

def decompose(frame, ref, final, target, code):
    cur=frame["current"]
    a,b=cur["votes_a"],cur["votes_b"]
    curvalid=a+b;final_valid=final["current"]["votes_a"]+final["current"]["votes_b"]
    actual_remaining=(final_valid-curvalid)
    ref_valid=sum(z["votes_a"]+z["votes_b"] for z in ref.values())
    rows={r["scope"]:r for r in frame["ledger"]}
    end={r["scope"]:r for r in final["ledger"]}
    coverage=sum(r["matched_first_a"]+r["matched_first_b"] for r in rows.values())/ref_valid
    alpha=min(1.,coverage/.20)
    m_a=sum(r["matched_first_a"] for r in rows.values())
    m_b=sum(r["matched_first_b"] for r in rows.values())
    if not(m_a>0 and m_b>0):
        return {"status":"ABSTAIN_NO_GLOBAL_SUPPORT","pct":frame["threshold_pct"],"coverage":coverage}
    rate_a=a/m_a;rate_b=b/m_b
    common=(a+b)/(m_a+m_b)
    pred=[0.,0.];v4_unseen=[0.,0.]
    details=[];zero_votes=0;unseen_zero_actual=0;actual_remaining_total=0
    zone_turnout=[]
    for scope in sorted(ref):
        observed=rows[scope];future=end[scope]
        past_ref=ref[scope]
        m=(observed["matched_first_a"],observed["matched_first_b"])
        o=(observed["votes_a"],observed["votes_b"])
        historic=(past_ref["votes_a"],past_ref["votes_b"])
        left=(historic[0]-m[0],historic[1]-m[1])
        observed_empty=sum(m)==0
        rate4=[o[i]/m[i] if m[i] else (rate_a,rate_b)[i] for i in range(2)]
        rate6=[alpha*rr+(1-alpha)*common if observed_empty else rate4[i]
               for i,rr in enumerate(rate4)]
        estimate6=[left[i]*rate6[i] for i in range(2)]
        estimate4=[left[i]*rate4[i] for i in range(2)]
        actual=[future["votes_a"]-o[0],future["votes_b"]-o[1]]
        if min(actual)<0:raise ValueError("negative unobserved future in "+code+" "+scope)
        actual_remaining_total+=sum(actual)
        pred[0]+=estimate6[0];pred[1]+=estimate6[1]
        v4_unseen[0]+=estimate4[0];v4_unseen[1]+=estimate4[1]
        if observed_empty:
            zero_votes+=sum(historic)
            unseen_zero_actual+=sum(actual)
        if sum(historic)>0:
            vote_rate_final=(future["votes_a"]+future["votes_b"])/sum(historic)
            zone_turnout.append((scope,vote_rate_final,sum(historic)))
        details.append({
            "scope":scope,"ref_first_a":historic[0],"ref_first_b":historic[1],
            "matched_first_a":m[0],"matched_first_b":m[1],
            "observed_a":o[0],"observed_b":o[1],
            "actual_remaining_a":actual[0],"actual_remaining_b":actual[1],
            "unseen_v6_raw_a":estimate6[0],"unseen_v6_raw_b":estimate6[1],
            "unseen_v4_raw_a":estimate4[0],"unseen_v4_raw_b":estimate4[1],
            "unobserved_scope":observed_empty,
            "final_2t_valid":future["votes_a"]+future["votes_b"],
            "final_ratio_to_1t_finalists":(future["votes_a"]+future["votes_b"])/sum(historic) if sum(historic) else None,
            "final_share_a":future["votes_a"]/(future["votes_a"]+future["votes_b"]) if future["votes_a"]+future["votes_b"] else None,
        })
    assert actual_remaining_total==actual_remaining
    remaining_eligible=cur["electorate_total"]-cur["electorate_counted"]
    factor=min(1.,remaining_eligible/sum(pred)) if sum(pred)>0 else 1.
    v4factor=min(1.,remaining_eligible/sum(v4_unseen)) if sum(v4_unseen)>0 else 1.
    unseen=[x*factor for x in pred]
    un4=[x*v4factor for x in v4_unseen]
    v6=100*(a+unseen[0])/(curvalid+sum(unseen))
    v4=100*(a+un4[0])/(curvalid+sum(un4))
    pred_valid=curvalid+sum(unseen)
    actual_valid=final_valid
    mix_a=unseen[0]/sum(unseen) if sum(unseen) else None
    oracle_with_actual_remaining=(100*(a+actual_remaining*mix_a)/(curvalid+actual_remaining)
                                   if mix_a is not None and actual_valid else None)
    # Error decomposition: model minus target = volume component + mix
    # component. The "oracle" uses future aggregate turnout; NOT deployable.
    mix_error=(oracle_with_actual_remaining-100*target
               if oracle_with_actual_remaining is not None else None)
    volume_error=(v6-oracle_with_actual_remaining
                  if oracle_with_actual_remaining is not None else None)
    for row in details:
        row["unseen_v6_capped_a"]=row["unseen_v6_raw_a"]*factor
        row["unseen_v6_capped_b"]=row["unseen_v6_raw_b"]*factor
        row["unseen_v4_capped_a"]=row["unseen_v4_raw_a"]*v4factor
        row["unseen_v4_capped_b"]=row["unseen_v4_raw_b"]*v4factor
        row["unseen_a_prediction_minus_actual"]=row["unseen_v6_capped_a"]-row["actual_remaining_a"]
        row["unseen_b_prediction_minus_actual"]=row["unseen_v6_capped_b"]-row["actual_remaining_b"]
        row["zone_final_votes_share"]=row["final_2t_valid"]/final_valid if final_valid else None
        # A one-zone future oracle, accounting for actual candidate mix and
        # turnout only in that one zone. This is a diagnostic counterfactual.
        xA=a+unseen[0]-row["unseen_v6_capped_a"]+row["actual_remaining_a"]
        xB=b+unseen[1]-row["unseen_v6_capped_b"]+row["actual_remaining_b"]
        row["oracle_zone_corrected_estimate_pct"]=100*xA/(xA+xB) if xA+xB else None
        row["single_zone_oracle_impact_pp"]=(row["oracle_zone_corrected_estimate_pct"]-v6
                                            if xA+xB else None)
    top_by_impact=sorted(details,key=lambda r:abs(r["single_zone_oracle_impact_pp"] or 0.),reverse=True)
    row_rates=[r[1] for r in zone_turnout]
    weights=[r[2] for r in zone_turnout]
    avg_rate=sum(x*w for x,w in zip(row_rates,weights))/sum(weights)
    heterogeneity=(math.sqrt(sum(w*(r-avg_rate)**2 for r,w in zip(row_rates,weights))/sum(weights))/avg_rate
                   if avg_rate>0 else None)
    return {
        "status":"ESTIMATED_DIAGNOSTIC","pct":frame["threshold_pct"],
        "timestamp":frame["current"]["timestamp"],"n_zones":len(ref),
        "v6_estimate_pct":v6,"v4_estimate_pct":v4,"truth_pct":100*target,
        "v6_error_pp":v6-100*target,"v4_error_pp":v4-100*target,
        "v6_minus_v4_pp":v6-v4,
        "raw_observed_error_pp":100*(a/curvalid-target),
        "coverage_first_finalists":coverage,"alpha_shrinkage":alpha,
        "zero_sample_zone_count":sum(r["unobserved_scope"] for r in details),
        "zero_sample_reference_fraction":zero_votes/ref_valid,
        "zero_sample_actual_future_valid_share":unseen_zero_actual/actual_remaining if actual_remaining else 0,
        "first_turnout_rates_std_over_mean":heterogeneity,
        "global_2t_over_1t_candidate_a":rate_a,
        "global_2t_over_1t_candidate_b":rate_b,
        "global_rate_asymmetry_log":math.log(rate_a/rate_b) if rate_a>0 and rate_b>0 else None,
        "remaining_eligible":remaining_eligible,
        "predicted_remaining_valid_uncapped":sum(pred),
        "predicted_remaining_valid_after_cap":sum(unseen),
        "actual_remaining_valid":actual_remaining,
        "predicted_total_valid":pred_valid,
        "actual_final_valid":actual_valid,
        "cap_applied":factor<1-1e-12,"cap_scale_factor":factor,
        "future_oracle_actual_volume_estimate_pct":oracle_with_actual_remaining,
        "oracle_mixture_error_pp":mix_error,
        "oracle_volume_component_pp":volume_error,
        "top_three_zones_oracle_impact":[{
            "scope":z["scope"],"single_zone_oracle_impact_pp":z["single_zone_oracle_impact_pp"],
            "zone_final_votes_share":z["zone_final_votes_share"],
            "unobserved_scope":z["unobserved_scope"],
            "first_a":z["ref_first_a"],"first_b":z["ref_first_b"],
            "remaining_a":z["actual_remaining_a"],"remaining_b":z["actual_remaining_b"],
            "pred_unseen_a":z["unseen_v6_capped_a"],
            "pred_unseen_b":z["unseen_v6_capped_b"]}
            for z in top_by_impact[:3]],
        "zone_decompositions":details if frame["threshold_pct"] in (5,10,20) else None,
    }

def summary_stats(rows):
    x=[z for z in rows if z["status"]=="ESTIMATED_DIAGNOSTIC"]
    early=[z for z in x if z["pct"] in (1,2,3,4,5,10)]
    core=[z for z in x if z["pct"] in PRIMARY]
    return {
        "diagnostic_n":len(x),"core_n":len(core),
        "first5":next((z for z in x if z["pct"]==5),None),
        "worst_abs_v6":max(core,key=lambda z:abs(z["v6_error_pp"])) if core else None,
        "worst_v6_minus_v4":max(core,key=lambda z:abs(z["v6_minus_v4_pp"])) if core else None,
        "count_v6_differs_from_v4":sum(abs(z["v6_minus_v4_pp"])>1e-10 for z in core),
        "count_v6_worse_than_v4":sum(abs(z["v6_error_pp"])>abs(z["v4_error_pp"])+1e-10 for z in core),
        "count_v6_worse_than_raw":sum(abs(z["v6_error_pp"])>abs(z["raw_observed_error_pp"])+1e-10 for z in core),
        "cap_applied_checkpoint_count":sum(z["cap_applied"] for z in core),
        "absolute_mean_oracle_mixture_error_pp":statistics.mean(abs(z["oracle_mixture_error_pp"]) for z in core if z["oracle_mixture_error_pp"] is not None) if core else None,
        "absolute_mean_volume_component_pp":statistics.mean(abs(z["oracle_volume_component_pp"]) for z in core if z["oracle_volume_component_pp"] is not None) if core else None,
        "max_zero_sample_ref_share_core":max(z["zero_sample_reference_fraction"] for z in core) if core else None,
        "max_heterogeneity_2t_to_prior":max(z["first_turnout_rates_std_over_mean"] for z in core) if core else None,
        "max_zone_single_oracle_pp_at5":max(abs(x["single_zone_oracle_impact_pp"]) for x in next((z for z in x if z["pct"]==5),core[0])["zone_decompositions"]) if core else None,
    }

def descriptive_bootstrap(cases,metric_name, seed=SEED, n=6000):
    rng=random.Random(seed)
    values=[c[metric_name] for c in cases]
    estimates=[statistics.mean([rng.choice(values) for _ in values]) for __ in range(n)]
    estimates.sort()
    return {"metric":metric_name,"point":statistics.mean(values),
            "percentile_2_5":estimates[int(.025*(n-1))],
            "percentile_97_5":estimates[int(.975*(n-1))],
            "unit":"one-election-resampled",
            "limit":"Descriptive only: sampled election roster not randomized."}

def run():
    lock=json.loads(LOCK.read_text())
    report=json.loads(ORIGINAL.read_text())
    case_by_uf={c["uf"]:c for c in report["cases"]}
    assert len(lock["states"])==15 and len(case_by_uf)==15
    diagnostics=[];compact=[]
    for uf,metadata in lock["states"].items():
        p=DATA/(uf+"_checkpoints_1_100.json")
        assert h(p)==metadata["input_sha256"]
        doc=json.loads(p.read_text())
        final=doc["checkpoints"][-1]
        target=doc["target_a"]
        rows=[]
        for frame in doc["checkpoints"]:
            if frame["threshold_pct"] not in CHECKPOINTS:continue
            if frame["threshold_pct"]==100:continue
            d=decompose(frame,doc["reference"],final,target,uf)
            expected=next(z for z in case_by_uf[uf]["all_checkpoints"] if z["pct"]==d["pct"])
            if d["status"]=="ESTIMATED_DIAGNOSTIC" and abs(d["v6_estimate_pct"]-expected["v6_a_pct"])>1e-9:
                raise AssertionError("MODEL_DRIFT_IN_DECOMPOSITION "+uf+" "+str(d["pct"]))
            rows.append(d)
        stats=summary_stats(rows)
        original=case_by_uf[uf]
        diag={
            "city":metadata["city"],"uf":uf,"region":metadata["region"],
            "passed_original_gate":original["gate_passed"],
            "error_v6_mae_pp":original["primary_19"]["v6"]["mae_pp"],
            "error_v4_mae_pp":original["primary_19"]["v4"]["mae_pp"],
            "error_raw_mae_pp":original["primary_19"]["raw"]["mae_pp"],
            "v6_minus_v4_mae_pp":original["primary_19"]["v6"]["mae_pp"]-original["primary_19"]["v4"]["mae_pp"],
            "v6_minus_raw_mae_pp":original["primary_19"]["v6"]["mae_pp"]-original["primary_19"]["raw"]["mae_pp"],
            "zones":metadata["zones"],"total_sections":metadata["sections"],
            "summary":stats,"checkpoints":rows,
        }
        diagnostics.append(diag)
        at5=stats["first5"]
        compact.append({
            "city":diag["city"],"uf":uf,"pass":diag["passed_original_gate"],
            "mae_v6":round(diag["error_v6_mae_pp"],4),
            "mae_v4":round(diag["error_v4_mae_pp"],4),
            "mae_raw":round(diag["error_raw_mae_pp"],4),
            "difference_v6_v4":round(diag["v6_minus_v4_mae_pp"],4),
            "first5_v6_error_pp":round(at5["v6_error_pp"],4) if at5 else None,
            "first5_v6_minus_v4_pp":round(at5["v6_minus_v4_pp"],4) if at5 else None,
            "first5_zero_zone_ref_pct":round(100*at5["zero_sample_reference_fraction"],2) if at5 else None,
            "first5_cap":at5["cap_applied"] if at5 else None,
            "cap_count_primary":stats["cap_applied_checkpoint_count"],
            "primary_v6_worse_than_v4":stats["count_v6_worse_than_v4"],
            "primary_v6_worse_than_raw":stats["count_v6_worse_than_raw"],
        })
        print(json.dumps({"city_diagnostic":compact[-1]},ensure_ascii=False),flush=True)
    print("MAIN_DIAGNOSTIC_COMPLETED",flush=True)
    overall={
        "status":"EX_POST_DIAGNOSTIC_V6_NOT_CERTIFICATION",
        "model_unchanged":True,"threshold_unchanged":True,
        "cities":len(diagnostics),
        "v6_worse_city_mae_than_v4":sum(c["v6_minus_v4_mae_pp"]>1e-12 for c in diagnostics),
        "v6_improves_city_mae_over_v4":sum(c["v6_minus_v4_mae_pp"]<-1e-12 for c in diagnostics),
        "v6_equals_city_mae_v4":sum(abs(c["v6_minus_v4_mae_pp"])<=1e-12 for c in diagnostics),
        "v6_worse_city_mae_than_raw":sum(c["v6_minus_raw_mae_pp"]>1e-12 for c in diagnostics),
        "v6_better_city_mae_than_raw":sum(c["v6_minus_raw_mae_pp"]<-1e-12 for c in diagnostics),
        "observed_cases":compact,"per_city_diagnostics":diagnostics,
        "bootstrap_city_mae_v6_minus_v4":descriptive_bootstrap(diagnostics,"v6_minus_v4_mae_pp"),
        "bootstrap_city_mae_v6_minus_raw":descriptive_bootstrap(diagnostics,"v6_minus_raw_mae_pp"),
        "limitations":[
            "All final candidate votes (per-zone and aggregate) used to calculate oracle decomposition are FUTURE DATA, forbidden in any deployable predictor.",
            "Reconstructed section internal totalization time is NOT public availability.",
            "These 15 municipalities have been tested and cannot be used as unseen V7 external validation.",
            "Sparsity and candidate-transfer effects are associated diagnostics, not fully identified causal mechanisms.",
            "Bootstrap confidence limits conditional on sampled city roster, not population confidence or calibrated win probability.",
            "Gates, sources, and V6 parameters remained unchanged; 15-cities rejection stands."
        ]
    }
    dest=DATA/"diagnostico_causas_v6_15_cidades.json"
    dest.write_text(json.dumps(overall,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in overall.items() if k not in ("observed_cases","per_city_diagnostics")},
                     ensure_ascii=False),flush=True)
if __name__=="__main__":run()
