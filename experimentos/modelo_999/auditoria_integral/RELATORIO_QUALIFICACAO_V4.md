# V4: qualificação técnica do replay pareado

## Conclusão e escopo

A V4 PASSOU NO PROTOCOLO DE QUALIFICAÇÃO DOS REPLAYS PAREADOS. O código foi congelado antes do teste externo municipal de São Paulo de 2020 e não foi reajustado depois. Os resultados foram reproduzidos no GitHub Actions, incluindo novo download dos arquivos oficiais de 2020 e reconstrução das entradas byte a byte em ambiente limpo.

CERTIFICAÇÃO INTEGRAL DO PAINEL NÃO CONCEDIDA. A qualificação demonstrada é restrita ao preditor v4, aos contratos e aos replays documentados. Não é chancela do TSE, auditoria humana independente, calibração de probabilidade nem certificação do código atualmente utilizado no painel.

Trabalho realizado apenas na branch experimento/modelo-territorial-999. Main preservada. V2 e V3 preservadas; a reprovação externa da V3 continua registrada.

## Evidência de reprodução em outro ambiente

Execução: https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41148598344

Commit executado: e5adfaadb08ee19f8e5f71932693fbfb499b5e26.

| Job | Resultado | O que verificou |
|---|---|---|
| replay-pinned | SUCESSO | 28 arquivos fixados por SHA-256, 37 testes unitários, três replays, 285 verificações de estresse e conferências por frações exatas |
| full-source-2020 | SUCESSO | Download dos dois ZIPs TSE2020, SHA-256 e CRC, reconstrução do pareamento, igualdade byte a byte das entradas e repetição do teste externo |

O job full-source-2020 confirmou a mesma entrada SHA-256 41f9ecfbcb37e3e4f211437f65fb280477fccf968af6be30ece9f3327840f9d6 produzida localmente. A execução reproduziu 22.399 seções de São Paulo, 58 zonas e 19 marcos, sem registros tardios ou seções sem par.

Os registros e identificadores dos artefatos estão em evidencia_ci_v4.json. Os hashes fixam identidade e reprodução; não autenticam retroativamente qual versão dos dados estava publicamente disponível em cada instante histórico.

## O que mudou em relação à V3

A V3 atenuava o swing agregado por um coeficiente escolhido em 2022. Falhou em 2018 porque a atenuação reduzia tanto o efeito da composição da amostra quanto a mudança eleitoral.

A V4 usa o primeiro turno das MESMAS seções já observadas no segundo turno. Para cada candidato e estrato, calcula a razão entre seus votos atuais e seus votos de primeiro turno nesse conjunto pareado, aplicando-a aos votos de primeiro turno das seções restantes. Quando um estrato não permite estimar uma razão local, usa a razão global identificável. Não há coeficiente ajustado por eleição.

A extrapolação é limitada pelo número físico máximo de votos ainda possíveis. Se o denominador global não for identificável, se o pareamento exceder a referência, se faltar estrato ou se o total territorial não conciliar com o total nacional/municipal, não há estimativa pontual. O contrato exige ledger completo e sincronizado; um feed somente agregado por UF não fornece automaticamente a coorte pareada necessária.

Congelamento: commit 04ea90abb8c535f8ee17eeb26fa781b246e03e88. Protocolo anterior: commit 5e316a9737518429a09b31f4a6fb7ee3a8ef83cd. Arquivos e SHA-256 em congelamento_v4.json.

## Desempenho

Erros em pontos percentuais da participação do candidato A entre os dois finalistas. Em 2018, A é Haddad; em 2022, Lula; em São Paulo2020, Boulos. O alvo final é usado apenas no avaliador. São 19 marcos de 5% a 95% em cada caso.

| Eleição e papel | MAE baseline | MAE V4 | Máximo baseline | Máximo V4 | Viés V4 |
|---|---:|---:|---:|---:|---:|
| Presidente2018 — desenvolvimento | 1,5819 | 0,7385 | 4,9890 | 1,2760 | +0,7385 |
| Presidente2022 — desenvolvimento | 1,4975 | 0,0992 | 4,1875 | 0,2223 | +0,0992 |
| São Paulo2020 — teste externo municipal | 0,6083 | 0,3762 | 0,8532 | 0,7635 | -0,3762 |

A redução do MAE foi 53,31%, 93,38% e 38,16%, respectivamente. A V4 melhorou 19/19 marcos em 2018 e 2022, mas 14/19 em São Paulo2020. Não houve superioridade em todos os instantes no teste externo.

No marco de 5% de São Paulo2020, a V4 estimou Boulos em 39,8872%, contra 40,6224% no resultado final. O erro foi 0,7352 pp, maior que 0,5627 pp do baseline naquele marco. Portanto, a aprovação nas métricas médias e máximas não demonstra uma promessa geral de precisão precoce.

Todos os critérios numéricos pré-registrados do caso externo passaram: menor MAE, máximo não superior ao baseline, alvo dentro dos limites condicionais, nenhuma indicação matemática errada e abstinência de estimativa quando os testes invalidaram o ledger. Um teste municipal externo não demonstra generalização operacional presidencial nem probabilidade de 99,9%.

## Estimativa e indicação matemática são diferentes

Com A e B já contados e R votos válidos ainda possíveis, os limites condicionais são:

limite inferior de A = A / (A + B + R)
limite superior de A = (A + R) / (A + B + R)

Somente A > B + R ou B > A + R permite indicação matemática condicional do vencedor. Empate no limite não permite indicação. O código usa desigualdades inteiras, sem decidir por percentuais arredondados.

A demonstração está em PROVA_LIMITES_V4.md. Além da prova algébrica, foram conferidas 7.672 conclusões possíveis em um domínio inteiro pequeno. Esse número não é uma amostra de eleições e não calibra confiança estatística.

Nos marcos testados, a primeira indicação matemática condicional ocorreu em 95% em 2018 e em 90% em São Paulo2020. Em 2022 não houve indicação até 95%, dada a margem apertada e a amplitude conservadora do limite de eleitores restantes. Isso é comportamento esperado do limite físico, não falha escondida por uma probabilidade nominal.

As condições são essenciais: A/B corretos sem revisão futura que invalide a desigualdade e R um limite superior verdadeiro. Os limites não são intervalos de confiança. A V4 retorna probability=None e não converte acerto retrospectivo em probabilidade.

## Verificações de implementação

- 37 testes unitários passaram nas versões V2, V3 e V4 preservadas.
- 285 verificações nas entradas dos três replays: retirar estrato, atrasar ledger, injetar dados futuros, permutar ordem e criar divergência nacional-territorial. A estimativa é suspensa quando o contrato deixa de valer.
- 57 estimativas foram recalculadas por implementação separada com Fraction, sem importar o preditor. Diferença máxima: 1,42e-14 pp.
- Os limites incluíram todos os alvos e nenhuma indicação matemática condicional foi errada nos marcos avaliados.
- O fechamento com R=0 devolve o resultado observado, conforme teste unitário.

Abster-se sob indisponibilidade não significa manter o mesmo erro com dados ausentes. O que foi verificado é a interrupção segura da estimativa pontual, preservando apenas limites condicionais derivados dos totais disponíveis.

## Proveniência e limitações dos dados

As fontes são os ZIPs de detalhe e votação por seção do Portal de Dados Abertos do TSE. Manifestos registram URLs, tamanhos, membros, CRC e SHA-256; os downloads de reprodução rejeitam mudança nos hashes fixados.

Para2020: detalhe_votacao_secao_2020.zip SHA-256 10a50a467763dce73d44eee9023ffeeb3ebe6279756edb6b437203eb2bc71a30; votacao_secao_2020_SP.zip SHA-256 79dbc252f6d6187f351ceaf1bbf2a0d3fba5043a90df1e2af9c4e8bae7244fc8. Os dois ZIPs somam 615.152.199 bytes. Foram conferidos nominais, brancos e nulos entre as fontes, chaves e pareamento. Totais de São Paulo2T: Boulos 2.168.109; Covas 3.169.121; brancos 273.216; nulos 607.062.

A cronologia utiliza DT_PRIM_TOT_PARCIAL_HOR_TSE. A disponibilidade simultânea à totalização é hipótese de replay interno, não registro de divulgação pública. Os cadastros do primeiro turno e do eleitorado foram recuperados retrospectivamente, sem autenticar suas versões contemporâneas. Para2022, a reconstrução nacional foi previamente confrontada com 5.286 parciais oficiais, com igualdade exata. Não foi obtida a mesma curva oficial integral para2018 ou para São Paulo2020.

Oito registros tardios de2018 permaneceram nas datas da fonte e não foram antecipados para os marcos. Seus votos integram apenas o alvo final do avaliador quando posteriores à janela. Essas limitações continuam válidas mesmo com CI verde.

2018 e2022 são desenvolvimento. São Paulo2020 foi externo para esta versão congelada; agora está examinado e não poderá orientar ajuste e continuar sendo apresentado como externo intocado. O caso é municipal e os estratos são zonas, enquanto os desenvolvimentos presidenciais usam UFs. Essa mudança de escala limita a transferência da conclusão.

## Rastreabilidade até o painel atual

Foi lido previsao.js na main, blob Git 9a420b6d00c2c1bb3dddcca4af79e29249ed519f. Ele consome dados/2026/previsao-territorial.json e exibe probabilidades nominais não calibradas. O gerador previsao_territorial.py usa outro modelo de pós-estratificação e distribuições beta, com suas próprias hipóteses e avisos.

A V4 não está integrada a esse fluxo e não foi demonstrada equivalência com ele. Também não se certifica automaticamente qualquer outro estimador presente em index.html. É tecnicamente incorreto usar a aprovação deste replay V4 como certificado de todas as previsões exibidas pelo site.

## Matriz de certificação integral

| Requisito | Evidência atual | Situação |
|---|---|---|
| Identidade e reprodução do código V4 | SHA-256, congelamento e CI | Demonstrado no escopo |
| Controles causais da função | Testes de futuro, disponibilidade e pareamento | Demonstrado sob entradas declaradas |
| Desempenho externo | São Paulo2020, sem reajuste | Aprovado no caso, alcance limitado |
| Robustez de disponibilidade | Abstinência em 285 verificações | Demonstrado para o contrato |
| Cadeia histórica pública autenticada | Arquivos retrospectivos, não capturas contemporâneas completas | Pendente |
| Calibração probabilística | V4 não fornece probabilidade; amostra insuficiente para esse requisito | Pendente |
| Integração e equivalência com o painel | Página atual usa outro modelo | Pendente |
| Revisão independente especializada | CI executa o mesmo código, sem revisão humana externa | Pendente |

Não é atribuída porcentagem de certificação misturando requisitos de pesquisa, dados e produção. Não há base para afirmar certificação integral ou 99,9% de acerto.

## Reprodução e revisão

Na pasta experimentos/modelo_999/auditoria_integral:

```sh
python qualificar_pacote_v4.py
```

Isso verifica arquivos fixados, testes, replays e cálculos separados. Para refazer o caso externo a partir das fontes:

```sh
python obter_microdados_2020_v4.py
python construir_entradas_pareadas_v4.py 2020
python avaliar_v4_pareado.py 2020
python verificar_v4_fracoes.py 2020
```

O workflow .github/workflows/qualificacao-v4.yml executou esses caminhos em ambiente limpo, com ambos os jobs aprovados. Os artefatos de execução têm retenção definida pelo GitHub; o repositório preserva código, entradas fixadas, manifestos, resultados e evidência da execução.

## Próximos requisitos concretos

1. Construir e autenticar o fluxo por seção necessário à V4, com referência anterior, instante de geração, recepção, versão e revisões, conciliando-o com o agregado oficial.
2. Demonstrar equivalência de implementação entre o modelo qualificado e uma integração experimental do painel, sem alterar main até concluir os testes.
3. Submeter o dossiê reproduzível a revisão especializada independente e definir eventual alegação probabilística com calibração entre eleições e cobertura fora da amostra. Os limites determinísticos não devem ser renomeados como probabilidades calibradas.

Este relatório registra uma qualificação técnica concluída no escopo especificado e expõe os impedimentos reais da certificação integral. O objetivo não é alcançado mudando os critérios depois do teste nem conferindo a si próprio uma revisão independente.
