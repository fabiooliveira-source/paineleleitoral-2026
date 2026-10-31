"""Data-only TSE 2024 broad-holdout preparation. NEVER imports forecasting code.

City selection is preregistered by exact name/UF; candidate identities are
derived solely from the distinct 2T ballot numbers, sorted numerically,
never from their vote totals. Internal 1st-totalization timestamps are
retrospective assumptions, NOT authentic public real-time snapshots.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import re
import unicodedata
import urllib.request
import zipfile

ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"microdados2024"
OUT=ROOT/"raio_nacional_v6_2024"
PROTOCOL=ROOT/"protocolo_raio_nacional_v6_2024_v1.json"
TZ=dt.timezone(dt.timedelta(hours=-3))

def normalized(name):
    value=unicodedata.normalize("NFKD",name)
    return re.sub(r"\s+"," ", "".join(c for c in value if not unicodedata.combining(c)).upper().strip())

def hash_file(p):
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def official_archive(name):
    DATA.mkdir(parents=True,exist_ok=True)
    p=DATA/name
    if not p.is_file():
        typ="detalhe_votacao_secao" if name.startswith("detalhe") else "votacao_secao"
        url="https://cdn.tse.jus.br/estatistica/sead/odsele/"+typ+"/"+name
        partial=p.with_name(p.name+".partial")
        if partial.is_file():partial.unlink()
        with urllib.request.urlopen(url,timeout=90) as src,partial.open("wb") as fh:
            for chunk in iter(lambda:src.read(1024*1024),b""):
                fh.write(chunk)
        partial.replace(p)
    with zipfile.ZipFile(p) as z:
        bad=z.testzip()
        if bad is not None:raise ValueError("CRC failure: "+name+" / "+bad)
    return {"name":name,"sha256":hash_file(p),"bytes":p.stat().st_size,
            "origin":"https://cdn.tse.jus.br/estatistica/sead/odsele/"+
              ("detalhe_votacao_secao" if name.startswith("detalhe") else "votacao_secao")+"/"+name}

def read_rows(archive,member):
    with zipfile.ZipFile(archive) as z,z.open(member) as f:
        rows=csv.reader(io.TextIOWrapper(f,encoding="latin1"),delimiter=";")
        header=next(rows)
        ix={col:index for index,col in enumerate(header)}
        for row in rows:yield row,ix

def section_key(r,ix):
    return (r[ix["SG_UF"]],r[ix["CD_MUNICIPIO"]].zfill(5),
            str(int(r[ix["NR_ZONA"]])),str(int(r[ix["NR_SECAO"]])))

def select(r,ix,uf,city):
    for col in ("NM_MUNICIPIO","SG_UF","CD_CARGO","CD_TIPO_ELEICAO","NR_TURNO"):
        if col not in ix:raise ValueError("missing official field "+col)
    return (r[ix["SG_UF"]]==uf and
            normalized(r[ix["NM_MUNICIPIO"]])==normalized(city) and
            r[ix["CD_CARGO"]]=="11" and
            r[ix["CD_TIPO_ELEICAO"]]=="2" and
            r[ix["NR_TURNO"]] in ("1","2"))

def prepare(uf):
    p=json.loads(PROTOCOL.read_text())
    targets=[c for c in p["cities"] if c["uf"]==uf]
    if len(targets)!=1:raise ValueError("Expected exactly one preregistered city in "+uf)
    target=targets[0]
    name=target["name"]
    detail_archive="detalhe_votacao_secao_2024.zip"
    votes_archive="votacao_secao_2024_"+uf+".zip"
    source_manifest=[official_archive(detail_archive),official_archive(votes_archive)]
    first=set();second={};city_codes=set()
    for row,ix in read_rows(DATA/detail_archive,"detalhe_votacao_secao_2024_"+uf+".csv"):
        if not select(row,ix,uf,name):continue
        key=section_key(row,ix);city_codes.add(key[1])
        turn=row[ix["NR_TURNO"]]
        if turn=="1":
            if key in first:raise ValueError("duplicate 1T section "+str(key))
            first.add(key)
        elif turn=="2":
            if key in second:raise ValueError("duplicate 2T section "+str(key))
            second[key]={
                "nominal":int(row[ix["QT_VOTOS_NOMINAIS"]]),
                "blank":int(row[ix["QT_VOTOS_BRANCOS"]]),
                "null":int(row[ix["QT_VOTOS_NULOS"]]),
                "electorate":int(row[ix["QT_APTOS"]]),
                "first_totalization":row[ix["DT_PRIM_TOT_PARCIAL_HOR_TSE"]]}
    if len(city_codes)!=1 or not first or not second:
        raise ValueError("Selected city not identified uniquely in official details: "+str(city_codes))
    code=next(iter(city_codes))
    removed_first=first-set(second)
    new_second=set(second)-first
    if removed_first or new_second:
        raise ValueError("SECTION_MISMATCH "+name+" 1T_ONLY="+str(len(removed_first))+
                         " 2T_ONLY="+str(len(new_second))+"; block, do not impute")
    first_votes=collections.defaultdict(lambda:collections.defaultdict(int))
    second_votes=collections.defaultdict(lambda:collections.defaultdict(int))
    candidates=set();seen=set()
    for row,ix in read_rows(DATA/votes_archive,"votacao_secao_2024_"+uf+".csv"):
        if not select(row,ix,uf,name):continue
        key=section_key(row,ix)
        turn=row[ix["NR_TURNO"]]
        cand=row[ix["NR_VOTAVEL"]]
        amount=int(row[ix["QT_VOTOS"]])
        if amount<0:raise ValueError("negative votes "+str(key))
        identifier=(turn,key,cand)
        if identifier in seen:raise ValueError("duplicate candidate record "+str(identifier))
        seen.add(identifier)
        if turn=="1":
            first_votes[key][cand]=amount
        else:
            second_votes[key][cand]=amount
            if cand not in ("95","96"):
                candidates.add(cand)
    if len(candidates)!=2:raise ValueError("expected 2 second-round candidate numbers: "+repr(candidates))
    a,b=sorted(candidates,key=lambda value:int(value))
    if any(k not in second for k in second_votes):
        raise ValueError("2T votes without 2T detail")
    zones=collections.defaultdict(lambda:[0,0])
    for key in first:
        values=first_votes[key]
        zones[key[2]][0]+=values.get(a,0)
        zones[key[2]][1]+=values.get(b,0)
    event_list=[];final=[0,0,0,0];total_electorate=0
    final_times=collections.Counter()
    for key,detail in second.items():
        values=second_votes.get(key,{})
        ballot=[values.get(candidate,0) for candidate in (a,b,"95","96")]
        if [ballot[0]+ballot[1],ballot[2],ballot[3]]!=[
            detail["nominal"],detail["blank"],detail["null"]]:
            raise ValueError("2T ballot categories not reconciled: "+str(key))
        if sum(ballot)>detail["electorate"]:
            raise ValueError("more votes than eligible: "+str(key))
        total_electorate+=detail["electorate"]
        for i,v in enumerate(ballot):final[i]+=v
        try:t=dt.datetime.strptime(detail["first_totalization"],"%d/%m/%Y %H:%M:%S")
        except ValueError as e:
            raise ValueError("bad first section totalization date: "+str(key)) from e
        final_times[t.date().isoformat()]+=1
        v1=[first_votes[key].get(candidate,0) for candidate in (a,b)]
        event_list.append((t,key,ballot,detail["electorate"],v1))
    event_list.sort(key=lambda event:(event[0],event[1]))
    n=len(event_list)
    requirements={x:math.ceil(n*x/100) for x in range(1,101)}
    ref={z:{"votes_a":v[0],"votes_b":v[1],"available_at":"2024-10-26T00:00:00-03:00"}
         for z,v in sorted(zones.items())}
    strata={z:[0,0,0,0] for z in zones}
    current=[0,0,0,0]
    counted=0;idx=0;next_pct=1;records=[]
    while idx<n:
        time=event_list[idx][0]
        while idx<n and event_list[idx][0]==time:
            _,key,ballot,aptos,v1=event_list[idx]
            accum=strata[key[2]]
            for i,x in enumerate((ballot[0],ballot[1],v1[0],v1[1])):accum[i]+=x
            for i,x in enumerate(ballot):current[i]+=x
            counted+=aptos;idx+=1
        timestamp=time.replace(tzinfo=TZ).isoformat()
        while next_pct<=100 and idx>=requirements[next_pct]:
            snapshot={"timestamp":timestamp,"available_at":timestamp,
                      "votes_a":current[0],"votes_b":current[1],
                      "electorate_total":total_electorate,"electorate_counted":counted}
            ledger=[{"scope":z,"timestamp":timestamp,"available_at":timestamp,
                     "votes_a":r[0],"votes_b":r[1],
                     "matched_first_a":r[2],"matched_first_b":r[3]}
                    for z,r in sorted(strata.items())]
            records.append({"threshold_pct":next_pct,"sections_total":n,
                            "sections_counted":idx,"sections_fraction":idx/n,
                            "totalization_time":timestamp,
                            "current":snapshot,"ledger":ledger})
            next_pct+=1
    if len(records)!=100 or counted!=total_electorate or current!=final:
        raise ValueError("reconstruction reconciliation failure "+name)
    artifact={"year":2024,"config":{"name":name,"uf":uf,"region":target["region"],"municipality":code,
                     "candidate_a":a,"candidate_b":b},
              "reference":ref,"checkpoints":records,
              "target_a":final[0]/(final[0]+final[1]),
              "final_votes":{"candidate_a":final[0],"candidate_b":final[1],
                             "blank":final[2],"null":final[3]},
              "availability_is_assumed":True,
              "official_public_snapshot_authenticated":False,
              "first_round_reference_retrospective":True,
              "source_sha256":{r["name"]:r["sha256"] for r in source_manifest}}
    OUT.mkdir(parents=True,exist_ok=True)
    dest=OUT/(uf+"_checkpoints_1_100.json")
    dest.write_text(json.dumps(artifact,ensure_ascii=False,separators=(",",":"))+"\n")
    result={"city":name,"uf":uf,"region":target["region"],"tse_code":code,
            "candidate_a":a,"candidate_b":b,"sections":n,
            "zones":len(zones),"checkpoint_count":len(records),
            "unique_checkpoint_times":len({r["totalization_time"] for r in records}),
            "electorate_total":total_electorate,"final_votes":artifact["final_votes"],
            "input_sha256":hash_file(dest),
            "input_file":dest.name,"sources":source_manifest,
            "latest_totalization":records[-1]["totalization_time"],
            "totalization_days":dict(final_times),
            "integrity_status":"DATA_ONLY_PREPARED_NO_MODEL_SCORING"}
    (OUT/(uf+"_manifest.json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":"PREPARED_NO_PREDICTIONS",**result},ensure_ascii=False),flush=True)

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--uf",required=True)
    args=cli.parse_args()
    prepare(args.uf)
