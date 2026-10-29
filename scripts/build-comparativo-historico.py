import csv,gzip,json,base64,pathlib,collections,unicodedata
root=pathlib.Path('.').resolve(); hist=root.parent/'historico';regions={u:r for r,us in {'Norte':'AC AM AP PA RO RR TO','Nordeste':'AL BA CE MA PB PE PI RN SE','Centro-Oeste':'DF GO MS MT','Sudeste':'ES MG RJ SP','Sul':'PR RS SC','Exterior':'ZZ'}.items() for u in us.split()}
capitals={'AC':'RIO BRANCO','AL':'MACEIO','AM':'MANAUS','AP':'MACAPA','BA':'SALVADOR','CE':'FORTALEZA','DF':'BRASILIA','ES':'VITORIA','GO':'GOIANIA','MA':'SAO LUIS','MG':'BELO HORIZONTE','MS':'CAMPO GRANDE','MT':'CUIABA','PA':'BELEM','PB':'JOAO PESSOA','PE':'RECIFE','PI':'TERESINA','PR':'CURITIBA','RJ':'RIO DE JANEIRO','RN':'NATAL','RO':'PORTO VELHO','RR':'BOA VISTA','RS':'PORTO ALEGRE','SC':'FLORIANOPOLIS','SE':'ARACAJU','SP':'SAO PAULO','TO':'PALMAS'}
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',s.upper()) if unicodedata.category(c)!='Mn')
def read(path):
 raw=path.read_bytes()
 try:t=raw.decode('utf-8-sig')
 except UnicodeDecodeError:t=raw.decode('latin1')
 return csv.DictReader(t.splitlines(),delimiter=';')
def build(year):
 records={}
 for r in read(hist/f'{year}-apuracao.csv'):
  if r['CD_CARGO']!='1':continue
  key=r['SG_UF']+':'+r['CD_MUNICIPIO'].zfill(5);obj=records.setdefault(key,{'uf':r['SG_UF'],'code':r['CD_MUNICIPIO'].zfill(5),'name':r['NM_MUNICIPIO'],'turns':{}});d=obj['turns'].setdefault(r['NR_TURNO'],{k:0 for k in ['aptos','comparecimento','abstencoes','validos','bn','pt','opponent']})
  for k,col in [('aptos','QT_APTOS'),('comparecimento','QT_COMPARECIMENTO'),('abstencoes','QT_ABSTENCOES'),('validos','QT_TOTAL_VOTOS_VALIDOS')]:d[k]+=int(r[col])
  d['bn']+=int(r['QT_VOTOS_BRANCOS'])+int(r['QT_TOTAL_VOTOS_NULOS'])
 opp='45' if year==2014 else '17' if year==2018 else '22'
 for r in read(hist/f'{year}-votos.csv'):
  if r['CD_CARGO']!='1' or r['NR_CANDIDATO'] not in ['13',opp]:continue
  d=records[r['SG_UF']+':'+r['CD_MUNICIPIO'].zfill(5)]['turns'][r['NR_TURNO']];d['pt' if r['NR_CANDIDATO']=='13' else 'opponent']+=int(r.get('QT_VOTOS_NOMINAIS_VALIDOS') or r['QT_VOTOS_NOMINAIS'])
 return records
def main():
 h22=build(2022);h18=build(2018);current=json.loads(gzip.decompress((root/'dados/2026/municipios.json.gz').read_bytes()));c26={}
 for r in current:
  c26[r['uf']+':'+r['codigo_municipio_tse']]={'uf':r['uf'],'code':r['codigo_municipio_tse'],'name':r['municipio'],'turns':{str(t):{'aptos':r[f'aptos_{t}t'],'comparecimento':r[f'comparecimento_{t}t'],'abstencoes':r[f'abstencoes_{t}t'],'validos':r[f'validos_{t}t'],'bn':r[f'brancos_{t}t']+r[f'nulos_{t}t'],'pt':r[f'lula_validos_{t}t'],'opponent':r[f'flavio_validos_{t}t']}for t in [1,2]}}
 paired=[]
 for key in sorted(h22.keys()&c26.keys()):
  a,b=h22[key],c26[key];assert a['uf']==b['uf'];paired.append({'key':key,'uf':b['uf'],'region':regions[b['uf']],'name':b['name'],'capital':capitals.get(b['uf'])==norm(b['name']),'y2022':a['turns'],'y2026':b['turns']})
 out={'years':[2022,2026],'method':'Pareamento por UF + código municipal TSE; votos e denominadores somados. Geometrias municipais não são presumidas idênticas entre eleições. Exterior separado. Brasília e Fernando de Noronha seguem as unidades eleitorais da base.','sources':['https://dadosabertos.tse.jus.br/dataset/resultados-2022','https://dadosabertos.tse.jus.br/dataset/resultados-2026'],'coverage':{'matched':len(paired),'brazil_matched':sum(r['uf']!='ZZ' for r in paired),'only2022':sorted(h22.keys()-c26.keys()),'only2026':sorted(c26.keys()-h22.keys()),'capitals':sum(r['capital'] for r in paired)},'rows':paired}
 (root/'dados/comparativo_historico_pacote.json').write_text(json.dumps({'codificacao':'gzip+base64','dados':base64.b64encode(gzip.compress(json.dumps(out,ensure_ascii=False,separators=(',',':')).encode())).decode()},separators=(',',':')),encoding='utf8')
 (root.parent/'model_input_municipal.json').write_text(json.dumps({'2018':h18,'2022':h22,'2026':c26},ensure_ascii=False),encoding='utf8');print(json.dumps(out['coverage'],ensure_ascii=False),flush=True)
 
 
 

if __name__=='__main__':main()
