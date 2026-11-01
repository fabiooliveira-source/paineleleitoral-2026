"""Reprocessamento independente: benchmark IDW2 dos totais de 2o turno.
Nao reproduz a regressao ecologica original; nao valida transferencias individuais.
"""
import gzip,base64,json,hashlib,math,pathlib
import numpy as np
from scipy.spatial import cKDTree
root=pathlib.Path("dados/2026")
ufs=[p.name.split("-")[1].split(".")[0] for p in root.glob("secoes-*.json.gz") if "-ZZ." not in p.name]
ufs=sorted(set(ufs))
rows=[]
for uf in ufs:
 p=root/f"secoes-{uf}.json.gz"
 obj=json.load(gzip.open(p,"rt"));columns=obj["colunas"]
 idx={c:i for i,c in enumerate(columns)}
 geo={}
 for path in sorted(root.glob(f"locais-geograficos-{uf}-*.json")):
  g=json.loads(gzip.decompress(base64.b64decode(json.loads(path.read_text())["parte"])))
  metadata=g["metadata"]
  for mun,places in g["turns"].get("1",{}).items():
   for metaidx,sections in places:
    m=metadata[metaidx]
    if len(m)<7 or m[5] is None or m[6] is None:continue
    lat,lon=float(m[5]),float(m[6])
    if not (-90<=lat<=90 and -180<=lon<=180):continue
    for sec in sections:
     # section record: [section number, Lula, Flavio, ...]
     geo[(str(mun),str(m[1]),str(sec[0]))]=(lat,lon)
 for a in obj["linhas"]:
  try:
   key=(str(a[idx["codigo_municipio_tse"]]),str(a[idx["zona"]]),str(a[idx["secao"]]))
   coord=geo.get(key)
   if coord is None:continue
   apt1=int(a[idx["aptos_1t"]]);apt2=int(a[idx["aptos_2t"]])
   if apt1<=0 or apt1!=apt2:continue
   if a[idx["situacao_dados_1t"]]!="conferido" or a[idx["situacao_dados_2t"]]!="conferido":continue
   if str(a[idx["mesmo_local_votacao"]]).lower()!="true":continue
   first=np.array([int(a[idx[c+"_1t"]]) for c in ("lula","flavio","brancos","nulos","abstencoes")])
   second=np.array([int(a[idx[c+"_2t"]]) for c in ("lula","flavio","brancos","nulos","abstencoes")])
   if min(first.min(),second.min())<0 or first.sum()>apt1 or second.sum()!=apt1:continue
   rows.append((uf,*coord,apt1,*first,*second))
  except (ValueError,TypeError,KeyError,IndexError):continue
 print(uf,"matched",sum(x[0]==uf for x in rows),flush=True)
assert len(rows)>100000,f"Poucas secoes georreferenciadas: {len(rows)}"
lat=np.asarray([r[1] for r in rows]);lon=np.asarray([r[2] for r in rows])
apt=np.asarray([r[3] for r in rows],dtype=float)
first=np.asarray([r[4:9] for r in rows],dtype=float)/apt[:,None]
second=np.asarray([r[9:14] for r in rows],dtype=float)/apt[:,None]
uf=np.asarray([r[0] for r in rows])
latcell=np.floor(lat/0.5).astype(int);loncell=np.floor(lon/0.5).astype(int)
def fold(a,b):return int(hashlib.sha256(f"{a}:{b}".encode()).hexdigest(),16)%5
cells=list(zip(latcell,loncell));cache={c:fold(*c) for c in set(cells)}
folds=np.fromiter((cache[c] for c in cells),dtype=np.int8,count=len(cells))
train=folds>=2;test=folds==0
assert train.sum()>10000 and test.sum()>10000
def xyz(la,lo):
 la=np.radians(la);lo=np.radians(lo)
 return np.column_stack((np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)))
coords=xyz(lat,lon)
prediction=np.full((len(rows),5),np.nan)
for state in sorted(set(uf)):
 ti=np.flatnonzero(test&(uf==state));tr=np.flatnonzero(train&(uf==state))
 if len(ti)==0 or len(tr)<8:continue
 tree=cKDTree(coords[tr]);dist,neighbors=tree.query(coords[ti],k=8,workers=2)
 # identical locations use equal weights among all zero-distance neighbors
 weights=np.where(dist<1e-12,1e24,1/np.maximum(dist,1e-12)**2)
 weights/=weights.sum(axis=1,keepdims=True)
 prediction[ti]=(weights[:,:,None]*second[tr[neighbors]]).sum(axis=1)
valid=test&np.isfinite(prediction).all(axis=1)
assert valid.sum()>10000
err=np.abs(prediction[valid]-second[valid])
w=apt[valid]
names=["Lula","Flavio Bolsonaro","Brancos","Nulos","Abstencoes"]
indicators={}
for k,name in enumerate(names):
 indicators[name]={"mae_pp":round(float(100*err[:,k].mean()),6),"weighted_mae_pp":round(float(100*np.average(err[:,k],weights=w)),6),"mae_votos_por_secao":round(float(np.mean(err[:,k]*w)),4)}
report={"method":"NOVO benchmark IDW2 8 vizinhos por UF, sem regressao ecologica; nao reproduz MAE 1.54 p.p. publicado","split":"blocos de 0.5 graus; SHA256(latcell:loncell)%5; teste 0, ajuste 1, treino 2-4","train_sections":int(train.sum()),"test_sections":int(valid.sum()),"excluded_no_geo_or_quality":None,"indicators":indicators,"global_finalists_weighted_mae_pp":round((indicators["Lula"]["weighted_mae_pp"]+indicators["Flavio Bolsonaro"]["weighted_mae_pp"])/2,6),"caveat":"Nao mede erros de transferencia individual; vizinhos com mesmo local podem correlacionar; geocodificacao e origem de dados ainda exigem auditoria independente."}
out=root/"reprocessamento-mae-indicadores.json";out.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
