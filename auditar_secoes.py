"""Auditoria contábil por seção; não infere votos individuais.
Entrada: CSV de seções conciliadas, separador ';'.
Saída: JSON com cobertura e amostras de divergências.
"""
import argparse,json
from pathlib import Path
import pandas as pd
KEY=['uf','codigo_municipio_tse','zona','secao']
FIELDS=['aptos','comparecimento','abstencoes','brancos','nulos']
def auditar(path):
    d=pd.read_csv(path,sep=';',dtype={k:str for k in KEY},low_memory=False)
    required=KEY+[f'{c}_{t}' for t in ('1t','2t') for c in FIELDS]
    missing=sorted(set(required)-set(d.columns))
    if missing:raise ValueError('Colunas ausentes: '+','.join(missing))
    if d.empty:raise ValueError('Base vazia')
    if d[KEY].isna().any().any():raise ValueError('Chaves nulas')
    if d.duplicated(KEY).any():raise ValueError('Chaves duplicadas')
    out={'rows':int(len(d)),'flags':{},'examples':{},'notes':['Flags não são provas de irregularidade; verificar condições e ressalvas oficiais.']}
    for t in ('1t','2t'):
        cols=[f'{c}_{t}' for c in FIELDS]
        n=d[cols].apply(pd.to_numeric,errors='coerce')
        invalid=n.isna().any(axis=1)|n.lt(0).any(axis=1)|n.mod(1).ne(0).any(axis=1)
        masks={
          f'invalid_{t}':invalid,
          f'turnout_balance_{t}':n[f'comparecimento_{t}'].add(n[f'abstencoes_{t}']).ne(n[f'aptos_{t}']),
          f'negative_valid_residual_{t}':n[f'comparecimento_{t}'].sub(n[f'brancos_{t}']).sub(n[f'nulos_{t}']).lt(0),
        }
        for name,mask in masks.items():
            out['flags'][name]=int(mask.sum())
            out['examples'][name]=d.loc[mask,KEY].head(10).to_dict('records')
    return out
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True);ap.add_argument('--saida',default='auditoria_secoes.json')
    args=ap.parse_args()
    result=auditar(args.base)
    Path(args.saida).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
