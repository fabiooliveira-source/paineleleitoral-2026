"""Integra V6 no painel sem confundir lideranca projetada com vencedor garantido.

Mantem todas as estimativas validas da V6; nao suspende estimativa so porque
a analise de zona e instavel. Nao emite chamada de vencedor sem limite
matematico de votos restantes. Nenhuma 'probabilidade de vitoria' e calculada.
"""
import copy
from preditor_v6_guardado import predict_v6_guarded

# Politica administrativa para chamar atencao do operador, nao acuracia certificada.
SENSITIVITY_ALERT_PP = 1.0

def predict_for_panel(current,reference,ledger,previous=None):
    p=predict_v6_guarded(current,reference,ledger,previous=previous)
    if p["estimate_a"] is None:
        return {**p, "provisional_leader":None,"winner_call":None,
                "winner_call_status":"NOT_CALLED", "estimated_winner_is_provisional":True,
                "territorial_alert":None,"probability":None}
    estimate=p["estimate_a"]
    leader="a" if estimate>0.5 else ("b" if estimate<0.5 else None)
    determinate=p.get("conditional_winner")
    # conditional_winner comes from deterministic mathematical electorate bounds.
    call=determinate if determinate in ("a","b") else None
    values=[];invalid=0
    for row in ledger:
        votes=row["votes_a"]+row["votes_b"]
        if votes==0:continue
        c=copy.deepcopy(current);data=copy.deepcopy(ledger)
        r=next(x for x in data if x["scope"]==row["scope"])
        for k in ("votes_a","votes_b","matched_first_a","matched_first_b"):r[k]=0
        c["votes_a"]-=row["votes_a"];c["votes_b"]-=row["votes_b"]
        # Lower bound of removed local turnout; its actual blank/null votes unknown.
        c["electorate_counted"]-=votes
        q=predict_v6_guarded(c,reference,data)
        if q["estimate_a"] is None:
            invalid+=1
            continue
        change_pp=100*(q["estimate_a"]-estimate)
        values.append({"zone":str(row["scope"]),"delta_pp":change_pp,
                       "leader_flip":((q["estimate_a"]>0.5)!=(estimate>0.5))})
    max_shift=max((abs(x["delta_pp"]) for x in values),default=None)
    any_flip=any(x["leader_flip"] for x in values)
    alert=("UNIDENTIFIABLE_ON_ZONE_REMOVAL" if invalid
           else "PROVISIONAL_LEADER_UNSTABLE" if any_flip
           else "TERRITORIAL_SHIFT_OVER_ONE_PP" if max_shift is not None and max_shift>SENSITIVITY_ALERT_PP
           else "NO_SINGLE_ZONE_ALERT")
    return {**p, "provisional_leader":leader,
            "estimated_winner_is_provisional":True,
            "winner_call":call,
            "winner_call_status":"CONDITIONAL_DETERMINISTIC" if call else "NOT_CALLED",
            "winner_call_is_conditional_on_no_revisions":True,
            "territorial_alert":alert,
            "single_zone_max_shift_pp":max_shift,
            "single_zone_leader_flip":any_flip,
            "single_zone_unidentifiable":invalid,
            "single_zone_variants_tested":len(values)+invalid,
            "v4_v6_estimated_leaders_disagree":leader!=
                ("a" if p.get("comparison_v4_estimate_a", estimate)>0.5 else
                 "b" if p.get("comparison_v4_estimate_a", estimate)<0.5 else None),
            "probability":None}
