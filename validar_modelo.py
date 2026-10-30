"""Validação independente de previsões eleitorais e integridade dos dados.
Uso: python validar_modelo.py --previsoes previsoes.csv --observados observados.csv --saida validacao.json
Previsões: id,probabilidade,estimativa,realizado_em,informacao_ate
Observados: id,resultado (0 ou 1),valor_final
Nenhuma previsão pode usar informação posterior ao instante declarado.
"""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

def validar(previsoes, observados):
    required_p={'id','probabilidade','estimativa','realizado_em','informacao_ate'}
    required_o={'id','resultado','valor_final'}
    for name,df,req in [('previsoes',previsoes,required_p),('observados',observados,required_o)]:
        missing=req-set(df.columns)
        if missing: raise ValueError(f'{name}: faltam colunas {sorted(missing)}')
        if df['id'].isna().any() or df['id'].duplicated().any():
            raise ValueError(f'{name}: IDs nulos ou repetidos')
    if previsoes.empty or observados.empty:
        raise ValueError('Amostra vazia')
    d=previsoes.merge(observados,on='id',validate='one_to_one',indicator=True)
    if not d['_merge'].eq('both').all() or len(d)!=len(observados) or len(d)!=len(previsoes):
        raise ValueError('Previsões e observados não possuem correspondência completa')
    for c in ['probabilidade','estimativa','resultado','valor_final']:
        d[c]=pd.to_numeric(d[c],errors='raise')
    if not np.isfinite(d[['probabilidade','estimativa','resultado','valor_final']].to_numpy(float)).all():
        raise ValueError('Valores não finitos')
    if not d.probabilidade.between(0,1).all() or not d.resultado.isin([0,1]).all():
        raise ValueError('Probabilidades fora de [0,1] ou resultado não binário')
    for c in ['realizado_em','informacao_ate']:
        d[c]=pd.to_datetime(d[c],utc=True,errors='raise')
    if d.informacao_ate.isna().any() or d.realizado_em.isna().any():
        raise ValueError('Datas inválidas')
    if (d.informacao_ate>d.realizado_em).any():
        raise ValueError('Vazamento temporal: informação posterior à emissão da previsão')
    p=d.probabilidade.to_numpy(float);y=d.resultado.to_numpy(float)
    error=d.estimativa.to_numpy(float)-d.valor_final.to_numpy(float)
    bins=[]
    for low in np.arange(0,1,.1):
        sel=(p>=low)&(p<(low+.1) if low<.9 else p<=1)
        if sel.sum():
            bins.append({'faixa':[round(float(low),1),round(float(low+.1),1)],
                         'n':int(sel.sum()),'probabilidade_media':float(p[sel].mean()),
                         'frequencia_observada':float(y[sel].mean())})
    return {'n':len(d),'brier_score':float(np.mean((p-y)**2)),
            'mae_estimativa':float(np.mean(np.abs(error))),
            'rmse_estimativa':float(np.sqrt(np.mean(error**2))),
            'vies_medio':float(np.mean(error)),
            'calibracao_por_faixa':bins,
            'aviso':'Validação exige previsões genuinamente prospectivas ou snapshots históricos sem vazamento. Métricas não comprovam ausência de irregularidades.'}

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--previsoes',required=True);a.add_argument('--observados',required=True)
    a.add_argument('--saida',default='validacao.json')
    args=a.parse_args()
    r=validar(pd.read_csv(args.previsoes),pd.read_csv(args.observados))
    Path(args.saida).write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
