"""Cenários ecológicos contábeis, não observações individuais nem modelo calibrado."""
import json,pathlib,hashlib,collections
import numpy as np
P=pathlib.Path(__file__).resolve().parent
UFS='AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ'.split()
NAMES={'13':'Lula','22':'Flávio'}
for uf in UFS:NAMES.update(json.loads((P/f'candidatos-secao-{uf}.json').read_text())['nomes'])
CODES=['13','22']+sorted(k for k in NAMES if k not in ['13','22'])
ORIGINS=[NAMES[k] for k in CODES]+['Brancos','Nulos','Abstenções','Não classificado / ajuste']
DEST=['Lula','Flávio','Brancos','Nulos','Abstenções','Não classificado / ajuste']
def analyze(uf):
 s=json.loads((P/f'secoes-{uf}.json').read_text());c=json.loads((P/f'candidatos-secao-{uf}.json').read_text());cols={k:i for i,k in enumerate(s['colunas'])};candidate={tuple(r[:3]):r[3:] for r in c['linhas']};assert len(candidate)==len(c['linhas'])
 rows=[];targets=[];strict=[];excluded=collections.Counter();seen=set()
 for row in s['linhas']:
  key=tuple(row[:3]);assert key not in seen;seen.add(key)
  def n(k):return int(row[cols[k]]) if row[cols[k]] not in [None,''] else 0
  if any(row[cols['situacao_dados_'+t]]!='conferido' for t in ['1t','2t']):excluded['dados_nao_conferidos']+=1;continue
  if key not in candidate:excluded['sem_detalhe_candidatos']+=1;continue
  votes=dict(zip(c['numeros'],candidate[key]));a=[n('lula_1t'),n('flavio_1t')]+[int(votes.get(k,0)) for k in CODES[2:]]
  if sum(a)!=n('nominais_1t'):excluded['nominais_1t_nao_conciliados']+=1;continue
  if n('lula_2t')+n('flavio_2t')!=n('nominais_2t'):excluded['nominais_2t_nao_conciliados']+=1;continue
  a += [n('brancos_1t'),n('nulos_1t'),n('abstencoes_1t')]
  b=[n('lula_2t'),n('flavio_2t'),n('brancos_2t'),n('nulos_2t'),n('abstencoes_2t')]
  if any(x<0 for x in a+b):excluded['contagem_negativa']+=1;continue
  M=max(n('aptos_1t'),n('aptos_2t'),sum(a),sum(b))
  if not M:excluded['universo_zero']+=1;continue
  a.append(M-sum(a));b.append(M-sum(b));rows.append(a);targets.append(b)
  strict.append(n('aptos_1t')==n('aptos_2t') and n('aptos_1t')>0 and str(row[cols['mesmo_local_votacao']]).lower()=='true' and a[-1]==0 and b[-1]==0)
 a=np.array(rows,dtype=float);b=np.array(targets,dtype=float);M=a.sum(axis=1);rs=a.copy();cs=b.copy();matrix=np.zeros((len(a),len(ORIGINS),6))
 # Cenário de permanência máxima das categorias que existem nos dois turnos.
 for i,j in [(0,0),(1,1),(len(CODES),2),(len(CODES)+1,3),(len(CODES)+2,4),(len(CODES)+3,5)]:
  v=np.minimum(rs[:,i],cs[:,j]);matrix[:,i,j]=v;rs[:,i]-=v;cs[:,j]-=v
 rest=rs.sum(axis=1);matrix+=rs[:,:,None]*cs[:,None,:]/np.where(rest>0,rest,1)[:,None,None]
 assert np.max(np.abs(matrix.sum(axis=2)-a))<1e-8
 assert np.max(np.abs(matrix.sum(axis=1)-b))<1e-8
 independence=a[:,:,None]*b[:,None,:]/M[:,None,None]
 lower=np.maximum(0,a[:,:,None]+b[:,None,:]-M[:,None,None]);upper=np.minimum(a[:,:,None],b[:,None,:])
 assert np.all(matrix>=lower-1e-8) and np.all(matrix<=upper+1e-8)
 hist={}
 for i,code in enumerate(CODES):
  mask=a[:,i]>0;bins=[]
  for j in [0,1]:
   rates=100*matrix[mask,i,j]/a[mask,i];index=np.minimum(19,np.maximum(0,np.floor((rates+1e-10)/5).astype(int)))
   bins.append({'urnas':np.bincount(index,minlength=20).tolist(),'votos_origem':np.bincount(index,weights=a[mask,i],minlength=20).astype(int).tolist()})
  hist[code]=bins
 comparable=np.array(strict)
 return {'uf':uf,'total_sections':len(s['linhas']),'included_sections':len(a),'strictly_comparable_sections':int(sum(strict)),'excluded':dict(excluded),'first':a.sum(axis=0).tolist(),'second':b.sum(axis=0).tolist(),'matrix':matrix.sum(axis=0).tolist(),'independence':independence.sum(axis=0).tolist(),'strict_matrix':matrix[comparable].sum(axis=0).tolist(),'lower':lower.sum(axis=0).tolist(),'upper':upper.sum(axis=0).tolist(),'histograms':hist}
def main():
 states=[]
 for uf in UFS:
  r=analyze(uf);states.append(r);print(uf,r['included_sections'],'/',r['total_sections'],flush=True)
 manifest=[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(P.glob('*.json')) if p.name.startswith(('secoes-','candidatos-secao-'))]
 out={'title':'Brasil + exterior — migração simulada por seção','source':'Derivados no repositório paineleleitoral-2026, dados/2026; autenticidade oficial não revalidada nesta execução','source_reference_commit':'104b8adbecbee2261b9b4883eb46ef6352996dd4','codes':CODES,'origins':ORIGINS,'destinations':DEST,'method':'Permanência máxima local; oferta e demanda remanescentes alocadas proporcionalmente. Cenário alternativo: independência completa por seção. Limites de Fréchet somados por seção, condicionados a universo comum.','limitations':['Fluxos não identificados individualmente. Seções de mesmo tamanho não comprovam mesmas pessoas.','Permanência máxima é hipótese forte que reduz artificialmente a troca entre finalistas.','Eliminados recebem a mesma proporção dos destinos residuais dentro de cada seção; diferenças nacionais vêm da distribuição territorial e não de preferências partidárias identificadas.','Todas as seções disponíveis foram avaliadas; seções sem conciliação ou dados conferidos são excluídas explicitamente.','Não classificado / ajuste é resíduo de universo, não eleitor com comportamento observado.','Os limites condicionais não são intervalos de confiança. Cenários não constituem certificação ou probabilidades.'],'states':states,'source_files':manifest}
 (P/'migracao-brasil-dados.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 print('TOTAL',sum(s['included_sections'] for s in states),'/',sum(s['total_sections'] for s in states),flush=True)
if __name__=='__main__':main()
