"""Verificação independente dos ZIPs do TSE contra manifesto versionado.

Uso:
  python verificar_arquivos_tse.py --pasta outputs/tse_2026 --manifesto dados/2026/downloads.json
Exige os quatro arquivos originais na pasta indicada. Não baixa arquivos.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path

def verificar(pasta,manifesto):
    entries=json.loads(Path(manifesto).read_text(encoding='utf-8-sig'))
    results=[]
    for entry in entries:
        filename=entry['url'].rsplit('/',1)[-1].split('?',1)[0]
        path=Path(pasta)/filename
        result={'arquivo':filename,'presente':path.is_file(),'sha256_esperado':entry['sha256']}
        if not path.is_file():
            result['status']='AUSENTE'
            results.append(result)
            continue
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(4*1024*1024),b''):
                h.update(block)
        result['bytes']=path.stat().st_size()
        result['sha256_obtido']=h.hexdigest()
        result['tamanho_confere']=result['bytes']==int(entry['bytes'])
        result['hash_confere']=result['sha256_obtido'].lower()==entry['sha256'].lower()
        if not result['tamanho_confere'] or not result['hash_confere']:
            result['status']='DIVERGENTE'
        else:
            with zipfile.ZipFile(path) as z:
                result['crc_primeiro_erro']=z.testzip()
                result['membros_esperados_ausentes']=sorted(
                    set(m['nome'] for m in entry['membros'])-set(z.namelist()))
            result['status']='APROVADO' if result['crc_primeiro_erro'] is None and not result['membros_esperados_ausentes'] else 'DIVERGENTE'
        results.append(result)
    return {'status':'APROVADO' if results and all(x['status']=='APROVADO' for x in results) else 'PENDENTE_OU_DIVERGENTE','arquivos':results}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--pasta',required=True)
    p.add_argument('--manifesto',default='dados/2026/downloads.json')
    p.add_argument('--saida',default='resultado_verificacao_zip.json')
    args=p.parse_args()
    result=verificar(args.pasta,args.manifesto)
    Path(args.saida).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['status']=='APROVADO' else 2)
