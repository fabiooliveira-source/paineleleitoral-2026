import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import sys,pathlib,gzip,json,base64,zlib,time,hashlib
import numpy as np
sys.path.insert(0,str(pathlib.Path('.').resolve()))
from inferencia_eleitoral import solve
root=pathlib.Path('.').resolve();raw=json.loads(gzip.decompress((root.parent/'model-input.json.gz').read_bytes()));X16=np.asarray(raw['X16'],float);Y5=np.asarray(raw['Y5'],float);X=np.asarray(raw['X'],float);Y=np.asarray(raw['Y'],float);N=np.asarray(raw['N'],float);ufs=np.asarray(raw['UF']);clusters=np.asarray(raw['C']);del raw
origins=['Lula','Flávio','Caiado','Renan','Cury','Zema','Demais candidatos','Brancos/nulos','Abstenção'];destinations=['Lula','Flávio','Brancos/nulos','Abstenção'];assert len(X)==443100

def fit(x,y,n,fallback=None):
 active=x.sum(axis=0)>0;a=x[:,active]/np.sqrt(n[:,None]);b=y/np.sqrt(n[:,None]);g=a.T@a/n.sum();h=a.T@b/n.sum();p=np.full((9,4),.25) if fallback is None else fallback.copy();p[active]=solve(g,h,ridge=.01);return p

def record(counts):
 sums=X.sum(axis=0);assert np.max(abs(counts.sum(axis=1)-sums))<1e-4
 return {'counts':counts.tolist(),'rates':(counts/sums[:,None]).tolist(),'destination_residual':(counts.sum(axis=0)-Y.sum(axis=0)).tolist()}

payload=json.loads(gzip.decompress(base64.b64decode(json.loads((root/'dados/2026/comportamento_rateios_pacote.json').read_text(encoding='utf8'))['dados'])));counts=np.zeros((9,4))
for uf,u in payload['ufs'].items():
 g=u['all'];items=[{'base':g['first']['Lula'],'dest':g['matrix']['Lula']},{'base':g['first']['Flávio'],'dest':g['matrix']['Flávio']},*g['detail'],{'base':g['first']['Brancos/nulos'],'dest':g['matrix']['Brancos/nulos']},{'base':g['first']['Abstenção'],'dest':g['matrix']['Abstenção']}]
 for i,row in enumerate(items):
  for j,d in enumerate(destinations):counts[i,j]+=row['dest'].get(d,0)
accounting=record(counts);assert max(abs(np.asarray(accounting['destination_residual'])))==0
old=json.loads(gzip.decompress(base64.b64decode(json.loads((root/'dados/2026/inferencia-resultados.json').read_text(encoding='utf8'))['dados'])))['territories']['BR'];assert old['n']==len(X);oldP=np.asarray(old['rates']);oldTotals=np.asarray(old['origin_totals']);counts=np.zeros((9,4));main={'55':2,'14':3,'70':4,'30':5}
for i,name in enumerate(old['origins']):
 idx=0 if name=='Lula' else 1 if name=='Flávio' else 7 if name in ['Brancos','Nulos'] else 8 if name=='Abstenção' else main.get(name.split('[')[-1].rstrip(']'),6)
 p=oldP[i];counts[idx]+=oldTotals[i]*np.asarray([p[0],p[1],p[2]+p[3],p[4]])
original=record(counts);P=fit(X,Y,N);globalFit=record(X.sum(axis=0)[:,None]*P);print('Regressões globais concluídas',flush=True)
ufP={u:fit(X[ufs==u],Y[ufs==u],N[ufs==u],P) for u in np.unique(ufs)};counts=np.zeros((9,4));localN=0;localGroups=0
ids,inverse=np.unique(clusters,return_inverse=True);order=np.argsort(inverse,kind='stable');starts=np.r_[0,np.flatnonzero(np.diff(inverse[order]))+1,len(order)]
for j,municipality in enumerate(ids):
 sel=order[starts[j]:starts[j+1]];uf=ufs[sel[0]]
 if len(sel)>=80:
  p=fit(X[sel],Y[sel],N[sel],ufP[uf]);localN+=len(sel);localGroups+=1
 else:p=ufP[uf]
 counts+=X[sel].sum(axis=0)[:,None]*p
 if j%700==0:print('Ajustes locais',j,'/',len(ids),flush=True)
local=record(counts);print('Modelos completos concluídos',flush=True)
fold=np.asarray([zlib.crc32((str(c)+'|20261029').encode())%5 for c in clusters]);test=fold==0;train=~test;assert set(clusters[train]).isdisjoint(set(clusters[test]));pg=fit(X[train],Y[train],N[train]);predGlobal=X[test]@pg;predUF=np.zeros_like(Y[test]);testUF=ufs[test]
for u in np.unique(testUF):
 mask=train&(ufs==u);p=fit(X[mask],Y[mask],N[mask],pg) if mask.sum()>=80 else pg;predUF[testUF==u]=X[test][testUF==u]@p

def metrics(pred,actual,n):
 rmse=np.sqrt(np.average(((pred-actual)/n[:,None])**2,axis=0,weights=n))*100
 return {'rmse_pp':rmse.tolist(),'destination_residual':(pred.sum(axis=0)-actual.sum(axis=0)).tolist(),'lula_share_error_pp':float(100*(pred[:,0].sum()/(pred[:,0].sum()+pred[:,1].sum())-actual[:,0].sum()/(actual[:,0].sum()+actual[:,1].sum())))}
a=X16[train]/np.sqrt(N[train,None]);b=Y5[train]/np.sqrt(N[train,None]);p16=solve(a.T@a/N[train].sum(),a.T@b/N[train].sum(),ridge=0);pred16raw=X16[test]@p16;pred16=np.column_stack([pred16raw[:,0],pred16raw[:,1],pred16raw[:,2]+pred16raw[:,3],pred16raw[:,4]])
validation={'original':metrics(pred16,Y[test],N[test]),'method':'Holdout espacial determinístico: municípios com CRC32(chave|20261029) mod 5 = 0 ficam fora do ajuste. Somente composição de 1º turno do teste entra na previsão. O local usa UF quando o município não foi visto. WLS original 16×5 sem ridge; WLS 9×4 global e por UF com ridge 0,01 em matrizes padronizadas.','split_audit':{'seed':20261029,'disjoint':True,'train_clusters_sha256':hashlib.sha256('\n'.join(sorted(set(clusters[train]))).encode()).hexdigest(),'test_clusters_sha256':hashlib.sha256('\n'.join(sorted(set(clusters[test]))).encode()).hexdigest()},'train_sections':int(train.sum()),'test_sections':int(test.sum()),'train_municipalities':int(len(np.unique(clusters[train]))),'test_municipalities':int(len(np.unique(clusters[test]))),'global':metrics(predGlobal,Y[test],N[test]),'local':metrics(predUF,Y[test],N[test]),'accounting':'Não pontuado: o rateio contábil utiliza as margens observadas do 2º turno e não prevê municípios ocultos.'}
municipal=json.loads((root.parent/'model_input_municipal.json').read_text(encoding='utf8'));backtests=[]
def ols_fit(a,y,w):
 scale=np.sqrt(w/w.sum());ridge=np.eye(a.shape[1])*.001;ridge[0,0]=0;return np.linalg.solve((a*scale[:,None]).T@(a*scale[:,None])+ridge,(a*scale[:,None]).T@(y*scale))
for year,records in municipal.items():
 good=[]
 for key,r in records.items():
  a,b=r['turns'].get('1'),r['turns'].get('2')
  if r['uf']=='ZZ' or not a or not b or min(a['pt']+a['opponent'],a['validos'],a['aptos'],a['comparecimento'],b['validos'])<=0:continue
  good.append((key,r['uf'],[1,a['pt']/(a['pt']+a['opponent']),max(0,a['validos']-a['pt']-a['opponent'])/a['validos'],a['abstencoes']/a['aptos'],a['bn']/a['comparecimento']],b['pt']/b['validos'],b['validos']))
 keys=[r[0]for r in good];u=np.asarray([r[1]for r in good]);a=np.asarray([r[2]for r in good]);y=np.asarray([r[3]for r in good]);w=np.asarray([r[4]for r in good]);folds=np.asarray([zlib.crc32((key+'|20261029').encode())%5 for key in keys]);preds={'Base do 1º turno':a[:,1].copy(),'Regressão nacional':np.zeros(len(a)),'Regressão por UF':np.zeros(len(a))}
 for f in range(5):
  tr=folds!=f;te=~tr;beta=ols_fit(a[tr],y[tr],w[tr]);preds['Regressão nacional'][te]=np.clip(a[te]@beta,0,1)
  for state in np.unique(u[te]):
   st=tr&(u==state);target=te&(u==state);betaLocal=ols_fit(a[st],y[st],w[st]) if st.sum()>=20 else beta;preds['Regressão por UF'][target]=np.clip(a[target]@betaLocal,0,1)
 result={'year':int(year),'municipalities':len(a),'valid_votes':int(w.sum()),'folds':5,'fold_counts':[int((folds==i).sum()) for i in range(5)],'models':{}}
 for name,p in preds.items():result['models'][name]={'rmse_pp':float(100*np.sqrt(np.average((p-y)**2,weights=w))),'mae_pp':float(100*np.average(abs(p-y),weights=w)),'national_share_error_pp':float(100*np.average(p-y,weights=w))}
 backtests.append(result);print('Validação histórica',year,result['models'],flush=True)
out={'scope':{'sections':len(X),'electors':int(N.sum()),'municipalities':len(ids),'local_municipalities':localGroups,'local_sections':localN,'criterion':payload['criterio']},'origins':origins,'destinations':destinations,'origin_totals':X.sum(axis=0).astype(int).tolist(),'destination_totals':Y.sum(axis=0).astype(int).tolist(),'models':{'contabil':accounting,'global16':original,'global9':globalFit,'local':local},'validation2026':validation,'historical':sorted(backtests,key=lambda r:r['year']),'method':'Comparação exploratória de quatro métodos no mesmo recorte. Rateio contábil exato; WLS original 16×5 agregado para exibição; WLS 9×4 com ridge 0,01; WLS municipal com pelo menos 80 seções elegíveis, UF para demais. Taxas de grupo = soma dos votos esperados / soma das bases; sem média simples.','historical_method':'Validação espacial retrospectiva em cinco grupos de municípios. A previsão usa apenas composição de 1º turno: participação entre finalistas, eliminados, abstenção e brancos/nulos. Os válidos de 2º turno são usados como pesos do ajuste nos municípios de treino e como pesos de avaliação nos de teste. Os três modelos históricos preveem participação municipal e não validam transferências individuais nem probabilidades de vitória.'}
(root/'dados/comparacao_modelos.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf8');print('Comparação pronta',json.dumps(out['scope']),flush=True)

