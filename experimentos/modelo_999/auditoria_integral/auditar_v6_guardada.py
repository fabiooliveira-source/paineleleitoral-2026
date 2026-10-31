"""Auditoria V6: stress de invariantes, regressao, disponibilidade e atrasos sinteticos.

Aprovacao de integridade de software NAO equivale a certificacao preditiva.
Os checkpoints de cada caso sao correlacionados; nao contar como eleicoes.
"""
import copy
import json
import math
import pathlib
import random
import statistics
from datetime import datetime, timedelta
from avaliar_cobertura_v6 import forecast
from preditor_v6_guardado import predict_v6_guarded

ROOT = pathlib.Path(__file__).resolve().parent
RNG = random.Random(20261031)
CASES = {
    "fortaleza_2024": ROOT / "externos2024/13897/entradas_pareadas_v4_2024.json",
    "pelotas_2024": ROOT / "externos2024/87912/entradas_pareadas_v4_2024.json",
    "natal_2024": ROOT / "externos2024/17612/entradas_pareadas_v4_2024.json",
    "sao_paulo_2020": ROOT / "entradas_pareadas_v4_2020.json",
    "presidencial_2022": ROOT / "entradas_pareadas_v4_2022.json",
}
def clone(value):
    return copy.deepcopy(value)

def delayed_zone(frame, scope, consistent):
    new = clone(frame)
    row = next(z for z in new["ledger"] if z["scope"] == scope)
    va, vb = row["votes_a"], row["votes_b"]
    for k in ("votes_a", "votes_b", "matched_first_a", "matched_first_b"):
        row[k] = 0
    if consistent:
        # Apenas perturbacao matematicamente compativel com o agregado.
        # Brancos/nulos locais NAO estao no ledger: ajuste de comparecimento
        # remove exclusivamente votos validos, nao reconstitui evento real.
        new["current"]["votes_a"] -= va
        new["current"]["votes_b"] -= vb
        new["current"]["electorate_counted"] -= va + vb
    return new

def mutations(frame, reference):
    current = frame["current"]; ledger = frame["ledger"]
    key = ledger[0]["scope"]
    future = (datetime.fromisoformat(current["timestamp"]) + timedelta(days=1)).isoformat()
    m = {}
    f=clone(frame);f["ledger"]=f["ledger"][1:];m["missing_scope"]=f
    f=clone(frame);f["current"]["votes_a"]+=1;m["national_territorial_mismatch"]=f
    f=clone(frame);f["ledger"][0]["matched_first_a"]=reference[key]["votes_a"]+1;m["matched_exceeds_reference"]=f
    f=clone(frame);f["current"]["electorate_counted"]=0;m["votes_exceed_counted"]=f
    f=clone(frame);f["current"]["available_at"]=future;m["national_future"]=f
    f=clone(frame);f["current"]["timestamp"]="2024-10-27T17:00:00";m["naive_timestamp"]=f
    f=clone(frame);bad=clone(f["ledger"][0]);bad["votes_a"]+=1;f["ledger"].append(bad);m["conflicting_duplicate"]=f
    f=clone(frame);f["ledger"][0]["available_at"]=future;m["future_territorial_only"]=f
    f=clone(frame);f["ledger"][0]["timestamp"]=(datetime.fromisoformat(current["timestamp"])-timedelta(minutes=5)).isoformat();f["ledger"][0]["available_at"]=f["ledger"][0]["timestamp"];m["stale_territorial_only"]=f
    f=clone(frame);f["current"]["votes_a"]=-1;m["negative_vote"]=f
    f=clone(frame);f["ledger"][0]["votes_a"]=True;m["boolean_vote"]=f
    f=clone(frame);f["ledger"][0]["matched_first_b"]="bad";m["text_matched_vote"]=f
    return m

def error_metrics(predictions, target):
    errors = [100*(p-target) for p in predictions]
    return {"n":len(errors), "mae_pp":statistics.mean(map(abs,errors)),
            "max_abs_pp":max(map(abs,errors)), "bias_pp":statistics.mean(errors),
            "winner_correct":sum((x>0.5)==(target>0.5) for x in predictions),
            "winner_correct_at5":(predictions[0]>0.5)==(target>0.5)}

def one_case(name, path):
    d=json.loads(path.read_text())
    reference=d["reference"];frames=d["checkpoints"];target=d["target_a"]
    checks=0; failures=[]; model=[]; baseline=[]; v4=[]; actual_coverage=[]
    random_shift=[];random_abstains=0;random_total=0
    largest_shift=[];largest_abstains=0
    for index,frame in enumerate(frames):
        current=frame["current"]; ledger=frame["ledger"]
        p=predict_v6_guarded(current,reference,ledger)
        if p["status"]!="ESTIMATED" or p["estimate_a"] is None:
            failures.append(f"{name} checkpoint {index}: unexpected baseline abstention {p['reason']}")
            continue
        model.append(p["estimate_a"]);v4.append(p["comparison_v4_estimate_a"])
        baseline.append(current["votes_a"]/(current["votes_a"]+current["votes_b"]))
        actual_coverage.append(p["coverage_first_valid"])
        old=forecast(frame,reference,"v6")/100
        checks+=1
        if abs(p["estimate_a"]-old)>1e-12:
            failures.append(f"{name} checkpoint {index}: V6 formula drift {p['estimate_a']-old}")
        checks+=1
        if p["probability"] is not None or not (p["lower_a"]-1e-12<=p["estimate_a"]<=p["upper_a"]+1e-12):
            failures.append(f"{name} checkpoint {index}: probability or physical bound invalid")
        shuffle=clone(frame);RNG.shuffle(shuffle["ledger"])
        sp=predict_v6_guarded(shuffle["current"],reference,shuffle["ledger"])
        checks+=1
        if sp["estimate_a"] is None or abs(sp["estimate_a"]-p["estimate_a"])>1e-12:
            failures.append(f"{name} checkpoint {index}: row shuffle changes estimate")
        dup=clone(frame);dup["ledger"].append(clone(dup["ledger"][0]))
        dp=predict_v6_guarded(dup["current"],reference,dup["ledger"])
        checks+=1
        if dp["estimate_a"] is None or abs(dp["estimate_a"]-p["estimate_a"])>1e-12:
            failures.append(f"{name} checkpoint {index}: identical duplicate changes estimate")
        future=clone(frame);extra=clone(future["ledger"][0])
        ft=(datetime.fromisoformat(current["timestamp"])+timedelta(days=1)).isoformat()
        extra["timestamp"]=ft;extra["available_at"]=ft;extra["votes_a"]=999999
        future["ledger"].append(extra)
        fp=predict_v6_guarded(future["current"],reference,future["ledger"])
        checks+=1
        if fp["estimate_a"] is None or abs(fp["estimate_a"]-p["estimate_a"])>1e-12:
            failures.append(f"{name} checkpoint {index}: future data leaked")
        for label,bad in mutations(frame,reference).items():
            q=predict_v6_guarded(bad["current"],reference,bad["ledger"])
            checks+=1
            if q["estimate_a"] is not None or q["status"]!="ABSTAIN" or q.get("clear_prior_forecast") is not True:
                failures.append(f"{name} checkpoint {index}: fail-open on {label}")
        damaged_ref=clone(reference)
        damaged_ref[ledger[0]["scope"]]["available_at"]=ft
        q=predict_v6_guarded(current,damaged_ref,ledger)
        checks+=1
        if q["estimate_a"] is not None:failures.append(f"{name} checkpoint {index}: future 1T reference leaked")
        bad_previous=clone(current)
        bad_previous["timestamp"]=ft;bad_previous["available_at"]=ft
        q=predict_v6_guarded(current,reference,ledger,previous=bad_previous)
        checks+=1
        if q["estimate_a"] is not None:failures.append(f"{name} checkpoint {index}: older snapshot not blocked")
        zone=max(ledger,key=lambda r:r["votes_a"]+r["votes_b"])["scope"]
        stale=delayed_zone(frame,zone,False)
        q=predict_v6_guarded(stale["current"],reference,stale["ledger"])
        checks+=1
        if q["estimate_a"] is not None:
            failures.append(f"{name} checkpoint {index}: national/territorial split fail-open")
        affected=delayed_zone(frame,zone,True)
        q=predict_v6_guarded(affected["current"],reference,affected["ledger"])
        checks+=1
        if q["estimate_a"] is None: largest_abstains+=1
        else: largest_shift.append(abs(100*(q["estimate_a"]-p["estimate_a"])))
        for _ in range(20):
            zone=RNG.choice(ledger)["scope"]
            affected=delayed_zone(frame,zone,True)
            q=predict_v6_guarded(affected["current"],reference,affected["ledger"])
            checks+=1;random_total+=1
            if q["estimate_a"] is None:random_abstains+=1
            else:random_shift.append(abs(100*(q["estimate_a"]-p["estimate_a"])))
    result={"case":name,"checkpoints":len(frames),"accepted":len(model),
            "checked_assertions":checks,"failures":failures[:30],
            "failure_count":len(failures),
            "v6":error_metrics(model,target) if model else None,
            "v4":error_metrics(v4,target) if v4 else None,
            "observed_baseline":error_metrics(baseline,target) if baseline else None,
            "coverage_range":[min(actual_coverage),max(actual_coverage)] if actual_coverage else None,
            "synthetic_largest_zone":{"accepted":len(largest_shift),"abstentions":largest_abstains,"max_shift_pp":max(largest_shift) if largest_shift else None},
            "synthetic_random_zone":{"runs":random_total,"accepted":len(random_shift),"abstentions":random_abstains,"max_shift_pp":max(random_shift) if random_shift else None,
                                     "p95_shift_pp":sorted(random_shift)[int(.95*(len(random_shift)-1))] if random_shift else None}}
    return result

def run():
    cases=[one_case(k,v) for k,v in CASES.items()]
    passed=all(c["failure_count"]==0 and c["accepted"]==c["checkpoints"] for c in cases)
    result={"model":"V6 original 20% with V4.1 guardrails",
            "test_seed":20261031,"cases":cases,
            "checked_assertions":sum(c["checked_assertions"] for c in cases),
            "engineering_integrity_passed":passed,
            "independent_predictive_certification":False,
            "decision":"GUARDED_V6_ENGINEERING_PASS_NOT_EXTERNAL_CERTIFICATION" if passed else "ENGINEERING_FAILURE",
            "limitations":["Checkpoint timestamps/first vote totals are retrospectively reconstructed.",
                           "Delay simulations subtract valid votes only; local turnout unavailable.",
                           "Prior cases used to develop V4/V6; no unseen external challenge.",
                           "Multiple checkpoints of one election are correlated.",
                           "No estimate is a win probability."]}
    (ROOT/"resultado_auditoria_v6_guardada.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"decision":result["decision"],"assertions":result["checked_assertions"],
                      "cases":[{"case":c["case"],"failure_count":c["failure_count"],
                                "v6":c["v6"],"v4":c["v4"],
                                "synthetic_random_zone":c["synthetic_random_zone"],
                                "synthetic_largest_zone":c["synthetic_largest_zone"]} for c in cases]}),flush=True)
    if not passed:raise SystemExit("V6 integrity gate failed")
if __name__=="__main__":run()
