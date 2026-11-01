"""Replay 2026 with explicit model eligibility and no hindsight leakage.

Historical BR and UF snapshots from the archived TSE EA20 collector.
The V7 estimator REQUIRES paired section-level 1T/2T ledgers; municipal
or UF snapshots are insufficient. Therefore this script evaluates
observable, time-causal raw-share baseline, and records V7 as BLOCKED,
not a fabricated 2026 V7 score.
"""
import csv
import hashlib
import json
import pathlib
from collections import defaultdict
from datetime import datetime

ROOT=pathlib.Path(__file__).resolve().parent
CSV=ROOT/"csv/acervo_2026_2/observacoes_nacional_uf.csv"
SOURCE=ROOT/"json/acervo_2026_2"
OUT=ROOT/"replay_2026_resultado.json"
FIELDS=("secoes_contabilizadas","eleitores_secoes_contabilizadas","comparecimento","brancos","nulos","votos_13","votos_22")
THRESHOLDS=list(range(5,101,5))
def parse(t):
    x=datetime.fromisoformat(t)
    if x.tzinfo is None:raise ValueError("missing timezone")
    return x
def main():
    manifest=json.loads((SOURCE/"manifest.json").read_text())
    validity=json.loads((SOURCE/"validacao.json").read_text())
    if manifest["source"]!="TSE" or manifest["electionId"]!="2026-2":
        raise ValueError("source or election mismatch")
    if validity["issues"] or validity["uf_sum_minus_national"]!=[0]*7:
        raise ValueError("failed archive reconciliation")
    if validity["national_final"][-2:]!=[64256232,59826041]:
        raise ValueError("final candidate totals changed")
    grouped=defaultdict(list)
    with CSV.open(newline="",encoding="utf-8-sig") as fp:
        for row in csv.DictReader(fp):
            scope=row["scope"]
            if scope != "BR" and (len(scope)!=2 or not scope.isalpha() or row["uf"]!=scope):
                raise ValueError("invalid UF scope: "+scope)
            uf=scope
            if not uf:raise ValueError("missing UF")
            at=parse(row["timestamp"])
            values={k:int(row[k]) for k in FIELDS}
            if min(values.values())<0 or values["votos_13"]+values["votos_22"]+values["brancos"]+values["nulos"]>values["comparecimento"]:
                raise ValueError("invalid votes at "+uf)
            grouped[uf].append((at,row["timestamp"],values))
    if "BR" not in grouped or "ZZ" not in grouped or len(grouped)!=29:
        raise ValueError("BR + 27 UFs + exterior ZZ required; got "+str(len(grouped)))
    final_national=validity["national_final"]
    if grouped["BR"][-1][2]["votos_13"]!=final_national[-2] or grouped["BR"][-1][2]["votos_22"]!=final_national[-1]:
        raise ValueError("national final mismatch")
    results=[]
    for uf,items in sorted(grouped.items(),key=lambda item:(item[0]!='BR',item[0])):
        items.sort(key=lambda r:r[0])
        if len({r[1] for r in items})!=len(items):
            raise ValueError("duplicate timestamps in "+uf)
        final=items[-1][2]
        total=final["secoes_contabilizadas"]
        if not total:raise ValueError("no final sections "+uf)
        target=final["votos_13"]/(final["votos_13"]+final["votos_22"])
        checkpoints=[]
        prev_index=-1
        for threshold in THRESHOLDS:
            eligible=[(i,r) for i,r in enumerate(items) if r[2]["secoes_contabilizadas"]*100>=threshold*total]
            if not eligible:
                checkpoints.append({"threshold_pct":threshold,"status":"NO_SNAPSHOT","v7_status":"BLOCKED_NO_PAIRED_SECTIONS"})
                continue
            i,(at,stamp,record)=eligible[0]
            if i<prev_index:raise ValueError("nonmonotone checkpoint")
            prev_index=i
            valid=record["votos_13"]+record["votos_22"]
            share=record["votos_13"]/valid if valid else None
            checkpoints.append({
                "threshold_pct":threshold,"timestamp":stamp,
                "actual_sections_pct":100*record["secoes_contabilizadas"]/total,
                "raw_observed_share_13":share,
                "raw_observed_error_pp":abs(share-target)*100 if share is not None else None,
                "raw_observed_provisional_leader":"13" if share is not None and share>.5 else "22" if share is not None and share<.5 else None,
                "v7_status":"BLOCKED_NO_PAIRED_SECTIONS",
                "v7_estimate_13":None,
                "v7_probability":None,
                "v7_reason":"EA20 snapshots have no exact section-by-section first/second round matched ledger",
                "source":"2026 historical EA20 archive"
            })
        primary=[z for z in checkpoints if 5<=z["threshold_pct"]<=95 and z.get("raw_observed_error_pp") is not None]
        wrong=sum(z["raw_observed_provisional_leader"]!=("13" if target>.5 else "22") for z in primary)
        results.append({"uf":uf,"final_votes_13":final["votos_13"],"final_votes_22":final["votos_22"],
                        "final_share_13":target,"final_sections":total,"snapshots":len(items),
                        "primary_checkpoints":len(primary),
                        "raw_mae_pp":sum(z["raw_observed_error_pp"] for z in primary)/len(primary) if primary else None,
                        "raw_wrong_leader_checkpoints":wrong,
                        "v7_evaluated_checkpoints":0,
                        "v7_blocked_checkpoints":len(checkpoints),
                        "checkpoints":checkpoints})
    total_primary=sum(z["primary_checkpoints"] for z in results)
    report={
      "status":"HISTORICAL_2026_REPLAY_COMPLETED_V7_NOT_IDENTIFIABLE",
      "model_version":"V7 frozen experimental; no substituted estimator",
      "archive_source":"TSE EA20 collector, archived historical snapshots",
      "archive_manifest_sha256":hashlib.sha256((SOURCE/"manifest.json").read_bytes()).hexdigest(),
      "input_csv_sha256":hashlib.sha256(CSV.read_bytes()).hexdigest(),
      "retrospective_availability_warning":"Archive timestamp alone does not authenticate public release or prevent post-hoc collector changes",
      "checkpoint_policy":"first timestamped snapshot with sections >= 5%,10%,...,100% of final section total; no future snapshots in estimate",
      "national_and_ufs":len(results),
      "checkpoints_requested":len(results)*len(THRESHOLDS),
      "raw_baseline_primary_checkpoints":total_primary,
      "v7_primary_checkpoints_evaluated":0,
      "v7_not_evaluated_reason":"The V7 contract requires section-paired first/second round votes by territorial scope and timestamp. Neither EA20 municipal nor UF snapshots provide that.",
      "certification_2026":False,
      "scopes":results
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"scopes":len(results),
                      "requested":report["checkpoints_requested"],
                      "raw_evaluated":total_primary,"v7_evaluated":0,
                      "national_mae_pp":results[0]["raw_mae_pp"],
                      "archive_manifest_sha256":report["archive_manifest_sha256"]},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
