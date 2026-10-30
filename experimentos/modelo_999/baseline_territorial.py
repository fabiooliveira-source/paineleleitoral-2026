"""Baseline causal de projeção territorial, sem dados futuros nos atributos.
Entrada CSV: timestamp,uf,municipio,votos_a,votos_b,eleitorado,
base_a,base_b,base_eleitorado. Linhas representam totais ACUMULADOS
observados até timestamp, não valores finais retroativamente atribuídos.
"""
import csv, argparse, collections, datetime, json, math
def parse_time(s): return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
def estimate(rows):
    """Razão histórica corrigida por swing observado; usa somente o snapshot."""
    a=b=0.0; remaining=0.0; observed=0.0
    for r in rows:
        va=float(r["votos_a"]); vb=float(r["votos_b"])
        base_a=float(r["base_a"]);base_b=float(r["base_b"])
        base_total=base_a+base_b
        eligible=float(r["eleitorado"])
        seen=float(r["eleitorado_apurado"])
        if min(va,vb,base_a,base_b,eligible,seen)<0 or seen>eligible:
            raise ValueError("Valores negativos ou eleitorado apurado acima do total")
        observed+=va+vb
        frac=min(1.0,seen/eligible) if eligible else 0.0
        # Sem dados de seções apuradas, não se pode estimar swing local causalmente.
        # Baseline conservador: distribuição histórica para votos ainda não vistos.
        total_future=max(0.0,(va+vb)/frac-(va+vb)) if frac else 0.0
        p=base_a/base_total if base_total else 0.5
        a+=va+total_future*p;b+=vb+total_future*(1-p)
        remaining+=total_future
    return {"percent_a":100*a/(a+b) if a+b else None,
            "percent_b":100*b/(a+b) if a+b else None,
            "observed_votes":observed,"estimated_unobserved_votes":remaining,
            "warning":"Baseline exploratório: extrapolação por cobertura pode ser enviesada; não certifica 99,9%."}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input_csv")
    ap.add_argument("--output",default="projecoes_baseline.json")
    args=ap.parse_args()
    with open(args.input_csv,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"timestamp","uf","municipio","votos_a","votos_b","eleitorado","eleitorado_apurado","base_a","base_b"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Colunas ausentes: "+str(sorted(required-set(reader.fieldnames or []))))
        groups=collections.defaultdict(list)
        for row in reader: groups[row["timestamp"]].append(row)
    result=[]
    for timestamp,rows in sorted(groups.items(),key=lambda x:parse_time(x[0])):
        result.append({"timestamp":timestamp,**estimate(rows)})
    with open(args.output,"w",encoding="utf8") as f:
        json.dump({"status":"EXPERIMENTAL_NAO_CERTIFICADO","snapshots":result},f,ensure_ascii=False,indent=2)
    print("Snapshots processados:",len(result))
if __name__=="__main__":main()
