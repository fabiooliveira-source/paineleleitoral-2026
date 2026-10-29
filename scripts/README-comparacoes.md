# Comparações municipais e de modelos

Os arquivos HTML/JS são estáticos. Os dois novos pacotes contêm totais públicos, sem dados individuais. Use `node tests/comparacoes.cjs` para conferir pareamento, filtros, denominadores, fechamento das linhas e resultados dos testes.

## Reprodução

Execute na raiz do repositório, com Python (numpy, pandas e scipy) e Node. Os caminhos de trabalho abaixo ficam na pasta imediatamente acima do repositório; não são publicados pelo site.

1. Crie `../historico/`. Extraia os CSVs presidenciais nacionais `*_BR.csv` dos ZIPs oficiais do TSE de 2018 e 2022. Salve o detalhe de apuração como `2018-apuracao.csv` / `2022-apuracao.csv` e a votação dos candidatos como `2018-votos.csv` / `2022-votos.csv`. Links: `https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_ANO.zip` e `https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_ANO.zip` (substituir ANO). Os arquivos BR destes pacotes contêm Presidência; o leitor também exige CD_CARGO=1.
2. `python scripts/build-comparativo-historico.py` gera `dados/comparativo_historico_pacote.json` e o intermediário `../model_input_municipal.json`.
3. `node scripts/prepare-model-input.cjs` seleciona as mesmas 443.100 seções elegíveis e gera `../model-input.json.gz`. Confere que as origens e destinos somam os mesmos aptos em cada seção.
4. `python scripts/build-comparacao-modelos.py` usa o estimador de `inferencia_eleitoral.py` e os pacotes existentes de inferência e rateios, calcula os ajustes e testes e gera `dados/comparacao_modelos.json`.
5. `node tests/comparacoes.cjs`, `node tests/historico.cjs` e `node tests/buildup-turnos.cjs`.

O pareamento histórico usa UF + código municipal TSE com cinco dígitos. Ausências não viram zero e alterações de limites territoriais não são resolvidas por essa chave. Exterior separado das regiões; nos testes históricos de previsão ele é excluído. Aptos do primeiro turno de 2026 definem os cinco portes, inclusive ao selecionar o segundo turno.

## Métodos e validação

- Contábil: motor por urna existente. Preserva margens por construção e não é pontuado como previsão.
- WLS original: 16 origens, cinco destinos, sem ridge. A comparação exibe nove origens e quatro destinos por soma de votos esperados. A taxa de cada grupo é sua soma de votos esperados dividida pela soma de sua base.
- WLS nacional agrupado: nove origens, quatro destinos e ridge 0,01, na parametrização padronizada do estimador existente.
- WLS local: mesmo estimador agrupado em municípios com pelo menos 80 seções elegíveis; demais usam UF. Essa escolha de granularidade não comprova homogeneidade das taxas locais. Não é uma reprodução do modelo de outro site.

Teste espacial 2026: chave municipal + `|20261029`, CRC32 módulo cinco. Resto zero é teste. Municípios inteiros são excluídos do treino. O WLS original e os novos modelos são reajustados somente no treino; o modelo local usa UF para municípios ocultos. RMSE por destino é calculado sobre proporções dos aptos por seção e ponderado pelos aptos. A diferença de participação de Lula no teste usa os totais esperados/observados de Lula e Flávio.

O teste histórico adicional prevê participação municipal do candidato do PT em cada eleição, em cinco grupos de municípios. Entradas: intercepto, participação de primeiro turno do PT entre os dois finalistas, demais candidatos sobre válidos, abstenção sobre aptos e brancos/nulos sobre comparecimento. Modelos: persistência da primeira participação, regressão nacional e regressão por UF (mínimo de 20 municípios de treino; alternativa nacional). As regressões usam ridge 0,001, sem penalizar o intercepto; previsões limitadas a [0,1]. Os válidos de segundo turno ponderam apenas o ajuste no treino e a avaliação no teste. Não entram como variável explicativa de municípios ocultos.

Esses testes não reconstituem parciais de apuração, não treinam exclusivamente em eleições anteriores e não calibram probabilidades de vitória. Também não validam os fluxos individuais latentes. Resíduos do ajuste estatístico são exibidos em vez de serem forçados a zero.
