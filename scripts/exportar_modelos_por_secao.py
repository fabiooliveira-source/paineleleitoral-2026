"""Rebuild and export section/block coefficients for the five existing spatial models.
Run from the repository root: python scripts/exportar_modelos_por_secao.py
Requires numpy/scipy; preserves the original fit protocol and reserved test split.
Outputs JSON gzip+base64 packages to dados/2026.
"""
import pathlib,tempfile,shutil,json,gzip,base64,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
UFS='AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ'.split()
EXPORT_CODE = "# Export the five fitted coefficient banks and the exact section/block mapping.\nimport gzip,base64\nexport=P/'export';export.mkdir(exist_ok=True)\nfor uf in src.UFS:\n mask=ufs==uf;indices=np.flatnonzero(mask);blocks=sorted(set(ci[mask]));coeff={}\n for block in blocks:\n  coeff[str(block)]=[(ufp[uf] if model_index==0 else bank_i.get(uf+':'+str(block),ufp[uf])).tolist() for model_index,bank_i in enumerate(ratebanks)]\n pack={'schema':1,'uf':uf,'origins':src.ORIGINS,'codes':src.CODES,'destinations':src.DEST,'models':[{'method':m['method'],'k':m['k']} for m in results],'selected_index':selected,'sections':[[':'.join(section_keys[i]),int(ci[i]),'test' if test[i] else 'selection' if tune[i] else 'train' if train[i] else 'unmapped'] for i in indices],'coefficients':coeff,'metric':'Mean absolute deviation across five fitted models, percentage points; not true transfer error or 95% confidence','source':'Repository derivatives; no independent TSE authentication'}\n raw=json.dumps(pack,separators=(',',':'),ensure_ascii=False).encode();z=gzip.compress(raw,mtime=0)\n (export/f'transferencias-modelos-{uf}.json').write_text(json.dumps({'codificacao':'gzip+base64','dados':base64.b64encode(z).decode()},separators=(',',':')))\n print('EXPORTED',uf,len(indices),len(blocks),len(z),flush=True)\n"
with tempfile.TemporaryDirectory(prefix='modelos-secao-') as tmp:
 p=pathlib.Path(tmp);data=ROOT/'dados/2026';source=ROOT/'experimentos/migracao_brasil'
 shutil.copy(source/'analisar_migracao_brasil.py',p/'analisar_migracao_brasil.py')
 manifest=json.loads((data/'locais-geograficos-manifest.json').read_text())
 for uf in UFS:
  (p/f'secoes-{uf}.json').write_bytes(gzip.decompress((data/f'secoes-{uf}.json.gz').read_bytes()))
  (p/f'candidatos-secao-{uf}.json').write_bytes(gzip.decompress(base64.b64decode(json.loads((data/f'candidatos-secao-{uf}.json').read_text())['dados'])))
  if uf!='ZZ':
   parts=''.join(json.loads((data/f'locais-geograficos-{uf}-{i}.json').read_text())['parte'] for i in range(manifest['ufs'][uf]['parts']))
   (p/f'geo-{uf}.json').write_bytes(gzip.decompress(base64.b64decode(parts)))
 code=(source/'ajustar_espacial.py').read_text().replace('xs=[];ys=[];ufs=[];coords=[]','xs=[];ys=[];ufs=[];coords=[];section_keys=[]').replace("a,b,keys=ns['extract'](uf);mapping={}","a,b,keys=ns['extract'](uf);section_keys.extend([list(map(str,k)) for k in keys]);mapping={}")
 (p/'ajustar_espacial.py').write_text(code+'\n'+EXPORT_CODE)
 subprocess.run([sys.executable,str(p/'ajustar_espacial.py')],check=True)
 for f in (p/'export').glob('*.json'):shutil.copy(f,data/f.name)
