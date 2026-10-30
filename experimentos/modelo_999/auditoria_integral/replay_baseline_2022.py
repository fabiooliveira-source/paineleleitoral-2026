import urllib.request,zipfile,io,hashlib,csv,json,datetime,pathlib
URL='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_2T_2022.zip'
def run():
 raw=urllib.request.urlopen(URL,timeout=60).read()
 z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
 name=next(n for n in z.namelist() if n.endswith('.csv'))
 data=z.read(name)
 rows=list(csv.DictReader(io.StringIO(data.decode('latin1')),delimiter=';'))
 rows=[{k.strip():v.strip() for k,v in r.items()} for r in rows]
 def stamp(r):return datetime.datetime.strptime(r['DT_TOTALIZACAO'],'%d/%m/%Y %H:%M:%S')
 assert all(stamp(a)<=stamp(b) for a,b in zip(rows,rows[1:])), 'Ordem temporal inconsistente'
 A='LULA_QT_VOTOS_TOT_ACUMULADO';B='JAIR_BOLSONARO_QT_VOTOS_TOT_ACUMULADO';S='QT_SECOES_TOT_ACUMULADO'
 target=100*int(rows[-1][A])/(int(rows[-1][A])+int(rows[-1][B]))
 revisions={c:sum(int(b[c])<int(a[c]) for a,b in zip(rows,rows[1:])) for c in [A,B,S]}
 points=[]
 for pct in range(5,100,5):
  r=next(r for r in rows if 100*int(r[S])/int(r['QT_SECOES_TOTAL'])>=pct)
  prediction=100*int(r[A])/(int(r[A])+int(r[B]))
  points.append({'threshold_pct':pct,'timestamp':r['DT_TOTALIZACAO'],'prediction_lula_pct':prediction,'error_pp':prediction-target})
 result={'status':'BASELINE_NACIONAL_2022_EXECUTADO_MODELO_TERRITORIAL_NAO_TESTADO','source_url':URL,'zip_sha256':hashlib.sha256(raw).hexdigest(),'csv_sha256':hashlib.sha256(data).hexdigest(),'zip_crc_ok':True,'rows':len(rows),'first_timestamp':rows[0]['DT_TOTALIZACAO'],'last_timestamp':rows[-1]['DT_TOTALIZACAO'],'scopes':sorted(set(r['SG_UE_UF'] for r in rows)),'revisions':revisions,'final_lula_pct':target,'mae_pp':sum(abs(p['error_pp']) for p in points)/19,'max_abs_error_pp':max(abs(p['error_pp']) for p in points),'bias_pp':sum(p['error_pp'] for p in points)/19,'checkpoints':points,'limitations':['Baseline observado nacional; nao valida o modelo territorial congelado.','Referencia final usada somente na avaliacao de erro.','Cobertura usa QT_SECOES_TOTAL da propria linha contemporanea.','Hash local assegura identidade dos bytes baixados, nao autenticidade criptografica assinada pelo TSE.','Checkpoints correlacionados de uma unica eleicao; sem calibracao probabilistica.','Script congelado audit-v1 ainda precisa ser identificado e ter hash confrontado.']}
 return result
if __name__=='__main__':
 result=run();pathlib.Path('/tmp/backtest2022_resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checkpoints'},ensure_ascii=False))
