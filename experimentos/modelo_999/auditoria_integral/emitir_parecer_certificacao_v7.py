"""Machine-readable certification verdict. Fail closed; never self-sign external review.

Scope: V7 2020 historical tests, 15-city 2024 development, and evidence
available to this repository. The status CERTIFIED is intentionally gated
on externally verifiable evidence; a successful GitHub workflow alone
cannot authenticate public real-time availability or independent review.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_temporal_v7_2020"
PROTOCOL=ROOT/"protocolo_v7_holdout_temporal_2020_v1.json"
LOCK=ROOT/"congelamento_v7_holdout_temporal_2020.json"
RESULTS=DATA/"resultado_v7_holdout_temporal_2020.json"
OUTPUT=DATA/"parecer_certificacao_integral_v7.json"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verdict():
    protocol=json.loads(PROTOCOL.read_text())
    result=json.loads(RESULTS.read_text())
    lock=json.loads(LOCK.read_text())
    if len(protocol["cases"])!=18:
        raise ValueError("preregistered cities missing")
    if digest(PROTOCOL)!=lock["protocol_sha256"]:
        raise ValueError("preregistration changed")
    if result["cases_total"]!=18 or len(result["cases"])!=18:
        raise ValueError("holdout reporting incomplete")
    if {c["uf"] for c in result["cases"]}!={c["uf"] for c in protocol["cases"]}:
        raise ValueError("not all 18 preregistered cases reported")
    if result["cases_passed"]!=sum(x["passed_all"] for x in result["cases"]):
        raise ValueError("contradictory gate arithmetic")
    if result.get("integral_certification") is not False:
        raise ValueError("historical evaluator attempted certification")
    model_path=ROOT/protocol["model_path"]
    sha=subprocess.check_output(["git","hash-object",str(model_path)],text=True).strip()
    if sha!=protocol["model_git_blob_sha1"]:
        raise ValueError("candidate model code modified after frozen protocol")
    all_inputs_match=True
    for c in protocol["cases"]:
        uf=c["uf"]
        name=DATA/(uf+"_checkpoints_1_100.json")
        record=DATA/(uf+"_manifest.json")
        if not name.is_file() or not record.is_file():
            all_inputs_match=False
            continue
        expected=lock["states"][uf]
        if digest(name)!=expected["input_sha256"] or digest(record)!=expected["manifest_sha256"]:
            all_inputs_match=False
    checks=[
        {"code":"A","name":"TSE dataset integrity, all 18 election cases",
         "passed":all_inputs_match,"reason":"Exact preregistered case SHA-256 and original source traceability" if all_inputs_match else "missing/modified data"},
        {"code":"B","name":"Authenticated *public* incremental timestamps",
         "passed":False,"reason":"Internal first-totalization timestamps reconstructed retrospectively; contemporaneous public release not authenticated"},
        {"code":"C","name":"Model, protocol and data frozen BEFORE validation",
         "passed":True,"reason":"Model Git blob, preregistered protocol SHA256, per-city input SHA256 match"},
        {"code":"D","name":"Independent engineering consistency and adversarial checks",
         "passed":False,"reason":"A successful development V7 adversarial run exists, but independent formal external reproduction and full release gate not yet established"},
        {"code":"E","name":"Preregistered holdout passed all 18/18 cases",
         "passed":result["strict_all_cases_gate_passed"] and result["cases_passed"]==18,
         "reason":"2020 benchmark pass count: %d/18" % result["cases_passed"]},
        {"code":"F","name":"Report comparison with frozen V4/V6 and raw observed baseline",
         "passed":all(all(k in row["metrics"] for k in ("v7","v6","v4","raw")) for row in result["cases"]),
         "reason":"All baselines included per election"},
        {"code":"G","name":"Real documented feed delays, revisions and territorial stress",
         "passed":False,"reason":"Only retrospective time assumption and synthetic perturbation; no verified public live feed/revisions"},
        {"code":"H","name":"Independent statistical reliability and calibrated winner confidence",
         "passed":False,"reason":"No validated predictive confidence calibration; checkpoints correlated by election"},
        {"code":"I","name":"External independent auditor signed assessment",
         "passed":False,"reason":"No signed third-party independent replication or report"},
        {"code":"J","name":"Pre-registered prospective election-night validation",
         "passed":False,"reason":"No independently timestamped prospective public snapshots compared against final truth"}
    ]
    earned=sum(z["passed"] for z in checks)
    # A certificate that cannot be evidenced must never be minted.
    status="NOT_CERTIFIED"
    report={
        "status":status,
        "verified_as_of_utc":datetime.now(timezone.utc).isoformat(),
        "version":"V7 experimental, NOT certified",
        "branch":"experimento/modelo-territorial-999",
        "code_blob_sha1":sha,
        "holdout_data_source_run":lock["data_only_run_id"],
        "holdout_test_cases":result["cases_total"],
        "holdout_passed_cases":result["cases_passed"],
        "holdout_primary_checkpoints":result["primary_checkpoints"],
        "holdout_all_checkpoints":result["diagnostic_checkpoints"],
        "engineering_and_science_checklist_passed":earned,
        "checklist_total":len(checks),
        "checklist_completion_percentage":100*earned/len(checks),
        "confidence_in_correct_winner_probability":None,
        "is_100_percent_accuracy_claim_valid":False,
        "is_integral_certification":False,
        "gates":checks,
        "warnings":[
          "Checklist completion ratio is NOT prediction accuracy or probability of correct winner.",
          "The 2020 test timeline is reconstructed from 2020 TSE final section data.",
          "A 100% checkpoint result is final tally reconciliation, not forecast accuracy.",
          "External independent audit, prospective public snapshots and calibration are absent.",
          "Do not reinterpret any failed case as a passing result."]
    }
    DATA.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":status,"holdout_cases_passed":result["cases_passed"],
                      "holdout_total":result["cases_total"],
                      "requirements_met":earned,"requirements_total":len(checks),
                      "checklist_percent":report["checklist_completion_percentage"],
                      "confidence_pct":None},ensure_ascii=False),flush=True)
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--require-certification",action="store_true",
                        help="Fail the CI if full certification was not evidenced")
    args=parser.parse_args()
    report=verdict()
    if args.require_certification and report["status"]!="CERTIFIED":
        raise SystemExit("CERTIFICATION BLOCKED: independent/prospective gates not satisfied.")
