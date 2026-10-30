#!/usr/bin/env python3
"""Confronta saldo TTE por secao com variacao de aptos na base do projeto.
Nao presume que transferencia temporaria prove causalidade de todas as mudancas.
"""
import csv,gzip,json,pathlib,collections,urllib.request,zipfile,io,hashlib
ROOT=pathlib.Path("dados/2026")
OUT=pathlib.Path("experimentos/modelo_999/resultados");OUT.mkdir(parents=True,exist_ok=True)
URL="https://cdn.tse.jus.br/estatistica/sead/odsele/transf_temporaria_secao/transf_temporaria_secao_2026.zip"
def norm(x):return str(x).strip().lstrip("0") or "0"
def key(uf,municipio,zona,secao):return (str(uf).upper(),norm(municipio),norm(zona),norm(secao))
def load_aptos():
 result={}
 for p in sorted(ROOT.glob("secoes-*.json.gz")):
  uf=p.stem.split("-")[1].split(".")[0]
  with gzip.open(p,"rt",encoding="utf-8") as f:d=json.load(f)
  ix={x:i for i,x in enumerate(d["colunas"])}
  for row in d["linhas"]:
   k=key(uf,row[ix["codigo_municipio_tse"]],row[ix["zona"]],row[ix["secao"]])
   if k in result:raise ValueError("Chave duplicada base aptos: "+str(k))
   a,b=row[ix["aptos_1t"]],row[ix["aptos_2t"]]
   if a is not None and b is not None:result[k]=int(b)-int(a)
 return result
def download():
 req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0"})
 with urllib.request.urlopen(req,timeout=120) as r:data=r.read()
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  assert z.testzip() is None
  names=[n for n in z.namelist() if n.lower().endswith(".csv")]
  assert len(names)==1,names
  content=z.read(names[0])
 return content,hashlib.sha256(data).hexdigest()
def tte_rows(data):
 text=data.decode("latin-1")
 rd=csv.DictReader(io.StringIO(text),delimiter=";")
 print("TTE columns:",rd.fieldnames)
 for r in rd:yield r
def parse_tte(data):
 totals=collections.Counter();rows=0
 for r in tte_rows(data):
  rows+=1
  # Canonical TSE schema: origem/destino and section numbers
  # Discover schema dynamically, fail closed on ambiguity
  if rows==1:
   cols=list(r)
   print("TTE schema",cols)
   globals()["_cols"]=cols
  cols=_cols
  def field(*fragments):
   hits=[c for c in cols if all(f in c.upper() for f in fragments)]
   if len(hits)!=1:raise ValueError("Campo ambiguo "+str(fragments)+": "+str(hits))
   return r[hits[0]]
  turn=int(field("TURNO"))
  qt=int(field("QT","ELEITOR")) if any("QT_ELEITOR" in c for c in cols) else 1
  for suffix,sign in (("ORIGEM",-1),("DESTINO",1)):
   uf=field("UF",suffix)
   mun=field("MUNICIPIO",suffix)
   zona=field("ZONA",suffix)
   sec=field("SECAO",suffix)
   totals[(key(uf,mun,zona,sec),turn)]+=sign*qt
 changes=collections.Counter()
 for (k,t),v in totals.items():changes[k]+=v*(1 if t==2 else -1)
 return dict(changes),rows
def main():
 report={"fonte_tte":URL,"estado":"INCOMPLETO"}
 try:
  aptos=load_aptos()
  report["secoes_base"]=len(aptos)
  data,sha=download();report["tte_zip_sha256"]=sha
  tte,n=parse_tte(data);report["registros_tte"]=n
  keys=set(aptos)|set(tte)
  exact=sum(aptos.get(k,0)==tte.get(k,0) for k in keys)
  nonzero_aptos={k for k,v in aptos.items() if v}
  nonzero_tte={k for k,v in tte.items() if v}
  mismatch=[(k,aptos.get(k,0),tte.get(k,0)) for k in keys if aptos.get(k,0)!=tte.get(k,0)]
  report.update(estado="CONCLUIDO",secoes_uniao=len(keys),correspondencias_exatas=exact,
    divergencias=len(mismatch),secoes_aptos_divergentes=len(nonzero_aptos),
    secoes_tte_divergentes=len(nonzero_tte),
    intersecao_secoes_divergentes=len(nonzero_aptos&nonzero_tte),
    aptos_divergentes_sem_tte=len(nonzero_aptos-nonzero_tte),
    tte_divergente_sem_aptos=len(nonzero_tte-nonzero_aptos),
    exemplos_divergentes=[{"chave":k,"delta_aptos":a,"delta_tte":t} for k,a,t in sorted(mismatch)[:100]])
 except Exception as e:report["erro"]=repr(e)
 (OUT/"cruzamento_tte_aptos.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({k:v for k,v in report.items() if k!="exemplos_divergentes"},ensure_ascii=False))
if __name__=="__main__":main()
