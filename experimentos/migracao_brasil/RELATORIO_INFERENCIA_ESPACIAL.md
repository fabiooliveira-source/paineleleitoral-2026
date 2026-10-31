# Inferência ecológica espacial exploratória

O rateio contábil anterior foi complementado por regressão de misturas ecológicas, ajuste por UF e interpolação de campos locais de coeficientes. Foram comparados IDW² e krigagem ordinária. Não há observação individual das transferências nem taxa de acerto certificada. Fontes são derivados do repositório; não houve nova autenticação oficial nesta fase.

## Escopo e validação

Foram modeladas 499.205 seções previamente conferidas, de 499.248 avaliadas na base inicial. As 43 excluídas são do exterior. Há coordenadas aproveitáveis para 496.153 seções; 3.052, incluindo exterior, usam fallback de UF/nacional ajustado apenas no treino.

Grade de 0,5° com 2.236 células. Hash determinístico da célula separa 309.686 seções de treino, 108.114 de seleção e 78.353 de teste. Células inteiras são reservadas. Não há buffer entre células adjacentes, e não se presume independência espacial completa. Tamanhos físicos das células variam com latitude.

Cada origem tem taxas próprias, não negativas e somando 100%. Origens incluem todos os candidatos, brancos, nulos, abstenção e ajuste de universo. Composição local do primeiro turno e universo de eleitores ponderam o ajuste. As observações do segundo turno de teste não entram no ajuste ou seleção.

## Comparação

Erro em pontos percentuais sobre o universo contábil da seção, incluindo abstenção. O MAE ponderado usa soma do erro absoluto de ambos os finalistas dividida por duas vezes o universo total.

| Modelo | MAE ponderado no teste | P95 absoluto no teste |
|---|---:|---:|
| UF regularizado | 1,578673 | 4,111097 |
| IDW², 8 vizinhos | 1,540120 | 4,022500 |
| IDW², 16 vizinhos | 1,542003 | 4,026559 |
| Krigagem ordinária, 8 vizinhos | 1,550389 | 4,051796 |
| Krigagem ordinária, 16 vizinhos | 1,553358 | 4,055412 |

IDW²/8 foi selecionado pelo menor MAE ponderado na amostra de seleção, antes de considerar o teste. Não se forçou a preferência pela krigagem. A redução de erro frente à UF é modesta. O erro máximo do selecionado no teste é 26,083635 pp; bom ajuste agregado não elimina erros locais grandes.

## Krigagem

A camada interpola cinco log-razões por origem, estimadas por regressão ecológica em blocos de treino e centralizadas na UF. Não kriga migrações observadas. Usa variograma esférico isotrópico por UF sobre campos de coeficientes padronizados. Distância de corda em esfera de raio 6.371 km; vizinhança móvel de 8 ou 16 blocos, sem busca entre UFs. A krigagem impõe soma dos pesos igual a 1; o IDW usa inverso do quadrado da distância. Taxas retornam ao simplex por transformação inversa. Fallback regional é explícito quando faltam blocos ou variograma.

Pepita, contribuição, alcance, pares por classe e ajuste empírico estão no JSON e no HTML. Não foi comprovada estacionariedade plena nem investigada anisotropia. A variância de krigagem é condicional aos coeficientes e ao variograma; não inclui toda a incerteza ecológica. Testes sintéticos verificaram soma dos pesos e reprodução de campo constante.

## Restrições à interpretação

O ajuste usa pseudoverossimilhança multinomial agregada, aproximação que não equivale à verossimilhança exata de tabelas individuais. O ajuste nacional terminou com 600 iterações e maior alteração de taxa 0,00015655; não atingiu o limiar 1e-7. Diagnósticos por UF também são preservados. Logo, não se afirma máximo global, convergência integral, identificação das origens ou taxa de acerto das migrações. Resultados são provisórios.

Os valores nacionais são somas dos fluxos em cada bloco/seção, ponderados pelos votos de origem. Os totais dos destinos não são artificialmente conciliados: resíduos são publicados. Histogramas contam seções com votos da candidatura ou ponderam pelos votos de origem; taxas são constantes dentro do bloco. A amplitude entre especificações é sensibilidade, não intervalo de confiança.

Colinearidade espacial entre candidatos, poucos votos e alterações de cadastro podem produzir taxas extremas sem identificação comportamental. Acrescentar vizinhança não resolve automaticamente a falácia ecológica. Para acurácia de transferência seria necessária referência independente sobre transições individuais ou hipóteses adicionais defensáveis.

Referências metodológicas: https://geostat-framework.readthedocs.io/projects/pykrige/en/stable/generated/pykrige.ok.OrdinaryKriging.html ; https://doc.esri.com/en/arcgis-pro/latest/help/analysis/geostatistical-analyst/understanding-ordinary-kriging.html . Implementação local usa NumPy/SciPy, não PyKrige. O sistema de covariâncias é resolvido explicitamente.

Main preservada. Não promover como certificação de migração.
