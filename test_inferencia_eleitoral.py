"""Testes de invariantes matemáticos e integridade da inferência ecológica.
Executar: python -m unittest test_inferencia_eleitoral.py -v
"""
import unittest
import numpy as np
import pandas as pd
from inferencia_eleitoral import canonical, strict_join, bounds, solve

class TestInferencia(unittest.TestCase):
    def test_chaves_normalizadas(self):
        a=pd.DataFrame({'uf':['ba'],'codigo_municipio_tse':['00012'],'zona':['01'],'secao':['003']})
        b=canonical(a)
        self.assertEqual(tuple(b.iloc[0]),('BA','12','1','3'))
    def test_duplicatas_rejeitadas(self):
        a=pd.DataFrame({'uf':['BA','BA'],'codigo_municipio_tse':['12','012'],'zona':['1','01'],'secao':['3','003']})
        with self.assertRaisesRegex(ValueError,'repetida'):canonical(a)
    def test_join_nao_inventa_secao(self):
        a=pd.DataFrame({'uf':['BA'],'codigo_municipio_tse':['12'],'zona':['1'],'secao':['3'],'votos':[10]})
        b=pd.DataFrame({'uf':['BA'],'codigo_municipio_tse':['12'],'zona':['1'],'secao':['4'],'votos':[9]})
        j,counts=strict_join(a,b)
        self.assertEqual(len(j),2)
        self.assertFalse(j['_merge'].eq('both').any())
    def test_bounds_exatos(self):
        X=np.array([[30,70],[0,100]],dtype=np.int64)
        Y=np.array([[40,60],[20,80]],dtype=np.int64)
        lo,hi=bounds(X,Y,np.array([100,100]))
        self.assertEqual(int(lo[0,0,0]),0)
        self.assertEqual(int(hi[0,0,0]),30)
        self.assertEqual(int(lo[1,1,1]),80)
        self.assertTrue((lo<=hi).all())
    def test_matriz_estocastica(self):
        # Dois grupos de origem, dois destinos; matriz identidade.
        X=np.array([[100,0],[0,100],[50,50]],dtype=float)
        Y=X.copy();N=X.sum(axis=1)
        G=(X/np.sqrt(N[:,None])).T@(X/np.sqrt(N[:,None]))
        H=(X/np.sqrt(N[:,None])).T@(Y/np.sqrt(N[:,None]))
        P=solve(G,H)
        np.testing.assert_allclose(P.sum(axis=1),1,atol=1e-6)
        self.assertTrue((P>=-1e-7).all())
        np.testing.assert_allclose(X@P,Y,atol=1e-4)
    def test_limites_nao_identificam_individuos(self):
        X=np.array([[50,50]],dtype=np.int64)
        Y=np.array([[50,50]],dtype=np.int64)
        lo,hi=bounds(X,Y,np.array([100]))
        self.assertEqual(int(lo[0,0,0]),0)
        self.assertEqual(int(hi[0,0,0]),50)
if __name__=='__main__':unittest.main()
