"""Avalia cobranca e abstencoes da politica de estabilidade V6: nao certifica.

Todos os 19 checkpoints por caso permanecem no denominador, inclusive
quando a politica deixa de emitir uma estimativa.
"""
import json
import pathlib
import statistics
from preditor_v6_guardado import predict_v6_guarded
from preditor_v6_estavel import predict_v6_stable, SHIFT_TOLERANCE_PP

ROOT=pathlib.Path(__file__).resolve().parent
CASES={
"fortaleza_2024":"externos2024/13897/entradas_pareadas_v4_2024.json",
"pelotas_2024":"externos2024/87912/entradas_pareadas_v4_2024.json",
"natal_2024":"externos2024/17612/entradas_pareadas_v4_2024.json",
"sao_paulo_2020":"entradas_pareadas_v4_2020.json",
"presidencial_2022":"entradas_pareadas_v4_2022.json",
}
def run():
 results=[]
 checks=0;failures=[]
 for name,location in CASES.items():
  d=json.loads((ROOT/location).read_text());target=d["target_a"]
  output=[];reasons={};unfiltered_errors=[];safe_errors=[];max_observed_shift=0
  for i,frame in enumerate(d["checkpoints"]):
   c=frame["current"];rows=frame["ledger"]
   base=predict_v6_guarded(c,d["reference"],rows)
   safe=predict_v6_stable(c,d["reference"],rows)
   if base["estimate_a"] is None:
    failures.append(name+": checkpoint "+str(i)+" V6 baseline abstained")
    continue
   unfiltered_errors.append(abs(100*(base["estimate_a"]-target)))
   checks+=1
   if safe["estimate_a"] is None:
    reason=safe["reason"];reasons[reason]=reasons.get(reason,0)+1
   else:
    safe_errors.append(abs(100*(safe["estimate_a"]-target)))
    checks+=1
    if abs(safe["estimate_a"]-base["estimate_a"])>1e-12:
     failures.append(name+": safe estimator unexpectedly modified formula")
    shift=safe["max_zone_removal_shift_pp"]
    max_observed_shift=max(max_observed_shift,shift)
    if safe["single_zone_winner_flip"] or shift>SHIFT_TOLERANCE_PP+1e-12:
     failures.append(name+": unsafe estimate was released")
   output.append({"checkpoint_pct":frame["threshold_pct"],
                  "decision":safe["status"],"reason":safe.get("reason"),
                  "shift_pp":safe.get("max_zone_removal_shift_pp"),
                  "winner_flip":safe.get("single_zone_winner_flip"),
                  "v6_estimate_pct":100*base["estimate_a"],
                  "released_estimate_pct":None if safe["estimate_a"] is None else 100*safe["estimate_a"]})
  results.append({"case":name,"checkpoints":len(d["checkpoints"]),"released":len(safe_errors),
                  "abstentions":len(d["checkpoints"])-len(safe_errors),
                  "release_pct":100*len(safe_errors)/len(d["checkpoints"]),
                  "reason_counts":reasons,"max_shift_among_released_pp":max_observed_shift,
                  "mae_unrestricted_pp":statistics.mean(unfiltered_errors) if unfiltered_errors else None,
                  "mae_selected_only_pp":statistics.mean(safe_errors) if safe_errors else None,
                  "first_checkpoint_released":bool(output and output[0]["decision"]=="ESTIMATED"),
                  "checkpoints_detail":output})
 result={"version":"V6 operational conservative option",
         "policy":"abstain if removing one observed zone changes predicted share >1pp or winner, or makes ratio unidentified",
         "policy_tolerance_pp":SHIFT_TOLERANCE_PP,
         "checks":checks,"failures":failures,
         "engineering_policy_passed":not failures,
         "predictive_certification":False,
         "cases":results,
         "warnings":["MAE of released subset suffers selection bias and is not model accuracy.",
                     "The policy was constructed after seeing development cases.",
                     "Zone removal simulates missing valid votes only, not audited real-time snapshots.",
                     "The policy does not ensure correct results under multiple missing zones or corrupted final votes."]}
 (ROOT/"resultado_politica_estabilidade_v6.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"checks":checks,"failures":len(failures),
                    "policy_passed":not failures,
                    "cases":[{k:v for k,v in c.items() if k!="checkpoints_detail"} for c in results]},ensure_ascii=False),flush=True)
 if failures:raise SystemExit("V6 stability release gate FAILED")
if __name__=="__main__":run()
