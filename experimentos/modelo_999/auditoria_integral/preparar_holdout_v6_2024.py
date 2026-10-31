"""Build previously-unseen municipal holdout replays from pinned official TSE ZIPs.

The 2T public-timeline is NOT authenticated: first internal section
totalization time is used as a retrospective availability assumption.
The predictor is NEVER called here; model evaluation is a separate step.
"""
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "microdados2024"
OUT = ROOT / "holdout_v6_2024"
PROTOCOL = ROOT / "protocolo_holdout_v6_2024_v1.json"
TZ = dt.timezone(dt.timedelta(hours=-3))

def read(archive, member):
    with zipfile.ZipFile(archive) as z, z.open(member) as f:
        r = csv.reader(io.TextIOWrapper(f, encoding="latin1"), delimiter=";")
        headers = next(r)
        ix = {k:i for i,k in enumerate(headers)}
        for values in r:
            yield values, ix

def key_for(r, ix):
    return (r[ix["SG_UF"]],r[ix["CD_MUNICIPIO"]].zfill(5),
            str(int(r[ix["NR_ZONA"]])),str(int(r[ix["NR_SECAO"]])))

def select(r, ix, cases):
    if r[ix["CD_CARGO"]] != "11" or r[ix["CD_TIPO_ELEICAO"]] != "2":
        return None
    code = r[ix["CD_MUNICIPIO"]].zfill(5)
    return code if code in cases else None

def main():
    protocol=json.loads(PROTOCOL.read_text())
    cases={c["code"]:c for c in protocol["external_cases"]}
    assert len(cases)==5 and protocol["v6_cover_threshold"]==0.20
    for name,want in protocol["source_archives"].items():
        path=DATA/name
        if not path.is_file():raise FileNotFoundError(str(path))
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=want:raise ValueError("Unpinned TSE source "+name+" "+digest)
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:raise ValueError("TSE archive CRC failure "+name)
    first={code:set() for code in cases}
    second={code:{} for code in cases}
    raw_detail=DATA/"detalhe_votacao_secao_2024.zip"
    for uf in sorted({c["uf"] for c in cases.values()}):
        member="detalhe_votacao_secao_2024_"+uf+".csv"
        n=0
        for r,ix in read(raw_detail,member):
            code=select(r,ix,cases)
            if code is None:continue
            k=key_for(r,ix)
            turn=r[ix["NR_TURNO"]]
            if turn=="1":
                if k in first[code]:raise ValueError("duplicate first-turn section "+str(k))
                first[code].add(k)
            elif turn=="2":
                if k in second[code]:raise ValueError("duplicate second-turn section "+str(k))
                second[code][k]={
                    "nominal":int(r[ix["QT_VOTOS_NOMINAIS"]]),
                    "blank":int(r[ix["QT_VOTOS_BRANCOS"]]),
                    "null":int(r[ix["QT_VOTOS_NULOS"]]),
                    "electorate":int(r[ix["QT_APTOS"]]),
                    "first_totalization":r[ix["DT_PRIM_TOT_PARCIAL_HOR_TSE"]]}
            n+=1
        print(json.dumps({"step":"detail","uf":uf,"selected_sections":n}),flush=True)

    votes_first={code:collections.defaultdict(lambda:[0,0]) for code in cases}
    votes_second={code:collections.defaultdict(lambda:[0,0,0,0]) for code in cases}
    seen=set()
    for uf in sorted({c["uf"] for c in cases.values()}):
        archive=DATA/("votacao_secao_2024_"+uf+".zip")
        member="votacao_secao_2024_"+uf+".csv"
        n=0
        for r,ix in read(archive,member):
            code=select(r,ix,cases)
            if code is None:continue
            k=key_for(r,ix)
            turn=r[ix["NR_TURNO"]]
            candidate=r[ix["NR_VOTAVEL"]]
            a,b=cases[code]["candidate_a"],cases[code]["candidate_b"]
            n_votes=int(r[ix["QT_VOTOS"]])
            if n_votes<0:raise ValueError("negative votes "+str(k))
            if turn=="1" and candidate in (a,b):
                identity=(turn,k,candidate)
                if identity in seen:raise ValueError("duplicate first candidate "+str(identity))
                seen.add(identity)
                votes_first[code][k][0 if candidate==a else 1]+=n_votes
            if turn=="2":
                identity=(turn,k,candidate)
                if identity in seen:raise ValueError("duplicate second candidate "+str(identity))
                seen.add(identity)
                if candidate not in (a,b,"95","96"):
                    if n_votes:raise ValueError("unexpected 2T candidate "+str(identity))
                    continue
                i={a:0,b:1,"95":2,"96":3}[candidate]
                votes_second[code][k][i]+=n_votes
            n+=1
        print(json.dumps({"step":"votes","uf":uf,"selected_records":n}),flush=True)

    outputs=[]
    OUT.mkdir(exist_ok=True)
    for code,config in cases.items():
        input_first=first[code]
        input_second=second[code]
        if not input_first or not input_second:
            raise ValueError("missing round for city "+code)
        unpaired=set(input_second)-input_first
        removed=input_first-set(input_second)
        if unpaired or removed:
            raise ValueError("section mismatch "+code+" 2T_unpaired="+str(len(unpaired))+
                             " 1T_unmatched="+str(len(removed)))
        totals=collections.defaultdict(lambda:[0,0])
        for k in input_first:
            z=k[2];a,b=votes_first[code].get(k,[0,0])
            totals[z][0]+=a;totals[z][1]+=b
        for k in votes_second[code]:
            if k not in input_second:raise ValueError("vote row without 2T detail "+str(k))
        events=[]
        final=[0,0,0,0]
        electorate_total=0
        late=0
        for k,record in input_second.items():
            va,vb,blank,null=votes_second[code].get(k,[0,0,0,0])
            if [va+vb,blank,null]!=[record["nominal"],record["blank"],record["null"]]:
                raise ValueError("section vote categories fail "+str(k))
            if sum([va,vb,blank,null])>record["electorate"]:
                raise ValueError("votes exceed registered electorate "+str(k))
            electorate_total+=record["electorate"]
            for i,v in enumerate((va,vb,blank,null)):final[i]+=v
            clock=record["first_totalization"]
            try:t=dt.datetime.strptime(clock,"%d/%m/%Y %H:%M:%S")
            except ValueError as e:raise ValueError("missing section time "+str(k)+" "+clock) from e
            if t>dt.datetime(2024,10,28,23,59,59):late+=1
            v1a,v1b=votes_first[code].get(k,[0,0])
            events.append((t,k,(va,vb,blank,null),record["electorate"],(v1a,v1b)))
        events.sort(key=lambda v:(v[0],v[1]))
        n_sections=len(events)
        milestones=list(range(1,101))
        deadline={pct:math.ceil(n_sections*pct/100) for pct in milestones}
        reference={scope:{"votes_a":val[0],"votes_b":val[1],
                          "available_at":"2024-10-26T00:00:00-03:00"}
                   for scope,val in sorted(totals.items())}
        aggregate={scope:[0,0,0,0] for scope in totals}
        now=[0,0,0,0]
        counted_electorate=0
        pos=0
        checkpoints=[]
        idx=0
        while idx<n_sections:
            t=events[idx][0]
            while idx<n_sections and events[idx][0]==t:
                _,k,(va,vb,blank,null),aptos,(v1a,v1b)=events[idx]
                z=k[2]
                accum=aggregate[z]
                for i,v in enumerate((va,vb,v1a,v1b)):accum[i]+=v
                for i,v in enumerate((va,vb,blank,null)):now[i]+=v
                counted_electorate+=aptos
                idx+=1
            iso=t.replace(tzinfo=TZ).isoformat()
            while pos<len(milestones) and idx>=deadline[milestones[pos]]:
                pct=milestones[pos]
                current={"timestamp":iso,"available_at":iso,
                         "votes_a":now[0],"votes_b":now[1],
                         "electorate_total":electorate_total,
                         "electorate_counted":counted_electorate}
                ledger=[{"scope":scope,"timestamp":iso,"available_at":iso,
                         "votes_a":v[0],"votes_b":v[1],
                         "matched_first_a":v[2],"matched_first_b":v[3]}
                        for scope,v in sorted(aggregate.items())]
                checkpoints.append({"threshold_pct":pct,
                                    "sections_total":n_sections,
                                    "sections_counted":idx,
                                    "sections_fraction":idx/n_sections,
                                    "totalization_time":iso,
                                    "current":current,"ledger":ledger})
                pos+=1
        if len(checkpoints)!=100:raise ValueError("incomplete 100 checkpoints "+code)
        if now!=final:raise ValueError("temporal final sum mismatch "+code)
        if counted_electorate!=electorate_total:raise ValueError("turnout final mismatch "+code)
        for item in checkpoints:
            if item["sections_counted"]<deadline[item["threshold_pct"]]:
                raise ValueError("checkpoint before threshold")
        doc={
            "year":2024,"config":config,"reference":reference,
            "checkpoints":checkpoints,
            "target_a":final[0]/(final[0]+final[1]),
            "final_votes":{"candidate_a":final[0],"candidate_b":final[1],
                           "blank":final[2],"null":final[3]},
            "scope":"held-out municipality: reconstructed first totalization timestamps",
            "availability_is_assumed":True,
            "official_public_snapshot_authenticated":False,
            "first_round_reference_retrospective":True,
            "source_archives":protocol["source_archives"],
        }
        dest=OUT/(code+"_checkpoints_1_100.json")
        dest.write_text(json.dumps(doc,ensure_ascii=False,separators=(",",":"))+"\n")
        digest=hashlib.sha256(dest.read_bytes()).hexdigest()
        result={
            "city":config["name"],"municipality":code,"uf":config["uf"],
            "sections_1t":len(input_first),"sections_2t":len(input_second),
            "zones":len(totals),"checkpoints":len(checkpoints),
            "electorate_total":electorate_total,"final_votes":doc["final_votes"],
            "late_first_totalizations_after_2024_10_28":late,
            "last_checkpoint_time":checkpoints[-1]["totalization_time"],
            "sha256":digest,"relative_path":str(dest.relative_to(ROOT))}
        outputs.append(result)
        print(json.dumps({"step":"prepared",**result},ensure_ascii=False),flush=True)
    manifest={"status":"FIVE_CASES_PREPARED_WITH_ASSUMED_AVAILABILITY",
              "protocol":"protocolo_holdout_v6_2024_v1.json",
              "sources_verified":list(protocol["source_archives"]),
              "cases":outputs,
              "not_public_realtime_snapshots":True}
    (OUT/"manifesto_reconstrucao.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"status":manifest["status"],"case_count":len(outputs)},ensure_ascii=False),flush=True)

if __name__=="__main__":main()
