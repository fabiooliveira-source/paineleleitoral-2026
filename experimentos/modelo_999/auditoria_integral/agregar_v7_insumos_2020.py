"""Data-only 2020 18-UF aggregation: produce hash lock BEFORE model execution."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"raio_temporal_v7_2020"
PROTOCOL=ROOT/"protocolo_v7_holdout_temporal_2020_v1.json"
RUN_ID=41252574828

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def run():
    p=json.loads(PROTOCOL.read_text())
    if len(p["cases"])!=18 or not p["model_parameter_tuning_prohibited"]:
        raise RuntimeError("preregistered roster changed")
    states={}
    for c in p["cases"]:
        uf=c["uf"]
        path=DATA/(uf+"_checkpoints_1_100.json")
        mp=DATA/(uf+"_manifest.json")
        if not path.is_file() or not mp.is_file():
            raise RuntimeError("Missing data-only source: "+uf)
        rec=json.loads(mp.read_text())
        doc=json.loads(path.read_text())
        detail={x["name"]:x["sha256"] for x in rec["sources"]}
        if detail.get("detalhe_votacao_secao_2020.zip")!=p["known_tse_detail_zip_sha256"]:
            raise RuntimeError("2020 TSE source drift "+uf)
        if rec["city"]!=c["city"] or rec["uf"]!=uf or rec["region"]!=c["region"]:
            raise RuntimeError("City identity changed "+uf)
        if rec["input_sha256"]!=sha(path):
            raise RuntimeError("Checkpoint SHA drift "+uf)
        if doc["config"]["municipality"]!=rec["tse_code"]:
            raise RuntimeError("Municipality code changed "+uf)
        if len(doc["checkpoints"])!=100:
            raise RuntimeError("Wrong checkpoint count "+uf)
        if doc["config"]["candidate_a"]!=rec["candidate_a"] or doc["config"]["candidate_b"]!=rec["candidate_b"]:
            raise RuntimeError("Candidate roster modified "+uf)
        states[uf]={
            "city":c["city"],"region":c["region"],"tse_code":rec["tse_code"],
            "input_sha256":sha(path),"manifest_sha256":sha(mp),
            "source_sha256":detail,"candidate_a":rec["candidate_a"],
            "candidate_b":rec["candidate_b"],
            "zones":rec["zones"],"sections":rec["sections"],
            "checkpoints":100}
        print(json.dumps({"uf":uf,"city":c["city"],"source_hash":states[uf]["input_sha256"],
                          "sections":rec["sections"]}),flush=True)
    locked={"status":"FROZEN_PRE_V7_2020_HOLDOUT_SCORE",
            "data_only_run_id":RUN_ID,
            "protocol_sha256":sha(PROTOCOL),"model_git_blob_sha1":p["model_git_blob_sha1"],
            "total_cases":len(states),"states":states,
            "warning":"Neither model scoring nor winner accuracy was executed in this data-only stage."}
    DATA.mkdir(exist_ok=True)
    (DATA/"proposed_hash_lock_before_scoring.json").write_text(json.dumps(locked,ensure_ascii=False,indent=2)+"\n")
    print("PROPOSED_V7_2020_HASH_LOCK="+json.dumps(locked,ensure_ascii=False,separators=(",",":")),flush=True)
if __name__=="__main__":run()
