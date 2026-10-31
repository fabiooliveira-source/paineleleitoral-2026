"""Development-only historical replay V7 vs frozen V6, V4 and raw baseline.

The 15 municipal results were disclosed before designing V7.
NEVER call this an independent external validation. Report ALL failures.
"""
import hashlib,json,pathlib,statistics
from preditor_v7_experimental import predict_v7
from preditor_v6_guardado import predict_v6_guarded
from preditor_v4_guardado import predict_guarded
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"
PRIMARY=set(range(5,100,5))

def score(points):
    vals=[x["error_pp"] for x in points if x["error_pp"] is not None]
    wrong=[x["pct"] for x in points if x["winner_correct"] is False]
    return {
        "n":len(vals),"total":len(points),
        "abstentions":len(points)-len(vals),
        "mae_pp":statistics.mean(abs(z) for z in vals) if vals else None,
        "max_abs_pp":max(abs(z) for z in vals) if vals else None,
        "bias_pp":statistics.mean(vals) if vals else None,
        "winner_wrong":wrong,
        "winner_correct_5":points[0]["winner_correct"] if points else None
    }
def run():
    lock=json.loads(LOCK.read_text())
    reports=[]
    for uf,meta in lock["states"].items():
        p=DATA/(uf+"_checkpoints_1_100.json")
        assert hashlib.sha256(p.read_bytes()).hexdigest()==meta["input_sha256"],"source replaced"
        d=json.loads(p.read_text());truth=d["target_a"]
        prev=None
        main={key:[] for key in ("v7","v6","v4","raw")}
        full=[]
        for frame in d["checkpoints"]:
            pct=frame["threshold_pct"];c=frame["current"];ref=d["reference"];ledger=frame["ledger"]
            models={
                "v7":predict_v7(c,ref,ledger,prev),
                "v6":predict_v6_guarded(c,ref,ledger,prev),
                "v4":predict_guarded(c,ref,ledger,prev)
            }
            if models["v7"]["status"] not in ("ESTIMATED","CLOSED"):
                if models["v7"]["estimate_a"] is not None:
                    raise AssertionError("V7 FAIL-OPEN "+uf+" "+str(pct))
            else:
                assert models["v7"]["probability"] is None
                assert models["v7"]["lower_a"]-1e-12<=models["v7"]["estimate_a"]<=models["v7"]["upper_a"]+1e-12
            if pct==100:
                assert models["v7"]["status"]=="CLOSED"
                assert abs(models["v7"]["estimate_a"]-truth)<1e-12
            total=c["votes_a"]+c["votes_b"]
            raw=c["votes_a"]/total if total else None
            estimates={k:z["estimate_a"] for k,z in models.items()}|{"raw":raw}
            entry={"pct":pct,"utc_cutoff":c["timestamp"],
                   "estimated_a_pct":{k:100*v if v is not None else None for k,v in estimates.items()},
                   "status":{k:z["status"] for k,z in models.items()},
                   "v7_weak_zone_count":models["v7"].get("zone_count_weak"),
                   "v7_prior_coverage":models["v7"].get("first_round_coverage")}
            full.append(entry)
            if pct in PRIMARY:
                for k,value in estimates.items():
                    main[k].append({
                        "pct":pct,"error_pp":100*(value-truth) if value is not None else None,
                        "winner_correct":((value>.5)==(truth>.5)) if value is not None and value!=.5 else None
                    })
            if models["v7"]["status"] in ("ESTIMATED","CLOSED"):
                prev=c
        metrics={k:score(series) for k,series in main.items()}
        reports.append({
            "city":meta["city"],"uf":uf,"source_hash":meta["input_sha256"],
            "primary_metrics":metrics,
            "v7_improves_mae_over_v6":metrics["v7"]["mae_pp"]<metrics["v6"]["mae_pp"],
            "v7_improves_mae_over_raw":metrics["v7"]["mae_pp"]<metrics["raw"]["mae_pp"],
            "v7_5pct_correct":metrics["v7"]["winner_correct_5"],
            "v7_primary_19_estimates":metrics["v7"]["n"]==19,
            "v7_failed_original_test_rules":{
                "mae_le_1pp":metrics["v7"]["mae_pp"]<=1,
                "mae_le_raw":metrics["v7"]["mae_pp"]<=metrics["raw"]["mae_pp"],
                "max_le_3pp":metrics["v7"]["max_abs_pp"]<=3,
                "max_le_raw":metrics["v7"]["max_abs_pp"]<=metrics["raw"]["max_abs_pp"],
                "winner_correct_at5":metrics["v7"]["winner_correct_5"] is True,
                "all_19_estimates":metrics["v7"]["n"]==19},
            "checkpoints":full})
        print(json.dumps({"city":meta["city"],"uf":uf,
                          "v7":metrics["v7"],"v6":metrics["v6"],"raw":metrics["raw"]},ensure_ascii=False),flush=True)
    passed=sum(all(c["v7_failed_original_test_rules"].values()) for c in reports)
    out={
        "status":"V7_RETROSPECTIVE_DEVELOPMENT_BENCHMARK_NOT_EXTERNAL_VALIDATION",
        "cases":reports,
        "n_cities":len(reports),"n_pass_original_subset_rules":passed,
        "n_improve_v6":sum(c["v7_improves_mae_over_v6"] for c in reports),
        "n_improve_raw":sum(c["v7_improves_mae_over_raw"] for c in reports),
        "n_5pct_correct":sum(c["v7_5pct_correct"] is True for c in reports),
        "n_19_estimates":sum(c["v7_primary_19_estimates"] for c in reports),
        "full_certification":False,
        "limitations":["These 15 were used to diagnose V6 and hence are contaminated as V7 holdout.",
                       "No model parameter tuning is conducted by this script.",
                       "Provisional leader calls are NOT statistically calibrated win probabilities.",
                       "Reconstructed clocks are NOT authenticated public availability timestamps."]}
    dest=DATA/"resultado_v7_desenvolvimento_15_cidades.json"
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="cases"},ensure_ascii=False),flush=True)
if __name__=="__main__":run()
