# V3: desenvolvimento em 2022 e teste externo em 2018

## Decisão

V3 NÃO APROVADA PARA PROMOÇÃO. A atenuação fixa do swing melhorou o desenvolvimento em 2022, mas piorou três dos quatro critérios numéricos pré-registrados no teste externo de 2018. Não houve reajuste depois de observar 2018. V2 preservada como referência; nenhuma alteração na main ou implantação no painel.

A conclusão refere-se aos replays reconstruídos e às hipóteses de disponibilidade neles adotadas. Não é certificação operacional ou de probabilidade de acerto.

## Diagnóstico do viés da v2

Foi feita uma decomposição com os mesmos pesos e limites de idade da v2, usando os votos de primeiro turno das exatas seções que já haviam entrado no segundo turno em 2022. Assim:

swing bruto UF = swing contra o primeiro turno das seções observadas + efeito da composição das seções observadas dentro da UF.

A componente de composição foi negativa nos 19 marcos, com média de -0,7171 ponto percentual de swing. Com 5% apurado, o swing bruto de -2,6700 pp se decompôs em -1,5258 pp contra as seções pareadas e -1,1442 pp de composição intra-UF. O resíduo máximo da identidade foi 1,04e-15 pp. Entre as seções já observadas nos marcos avaliados, nenhuma com votos dos finalistas no segundo turno ficou sem referência pareada dos dois finalistas no primeiro turno.

Portanto, o swing agregado confundia uma mudança de composição da amostra com mudança eleitoral. Isso foi quantificado; não é inferência de transferência individual de votos. A decomposição não prova que o swing pareado seja, sozinho, um estimador sem viés para as seções restantes. O pareamento foi diagnóstico e não foi introduzido como variável nova da v3.

## Desenvolvimento e congelamento

A grade e a regra de seleção foram registradas no commit cb7a150896c1971d2b32dc2c5fe4987a497e5161 antes do cálculo da grade:

- Coeficientes de swing: 0; 0,25; 0,50; 0,75; 1.
- Seleção por menor MAE de referência em 2022, sob limites de erro máximo, viés absoluto e pior erro máximo nos sete cenários, comparados à v2.
- Permanecem os limites de idade de 300 segundos e decaimento de 600 segundos.
- Empates favorecem o coeficiente mais próximo de 1. Se nenhum candidato passar, manter v2.

Foi selecionado 0,25: a v3 aplica um quarto do swing bruto, sem incluir novos dados futuros. O coeficiente 0,50 teria erro máximo menor em 2022, mas MAE maior; não foi escolhido porque a regra primária registrada era MAE sob limites de risco, não minimização isolada do máximo.

Código, parâmetros, testes e hashes foram congelados no commit 8fd1d1705e9d843fbf6a8209432d0fa6bcdf9ae4 antes do teste preditivo de 2018. Os 12 testes unitários passaram. O download dos arquivos de 2018 é aquisição de dados, não seleção por desempenho; nenhum resultado preditivo de 2018 foi usado para escolher a v3.

## Resultados de referência

Erros em pontos percentuais da participação do candidato do PT entre os dois finalistas. Médias simples dos 19 marcos de 5% a 95%; marcos temporalmente dependentes.

| Eleição e uso | Modelo | MAE (pp) | Máximo absoluto (pp) | Viés (pp) |
|---|---|---:|---:|---:|
| 2022 — desenvolvimento | V2 | 0,8726 | 1,1875 | -0,8726 |
| 2022 — desenvolvimento | V3 | 0,2702 | 0,8583 | +0,0815 |
| 2018 — teste externo | Baseline observado | 1,5819 | 4,9890 | -1,5819 |
| 2018 — teste externo | V2 | 1,3286 | 3,6996 | -1,3286 |
| 2018 — teste externo | V3 | 3,1171 | 5,7089 | -3,1171 |

A redução do MAE no desenvolvimento foi 69,03%. No teste externo, o MAE cresceu 134,62% frente à v2 e também ficou pior que o baseline observado. Melhorar 2022 não demonstrou generalização.

| Critério externo pré-registrado | Resultado |
|---|---|
| MAE de referência menor que v2 | REPROVADO |
| Máximo de referência não maior que v2 | REPROVADO |
| Viés absoluto de referência não maior que v2 | REPROVADO |
| Pior máximo nos sete cenários não maior que v2 | APROVADO |

## Atrasos e indisponibilidade em 2018

| Cenário | MAE V2 (pp) | MAE V3 (pp) | Máximo V2 (pp) | Máximo V3 (pp) |
|---|---:|---:|---:|---:|
| Referência | 1,3286 | 3,1171 | 3,6996 | 5,7089 |
| Atraso 5 min | 3,3607 | 3,5831 | 6,7652 | 6,2362 |
| Atraso 15 min | 3,7133 | 3,7133 | 6,3786 | 6,3786 |
| Atraso 30 min | 3,7133 | 3,7133 | 6,3786 | 6,3786 |
| Sem SP | 1,4462 | 3,1465 | 3,7308 | 5,7166 |
| Sem SP, MG e RJ | 1,5610 | 3,1752 | 3,6200 | 5,6889 |
| Sem Nordeste | 1,0712 | 3,0528 | 3,7516 | 5,7218 |

Atrasos de 15 e 30 minutos retiram todas as observações UF do limite de idade, levando ambos os modelos ao mesmo fallback. A pequena redução do pior máximo global não compensa os três critérios de referência reprovados. As perturbações mudam apenas disponibilidade UF; não recriam outra ordem nacional de totalização.

Nos marcos testados de 2018, baseline, v2 e v3 indicaram o vencedor correto desde 5%. Esse caso teve margem final ampla e não demonstra probabilidade de acerto para eleições apertadas. Em 2022, a v3 passou a apontar o vencedor correto desde 5%, mas isso pertence ao conjunto de desenvolvimento.

## O que os dados sugerem sobre a falha

O peso de terceiros no primeiro turno foi 8,37% em 2022 e 24,69% em 2018, nas tabelas utilizadas. A participação do PT entre os dois finalistas mudou -1,9532 pp em 2022 e +5,9930 pp em 2018 entre os turnos. Esses números são mudanças agregadas, não identificação de migração individual.

A atenuação fixa reduz tanto a componente de composição quanto o swing eleitoral. O teste mostrou que isso não se transportou bem entre os dois contextos. A hipótese metodológica para desenvolvimento futuro é separar composição territorial da amostra e mudança eleitoral; aplicar um coeficiente único ao sinal inteiro não resolveu a questão. Não foi criada uma v4 nem reaberta a grade depois do resultado externo.

## Dados e limites de 2018

Fontes oficiais:

- https://dadosabertos.tse.jus.br/dataset/resultados-2018
- https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2018.zip
- https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2018_BR.zip
- Controle institucional de encerramento e totais: https://www.tse.jus.br/comunicacao/noticias/2018/Outubro/eleicoes-2018-justica-eleitoral-conclui-totalizacao-dos-votos-do-segundo-turno

Os dois ZIPs somam 507.118.319 bytes, com CRC válido e SHA-256 registrado. O downloader exige os hashes recuperados para reproduzir a mesma versão. A preparação conferiu 454.490 seções presidenciais por turno, chaves sem duplicidade, nenhuma linha de votos sem detalhe e nenhuma diferença entre nominais/brancos/nulos das duas bases, inclusive por UF. Há 42 seções sem linhas de votação e com totais zero.

O denominador dos marcos é o cadastro de 454.490 seções do primeiro turno, anterior ao segundo na hipótese do replay, e não o total do último snapshot. Sua versão efetivamente disponível naquela data não foi autenticada. Horários de geração do arquivo retrospectivo não foram apresentados como horários de publicação da noite eleitoral.

A fonte contém 40 seções com totalização datada de 27/10/2018 e oito de 25/02/2019. As datas foram preservadas. Os oito registros tardios, com 799 votos do PT e 913 de Bolsonaro, não entraram como atributos na janela de 28 e 29/10, mas seus votos integram o alvo final de avaliação, conforme regra congelada. Não foi determinada a razão administrativa dessas datas.

Os totais finais do segundo turno coincidem com o controle institucional: PT 47.040.906, Bolsonaro 57.797.847, brancos 2.486.593, nulos 8.608.105. Não foi obtida uma curva nacional oficial de 2018 para comparação integral dos timestamps como ocorreu em 2022. Portanto, não se afirma que a reconstrução reproduz todas as parciais públicas de 2018.

A referência retrospectiva de primeiro turno soma 107.050.749 nominais, coincidindo entre as duas fontes atuais. A notícia institucional da época informa 107.050.673 válidos, diferença de 76 votos frente aos nominais atuais. Conceitos e versões não são necessariamente idênticos; a diferença está registrada em reconciliacao_referencia_1t_2018.json, sem ajustar os dados depois do teste. Isso reforça a limitação de autenticidade temporal da referência 1T.

Disponibilidade simultânea à primeira totalização e disponibilidade anterior das referências 1T são hipóteses de reconstrução. Não constituem prova de aquisição pública contemporânea. Uma eleição externa, com dados retrospectivos e marcos correlacionados, não calibra probabilidades ou certifica todo o sistema.

## Verificação e reprodução

A conferência aritmética separada reproduziu os 19 resultados de cada modelo em 2018 com diferença máxima de 1,42e-14 pp. Conferiu métricas de 21 combinações de cenário/modelo e executou 38 testes de injeção de informação futura nas entradas reais do replay, sem alterar nenhuma previsão. Isso é validação de implementação, não revisão humana independente.

Na pasta experimentos/modelo_999/auditoria_integral:

```sh
# Desenvolvimento: depende dos microdados/cache2022 já documentados
python diagnosticar_vies_2022_v3.py
python desenvolver_v3_2022.py

# Teste externo da versão já congelada
python obter_microdados_2018.py
python preparar_replay_2018.py
python avaliar_v3_externo_2018.py
python verificar_externo_2018_v3.py
python -m unittest discover -s . -p test_preditor_causal_v3.py -v
```

As entradas dos 19 marcos e os resultados estão versionados, permitindo conferir aritmética e filtros sem baixar os ZIPs novamente. O cache local é derivado pelos scripts e não é necessário como fonte primária.

## Próximo desenvolvimento indicado

Preservar a v2 como referência não certificada e arquivar a v3 como hipótese reprovada para promoção. Uma futura v4 deverá tratar explicitamente a composição da amostra, sem confundi-la com mudança eleitoral. Tanto 2022 quanto 2018 já foram examinados; nenhum deles poderá voltar a ser chamado de teste externo intocado depois de orientar uma nova revisão. Será necessária validação em outra eleição ou um desenho entre eleições explicitamente separado, além das pendências de disponibilidade contemporânea e calibração.
