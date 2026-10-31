"""Experimental V7: candidate SHARE and expected valid VOLUME separately.

The structure and constants here are fixed BEFORE first external 2020 replay.
No target/final election results are read. This is a candidate model, never
a certified win probability, and is NEVER imported by frozen V6.

For missing-zone issue, estimate A/B composition with log-odds swing from
paired observed sections and 1T prior by zone; shrink local swing toward
global swing for weak observed zones. Estimate *valid-vote volume* with a
single common conversion factor, separately from A/B mix.

Parameters are principled *choices*, not independently validated:
JEFFREYS = .5 pseudocount; PRIOR_VALID = 1000 observed 2T votes/zone;
MAX_DEVIATION_LOGODDS = ln(4) a robust clamp on local swing. Release policy
is not probabilistic.
"""
import math
from preditor_v4_guardado import predict_guarded

MODEL_VERSION="v7-experimental-separate-composition-volume-2026-10-31"
PRIOR_VALID=1000.
PSEUDOCOUNT=0.5
MAX_DEVIATION_LOGODDS=math.log(4.)

def _log_ratio(a,b):
    return math.log((a+PSEUDOCOUNT)/(b+PSEUDOCOUNT))
def _sigmoid(x):
    if x>=0:
        return 1./(1.+math.exp(-x))
    ex=math.exp(x)
    return ex/(1.+ex)
def _fail(checked,reason):
    return {**checked,"model_version":MODEL_VERSION,"status":"ABSTAIN",
            "reason":reason,"estimate_a":None,"probability":None,
            "clear_prior_forecast":True}

def predict_v7(current,reference,ledger,previous=None):
    verified=predict_guarded(current,reference,ledger,previous=previous)
    result={**verified,"model_version":MODEL_VERSION,"probability":None,
            "candidate_model_only":True}
    if verified["status"]!="ESTIMATED":
        return result
    try:
        a,b=current["votes_a"],current["votes_b"]
        remaining_eligible=current["electorate_total"]-current["electorate_counted"]
        by_scope={str(r["scope"]):r for r in ledger if r["timestamp"]==current["timestamp"] and
                                               r["available_at"]==current["timestamp"]}
        if len(by_scope)!=len(reference) or set(by_scope)!=set(reference):
            raise ValueError("noncanonical ledger")
        matched_a=sum(r["matched_first_a"] for r in by_scope.values())
        matched_b=sum(r["matched_first_b"] for r in by_scope.values())
        if min(matched_a,matched_b)<=0:
            raise ValueError("unidentifiable global transfer")
        total_matched=matched_a+matched_b
        observed_valid=a+b
        global_swing=_log_ratio(a,b)-_log_ratio(matched_a,matched_b)
        common_volume_conversion=observed_valid/total_matched
        if not math.isfinite(common_volume_conversion) or common_volume_conversion<=0:
            raise ValueError("invalid volume conversion")
        expected_unseen=[0.,0.]
        zone_output=[]
        for scope in sorted(reference):
            ref=reference[scope]
            row=by_scope[scope]
            left_a=ref["votes_a"]-row["matched_first_a"]
            left_b=ref["votes_b"]-row["matched_first_b"]
            if left_a<0 or left_b<0:
                raise ValueError("reference mismatch")
            remaining_prior=left_a+left_b
            if remaining_prior==0:
                continue
            m_a=row["matched_first_a"]
            m_b=row["matched_first_b"]
            valid=row["votes_a"]+row["votes_b"]
            weak=(m_a==0 or m_b==0 or valid==0)
            local_swing=_log_ratio(row["votes_a"],row["votes_b"])-_log_ratio(m_a,m_b) if not weak else global_swing
            departure=max(-MAX_DEVIATION_LOGODDS,min(MAX_DEVIATION_LOGODDS,local_swing-global_swing))
            local_weight=valid/(valid+PRIOR_VALID) if not weak else 0.
            posterior_swing=global_swing+local_weight*departure
            projected_share=_sigmoid(_log_ratio(left_a,left_b)+posterior_swing)
            future_valid=remaining_prior*common_volume_conversion
            expected_unseen[0]+=future_valid*projected_share
            expected_unseen[1]+=future_valid*(1-projected_share)
            zone_output.append({
                "scope":scope,"empty_or_unidentifiable_zone":weak,
                "prior_remaining_finalist_votes":remaining_prior,
                "observed_valid_for_shrinkage":valid,
                "local_weight":local_weight
            })
        predicted_future=sum(expected_unseen)
        volume_scale=min(1.,remaining_eligible/predicted_future) if predicted_future>0 else 1.
        expected_unseen=[v*volume_scale for v in expected_unseen]
        denominator=a+b+sum(expected_unseen)
        if denominator<=0:raise ValueError("zero predicted votes")
        estimate=(a+expected_unseen[0])/denominator
        if not math.isfinite(estimate):
            raise ValueError("nonfinite prediction")
        if not (result["lower_a"]-1e-12<=estimate<=result["upper_a"]+1e-12):
            raise ValueError("outside physical bounds")
        total_prior=sum(r["votes_a"]+r["votes_b"] for r in reference.values())
        return {**result,"estimate_a":estimate,"status":"ESTIMATED","reason":None,
                "estimated_unseen_a":expected_unseen[0],
                "estimated_unseen_b":expected_unseen[1],
                "global_swing_logodds":global_swing,
                "volume_conversion":common_volume_conversion,
                "volume_scale":volume_scale,
                "first_round_coverage":total_matched/total_prior if total_prior else None,
                "unobserved_scope_fraction_of_first_round":sum(
                    z["prior_remaining_finalist_votes"] for z in zone_output
                    if z["empty_or_unidentifiable_zone"])/total_prior if total_prior else None,
                "effective_zones":sum(z["local_weight"] for z in zone_output),
                "zone_count_weak":sum(z["empty_or_unidentifiable_zone"] for z in zone_output),
                "probability":None}
    except (ValueError,KeyError,ArithmeticError,OverflowError,TypeError):
        return _fail(result,"v7_invalid_or_unidentified")
