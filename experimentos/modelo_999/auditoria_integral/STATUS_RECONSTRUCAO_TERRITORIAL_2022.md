# Validação territorial 2022: reconstrução oficial conferida

## Resultado atual

Foi recuperada uma via para o backtest por UF de 2022 sem alterar o preditor congelado. Os votos finais por seção foram cruzados com o horário oficial da primeira totalização parcial. A reconstrução reproduziu exatamente os 5.286 registros nacionais do histórico oficial em todas as cinco grandezas verificadas: Lula, Bolsonaro, brancos, nulos e seções totalizadas.

Isso resolve a obtenção de uma base territorial temporal RECONSTRUÍDA e verificável. Não recupera os snapshots UF originais nem seus horários de publicação pública. O teste é retrospectivo e condicionado às hipóteses descritas abaixo. Certificação integral NÃO CONCEDIDA.

Este relatório atualiza a conclusão anterior de bloqueio: a ausência de endpoints EA13 acessíveis permanece registrada, mas foi contornada para a reconstrução por microdados. Nenhuma alteração na branch main foi realizada.

## Fontes e integridade

Quatro ZIPs oficiais do TSE (517.565.698 bytes no total) foram baixados, submetidos à verificação CRC e identificados por SHA-256. O manifesto inclui nomes dos membros, tamanhos e URLs. O downloader agora exige os mesmos hashes e interrompe a reprodução se a origem mudar.

- Detalhe por seção: https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_2022.zip
- Votos presidenciais por seção: https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2022_BR.zip
- Histórico BR 1T: https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_1T_2022.zip
- Histórico BR 2T: https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2022/Historico_Totalizacao_Presidente_BR_2T_2022.zip
- Catálogo institucional: https://dadosabertos.tse.jus.br/dataset/resultados-2022

O leiame.pdf incluído no ZIP de detalhe define DT_PRIM_TOT_PARCIAL_HOR_TSE como data e hora da primeira totalização parcial do BU da seção (Hora TSE), distinguindo-a de DT_RECEBIMENTO_BU_HOR_TSE. Não foi usado horário de recebimento como se fosse totalização. Os SHA-256 calculados localmente identificam os arquivos recuperados; não equivalem a assinatura digital do TSE.

## Conferências da reconstrução

472.075 registros presidenciais de detalhe por turno; 472.028 seções com linhas de votos no segundo turno; 47 seções sem linhas de voto, com totais zero no detalhe. Todas as 472.075 seções do segundo turno têm primeira totalização utilizável. Não foram encontrados candidatos-seção duplicados, votos sem detalhe correspondente ou divergências de nominais, brancos e nulos entre as duas bases. As 47 seções de votos zero mantiveram seus horários reais de totalização, sem criar votos ou horários artificiais.

Foram agregadas as seções por UF e timestamp, preservando datas e segundos originais. Na comparação com cada um dos 5.286 timestamps BR oficiais, os desvios foram exatamente zero nas cinco grandezas, inclusive na contagem de seções. Não houve ajuste de relógio nem deslocamento de registros para forçar essa igualdade.

O primeiro turno agregado por UF também coincide com o último controle nacional 1T em votos de Lula, Bolsonaro e total de concorrentes. Isso não autentica, isoladamente, qual versão estadual estava disponível antes do segundo turno.

## Modelo, congelamento e protocolo

Preditor: audit-v2-causal, commit 419593081c7178a9b4e293cb0b13befe1808fe1a. SHA-256 confrontado antes do teste, sem alteração do código ou dos parâmetros de 300/600 segundos. O protocolo de reconstrução foi publicado no commit 43d355d5b22a869ecd5e02b9487784ebd45e7030 antes do teste preditivo.

Avaliação nos primeiros registros BR que alcançam 5%, 10%, ..., 95%. Cobertura usa seções contabilizadas e total de seções da própria linha oficial. Resultado final usado apenas pelo avaliador de erros. As entradas UF são estados cumulativos reconstruídos até o horário avaliado, sob hipótese de disponibilidade interna simultânea à primeira totalização; essa hipótese NÃO comprova divulgação pública.

## Resultados

Erro em pontos percentuais da participação de Lula entre os dois finalistas. MAE e viés são médias simples dos 19 marcos, temporalmente dependentes.

| Cenário | MAE (pp) | Máximo absoluto (pp) | Viés (pp) | Marcos melhores que baseline |
|---|---:|---:|---:|---:|
| Baseline: proporção dos votos observados | 1,4975 | 4,1875 | -1,4975 | — |
| Territorial de referência | 0,8726 | 1,1875 | -0,8726 | 19/19 |
| Atraso UF 5 minutos | 0,8649 | 3,4558 | -0,6063 | 15/19 |
| Atraso UF 15 minutos | 0,4769 | 1,4924 | +0,3996 | 19/19 |
| Atraso UF 30 minutos | 0,4769 | 1,4924 | +0,3996 | 19/19 |
| Sem SP | 0,8227 | 1,0610 | -0,8227 | 18/19 |
| Sem SP, MG e RJ | 0,8558 | 1,0935 | -0,8558 | 17/19 |
| Sem Nordeste | 0,9223 | 1,3616 | -0,9223 | 19/19 |

Redução do MAE de referência: 41,73%. Conferência aritmética separada, sem importar o preditor, reproduziu os 19 valores de referência com diferença máxima de 1,42e-14 pp; as métricas dos sete cenários também foram rechecadas. Isso é conferência de implementação, não revisão humana independente.

## Fragilidades demonstradas

O modelo de referência subestimou Lula em todos os 19 marcos. Com 5% de seções, projetou 49,858%, contra resultado final de 50,902%; indicava o vencedor errado. Entre os marcos testados, só passou a indicar Lula à frente em 60%. Portanto, este teste NÃO sustenta uma promessa de acerto do vencedor com 5% de apuração.

Os atrasos de 15 e 30 minutos produziram o mesmo resultado porque todas as entradas UF ficaram fora do limite de idade de 300 segundos: o modelo entrou no modo degradado e usou o histórico sem swing fresco. O MAE desse fallback foi menor que o de referência, mas seu erro máximo foi maior. Isso sugere que a correção de swing pode piorar parte das estimativas neste caso; não se deve interpretar o melhor MAE sob atraso como segurança operacional. Não houve retuning para aproveitar esse resultado.

O atraso de 5 minutos elevou o erro máximo para 3,456 pp, apesar de MAE ligeiramente menor. Assim, avaliar apenas a média ocultaria uma vulnerabilidade relevante. Atrasos e exclusões afetam somente entradas UF; os votos nacionais observados continuam oficiais. Esses cenários não são nova ordem real de totalização nacional.

## Limites do que foi demonstrado

1. Igualdade nacional em todos os registros é uma evidência forte de consistência, mas não prova igualdade de cada parcial UF: compensações entre UFs continuam logicamente possíveis.
2. Os valores por seção são finais, inseridos na primeira totalização; não foram recuperadas todas as versões intermediárias dos BUs. A concordância BR reduz, mas não elimina, esse risco por UF.
3. Horário de totalização não comprova disponibilidade ao público. As entradas salvas marcam available_at como hipótese de cenário, sem apresentá-la como observação de coleta.
4. A referência estadual de primeiro turno é retrospectiva. Sua versão disponível antes do segundo turno não foi autenticada, embora seus totais nacionais coincidam com o histórico 1T.
5. Idade UF foi medida desde a última alteração reconstruída, não desde republicações sem mudança ou recebimento por um coletor real.
6. Uma eleição, 19 marcos correlacionados e sete perturbações não calibram probabilidade de acerto. Não há base para 99,9% nem para certificação integral.

## Reprodução

Na branch experimental, dentro de experimentos/modelo_999/auditoria_integral:

```sh
python obter_microdados_2022.py
python reconstruir_territorial_2022.py
python avaliar_reconstrucao_2022.py
python verificar_replay_2022.py
python -m unittest discover -s . -p test_preditor_causal_v2.py -v
```

O downloader requer rede e cerca de 0,52 GB para os ZIPs, mais espaço para o cache derivado. Os CSVs são lidos diretamente dos ZIPs. O cache pickle é gerado localmente pelo próprio script; não carregar pickle recebido de terceiros. As entradas dos 19 marcos e os resultados estão versionados, permitindo conferir a aritmética sem repetir o download.

## Próxima decisão técnica

Manter a v2 congelada como referência avaliada. Qualquer correção de swing deve gerar nova versão e ser avaliada em outra eleição, sem reutilizar 2022 como teste independente após ajuste. Para validação operacional plena, ainda é necessário autenticar snapshots UF contemporâneos e seu horário de disponibilização. A reconstrução atual fornece um backtest territorial útil e auditável, com escopo explícito, e não uma certificação que a evidência ainda não permite.
