"""Cenário contábil por seção, incluindo diferenças de universo.
IPF condicionado às margens observadas; não estima trajetórias individuais.
"""
import base64,gzip,hashlib,json,re
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent

def unpack(path):
    obj=json.loads(path.read_text());return json.loads(gzip.decompress(base64.b64decode(obj['dados'])))

def balance(X,Y,prior,tol=1e-7):
    if not np.allclose(X.sum(1),Y.sum(1),atol=0,rtol=0):raise ValueError('Universos incompatíveis')
    # Piso positivo evita que zeros do ajuste anterior impeçam fechar margens.
    prior=np.maximum(prior,1e-4)
    M=np.zeros((len(X),X.shape[1],Y.shape[1]))
    active=np.arange(len(X));U=X.copy();V=np.ones_like(Y)
    for iteration in range(1000):
        columns=U@prior
        V=np.divide(Y[active],columns,out=np.zeros_like(columns),where=columns>0)
        rows=V@prior.T
        U=np.divide(X[active],rows,out=np.zeros_like(rows),where=rows>0)
        error=np.max(np.abs((U@prior)*V-Y[active]),axis=1)
        done=error<tol
        M[active[done]]=U[done,:,None]*prior[None,:,:]*V[done,None,:]
        active=active[~done];U=U[~done];V=V[~done]
        if not len(active):return M,[]
    # Casos mal condicionados usam independência, explicitamente auditada.
    totals=X[active].sum(1)
    M[active]=np.divide(X[active,:,None]*Y[active,None,:],totals[:,None,None],out=np.zeros_like(M[active]),where=totals[:,None,None]>0)
    return M,active.tolist()

def add_official_municipal_blocks(report,root):
    """Preserva totais oficiais de locais sem nenhuma seção utilizável."""
    official_path=root/'municipios.json.gz'
    report['audit']['official_municipal_sha256']=hashlib.sha256(official_path.read_bytes()).hexdigest()
    official=json.loads(gzip.decompress(official_path.read_bytes()));cache={};added=0
    R=len(report['origins']);C=len(report['destinations'])
    for row in official:
        uf=row['uf'];code=str(int(row['codigo_municipio_tse']))
        if uf not in cache:cache[uf]=json.loads(gzip.decompress((root/f'rateio-inclusivo-{uf}.json.gz').read_bytes()))
        municipal=cache[uf]
        if code in municipal and not municipal[code].get('official_municipal_fallback'):continue
        x=np.zeros(R);y=np.zeros(C)
        x[0]=row['lula_1t'];x[1]=row['flavio_1t'];x[R-5:R-2]=[row['brancos_1t'],row['nulos_1t'],row['abstencoes_1t']]
        x[-2]=row['validos_1t']-row['lula_1t']-row['flavio_1t'];y[:5]=[row[k+'_2t'] for k in ['lula','flavio','brancos','nulos','abstencoes']]
        if x[-2]<0 or y.sum()>row['aptos_2t'] or x.sum()>row['aptos_1t']:raise ValueError('Totais municipais de fallback inválidos')
        missing_1t=float(row['aptos_1t']-x.sum());missing_2t=float(row['aptos_2t']-y.sum());delta=float(y.sum()-x.sum());x[-1]=max(delta,0);y[-1]=max(-delta,0)
        flow=np.outer(x,y)/x.sum() if x.sum() else np.zeros((R,C))
        block={'sections':0,'changed_electorate':0,'changed_place':0,'origin_totals':x.tolist(),'destination_totals':y.tolist(),'flow':flow.tolist(),'independence_flow':flow.tolist(),'sensitivity_max_votes':0,'prior':'Totais oficiais municipais; independência; sem detalhamento utilizável por seção','independence_fallback_sections':0,'official_municipal_fallback':True,'official_municipal_fallback_blocks':1,'aptos_without_category_1t':missing_1t,'aptos_without_category_2t':missing_2t}
        municipal[code]=block;added+=1
        for territory in [uf,'BR']:
            target=report['territories'][territory]
            for key,value in [('origin_totals',x),('destination_totals',y),('flow',flow),('independence_flow',flow)]:target[key]=(np.asarray(target[key])+value).tolist()
            target['official_municipal_fallback_blocks']=target.get('official_municipal_fallback_blocks',0)+1
            target['sensitivity_max_votes']=float(np.max(abs(np.array(target['flow'])-target['independence_flow'])))
    for uf,municipal in cache.items():
        (root/f'rateio-inclusivo-{uf}.json.gz').write_bytes(gzip.compress(json.dumps(municipal,ensure_ascii=False,separators=(',',':')).encode(),mtime=0))
    report['audit']['official_municipal_fallback_blocks']=added
    report['warning']+=' Locais sem seção utilizável preservam os totais oficiais em bloco municipal separado; isso não reconstrói a urna. Aptos de locais não instalados sem categoria não são convertidos em abstenções.'

def main():
    root=ROOT/'dados/2026';db=unpack(root/'inferencia-resultados.json')
    names=db['origins']+['Origem nominal sem detalhamento','Ajuste de universo — entrada']
    dest=db['destinations']+['Ajuste de universo — saída']
    report={'method':'Cenário IPF por seção condicionado às margens; prior do modelo estadual ou nacional, sem ajuste municipal independente','warning':'Ajuste de universo é contábil, não eleitor observado; representa a diferença líquida de aptos, sem medir troca real de eleitores. Valores são cenários fracionários, não rastreamento de votos ou probabilidades. Sensibilidade compara prior do modelo e independência; não é intervalo de confiança. Casos sem convergência usam independência e são contabilizados na auditoria.','origins':names,'destinations':dest,'territories':{},'audit':{'sources':{},'pending':[],'model_sha256':hashlib.sha256((root/'inferencia-resultados.json').read_bytes()).hexdigest(),'ipf':{'tolerance_votes':1e-7,'max_iterations_new_partitions':1000,'reuse_frozen_checkpoints':True,'prior_floor':1e-4}}}
    results={};national=np.zeros((len(names),len(dest)));independent=national.copy();maxerr=0.;total=0;changed=0;places=0
    for path in sorted(root.glob('secoes-*.json.gz')):
        uf=path.name.split('-')[1].split('.')[0];raw=path.read_bytes();sec=json.loads(gzip.decompress(raw));candpath=root/f'candidatos-secao-{uf}.json';can=unpack(candpath)
        report['audit']['sources'][uf]={'sections_sha256':hashlib.sha256(raw).hexdigest(),'candidates_sha256':hashlib.sha256(candpath.read_bytes()).hexdigest()}
        lookup={tuple(str(int(v)) for v in row[:3]):dict(zip(can['numeros'],row[3:])) for row in can['linhas']}
        xs=[];ys=[];keys=[];flags=[]
        for row in sec['linhas']:
            r=dict(zip(sec['colunas'],row));key=tuple(str(int(r[k])) for k in ['codigo_municipio_tse','zona','secao'])
            try:
                if any(r['situacao_dados_'+t]!='conferido' for t in ['1t','2t']):raise ValueError('dados não conferidos')
                c=lookup.get(key);x=[r['lula_1t'],r['flavio_1t']]+[(c or {}).get(re.search(r'\[(\d+)\]',n).group(1),0) for n in db['origins'][2:-3]]+[r['brancos_1t'],r['nulos_1t'],r['abstencoes_1t']]
                residual=r['aptos_1t']-sum(x)
                y=[r[k+'_2t'] for k in ['lula','flavio','brancos','nulos','abstencoes']]
                if residual<0 or sum(y)!=r['aptos_2t']:raise ValueError('categorias não conciliadas')
                for t in ['1t','2t']:
                    if r['comparecimento_'+t]+r['abstencoes_'+t]!=r['aptos_'+t]:raise ValueError('comparecimento não conciliado')
                delta=r['aptos_2t']-r['aptos_1t'];x +=[residual,max(delta,0)];y +=[max(-delta,0)]
                if any(not isinstance(v,(int,float)) or not np.isfinite(v) or v<0 or int(v)!=v for v in x+y):raise ValueError('contagem inválida')
                xs.append(x);ys.append(y);keys.append(key);flags.append((delta!=0,r['local_votacao_1t']!=r['local_votacao_2t']))
            except (ValueError,TypeError) as e:report['audit']['pending'].append({'uf':uf,'key':key,'reason':str(e)})
        X=np.array(xs,dtype=float);Y=np.array(ys,dtype=float);fit=db['territories'].get(uf,db['territories']['BR']);prior=np.ones((len(names),len(dest)))*1e-4
        for i,n in enumerate(fit['origins']):prior[names.index(n),:5]=fit['rates'][i]
        prior[-2:,:5]=1/5;prior[:,-1]=1/6
        target=root/f'rateio-inclusivo-{uf}.json.gz'
        if target.exists():
            municipal=json.loads(gzip.decompress(target.read_bytes()));parts=[r for r in municipal.values() if not r.get('official_municipal_fallback')];report['audit']['sources'][uf]['checkpoint_sha256']=hashlib.sha256(target.read_bytes()).hexdigest();report['audit']['sources'][uf]['checkpoint_iteration_limit']=10000 if any('independence_fallback_sections' not in r for r in parts) else 1000
            f=np.sum([r['flow'] for r in parts],axis=0);a=np.sum([r['independence_flow'] for r in parts],axis=0)
            ox=np.sum([r['origin_totals'] for r in parts],axis=0);oy=np.sum([r['destination_totals'] for r in parts],axis=0)
            if not np.array_equal(ox,X.sum(0)) or not np.array_equal(oy,Y.sum(0)):raise ValueError('Checkpoint incompatível com margens de '+uf)
            results[uf]={'sections':len(X),'changed_electorate':sum(f[0] for f in flags),'changed_place':sum(f[1] for f in flags),'origin_totals':ox.tolist(),'destination_totals':oy.tolist(),'flow':f.tolist(),'independence_flow':a.tolist(),'sensitivity_max_votes':float(abs(f-a).max()),'prior':uf if uf in db['territories'] else 'BR','independence_fallback_sections':sum(r.get('independence_fallback_sections',0) for r in parts)}
            national+=f;independent+=a;total+=len(X);changed+=sum(f[0] for f in flags);places+=sum(f[1] for f in flags)
            maxerr=max(maxerr,1e-7);print('Checkpoint verificado',uf,len(X),flush=True);continue
        M,fallback=balance(X,Y,prior);I,_=balance(X,Y,np.ones_like(prior))
        err=max(np.max(abs(M.sum(2)-X),initial=0),np.max(abs(M.sum(1)-Y),initial=0));maxerr=max(maxerr,float(err));total+=len(X);changed+=sum(f[0] for f in flags);places+=sum(f[1] for f in flags)
        def aggregate(sel):
            f=M[sel].sum(0);a=I[sel].sum(0);return {'sections':int(np.count_nonzero(sel)),'changed_electorate':sum(flags[i][0] for i in np.flatnonzero(sel)),'changed_place':sum(flags[i][1] for i in np.flatnonzero(sel)),'origin_totals':X[sel].sum(0).tolist(),'destination_totals':Y[sel].sum(0).tolist(),'flow':f.tolist(),'independence_flow':a.tolist(),'sensitivity_max_votes':float(abs(f-a).max()),'prior':uf if uf in db['territories'] else 'BR','independence_fallback_sections':sum(bool(sel[i]) for i in fallback)}
        results[uf]=aggregate(np.ones(len(X),dtype=bool));national+=M.sum(0);independent+=I.sum(0)
        cities=np.array([k[0] for k in keys]);municipal={c:aggregate(cities==c) for c in sorted(set(cities))}
        target=root/f'rateio-inclusivo-{uf}.json.gz';target.write_bytes(gzip.compress(json.dumps(municipal,ensure_ascii=False,separators=(',',':')).encode(),mtime=0));print(uf,len(X),'aptos distintos',sum(f[0] for f in flags),'erro',err,flush=True)
    results['BR']={'sections':total,'changed_electorate':changed,'changed_place':places,'origin_totals':np.sum([r['origin_totals'] for r in results.values()],axis=0).tolist(),'destination_totals':np.sum([r['destination_totals'] for r in results.values()],axis=0).tolist(),'flow':national.tolist(),'independence_flow':independent.tolist(),'sensitivity_max_votes':float(abs(national-independent).max()),'prior':'Estadual; fallback nacional','independence_fallback_sections':sum(r.get('independence_fallback_sections',0) for r in results.values())}
    report['territories']=results;report['audit'].update({'included':total,'additional_sections_vs_paired':total-db['audit']['included'],'paired_baseline_sections':db['audit']['included'],'changed_electorate_included':changed,'changed_place_included':places,'pending_count':len(report['audit']['pending']),'section_margin_error_upper_bound_votes':maxerr,'independence_fallback_sections':sum(r.get('independence_fallback_sections',0) for k,r in results.items() if k!='BR')})
    add_official_municipal_blocks(report,root)
    (root/'rateio-inclusivo.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')))
    print(json.dumps({k:v for k,v in report['audit'].items() if k not in ['sources','pending']}))
if __name__=='__main__':main()
