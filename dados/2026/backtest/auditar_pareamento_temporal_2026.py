"""Audit whether 2026 V7 can be replayed without leaking final section totals.

No retrospective assignment of final per-section vote totals to historical
municipal aggregates is allowed. Produce a machine-readable feasibility audit.
"""
import csv,gzip,json,hashlib,pathlib,collections,datetime
ROOT=pathlib.Path(__file__).resolve().parents[3]
BACK=ROOT/"dados/2026/backtest"
OUT=BACK/"auditoria_pareamento_temporal_2026.json"
def fields_in(o,seen,limit=3000):
    if len(seen)>=limit:return
    if isinstance(o,dict):
        for k,v in o.items():
            seen.add(str(k))
            if isinstance(v,(dict,list)):fields_in(v,seen,limit)
    elif isinstance(o,list):
        for v in o[:6]:fields_in(v,seen,limit)
def walk(o,stats,depth=0):
    if depth>9:return
    if isinstance(o,dict):
        for k,v in o.items():
            key=str(k).lower()
            if any(term in key for term in ('timestamp','horario','horário','recebimento','prim_tot','dt_tot','available_at','updated_at','first_seen','apresentacao')):
                stats[key]+=1
            if isinstance(v,(dict,list)):walk(v,stats,depth+1)
    elif isinstance(o,list):
        for v in o[:6]:walk(v,stats,depth+1)
def main():
    source=BACK/"csv/acervo_2026_2/observacoes_nacional_uf.csv"
    with source.open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    source_fields=set(rows[0])
    result={"status":"AUDITED","source":"2026 GitHub archive",
      "source_csv_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
      "source_fields":sorted(source_fields),"source_rows":len(rows),
      "scopes":sorted(set(r["scope"] for r in rows)),
      "section_archives":[],"raw_snapshot_fields":[],
      "temporal_join_key_verified":False,
      "v7_replay_permitted":False,
      "warning":"Historical aggregate snapshots do not identify exactly which sections were counted at each timestamp. Final section totals cannot be treated as if known at earlier checkpoints."}
    for file in sorted((ROOT/"dados/2026").glob("secoes-*.json.gz")):
        with gzip.open(file,"rt",encoding="utf-8") as f:obj=json.load(f)
        keys=set();fields_in(obj,keys)
        timestamps=collections.Counter();walk(obj,timestamps)
        item={"file":file.name,"bytes":file.stat().st_size,
          "root_type":type(obj).__name__,"root_keys":list(obj)[:12] if isinstance(obj,dict) else [],
          "fields":sorted(keys)[:200],
          "temporal_field_occurrences":dict(timestamps)}
        result["section_archives"].append(item)
    raw=BACK/"json/acervo_2026_2/raw/1_BA.json"
    obj=json.loads(raw.read_text(encoding="utf-8"))
    keys=set();fields_in(obj,keys)
    result["raw_snapshot_fields"]=sorted(keys)[:200]
    result["source_has_section_id"]=any("secao" in x.lower() or "seção" in x.lower() for x in source_fields if x not in ("secoes_contabilizadas",))
    result["section_archives_count"]=len(result["section_archives"])
    result["timestamp_field_candidates"]={x["file"]:x["temporal_field_occurrences"] for x in result["section_archives"] if x["temporal_field_occurrences"]}
    result["missing_critical_information"]=[
      "Timestamp of public availability for each second-round section, tied to its unique UF/municipio/zona/secao key",
      "First-round reference votes from exactly the same counted sections at each checkpoint",
      "Reconciliation between per-section arrival sequence and every archived national/UF/municipal snapshot",
      "Evidence that no future section-level totals were used in earlier checkpoints"
    ]
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"section_archives":len(result["section_archives"]),"source_rows":len(rows),
      "section_temporal_fields":result["timestamp_field_candidates"],
      "v7_replay_permitted":result["v7_replay_permitted"]},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
