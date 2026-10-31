"""Audit clocks and temporal provenance in TSE 2024 municipal section results.

This examines full HISTORICAL rows; does not authenticate contemporaneous
public availability and must not be used to retune a frozen predictor.
"""
import collections,csv,datetime as dt,hashlib,io,json,pathlib,statistics,zipfile
from concurrent.futures import ThreadPoolExecutor
from obter_fontes_2024_v41 import download
ROOT=pathlib.Path(__file__).resolve().parent
DATA=ROOT/"microdados2024"
OUT=ROOT/"raio_nacional_v6_2024"
LOCK=ROOT/"congelamento_raio_nacional_v6_2024.json"
def median_or_none(values):
    return statistics.median(values) if values else None
def quantile95(values):
    return sorted(values)[int(.95*(len(values)-1))] if values else None
def parse(value):
    if not value:return None
    try:return dt.datetime.strptime(value,"%d/%m/%Y %H:%M:%S")
    except ValueError:return None
def clock():
    locked=json.loads(LOCK.read_text())
    source=download("detalhe_votacao_secao_2024.zip")
    want=next(iter(locked["states"].values()))["source_sha256"]["detalhe_votacao_secao_2024.zip"]
    if source["sha256"]!=want:raise ValueError("source hash changed")
    group=collections.defaultdict(list)
    members=set()
    missing=collections.Counter()
    headers_by_uf={}
    with zipfile.ZipFile(DATA/"detalhe_votacao_secao_2024.zip") as z:
        for uf,meta in locked["states"].items():
            member=f"detalhe_votacao_secao_2024_{uf}.csv"
            with z.open(member) as raw:
                rows=csv.reader(io.TextIOWrapper(raw,encoding="latin1"),delimiter=";")
                cols=next(rows);ix={k:i for i,k in enumerate(cols)}
                timestamps=[k for k in cols if k.startswith(("DT_","HH_"))]
                headers_by_uf[uf]=timestamps
                col_first="DT_PRIM_TOT_PARCIAL_HOR_TSE"
                late_col=next((k for k in ("DT_ULT_TOT_PARCIAL_HOR_TSE",
                                             "DT_ULT_TOT_HOR_TSE",
                                             "DT_ULT_TOT_PARCIAL") if k in ix),None)
                received=next((k for k in ("DT_RECEBIMENTO_BU_HOR_TSE","DT_RECEBIMENTO_BU_HOR_TRE")
                                  if k in ix),None)
                for r in rows:
                    if r[ix["SG_UF"]]!=uf or r[ix["CD_MUNICIPIO"]].zfill(5)!=meta["tse_code"] or r[ix["CD_CARGO"]]!="11" or r[ix["CD_TIPO_ELEICAO"]]!="2" or r[ix["NR_TURNO"]]!="2":continue
                    first=parse(r[ix[col_first]])
                    last=parse(r[ix[late_col]]) if late_col else None
                    income=parse(r[ix[received]]) if received else None
                    group[uf].append((first,last,income))
    results=[]
    for uf,meta in locked["states"].items():
        rows=group[uf]
        first_missing=sum(x[0] is None for x in rows)
        last_available=[(x[1]-x[0]).total_seconds() for x in rows if x[0] and x[1]]
        after_first=sum(x>0 for x in last_available)
        before_first=sum(x<0 for x in last_available)
        receive_available=[(x[0]-x[2]).total_seconds() for x in rows if x[0] and x[2]]
        row={
            "uf":uf,"name":meta["city"],"sections_found":len(rows),
            "expected_sections":meta["sections"],"first_missing":first_missing,
            "clock_cols":headers_by_uf[uf],
            "has_last_totalization":len(last_available)>0,
            "last_after_first_count":after_first,
            "last_before_first_count":before_first,
            "last_minus_first_max_seconds":max(last_available) if last_available else None,
            "last_minus_first_p95_seconds":quantile95(last_available),
            "last_minus_first_median_seconds":median_or_none(last_available),
            "first_minus_BU_received_median_seconds":median_or_none(receive_available),
            "first_minus_BU_received_p95_seconds":quantile95(receive_available),
            "first_minus_BU_received_negative_count":sum(x<0 for x in receive_available),
            "first_section_time":min((x[0].isoformat() for x in rows if x[0]),default=None),
            "last_section_first_time":max((x[0].isoformat() for x in rows if x[0]),default=None),
        }
        if len(rows)!=meta["sections"] or first_missing:
            raise ValueError("reconstruction missing or impossible first times: "+uf)
        results.append(row)
        print(json.dumps({"uf":uf,"sections":len(rows),
                         "last_after_first":after_first,"last_before_first":before_first,
                         "last_delta_median_seconds":row["last_minus_first_median_seconds"],
                         "receive_first_delta_median":row["first_minus_BU_received_median_seconds"],
                         "fields":headers_by_uf[uf]},ensure_ascii=False),flush=True)
    report={"status":"RETROSPECTIVE_TEMPORAL_SOURCE_AUDIT_ONLY",
            "source_sha256":source["sha256"],
            "cities":results,
            "total_sections":sum(r["sections_found"] for r in results),
            "all_sections_accounted":True,
            "independent_public_availability_verified":False,
            "caveats":["First internal totalization is not proof of public reception.",
                       "Final section voting totals are retrospectively paired with first timestamp.",
                       "A different last timestamp, if present, does not itself prove that votes were revised.",
                       "No model forecasting was performed in this audit."]}
    OUT.mkdir(exist_ok=True)
    (OUT/"relogio_auditoria_15_ufs.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"total_sections":report["total_sections"],
                      "cities":len(results),"status":report["status"]},ensure_ascii=False),flush=True)
if __name__=="__main__":clock()
