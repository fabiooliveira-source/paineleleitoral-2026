"""Backtest exploratório por amostras municipais/estaduais.

ATENÇÃO: usa reconstrução de primeira parcial com votos finais. Não valida
anúncio histórico nem probabilidade calibrada. Frações beta são uma
composite-likelihood com tamanho efetivo de seções, não de indivíduos.
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd

def neff(sumw,sumw2):return np.divide(sumw**2,sumw2,out=np.zeros_like(sumw),where=sumw2>0)
def wilson(k,n):
 p=k/n;z=1.959964;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return [float(max(0,c-h)),float(min(1,c+h))]

def run(pickle,out,draws=2000,targets=None):
 if draws<1:raise ValueError('draws deve ser positivo')
 d=pd.read_pickle(pickle).sort_values('time',kind='stable').reset_index(drop=True)
 if d.empty:raise ValueError('Amostra de seções vazia')
 for t in ['1t','2t']:
  for c in ['lula','flavio']:
   missing=d[c+'_'+t].isna()
   if (missing & d['nominais_'+t].fillna(0).gt(0)).any():raise ValueError('Votos de candidato ausentes em seção com votação nominal')
   d.loc[missing,c+'_'+t]=0
 if d.time.isna().any():raise ValueError('Seção sem horário: não imputar')
 d['municipal_key']=d.uf+':'+d.codigo_municipio_tse
 mun,mi=np.unique(d.municipal_key,return_inverse=True);ufs,ui=np.unique(d.uf,return_inverse=True)
 M,U=len(mun),len(ufs);muf=np.zeros(M,int);muf[mi]=ui
 apt=d.aptos_2t.to_numpy(float);L=d.lula_2t.to_numpy(float);F=d.flavio_2t.to_numpy(float)
 totalapt=np.bincount(mi,weights=apt,minlength=M);stateapt=np.bincount(ui,weights=apt,minlength=U)
 # Somente primeiro turno para os centros iniciais; não usa final 2T.
 l1=np.bincount(ui,weights=d.lula_1t,minlength=U);f1=np.bincount(ui,weights=d.flavio_1t,minlength=U)
 q0=np.divide(l1,l1+f1,out=np.full(U,.5),where=l1+f1>0)
 r0=np.clip((l1+f1)/stateapt,.01,.99)
 times=d.time.to_numpy();targets=[]
 for pct in (range(1,101) if targets is None else targets):
  if not isinstance(pct,int) or not 1<=pct<=100:raise ValueError('Percentual fora de 1..100')
  index=min(len(d)-1,int(np.ceil(len(d)*pct/100))-1);cutoff=times[index]
  # Nenhuma ordem artificial dentro de um horário simultâneo.
  end=np.searchsorted(times,cutoff,side='right');targets.append((pct,end,cutoff))
 result={'method':'Pós-estratificação municipal/estadual; beta de tamanho efetivo por seções; referência estadual compartilhada','source':'Votos finais atribuídos a DT_PRIM_TOT_PARCIAL_HOR_TSE','warning':'Backtest retrospectivo com versões finais. Probabilidades nominais condicionais, não certeza calibrada nem previsão histórica validada. Primeiro turno fornece priors; ausência de seleção geográfica não aleatória não é garantida.','draws':draws,'seed':20261028,'assumptions':['Representatividade das seções já apuradas dentro de cada estrato.','Tamanho efetivo de Kish com pesos votos/eleitorado; não corrige seleção não aleatória.','Beta fracionária como modelo de trabalho. Dependência UF compartilhada no modelo municipal.','Referência municipal via estado é empírica, com reutilização de dados e sem inferência bayesiana hierárquica integral.','Priors estaduais de 2,20,100 pseudo-seções e referência municipal de 20 pseudo-seções: sensibilidade arbitrária explícita, não aprendida de pesquisa.','Precisão histórica não validada; intervalos de projeção não são frequências empiricamente calibradas.'],'ticks':[]}
 for pct,end,cutoff in targets:
  m=mi[:end];u=ui[:end];a=apt[:end];v=L[:end]+F[:end];l=L[:end]
  observedL=float(l.sum());observedF=float(F[:end].sum())
  ma=np.bincount(m,weights=a,minlength=M);mv=np.bincount(m,weights=v,minlength=M);ml=np.bincount(m,weights=l,minlength=M)
  meq=neff(mv,np.bincount(m,weights=v*v,minlength=M));mer=neff(ma,np.bincount(m,weights=a*a,minlength=M))
  mq=np.divide(ml,mv,out=np.full(M,.5),where=mv>0);mr=np.divide(mv,ma,out=np.full(M,.5),where=ma>0)
  ua=np.bincount(u,weights=a,minlength=U);uv=np.bincount(u,weights=v,minlength=U);ul=np.bincount(u,weights=l,minlength=U)
  ueq=neff(uv,np.bincount(u,weights=v*v,minlength=U));uer=neff(ua,np.bincount(u,weights=a*a,minlength=U))
  uq=np.divide(ul,uv,out=q0.copy(),where=uv>0);ur=np.divide(uv,ua,out=r0.copy(),where=ua>0)
  remaining=np.maximum(totalapt-ma,0);ur_remaining=np.maximum(stateapt-ua,0);active=remaining>0
  tick={'target':pct,'sections_share':end/len(d),'time':str(pd.Timestamp(cutoff)),'observed_lula':int(observedL),'observed_flavio':int(observedF),'state_coverage':int((ua>0).sum()),'municipal_coverage':int((ma>0).sum()),'remaining_electorate':int(remaining.sum()),'models':{}}
  for mode in ['estadual','municipal']:
   scenarios=[]
   for strength in [2,20,100]:
    rng=np.random.default_rng(20261028+pct)
    qall=rng.beta(np.maximum(.01,strength*q0+ueq*uq),np.maximum(.01,strength*(1-q0)+ueq*(1-uq)),size=(draws,U))
    rall=rng.beta(np.maximum(.01,strength*r0+uer*ur),np.maximum(.01,strength*(1-r0)+uer*(1-ur)),size=(draws,U))
    if mode=='estadual':
     pl=observedL+((qall*rall)*ur_remaining).sum(axis=1);pf=observedF+(((1-qall)*rall)*ur_remaining).sum(axis=1)
    else:
     pl=np.full(draws,observedL);pf=np.full(draws,observedF)
     # Pequenos lotes limitam memória; estado sorteado é compartilhado.
     indices=np.flatnonzero(active)
     for start in range(0,len(indices),128):
      ids=indices[start:start+128];refq=qall[:,muf[ids]];refr=rall[:,muf[ids]]
      q=rng.beta(np.maximum(.01,20*refq+meq[ids]*mq[ids]),np.maximum(.01,20*(1-refq)+meq[ids]*(1-mq[ids])))
      r=rng.beta(np.maximum(.01,20*refr+mer[ids]*mr[ids]),np.maximum(.01,20*(1-refr)+mer[ids]*(1-mr[ids])))
      pl+=(q*r*remaining[ids]).sum(axis=1);pf+=((1-q)*r*remaining[ids]).sum(axis=1)
    k=int((pl>pf).sum());share=pl/(pl+pf)
    scenarios.append({'prior_pseudo_sections':strength,'p_lula':k/draws,'p_flavio':int((pf>pl).sum())/draws,'p_tie':int((pf==pl).sum())/draws,'mc_wilson95_lula':wilson(k,draws),'share_lula_median':float(np.median(share)),'share_lula_interval95':np.quantile(share,[.025,.975]).tolist(),'projected_lula_median':int(np.median(pl)),'projected_flavio_median':int(np.median(pf))})
   tick['models'][mode]={'scenarios':scenarios,'sensitivity_p_lula':[min(x['p_lula'] for x in scenarios),max(x['p_lula'] for x in scenarios)],'lower_mc_robust_lula':min(x['mc_wilson95_lula'][0] for x in scenarios)}
  result['ticks'].append(tick)
  Path(out).parent.mkdir(parents=True,exist_ok=True);Path(out).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
  print(pct,tick['time'],{k:v['sensitivity_p_lula'] for k,v in tick['models'].items()},flush=True)
 for mode in ['estadual','municipal']:
  hit=next((t for t in result['ticks'] if t['models'][mode]['lower_mc_robust_lula']>=.99),None)
  result[mode+'_first_99']=None if hit is None else {'target':hit['target'],'time':hit['time'],'sections_share':hit['sections_share']}
 Path(out).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
 print('Marcos99',result.get('estadual_first_99'),result.get('municipal_first_99'),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sections',default='work/secoes-temporais.pkl');p.add_argument('--out',default='outputs/previsao_territorial.json');p.add_argument('--draws',type=int,default=2000);p.add_argument('--targets',type=int,nargs='+');a=p.parse_args();run(a.sections,a.out,a.draws,a.targets)