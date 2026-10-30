#!/usr/bin/env python3
"""Auditoria reprodutível das pesquisas presidenciais de 2026.
Uso: python auditar_pesquisas.py --pesquisas pesquisas_2turno_matriz_preliminar.csv --lula-votos N --flavio-votos N --saida auditoria_pesquisas_resultado.csv
Exige percentuais no denominador de votos válidos, com documentação original conferida.
"""
import argparse,csv,math
from pathlib import Path

def number(s):
    try:return float(str(s).strip().replace(',','.'))
    except (ValueError,TypeError):return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pesquisas',required=True)
    p.add_argument('--lula-votos',required=True,type=int)
    p.add_argument('--flavio-votos',required=True,type=int)
    p.add_argument('--saida',default='auditoria_pesquisas_resultado.csv')
    p.add_argument('--permitir-provisorios',action='store_true',help='Apenas simulação exploratória, nunca resultado auditado')
    a=p.parse_args()
    assert a.lula_votos>=0 and a.flavio_votos>=0 and a.lula_votos+a.flavio_votos>0
    lula=100*a.lula_votos/(a.lula_votos+a.flavio_votos)
    with open(a.pesquisas,encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    result=[]
    for r in rows:
        lp=number(r.get('lula_validos_pct'));fp=number(r.get('flavio_validos_pct'))
        verified=str(r.get('registro_conferido_pesqele','')).upper()=='SIM' and str(r.get('relatorio_original_obtido','')).upper()=='SIM'
        if lp is None or fp is None:continue
        if not math.isclose(lp+fp,100,abs_tol=.3):
            print('Ignorado: denominador inconsistente',r.get('instituto'));continue
        if not verified and not a.permitir_provisorios:
            print('Ignorado: documentação não conferida',r.get('instituto'));continue
        err=lp-lula
        result.append(dict(instituto=r['instituto'],registro=r.get('registro_informado_na_imprensa',''),documentacao='CONFERIDA' if verified else 'PROVISORIA',lula_pesquisa_pct=lp,flavio_pesquisa_pct=fp,lula_oficial_pct=round(lula,6),erro_lula_pp=round(err,6),erro_absoluto_pp=round(abs(err),6),inversao_lideranca=(lp>50)!=(lula>50)))
    with open(a.saida,'w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['instituto','registro','documentacao','lula_pesquisa_pct','flavio_pesquisa_pct','lula_oficial_pct','erro_lula_pp','erro_absoluto_pp','inversao_lideranca'],delimiter=';')
        w.writeheader();w.writerows(result)
    print(f'Linhas auditáveis: {sum(x["documentacao"]=="CONFERIDA" for x in result)}; exploratórias: {sum(x["documentacao"]=="PROVISORIA" for x in result)}; Lula oficial: {lula:.4f}%; saída: {a.saida}')
    if not result:print('Nenhuma pesquisa original conferida; não calcular média ou significância estatística.')

if __name__=='__main__':main()
