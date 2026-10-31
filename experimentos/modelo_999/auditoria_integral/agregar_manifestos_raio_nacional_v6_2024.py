"""Freeze candidate identities and original hashes BEFORE executing V6 on holdout.

This data-only aggregation performs integrity/provenance checks and prints
the dictionary to pin in a separate GitHub commit. It imports no predictor.
"""
import hashlib
import json
import pathlib
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_nacional_v6_2024"
P=ROOT/"protocolo_raio_nacional_v6_2024_v1.json"
DETAIL_PIN="ae879eb09d1ceca9ca05c1b9759a7646800b4efe57ca3d5d7f33f91287bcca3e"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def aggregate():
    protocol=json.loads(P.read_text())
    states={}
    for chosen in protocol["cities"]:
        uf=chosen["uf"]
        f=DATA/(uf+"_checkpoints_1_100.json")
        mp=DATA/(uf+"_manifest.json")
        if not f.exists() or not mp.exists():
            raise RuntimeError("BLOCKED_MISSING_STATE_FILE "+uf)
        result=json.loads(mp.read_text())
        artifact=json.loads(f.read_text())
        if (result["city"]!=chosen["name"] or result["region"]!=chosen["region"]
            or result["uf"]!=uf or artifact["config"]["municipality"]!=result["tse_code"]
            or result["checkpoint_count"]!=100 or len(artifact["checkpoints"])!=100
            or result["input_sha256"]!=digest(f)):
            raise ValueError("STATE_INPUT_IDENTITY_MISMATCH "+uf)
        source={p["name"]:p["sha256"] for p in result["sources"]}
        if source.get("detalhe_votacao_secao_2024.zip")!=DETAIL_PIN:
            raise ValueError("UNEXPECTED_TSE_SOURCE_DETAIL "+uf)
        if len(source)!=2:
            raise ValueError("EXPECTED_TWO_OFFICIAL_ARCHIVES "+uf)
        states[uf]={
            "city":result["city"],"region":result["region"],
            "tse_code":result["tse_code"],
            "input_sha256":result["input_sha256"],
            "manifest_sha256":digest(mp),
            "source_sha256":source,
            "original_source_bytes":{x["name"]:x["bytes"] for x in result["sources"]},
            "candidate_a":result["candidate_a"],
            "candidate_b":result["candidate_b"],
            "sections":result["sections"],
            "zones":result["zones"],
            "checkpoints":100}
        print(json.dumps({"data_checked":uf,
                          "sha256":result["input_sha256"],
                          "candidate_roster":[result["candidate_a"],result["candidate_b"]],
                          "sections":result["sections"],"zones":result["zones"]}),flush=True)
    frozen={
        "status":"FROZEN_PRE_SCORING",
        "protocol_sha256":digest(P),
        "data_preparation_run_id":41250338824,
        "cities":len(states),
        "states":states,
        "warning":"Retrospective historical section snapshots, not observed public real-time data."
    }
    (DATA/"proposed_frozen_manifest.json").write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+"\n")
    print("PROPOSED_FROZEN_MANIFEST_JSON="+json.dumps(frozen,ensure_ascii=False,separators=(",",":")),flush=True)
    print(json.dumps({"prepared_cities":len(states),"all_source_hashes_verified":True,
                      "scoring_executed":False}),flush=True)

if __name__=="__main__":aggregate()
