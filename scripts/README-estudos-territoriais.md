# Estudos territoriais estáticos — TSE × IBGE

A página `estudos-territoriais.html` funciona com arquivos do próprio GitHub Pages. Não faz consultas ao IBGE em tempo de navegação e não usa entrevistas. Fonte, data do congelamento, ano de referência e hash SHA-256 dos arquivos do IBGE estão no pacote `dados/estudos_territoriais_pacote.json` (gzip/base64).

## Reprodução

Na raiz do repositório, com Python, numpy e scipy instalados:

1. Prepare os CSVs BR de votação dos candidatos e detalhe de apuração de 2014, 2018 e 2022 em `../historico/`, nos nomes `ANO-votos.csv` e `ANO-apuracao.csv`. Os ZIPs oficiais são `https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_ANO.zip` e `https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_ANO.zip`.
2. Execute `python scripts/build-comparativo-historico.py` para criar o intermediário municipal de 2018/2022/2026. A leitura de 2014 é realizada diretamente pelo novo construtor, com Aécio (45) como adversário.
3. Execute `python scripts/build-estudos-territoriais.py`. Os dados oficiais do IBGE são baixados uma vez para `../ibge/` e reutilizados. Arquivos preexistentes não são substituídos por novas consultas. Para repetir exatamente o congelamento, preserve os arquivos com os hashes do pacote publicado. Remover o cache produz uma nova consulta, potencialmente revisada pelo IBGE, e exige nova validação.
4. Execute `node tests/estudos-territoriais.cjs`. Para visualizar localmente, sirva a raiz do repositório por HTTP.

## Universo e ausências

Segundo turno, municípios brasileiros com votos válidos e aptos positivos em 2014, 2018, 2022 e 2026. Pareamento eleitoral por UF + código TSE com cinco dígitos. A continuidade do código não garante os mesmos limites territoriais; o estudo é descritivo. Exterior e unidades sem histórico completo são excluídos. A participação é do candidato do PT: Dilma, Haddad e Lula nos respectivos pleitos.

O cruzamento IBGE usa nome normalizado + UF (acentos, espaços e pontuação removidos), exigindo chave única e igualdade exata. Não é um crosswalk oficial de códigos TSE/IBGE. As diferenças de nome não resolvidas ficam sem valores IBGE e são listadas; não se aplica aproximação textual ou preenchimento por zero. O código IBGE de sete dígitos é conservado em cada linha pareada. Os estudos eleitorais continuam incluindo municípios sem vínculo IBGE; as correlações usam somente pares válidos.

## Indicadores IBGE

- População residente e densidade: Censo 2022, SIDRA 4714, variáveis 93 e 614.
- Taxa de alfabetização das pessoas de 15 anos ou mais: Censo 2022, SIDRA 9543, variável 2513; totais de sexo (6794), cor/raça (95251) e idade (100362).
- PIB por habitante calculado de 2021: PIB municipal a preços correntes em mil reais (5938, variável 37) × 1.000 / população residente estimada de 2021 (6579, variável 9324). Não representa renda familiar ou renda disponível.

Os indicadores são referências de 2021/2022 para todas as eleições. Não foram retroprojetados para 2014/2018 nem atualizados artificialmente para 2026. As relações são retrospectivas, não testes de previsão.

## Estatística e visualização

Pearson usa escala original ou log10 para população, densidade e PIB; alfabetização permanece original. Spearman usa posições médias em empates. Peso opcional na coluna de Pearson ponderado: aptos do ano selecionado. Na coluna dentro das UFs, retiram-se as médias não ponderadas de cada UF nas duas variáveis. Correlação indefinida por falta de variância ou menos de três pares é nula, nunca zero imputado. As correlações são descritivas: não há afirmações de significância por amostra independente, causalidade ou comportamento de indivíduos. Dependência espacial e confundimento permanecem possíveis.

Quartos do indicador ordenam os municípios e dividem as linhas em quatro tamanhos semelhantes. A participação PT e a abstenção dos grupos usam soma dos numeradores / soma dos denominadores, nunca média simples. Os grupos podem separar empates adjacentes; faixas são exibidas.

Perfis: K-means em oito variáveis padronizadas, municípios com pesos iguais, 12 inicializações e semente 20261029, alternativas K=3,4,5. Cada classificação é nacional e fixa. Silhueta em 1.000 municípios sorteados, avaliados contra a base integral, é uma medida exploratória de separação e não probabilidade. Os perfis não reproduzem a detecção de comunidades de rede do artigo sueco e não precisam ser contíguos. As trajetórias dos perfis somam votos e bases a cada ano antes de dividir.

A amplitude histórica é máximo menos mínimo da participação PT nas quatro eleições. Matriz de persistência: Spearman entre as participações municipais nos diferentes anos, com o mesmo recorte filtrado. Ela não acompanha eleitores individuais.

Vizinhança: média de coordenadas válidas de locais eleitorais distintos por zona/local no segundo turno de 2026; não é centroide territorial do IBGE. Oito municípios mais próximos em esfera, grafo direcionado, pesos 1/8. Sem coordenadas: excluído somente do estudo espacial. A distância do vizinho mais distante é exibida no detalhamento municipal. Os vizinhos podem estar fora da UF filtrada. A malha de vizinhança é fixa e retrospectiva em todas as eleições.

Moran I nacional: soma de z_i × média de z dos oito vizinhos / soma de z_i². Teste bilateral: 499 embaralhamentos globais das taxas, comparação em torno de −1/(n−1), valor-p corrigido por (extremos+1)/500. Os valores nacionais não mudam nos filtros, conforme rótulos da página. A referência alta/alta usa a média municipal simples nacional de cada ano. Não há teste de significância local; os bolsões são classificações descritivas, sem alegação de contágio.

As referências internacionais estão ligadas na própria página. O método é uma adaptação descritiva às bases disponíveis, não reprodução integral dos estudos nem garantia de inferência causal.

## Correlograma inspirado no estudo francês

Transformação phi = log((aptos − abstenções) / abstenções), padronizada nacionalmente em cada eleição. Mesma amostra fixa de 500.000 pares de municípios distintos, sorteados uniformemente com reposição (semente 20261029), para os quatro anos. Média dos produtos z_i*z_j por faixa de distância esférica [0,25), [25,50), ..., [3200,6400] km. É covariância normalizada pela variância nacional, não Pearson calculado dentro da faixa. O eixo exibe faixas em espaçamento igual, não distâncias lineares; não foi ajustado o modelo de campo difusivo do artigo francês. Referência nacional fixa mesmo com filtros territoriais. O sorteio pode repetir pares, e não há alegação de independência estatística dos pares ou intervalos de confiança calibrados.
