#!/usr/bin/env python3
"""Auditoria temporal de totalização; não infere votos individuais.
Uso: python auditar_847s.py parciais.csv secoes.csv --out auditoria_847s.csv
Colunas exigidas em ambos CSVs: timestamp,lula,flavio.
Parciais: totais acumulados. Secoes: incrementos por BU recebido.
Timestamps ISO-8601 com timezone; ordenação cronológica.
"""
import argparse,csv,datetime as dt
from pathlib import Path

def read(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        required={"timestamp","lula","flavio"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: faltam {required-set(reader.fieldnames or [])}")
        rows=[]
        for n,r in enumerate(reader,2):
            t=dt.datetime.fromisoformat(r["timestamp"].replace("Z","+00:00"))
            if t.tzinfo is None: raise ValueError(f"{path}:{n}: timestamp sem fuso")
            a,b=int(r["lula"]),int(r["flavio"])
            if a<0 or b<0: raise ValueError(f"{path}:{n}: voto negativo")
            rows.append((t.astimezone(dt.timezone.utc),a,b))
    return sorted(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("parciais");p.add_argument("secoes")
    p.add_argument("--out",default="auditoria_847s.csv")
    p.add_argument("--tolerancia-segundos",type=float,default=0)
    args=p.parse_args()
    par,sec=read(args.parciais),read(args.secoes)
    if args.tolerancia_segundos<0: raise ValueError("Tolerância negativa")
    if len(par)<2 or not sec: raise ValueError("Dados insuficientes")
    for x,y in zip(par,par[1:]):
        if y[0]<=x[0] or y[1]<x[1] or y[2]<x[2]:
            raise ValueError("Parciais não estritamente temporais ou totais decrescentes")
    results=[]
    for start,end in zip(par,par[1:]):
        duration=(end[0]-start[0]).total_seconds()
        if duration>84.7: continue
        delta_l=end[1]-start[1];delta_f=end[2]-start[2]
        low=start[0]-dt.timedelta(seconds=args.tolerancia_segundos)
        high=end[0]+dt.timedelta(seconds=args.tolerancia_segundos)
        in_window=[r for r in sec if low<r[0]<=high]
        sum_l=sum(r[1] for r in in_window);sum_f=sum(r[2] for r in in_window)
        results.append({"inicio_utc":start[0].isoformat(),"fim_utc":end[0].isoformat(),
          "duracao_s":duration,"delta_lula":delta_l,"delta_flavio":delta_f,
          "soma_bu_lula":sum_l,"soma_bu_flavio":sum_f,
          "residuo_lula":delta_l-sum_l,"residuo_flavio":delta_f-sum_f,
          "n_bu":len(in_window),"tolerancia_s":args.tolerancia_segundos})
    if not results: print("Sem pares de parciais separados por até 84,7 s");return
    with open(args.out,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=results[0].keys());w.writeheader();w.writerows(results)
    print(f"{len(results)} intervalos exportados em {args.out}. Resíduos não nulos exigem verificar timestamps, lotes e cobertura da base antes de inferir irregularidade.")
if __name__=="__main__":main()
