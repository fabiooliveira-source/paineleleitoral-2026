"""Fail-closed source-code/input freeze gate for the 2024 V6 three-city benchmark."""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
MANIFEST=pathlib.Path(__file__).resolve().with_name("congelamento_v6_3_cidades.json")

def run():
    lock=json.loads(MANIFEST.read_text())
    assert lock["status"]=="FROZEN_CODE_AND_EXISTING_DATA_NOT_EXTERNAL_CERTIFICATION"
    assert lock["v6_coverage_threshold"]==0.20
    results=[]
    for record in lock["files"]:
        name=record["path"]
        path=ROOT / name
        if not path.is_file():
            raise RuntimeError("Missing frozen file: "+name)
        actual=subprocess.check_output(["git","hash-object","--",str(path)],text=True).strip()
        valid=actual==record["git_blob_sha1"]
        results.append({"path":name,"matched":valid})
        if not valid:
            raise RuntimeError("Frozen file changed: "+name+" expected "+record["git_blob_sha1"]+" got "+actual)
    print(json.dumps({"status":"PASS_FROZEN_DEVELOPMENT_ARTIFACTS",
                      "verified_files":len(results),
                      "all_match":all(x["matched"] for x in results),
                      "not_independent_certification":True},ensure_ascii=False),flush=True)

if __name__=="__main__":
    run()
