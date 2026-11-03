"""Testes reproduzíveis da auditoria contábil de seções."""
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from auditar_secoes import auditar

class TestAuditoriaSecoes(unittest.TestCase):
    def setUp(self):
        self.d=pd.DataFrame({
            'uf':['BA','BA'],'codigo_municipio_tse':['12345','12345'],
            'zona':['1','1'],'secao':['10','11'],
            'aptos_1t':[100,100],'comparecimento_1t':[80,80],
            'abstencoes_1t':[20,20],'brancos_1t':[2,2],'nulos_1t':[3,3],
            'aptos_2t':[100,100],'comparecimento_2t':[90,90],
            'abstencoes_2t':[10,10],'brancos_2t':[2,2],'nulos_2t':[3,3]})
    def check(self,d):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'base.csv'
            d.to_csv(path,sep=';',index=False)
            return auditar(path)
    def test_base_coerente(self):
        result=self.check(self.d)
        self.assertEqual(result['rows'],2)
        self.assertTrue(all(v==0 for v in result['flags'].values()))
    def test_inconsistencia_comparecimento(self):
        d=self.d.copy()
        d.loc[0,'comparecimento_2t']=99
        self.assertEqual(self.check(d)['flags']['turnout_balance_2t'],1)
    def test_duplicidade(self):
        d=pd.concat([self.d,self.d.iloc[[0]]],ignore_index=True)
        with self.assertRaisesRegex(ValueError,'duplicadas'):
            self.check(d)
    def test_amostra_vazia(self):
        with self.assertRaisesRegex(ValueError,'vazia'):
            self.check(self.d.iloc[:0])
    def test_votos_negativos(self):
        d=self.d.copy();d.loc[0,'brancos_1t']=-1
        self.assertEqual(self.check(d)['flags']['invalid_1t'],1)
    def test_brancos_nulos_acima_comparecimento(self):
        d=self.d.copy();d.loc[0,'brancos_1t']=100
        self.assertEqual(self.check(d)['flags']['negative_valid_residual_1t'],1)

if __name__=='__main__':
    unittest.main()
