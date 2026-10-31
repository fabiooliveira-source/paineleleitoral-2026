"""Politica operacional conservadora para V6: NAO uma nova calibracao.

Tolerancia de 1 ponto percentual e decisao de risco operacional, NAO garantia
de erro preditivo. Testa retirada completa de uma zona, usando um minimo de
comparecimento retirado (votos validos); nao reconstrui dados reais.
"""
import copy
from preditor_v6_guardado import predict_v6_guarded

SHIFT_TOLERANCE_PP = 1.0

def _abstain(p, reason, **details):
    return {**p, **details, "estimate_a":None, "status":"ABSTAIN",
            "reason":reason, "clear_prior_forecast":True, "probability":None}

def predict_v6_stable(current, reference, ledger, previous=None):
    p=predict_v6_guarded(current,reference,ledger,previous=previous)
    p={**p, "stability_policy":"single_observed_zone_removal",
       "stability_tolerance_pp":SHIFT_TOLERANCE_PP}
    if p["status"]!="ESTIMATED":
        return p
    estimate=p["estimate_a"]
    scenarios=[]
    for row in ledger:
        va,vb=row["votes_a"],row["votes_b"]
        if not (va+vb):
            continue
        c=copy.deepcopy(current);r=copy.deepcopy(ledger)
        x=next(z for z in r if z["scope"]==row["scope"])
        for k in ("votes_a","votes_b","matched_first_a","matched_first_b"):
            x[k]=0
        c["votes_a"]-=va;c["votes_b"]-=vb
        c["electorate_counted"]-=va+vb
        trial=predict_v6_guarded(c,reference,r)
        if trial["estimate_a"] is None:
            return _abstain(p,"zone_removal_makes_model_unidentifiable",
                            stress_zone=row["scope"],stress_scenarios=len(scenarios)+1)
        shift_pp=100*(trial["estimate_a"]-estimate)
        flips=(trial["estimate_a"]>.5)!=(estimate>.5)
        scenarios.append({"zone":row["scope"],"shift_pp":shift_pp,"winner_flip":flips})
    if not scenarios:
        return _abstain(p,"no_observed_zone_for_stability_check")
    largest=max(scenarios,key=lambda v:abs(v["shift_pp"]))
    risk={"stress_scenarios":len(scenarios),
          "max_zone_removal_shift_pp":abs(largest["shift_pp"]),
          "worst_zone":largest["zone"],
          "single_zone_winner_flip":any(s["winner_flip"] for s in scenarios)}
    if risk["single_zone_winner_flip"]:
        return _abstain(p,"unstable_projected_winner_after_zone_removal",**risk)
    if risk["max_zone_removal_shift_pp"]>SHIFT_TOLERANCE_PP+1e-12:
        return _abstain(p,"territorial_single_zone_sensitivity_over_policy",**risk)
    return {**p,**risk,"stability_status":"PASS_SINGLE_ZONE_POLICY"}
