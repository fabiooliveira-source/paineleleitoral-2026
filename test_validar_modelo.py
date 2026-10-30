"""Testes sintéticos independentes para validar_modelo.py.
Executar: python -m unittest test_validar_modelo.py -v
"""
import unittest
import pandas as pd
from validar_modelo import validar

class TestValidacao(unittest.TestCase):
    def setUp(self):
        self.p=pd.DataFrame({'id':['a','b'],'probabilidade':[.8,.2],
            'estimativa':[60,40],'realizado_em':['2026-10-25T18:00:00Z']*2,
            'informacao_ate':['2026-10-25T17:00:00Z']*2})
        self.o=pd.DataFrame({'id':['a','b'],'resultado':[1,0],'valor_final':[55,45]})
    def test_metricas(self):
        r=validar(self.p,self.o)
        self.assertAlmostEqual(r['brier_score'],.04)
        self.assertAlmostEqual(r['mae_estimativa'],5)
        self.assertAlmostEqual(r['rmse_estimativa'],5)
        self.assertAlmostEqual(r['vies_medio'],0)
    def test_vazamento_temporal(self):
        self.p.loc[0,'informacao_ate']='2026-10-25T19:00:00Z'
        with self.assertRaisesRegex(ValueError,'Vazamento'):
            validar(self.p,self.o)
    def test_ids_duplicados(self):
        self.p.loc[1,'id']='a'
        with self.assertRaisesRegex(ValueError,'repetidos'):
            validar(self.p,self.o)
    def test_probabilidade_invalida(self):
        self.p.loc[0,'probabilidade']=1.2
        with self.assertRaisesRegex(ValueError,'Probabilidades'):
            validar(self.p,self.o)
    def test_resultado_faltante(self):
        with self.assertRaisesRegex(ValueError,'correspondência'):
            validar(self.p,self.o.iloc[:1])
    def test_nao_finito(self):
        self.p.loc[0,'estimativa']=float('nan')
        with self.assertRaisesRegex(ValueError,'não finitos'):
            validar(self.p,self.o)

if __name__=='__main__':unittest.main()
