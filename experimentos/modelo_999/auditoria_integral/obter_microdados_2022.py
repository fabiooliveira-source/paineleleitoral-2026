import urllib.request,pathlib,hashlib,json,zipfile,datetime,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parent/'microdados';ROOT.mkdir(exist_ok=True)
SOURCES={
'Historico_Totalizacao_Presidente_BR_1T_2022.zip':'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_1T_2022.zip',
'detalhe_votacao_secao_2022.zip':'https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip',
'votacao_secao_2022_BR.zip':'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2022_BR.zip',
'Historico_Totalizacao_Presidente_BR_2T_2022.zip':'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_2T_2022.zip'}
EXPECTED_SHA256={'Historico_Totalizacao_Presidente_BR_1T_2022.zip': '55961aa1ecc87d0fd9c02730864f1b69a9f2eb3456327542dfc507217cd74a05', 'detalhe_votacao_secao_2022.zip': 'ad22c50b9e6d9dfb096a2170680a190f1734895ba89d8977b95fd63ca02c03da', 'votacao_secao_2022_BR.zip': '9353993de5cf03778aef44e01d4925e7ee105f5262491d344a2f0dbc956b0139', 'Historico_Totalizacao_Presidente_BR_2T_2022.zip': '1f12128fbcfacab755e0e83d9c0a350ed99ae68ea3d024aaa7bc58fe0c1dda3c'}
def download(item):
 name,url=item;p=ROOT/name
 if not p.exists():
  with urllib.request.urlopen(url,timeout=60) as r,open(str(p)+'.part','wb') as f:
   while True:
    b=r.read(1024*1024)
    if not b:break
    f.write(b)
  pathlib.Path(str(p)+'.part').rename(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 assert h.hexdigest()==EXPECTED_SHA256[name], 'Hash de origem alterado: '+name
 with zipfile.ZipFile(p) as z:
  bad=z.testzip();assert bad is None,bad
  members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist()]
  print(json.dumps({'name':name,'bytes':p.stat().st_size,'members':members[:4]},ensure_ascii=False),flush=True)
 return {'name':name,'source_url':url,'bytes':p.stat().st_size,'sha256':h.hexdigest(),'zip_crc_ok':True,'members':members,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(3) as pool:manifest=list(pool.map(download,SOURCES.items()))
 (ROOT/'manifesto_microdados_2022.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 for x in manifest:print(x['name'],x['sha256'],flush=True)
