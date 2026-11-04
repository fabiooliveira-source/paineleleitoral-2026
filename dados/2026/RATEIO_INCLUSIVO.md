# Inclusão das seções com diferenças de universo

O painel passa a disponibilizar um cenário contábil com as seções conciliadas dos dois turnos, incluindo diferenças de aptos e de local. O ajuste pareado anterior permanece como referência e não deve ser confundido com este cenário ampliado.

Cada seção recebe uma matriz não negativa, com margens correspondentes às contagens observadas. A diferença líquida de aptos é representada por origem ou destino próprios de ajuste de universo; não é atribuída automaticamente a candidatos, brancos, nulos ou abstenção. Esse ajuste não mede entradas e saídas reais de pessoas nem resolve mudanças de composição do eleitorado.

O prior é o modelo estadual já publicado, com fallback nacional quando necessário. IPF condiciona o cenário às margens de cada seção. A tabela municipal soma cenários calculados nas suas próprias seções, sem chamar coeficientes estaduais de inferência municipal independente. Zeros do prior recebem piso 0,0001. A sensibilidade compara com uma matriz de independência em cada seção; não é intervalo de confiança. Se o IPF não converge dentro do limite, utiliza-se independência e contabiliza-se o caso explicitamente.

Os checkpoints publicados têm hashes e limites de iterações registrados na auditoria. A execução verifica suas margens antes de reutilizá-los. As primeiras partições tiveram orçamento de 10.000 iterações; as demais, 1.000. Os resultados são cenários condicionais e não uma estimativa identificada de transferências individuais. Não se atribui confiança de 95% às células.

Detalhe nominal ausente é registrado em origem própria, sem inventar votos por candidato eliminado. A classificação nominal da candidatura 28 e de nulos na base por seção é preservada. Registros não conferidos ou com categorias não conciliadas ficam listados em `audit.pending`; não se substituem contagens ausentes por votos inventados.

Reprodução e verificação:

```bash
OPENBLAS_NUM_THREADS=1 python rateio_inclusivo.py
python -m unittest discover -s tests -p 'test_rateio_inclusivo.py'
python tests/validar_rateio_inclusivo.py
node tests/rateio-inclusivo.cjs
```

A auditoria e os totais estão em `rateio-inclusivo.json`. Os arquivos municipais são particionados por UF. Os testes conferem matrizes, totais por município, UF e Brasil, contagens dos finalistas contra a base municipal e a consulta de Serrinha na interface.

Na conferência final, 42 localidades sem seção utilizável foram preservadas em blocos municipais oficiais separados. Isso recupera também os 2 votos de Lula no primeiro turno em Trípoli. Aptos de locais não instalados sem categoria informada ficam como metadado pendente, sem recodificação como abstenção. O fechamento nacional dos votos dos finalistas nos dois turnos é testado contra a soma de todos os 5.757 territórios.
