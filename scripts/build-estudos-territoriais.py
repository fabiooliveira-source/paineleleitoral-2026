"""Estudos estáticos TSE × IBGE. Nenhum dado de entrevistas ou consulta no navegador do usuário."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import pathlib,json,gzip,base64,hashlib,urllib.request,unicodedata,re,importlib.util
import numpy as np
from scipy.stats import spearmanr
from scipy.cluster.vq import kmeans2
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
root=pathlib.Path('.').resolve();cache=root.parent/'ibge';cache.mkdir(exist_ok=True)
urls={'localidades.json':'https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=id','censo2022.json':'https://apisidra.ibge.gov.br/values/t/4714/n6/all/v/all/p/2022','alfabetizacao2022.json':'https://apisidra.ibge.gov.br/values/t/9543/n6/all/v/all/p/2022','pib2021.json':'https://apisidra.ibge.gov.br/values/t/5938/n6/all/v/37/p/2021','populacao2021.json':'https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/all/p/2021'}
provenance=[]
for name,url in urls.items():
 path=cache/name
 if not path.exists():path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
 b=path.read_bytes();b=gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b;path.write_bytes(b);json.loads(b);provenance.append({'file':name,'url':url,'sha256':hashlib.sha256(b).hexdigest(),'snapshot_date':'2026-10-29'})
load=lambda name:json.loads((cache/name).read_text(encoding='utf8'))
def norm(s):return re.sub('[^A-Z0-9]','', ''.join(c for c in unicodedata.normalize('NFD',s.upper()) if unicodedata.category(c)!='Mn'))
def numeric(s):
 try:n=float(s);return n if np.isfinite(n) else None
 except (ValueError,TypeError):return None
lookup={}
for r in load('localidades.json'):
 uf=r['regiao-imediata']['regiao-intermediaria']['UF']['sigla'];key=uf+':'+norm(r['nome']);assert key not in lookup;lookup[key]=str(r['id'])
ibge={}
for r in load('censo2022.json')[1:]:
 assert r['D3C']=='2022';var={'93':'population','6318':'area','614':'density'}[r['D2C']];item=ibge.setdefault(r['D1C'],{});assert var not in item;item[var]=numeric(r['V'])
for r in load('alfabetizacao2022.json')[1:]:
 assert (r['D2C'],r['D3C'],r['D4C'],r['D5C'],r['D6C'])==('2513','2022','6794','95251','100362');ibge.setdefault(r['D1C'],{})['literacy']=numeric(r['V'])
pop={r['D1C']:numeric(r['V'])for r in load('populacao2021.json')[1:]if r['NC']=='6' and r['D2C']=='9324'}
for r in load('pib2021.json')[1:]:
 assert r['D2C']=='37' and r['D3C']=='2021' and r['MC']=='40';v=numeric(r['V']);p=pop.get(r['D1C']);ibge.setdefault(r['D1C'],{})['gdp_pc']=1000*v/p if v is not None and p else None
spec=importlib.util.spec_from_file_location('historical',root/'scripts/build-comparativo-historico.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
h=json.loads((root.parent/'model_input_municipal.json').read_text(encoding='utf8'));h['2014']=module.build(2014);years=['2014','2018','2022','2026'];keys=sorted(set.intersection(*(set(h[y]) for y in years)));rows=[];excluded=[]
for key in keys:
 r=h['2026'][key]
 if r['uf']=='ZZ':continue
 series=[h[y][key]['turns'].get('2')for y in years]
 if any(not d or min(d['validos'],d['aptos'])<=0 for d in series):excluded.append(key);continue
 code=lookup.get(r['uf']+':'+norm(r['name']));raw=ibge.get(code,{}) if code else {};values=[raw.get(v)for v in ['population','density','literacy','gdp_pc']];rows.append({'key':key,'uf':r['uf'],'region':module.regions[r['uf']],'name':r['name'],'ibge_code':code,'ibge':values,'years':[[d[k]for k in ['pt','opponent','validos','aptos','abstencoes','bn']]for d in series]})
assert len(set(r['key']for r in rows))==len(rows)
X=np.asarray([[100*d[0]/d[2]for d in r['years']]+[100*d[4]/d[3]for d in r['years']]for r in rows]);mean=X.mean(axis=0);std=X.std(axis=0);Z=(X-mean)/std;models={};sample=np.random.default_rng(20261029).choice(len(rows),min(1000,len(rows)),replace=False);dist=cdist(Z[sample],Z)
for k in [3,4,5]:
 best=None
 for seed in range(12):
  centers,labels=kmeans2(Z,k,iter=100,minit='++',seed=20261029+seed);error=float(((Z-centers[labels])**2).sum())
  if len(np.unique(labels))==k and (best is None or error<best[0]):best=(error,centers,labels)
 error,centers,labels=best;order=np.argsort((centers*std+mean)[:,3]);mapping={int(old):new for new,old in enumerate(order)};labels=np.asarray([mapping[int(i)]for i in labels]);sil=[]
 for j,i in enumerate(sample):
  group=labels[i];a=dist[j,labels==group].sum()/max(1,(labels==group).sum()-1);b=min(dist[j,labels==g].mean()for g in range(k)if g!=group);sil.append((b-a)/max(a,b))
 for r,label in zip(rows,labels):r.setdefault('clusters',{})[str(k)]=int(label)
 models[str(k)]={'inertia':error,'silhouette_sample':float(np.mean(sil)),'sample_size':len(sample),'counts':[int((labels==i).sum())for i in range(k)]};print('Perfis',k,models[str(k)],flush=True)
locations={}
manifest=json.loads((root/'dados/2026/locais-geograficos-manifest.json').read_text(encoding='utf8'))
for uf,info in manifest['ufs'].items():
 if uf=='ZZ':continue
 encoded=''.join(json.loads((root/f'dados/2026/locais-geograficos-{uf}-{part}.json').read_text(encoding='utf8'))['parte'] for part in range(info['parts']));geo=json.loads(gzip.decompress(base64.b64decode(encoded)))
 for code,groups in geo['turns']['2'].items():
  points=locations.setdefault(uf+':'+code,{})
  for index,_ in groups:
   m=geo['metadata'][index];lat,lon=m[5:7]
   if isinstance(lat,(int,float))and isinstance(lon,(int,float))and -34<=lat<=6 and -74<=lon<=-34:points[(m[1],m[0])]=(lat,lon)
geo_rows=[]
for i,r in enumerate(rows):
 points=locations.get(r['key'],{});r['coord']=np.mean(list(points.values()),axis=0).tolist() if points else None;r['locations']=len(points)
 if r['coord'] is not None:geo_rows.append(i)
coords=np.radians(np.asarray([rows[i]['coord']for i in geo_rows]));vectors=np.column_stack([np.cos(coords[:,0])*np.cos(coords[:,1]),np.cos(coords[:,0])*np.sin(coords[:,1]),np.sin(coords[:,0])]);tree=cKDTree(vectors);_,neighbors=tree.query(vectors,k=9);neighbors=np.asarray([[j for j in ns if j!=i][:8]for i,ns in enumerate(neighbors)]);assert neighbors.shape==(len(geo_rows),8);assert all(i not in ns for i,ns in enumerate(neighbors));spatial={}
for year in range(4):
 v=np.asarray([100*rows[i]['years'][year][4]/rows[i]['years'][year][3]for i in geo_rows]);z=v-v.mean();I=float((z*z[neighbors].mean(axis=1)).sum()/(z*z).sum());rng=np.random.default_rng(20261029);null=[]
 for _ in range(499):
  p=rng.permutation(z);null.append(float((p*p[neighbors].mean(axis=1)).sum()/(p*p).sum()))
 expected=-1/(len(v)-1);pvalue=(1+sum(abs(t-expected)>=abs(I-expected)for t in null))/500
 spatial[years[year]]={'moran_i':I,'permutation_p':pvalue,'permutations':499,'mean_abstention_municipal':float(v.mean()),'mapped':len(v),'neighbors':8}
 for j,i in enumerate(geo_rows):
  neighborMean=float(v[neighbors[j]].mean());rows[i].setdefault('spatial',{})[years[year]]={'neighbor_abstention':neighborMean,'high_high':bool(v[j]>v.mean()and neighborMean>v.mean())}
for j,i in enumerate(geo_rows):
 rows[i]['neighbors']=[rows[geo_rows[n]]['key']for n in neighbors[j]];chord=max(np.linalg.norm(vectors[j]-vectors[n]) for n in neighbors[j]);rows[i]['neighbor_farthest_km']=float(2*6371*np.arcsin(min(1,chord/2)))
coverage={'municipalities':len(rows),'excluded_nonpositive':excluded,'common_keys_including_exterior':len(keys),'ibge_joined':sum(r['ibge_code']is not None for r in rows),'ibge_complete':sum(all(v is not None for v in r['ibge'])for r in rows),'ibge_unmatched':[{'key':r['key'],'name':r['name']}for r in rows if r['ibge_code']is None],'mapped':len(geo_rows),'missing_coordinates':[r['key']for r in rows if r['coord']is None]}
output={'years':[2014,2018,2022,2026],'turn':2,'year_columns':['pt','opponent','validos','aptos','abstencoes','brancos_nulos'],'ibge_columns':['population','density','literacy','gdp_pc'],'coverage':coverage,'cluster_models':models,'cluster_standardization':{'means':mean.tolist(),'std':std.tolist(),'features':'Quatro participações PT nos válidos e quatro taxas de abstenção, segundo turno; padronização por coluna, municípios com pesos iguais; K-means, 12 inicializações, semente 20261029. Perfis ordenados pela participação PT em 2026. São agrupamentos de similaridade, não comunidades de rede nem previsão.'},'spatial':spatial,'ibge_sources':provenance,'coordinate_source':{'url':manifest['source'],'sha256':manifest['sha256'],'method':'Média dos locais de votação distintos por zona/local em cada município no segundo turno de 2026, com coordenadas oficiais válidas. Representa localização eleitoral aproximada, não centroide territorial IBGE; oito vizinhos mais próximos em esfera, sem exigir contiguidade.'},'join_method':'UF + nome municipal normalizado (acentos, espaços e pontuação removidos), somente correspondência exata e única; código IBGE mantido no resultado. Sem pareamento aproximado nem imputação das ausências. Não é uma tabela oficial de correspondência de códigos.','rows':rows}
reference=[]
for indicator in range(4):
 pairs=[(r['ibge'][indicator],100*r['years'][3][0]/r['years'][3][2]) for r in rows if r['ibge'][indicator] is not None];a,b=np.asarray(pairs).T;reference.append({'n':len(pairs),'pearson_raw':float(np.corrcoef(a,b)[0,1]),'spearman':float(spearmanr(a,b).statistic)})
output['correlation_reference_2026_vote']=reference
rng=np.random.default_rng(20261029);a=rng.integers(0,len(geo_rows),520000);b=rng.integers(0,len(geo_rows),520000);valid=a!=b;a=a[valid][:500000];b=b[valid][:500000];assert len(a)==500000
chord=np.linalg.norm(vectors[a]-vectors[b],axis=1);km=2*6371*np.arcsin(np.minimum(1,chord/2));edges=[0,25,50,100,200,400,800,1600,3200,6400];bins=np.searchsorted(edges,km,side='right')-1;assert bins.min()>=0 and bins.max()<9;counts=np.bincount(bins,minlength=9);curves={}
for year in range(4):
 totals=np.asarray([rows[i]['years'][year][3] for i in geo_rows]);absent=np.asarray([rows[i]['years'][year][4] for i in geo_rows]);assert np.all((absent>0)&(absent<totals));phi=np.log((totals-absent)/absent);z=(phi-phi.mean())/phi.std();sums=np.bincount(bins,weights=z[a]*z[b],minlength=9);curves[str(years[year])]={'correlation':[float(sums[i]/counts[i]) if counts[i] else None for i in range(9)],'pairs':counts.astype(int).tolist()}
output['spatial_correlogram']={'sample_pairs':len(a),'edges_km':edges,'years':curves,'method':'Amostra fixa de 500.000 pares de municípios distintos, sorteados uniformemente com reposição, semente 20261029; mesmos pares nas quatro eleições. phi = log((aptos-abstenções)/abstenções); z padronizado pela média e desvio-padrão municipal nacional. C(r) é a média de z_i*z_j por faixa de distância em esfera, não Pearson dentro da faixa, não teste causal. Referência nacional fixa nos filtros.'}

output['electoral_sources']=[{'year':y,'url':f'https://dadosabertos.tse.jus.br/dataset/resultados-{y}'} for y in years]
raw=json.dumps(output,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode();(root/'dados/estudos_territoriais_pacote.json').write_text(json.dumps({'codificacao':'gzip+base64','dados':base64.b64encode(gzip.compress(raw,mtime=0)).decode()},separators=(',',':')),encoding='utf8');print('Cobertura',json.dumps(coverage,ensure_ascii=False),flush=True);print('Moran',spatial,flush=True)
