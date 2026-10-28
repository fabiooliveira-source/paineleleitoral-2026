import csv,json,collections,heapq,pathlib,argparse
parser=argparse.ArgumentParser(description='Analisar CSVs comparativos conferidos do TSE')
parser.add_argument('--base',required=True,help='Pasta com comparacao_municipios.csv e comparacao_secoes.csv')
parser.add_argument('--saida',required=True,help='Pasta de destino da análise JSON')
args=parser.parse_args()
base=pathlib.Path(args.base)
out=pathlib.Path(args.saida)
out.mkdir(parents=True,exist_ok=True)
def rows(name):
 with (base/name).open(encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f,delimiter=';'):
   for k,v in r.items():
    if k.startswith(('dif_','comparecimento_','lula_','flavio_','validos_','brancos_','nulos_','aptos_','abstencoes_')) and v:
     try:r[k]=int(v)
     except ValueError:pass
   yield r
def winner(r,t):
 a,b=r['lula_'+t],r['flavio_'+t]
 return 'lula' if a>b else 'flavio' if b>a else 'empate'
def summarize(rs,section=False):
 c=collections.Counter();top={f'{p}_{d}':[] for p in ['lula','flavio'] for d in ['perdas','ganhos']}
 for i,r in enumerate(rs):
  c['total']+=1
  if section and any(r['situacao_dados_'+t]!='conferido' for t in ['1t','2t']):c['nao_comparaveis']+=1;continue
  c['comparaveis']+=1
  a,b=winner(r,'1t'),winner(r,'2t')
  if a!=b:c['lideranca_'+a+'_para_'+b]+=1
  for p in ['lula','flavio']:
   v=r['dif_'+p];d='perdas' if v<0 else 'ganhos' if v>0 else 'estavel';c[p+'_'+d]+=1
   if v<0:
    turnout=r['dif_comparecimento'];c[p+'_perdeu_comparecimento_'+('subiu' if turnout>0 else 'caiu' if turnout<0 else 'igual')]+=1
   if v:
    key=p+'_'+d;score=abs(v)
    item=(score,i,r)
    if len(top[key])<30:heapq.heappush(top[key],item)
    elif score>top[key][0][0]:heapq.heapreplace(top[key],item)
 return {'contagens':dict(c),'rankings':{k:[r for _,_,r in sorted(v,reverse=True)] for k,v in top.items()}}
municipal=list(rows('comparacao_municipios.csv'))
result={'data':'2026-10-28','fonte':'https://dadosabertos.tse.jus.br/dataset/resultados-2026','brasil':summarize(r for r in municipal if r['uf']!='ZZ'),'exterior':summarize(r for r in municipal if r['uf']=='ZZ')}
result['secoes']=summarize(rows('comparacao_secoes.csv'),True)
(out/'analise_microdados.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
print(json.dumps({k:v['contagens'] for k,v in result.items() if isinstance(v,dict)},ensure_ascii=False,indent=2))

