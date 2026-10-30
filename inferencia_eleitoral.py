"""Inferência ecológica exploratória e limites contábeis por seção.

Não recupera votos individuais e não implementa EI de King. O estimador é
regressão ecológica multivariada com linhas estocásticas, mínimos quadrados
ponderados e bootstrap de municípios. Hipótese identificadora: taxas médias
homogêneas no território e resíduo sem associação à composição de origem.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(name,'1')
import argparse,base64,gzip,json,hashlib,zipfile,time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import minimize,LinearConstraint

KEY=['uf','codigo_municipio_tse','zona','secao']
SEED=20261028

def canonical(df):
    """Código de município TSE, e não nome/IBGE. UF integra a chave."""
    df=df.copy()
    for k in KEY:
        if df[k].isna().any(): raise ValueError('Chave nula: '+k)
        df[k]=df[k].astype(str).str.strip()
        if k!='uf':
            if not df[k].str.fullmatch(r'\d+').all():
                raise ValueError('Código não inteiro em '+k)
            df[k]=df[k].map(lambda s:str(int(s)))
    df['uf']=df.uf.str.upper()
    if df.duplicated(KEY).any():
        raise ValueError('Chave repetida: não somar revisões, cargos ou seções agregadas automaticamente')
    return df

def strict_join(first,second):
    """Recebe dataframes NORMALIZADOS, com colunas sem sufixo de turno.

    Cada origem/destino deve ser contagem inteira mutuamente exclusiva.
    Agregações oficiais exigem crosswalk prévio verificado; sem isso, excluir.
    """
    a,b=canonical(first),canonical(second)
    joined=a.merge(b,on=KEY,how='outer',suffixes=('_1t','_2t'),
                   indicator=True,validate='one_to_one')
    return joined,joined['_merge'].value_counts().to_dict()

def load_existing(path,candidate_dir):
    """Adapta a base conciliada existente e todos os candidatos por seção.
    A fonte nominal inclui candidatura 28: manter separada, sem confundir
    com votos válidos. Nulos desta base são a categoria do arquivo por seção.
    """
    d=pd.read_csv(path,sep=';',dtype={k:str for k in KEY})
    # Reexecuta o join para auditar a unicidade de cada turno.
    a=d[KEY+[c for c in d if c.endswith('_1t')]].rename(
        columns={c:c[:-3] for c in d if c.endswith('_1t')})
    b=d[KEY+[c for c in d if c.endswith('_2t')]].rename(
        columns={c:c[:-3] for c in d if c.endswith('_2t')})
    d,join_audit=strict_join(a,b)
    pieces=[];names={}
    for path in sorted(Path(candidate_dir).glob('candidatos-secao-*.json')):
        obj=json.loads(path.read_text(encoding='utf-8'))
        payload=json.loads(gzip.decompress(base64.b64decode(obj['dados'])))
        uf=path.stem.rsplit('-',1)[-1]
        columns=KEY[1:]+['cand_'+n for n in payload['numeros']]
        frame=pd.DataFrame(payload['linhas'],columns=columns)
        frame['uf']=uf
        pieces.append(canonical(frame));names.update(payload['nomes'])
    if not pieces: raise ValueError('Pacotes de candidatos por seção ausentes')
    candidates=pd.concat(pieces,ignore_index=True)
    if candidates.duplicated(KEY).any():raise ValueError('Candidato/seção duplicado')
    # Lula (13) e Flávio (22) já integram X por suas colunas próprias.
    # A contagem nominal destes candidatos nos pacotes deve coincidir com
    # o primeiro turno; nunca acrescentá-los novamente às origens.
    for numero,col in [('13','lula_1t'),('22','flavio_1t')]:
        cand='cand_'+numero
        if cand in candidates:
            confer=canonical(d[KEY+[col]]).merge(candidates[KEY+[cand]],on=KEY,how='left',validate='one_to_one')
            # Listas nominais esparsas omitem candidatos com zero votos.
            # Uma seção ausente do pacote completo é detectada no join posterior.
            a=pd.to_numeric(confer[col],errors='raise')
            b=pd.to_numeric(confer[cand],errors='raise').fillna(0)
            if not a.eq(b).all():
                raise ValueError('Votos do candidato '+numero+' divergem entre bases: impedir dupla contagem')
            candidates=candidates.drop(columns=[cand])
    # Excluir explicitamente candidatos principais do vetor de origens.
    if any(c in candidates.columns for c in ('cand_13','cand_22')):
        raise AssertionError('Dupla contagem de candidatos finalistas')
    d=d.merge(candidates,on=KEY,how='left',validate='one_to_one',indicator='candidates_merge')
    cols=sorted(c for c in d if c.startswith('cand_'))
    # Zero só é aceito quando a seção foi encontrada no pacote nominal.
    found=d.candidates_merge.eq('both')
    d.loc[found,cols]=d.loc[found,cols].fillna(0)
    return d,cols,names,join_audit

def prepare(d,candidate_cols):
    audit={'total_keys':len(d),'flags':{}}
    Xcols=['lula_1t','flavio_1t']+candidate_cols+['brancos_1t','nulos_1t','abstencoes_1t']
    Ycols=['lula_2t','flavio_2t','brancos_2t','nulos_2t','abstencoes_2t']
    for c in Xcols+Ycols+['aptos_1t','aptos_2t','comparecimento_1t','comparecimento_2t']:
        d[c]=pd.to_numeric(d[c],errors='coerce')
    valid=np.ones(len(d),dtype=bool)
    checks={
      'unpaired':~d['_merge'].eq('both'),
      'missing_candidate_detail':~d.candidates_merge.eq('both'),
      'different_electorate':d.aptos_1t.ne(d.aptos_2t),
      'different_voting_place':d.local_votacao_1t.ne(d.local_votacao_2t),
      'not_checked':~d.situacao_dados_1t.eq('conferido')|~d.situacao_dados_2t.eq('conferido'),
      'not_installed':~d.instalada_1t.eq('Sim')|~d.instalada_2t.eq('Sim'),
      'annulled':d.anulada_1t.eq('Sim')|d.anulada_2t.eq('Sim'),
      'nonpositive_electorate':d.aptos_1t.le(0)|d.aptos_2t.le(0),
    }
    arr=d[Xcols+Ycols].to_numpy(float)
    checks['invalid_counts']=pd.Series(~np.isfinite(arr).all(axis=1)|(np.nan_to_num(arr)<0).any(axis=1)|(np.nan_to_num(arr)%1!=0).any(axis=1),index=d.index)
    for t,cols in [('1t',Xcols),('2t',Ycols)]:
        checks['categories_not_reconciled_'+t]=d[cols].sum(axis=1).ne(d['aptos_'+t])
        checks['turnout_not_reconciled_'+t]=d['comparecimento_'+t].add(d['abstencoes_'+t]).ne(d['aptos_'+t])
    for name,mask in checks.items():
        audit['flags'][name]=int(mask.sum());valid&=~mask.to_numpy()
    audit['included']=int(valid.sum());audit['excluded']=int((~valid).sum())
    audit['electors_included']=int(d.loc[valid,'aptos_1t'].sum())
    audit['notes']=['Flags sobrepostas: não somar exclusões.',
        'Mesmo cadastro/local não garante identidade das pessoas.',
        'Sem identificador de urna física ou crosswalk de agregações, substituições/agrupamentos não são resolvidos.',
        'Fonte: consolidados oficiais por seção; não autenticação criptográfica de BUs.']
    exclusions=d.loc[~valid,KEY].copy()
    exclusions['motivos']=['|'.join(k for k,v in checks.items() if v.iloc[i]) for i in np.flatnonzero(~valid)]
    good=d.loc[valid].reset_index(drop=True)
    return good,good[Xcols].to_numpy(np.int64),good[Ycols].to_numpy(np.int64),audit,exclusions

def bounds(X,Y,N):
    """Limites exatos de cada célula, condicionados às margens e universo."""
    return np.maximum(0,X[:,:,None]+Y[:,None,:]-N[:,None,None]),np.minimum(X[:,:,None],Y[:,None,:])

def solve(G,H,start=None,ridge=0):
    """Minimiza soma_i N_i ||Y_i/N_i - (X_i/N_i) P||².
    Restrições P>=0 e soma por origem=1. Não é likelihood de King/PyMC.
    """
    R,C=H.shape
    scale=np.sqrt(np.maximum(np.diag(G),1e-12))
    A=G/scale[:,None]/scale[None,:]+ridge*np.eye(R)
    B=H/scale[:,None]
    constraint=np.zeros((R,R*C))
    for r in range(R):constraint[r,r*C:(r+1)*C]=1
    q=(np.full((R,C),1/C) if start is None else start)*scale[:,None]
    def fun(v):
        q=v.reshape(R,C);return float(np.sum(q*(A@q))-2*np.sum(q*B))
    def jac(v):return (2*(A@v.reshape(R,C)-B)).ravel()
    fit=minimize(fun,q.ravel(),jac=jac,method='SLSQP',bounds=[(0,float(s)) for s in scale for _ in range(C)],constraints=LinearConstraint(constraint,scale,scale),options={'maxiter':600,'ftol':1e-11})
    if not fit.success:raise RuntimeError('Falha na otimização: '+fit.message)
    P=fit.x.reshape(R,C)/scale[:,None]
    if np.max(abs(P.sum(axis=1)-1))>1e-6 or np.min(P)<-1e-7:raise RuntimeError('Matriz não estocástica')
    return P

def fit_territory(X,Y,N,clusters,origin_names,B=100):
    active=X.sum(axis=0)>0;Xa=X[:,active];names=np.array(origin_names)[active].tolist()
    if len(X)<max(30,Xa.shape[1]*3):return {'status':'insufficient_sections','n':len(X)}
    ids,inv=np.unique(clusters,return_inverse=True)
    # Cada município é um bloco; replicações preservam a dependência interna.
    blocks=[]
    for g in range(len(ids)):
        sel=inv==g;x=Xa[sel]/np.sqrt(N[sel,None]);y=Y[sel]/np.sqrt(N[sel,None])
        blocks.append((x.T@x,x.T@y))
    gs=np.stack([b[0] for b in blocks]);hs=np.stack([b[1] for b in blocks]);total=N.sum()
    G=gs.sum(axis=0)/total;H=hs.sum(axis=0)/total
    P=solve(G,H);pred=Xa@P;error=(pred-Y)/N[:,None]
    rng=np.random.default_rng(SEED);samples=[];fails=0
    if len(ids)>=20:
        for _ in range(B):
            weights=rng.multinomial(len(ids),np.full(len(ids),1/len(ids)))
            try:samples.append(solve(np.einsum('g,gij->ij',weights,gs)/total,np.einsum('g,gij->ij',weights,hs)/total,start=P))
            except RuntimeError:fails+=1
    draws=np.stack(samples) if samples else None
    lo,hi=np.quantile(draws,[.025,.975],axis=0) if draws is not None else (None,None)
    alien=P[:,2:].sum(axis=1)
    alien_ci=np.quantile(draws[:,:,2:].sum(axis=2),[.025,.975],axis=0) if draws is not None else None
    singular=np.linalg.svd(G,compute_uv=False);condition=float(singular[0]/max(singular[-1],1e-30))
    effects=[]
    abst=names.index('Abstenção') if 'Abstenção' in names else None
    if abst is not None:
        def net(p,c):return float(Xa[:,abst].sum()*p[abst,c]-Xa[:,c].sum()*p[c,4])
        for c in [0,1]:
            vals=np.array([net(p,c) for p in draws]) if draws is not None else None
            effects.append({'candidate':names[c],'expected_net_abstention':net(P,c),'bootstrap95':np.quantile(vals,[.025,.975]).tolist() if vals is not None else None})
    ridgeP=solve(G,H,start=P,ridge=.01)
    return {'status':'exploratory_assumption_dependent','n':len(X),'electors':int(total),'municipal_clusters':len(ids),'origins':names,'destinations':['Lula','Flávio','Brancos','Nulos','Abstenção'],'rates':P.tolist(),'bootstrap95_lower':lo.tolist() if lo is not None else None,'bootstrap95_upper':hi.tolist() if hi is not None else None,'alienation_rate':alien.tolist(),'alienation_bootstrap95':alien_ci.T.tolist() if alien_ci is not None else None,'bootstrap_success':len(samples),'bootstrap_failed':fails,'condition_number_gram':condition,'rank':int(np.linalg.matrix_rank(G)),'parameters_origins':len(names),'ridge_sensitivity_max_pp':float(100*np.max(abs(ridgeP-P))),'weighted_rmse_proportions':np.sqrt(np.average(error**2,axis=0,weights=N)).tolist(),'aggregate_expected_minus_observed':(pred.sum(axis=0)-Y.sum(axis=0)).tolist(),'abstention_effects_expected':effects,'warning':'Taxas médias modeladas, não fluxos individuais observados; intervalos bootstrap condicionais ao modelo. Sem calibração causal ou garantia contra viés ecológico.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--candidates',required=True);ap.add_argument('--out',required=True);ap.add_argument('--bootstrap',type=int,default=100);ap.add_argument('--states',action='store_true');args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    d,cols,names,join=load_existing(args.base,args.candidates);good,X,Y,audit,excluded=prepare(d,cols);N=good.aptos_1t.to_numpy(np.int64)
    origins=['Lula','Flávio']+[names.get(c[5:],c[5:])+' ['+c[5:]+']' for c in cols]+['Brancos','Nulos','Abstenção'];lo,hi=bounds(X,Y,N)
    audit['join']=join;audit['nominal_note']='Candidatura 28 mantida nominalmente; a análise por seção não usa a classificação municipal de votos válidos para recodificar sua origem.'
    excluded.to_csv(out/'secoes_excluidas.csv',sep=';',index=False)
    # Exportação de limites por seção para Lula/Flávio: formato largo comprimido.
    b=good[KEY].copy()
    for r,name in enumerate(origins):
        for c,target in enumerate(['Lula','Flavio']):
            b[f'{r}_{target}_min']=lo[:,r,c];b[f'{r}_{target}_max']=hi[:,r,c]
    b.to_csv(out/'limites_por_secao.csv.gz',sep=';',index=False,compression='gzip')
    result={'method':'Regressão ecológica multivariada restrita, WLS + bootstrap de municípios','seed':SEED,'audit':audit,'origins':origins,'destinations':['Lula','Flávio','Brancos','Nulos','Abstenção'],'territories':{}}
    targets=['BR']+(sorted(good.uf.unique()) if args.states else [])
    for territory in targets:
        sel=np.ones(len(good),bool) if territory=='BR' else good.uf.eq(territory).to_numpy()
        print('Ajustando',territory,int(sel.sum()),flush=True)
        fit=fit_territory(X[sel],Y[sel],N[sel],(good.uf+':'+good.codigo_municipio_tse).to_numpy()[sel],origins,args.bootstrap)
        fit['bounds_min']=lo[sel].sum(axis=0).tolist();fit['bounds_max']=hi[sel].sum(axis=0).tolist();fit['origin_totals']=X[sel].sum(axis=0).tolist();fit['destination_totals']=Y[sel].sum(axis=0).tolist()
        fit['grouped_bounds']={}
        for group,indices in [('Eliminados',list(range(2,len(origins)-3))),('Brancos + nulos + abstenção',list(range(len(origins)-3,len(origins))))]:
            A=X[sel][:,indices].sum(axis=1)
            fit['grouped_bounds'][group]={'lower':np.maximum(0,A[:,None]+Y[sel]-N[sel,None]).sum(axis=0).tolist(),'upper':np.minimum(A[:,None],Y[sel]).sum(axis=0).tolist()}
        result['territories'][territory]=fit
        (out/'resultados_ei.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Concluído',territory,fit.get('bootstrap_success'),flush=True)
    print('Arquivos em',out,flush=True)

if __name__=='__main__':main()