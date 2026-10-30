"""Consulta catálogo oficial e URLs EA13/índices; preserva evidências e bytes."""
import urllib.request,urllib.error,json,hashlib,pathlib,concurrent.futures,datetime,argparse
ROOT=pathlib.Path(__file__).resolve().parent/'fontes_2022'
UF='AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO ZZ'.split()
BASE='https://resultados.tse.jus.br/oficial/ele2022/545'
def get(item):
 name,url=item
 try:
  with urllib.request.urlopen(url,timeout=15) as r:
   b=r.read();result={'name':name,'url':url,'status':r.status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
   ROOT.mkdir(exist_ok=True);(ROOT/name).write_bytes(b)
   if name.endswith('.json'):
    try:result['keys']=list(json.loads(b))[:20]
    except (ValueError,TypeError):result['valid_json']=False
   return result
 except urllib.error.HTTPError as e:return {'name':name,'url':url,'status':e.code}
 except Exception as e:return {'name':name,'url':url,'status':None,'error':str(e)}
def run():
 resources=[('catalogo_resultados_2022.json','https://dadosabertos.tse.jus.br/api/3/action/package_show?id=resultados-2022')]
 for u in ['BR']+UF:
  lo=u.lower()
  resources.append((f'{lo}-c0001-e000545-t.json',f'{BASE}/dados/{lo}/{lo}-c0001-e000545-t.json'))
 for u in ['br','sp','ba']:
  resources.append((f'{u}-e000545-i.json',f'{BASE}/config/{u}/{u}-e000545-i.json'))
 with concurrent.futures.ThreadPoolExecutor(4) as pool:results=list(pool.map(get,resources))
 out={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'documentation':'https://www.tse.jus.br/eleicoes/eleicoes-2022/arquivos/interessados','catalog':'https://dadosabertos.tse.jus.br/dataset/resultados-2022','probes':results,'conclusion':'Consultar resultados; falha de endpoint nao prova inexistencia de acervo em outra fonte.'}
 path=pathlib.Path(__file__).resolve().parent/'disponibilidade_uf_2022.json';path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'requests':len(results),'statuses':{str(k):sum(x['status']==k for x in results) for k in set(x['status'] for x in results)},'output':str(path)}))
if __name__=='__main__':run()
