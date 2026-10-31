# V6 — auditoria reforcada, protecao de entrada e politica de estabilidade

Data de referencia: 2026-10-31. Branch exclusiva: `experimento/modelo-territorial-999`. `main` nao modificada.

## Decisao auditavel

**Integridade de software: PASSOU na bateria atual.**
**Robustez preditiva: NAO APROVADA para liberacao irrestrita.**
**Certificacao externa independente: NAO CONCEDIDA.**

Nenhum resultado de sucesso no GitHub Actions implica certificacao cientifica.

## Alteracoes tecnicas

- `preditor_v6_guardado.py`: preserva integralmente a regra adaptativa da V6 com limite 0,20 e usa o contrato de integridade temporal/territorial da V4.1. Bloqueia ledger incompleto ou conflitante, votos nacionais divergentes, referencia futura, timestamps improprios, totais fisicamente invalidos e revisoes de snapshots. Bloqueios retornam `ABSTAIN`, sem probabilidade inventada.
- `auditar_v6_guardada.py`: regressao numerica comparada ao calculo V6 original; testes de ordem, duplicata idempotente, injeção futura, 12 mutacoes invalidas, fonte futura, snapshot fora de ordem e atraso territorial. Cinco casos, 19 checkpoints por caso, semente fixa 20261031. **3.895 verificacoes, zero falha**. Inclui 20 remocoes aleatorias por checkpoint e uma remocao da zona mais representativa.
- `preditor_v6_estavel.py`: modo **opcional** e conservador. Retira hipoteticamente cada zona observada, recalcula a previsao sem olhar o resultado real e suspende a emissao se houver troca do vencedor projetado, desvio acima de **1,0 ponto percentual** ou impossibilidade de estimativa. Essa tolerancia e uma **politica de risco escolhida nesta fase**, nao um parametro validado externamente nem uma norma.
- `avaliar_politica_estabilidade_v6.py`: controla todos os checkpoints no denominador e mede cobertura da politica, sem esconder abstencoes. Gate de engenharia passou, sem falhas.

Execucoes verificadas:
- Auditoria adversarial: https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41248914738 — `success`.
- Politica de estabilidade: https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41248996040 — `success`.

## Desempenho historico — MAE em pontos percentuais

| Caso | V4 | V6 sem suspensao | Melhorou? |
|---|---:|---:|---|
| Fortaleza 2024 | 0,115497 | 0,115497 | Igual |
| Pelotas 2024 | 0,326510 | 0,378985 | **Nao** |
| Natal 2024 | 0,267260 | 0,207731 | Sim |
| Sao Paulo 2020 | 0,376200 | 0,389401 | **Nao** |
| Presidencial 2022 | 0,099202 | 0,099202 | Igual |

**Nao ha superioridade uniforme da V6 sobre a V4.** O mesmo conjunto historico usado no desenvolvimento nao estabelece acuracia prospectiva.

## Stress territorial

Sob remocao sintetica de uma zona (20 sorteios/checkpoint), a maior alteracao da V6 em pontos percentuais foi:
- Fortaleza 2024: **0,517 pp**.
- Pelotas 2024: **1,879 pp**.
- Natal 2024: **1,440 pp**.
- Sao Paulo 2020: **0,361 pp**.
- Presidencial 2022: **0,173 pp**.

A regressao da V6 guardada coincide com a V6 anterior em todos os 95 checkpoints, dentro de tolerancia numerica de 1e-12 na fracao.

**Limitacao do stress anterior:** o experimento inicial nao dispunha de `electorate_counted` por zona; a remocao da zona subtraia seus votos do agregado, mas nao conseguia remover corretamente o comparecimento da zona. A versao reforcada usa **apenas votos validos da zona como minimo de comparecimento removido** e documenta essa hipotese. Isso torna a entrada matematicamente conciliante, mas **nao e reconstrucao fiel de um evento real de atraso**, pois brancos/nulos locais nao sao conhecidos nesse ledger.

## Custo da politica conservadora (19 checkpoints em cada caso)

| Caso | Previsoes liberadas | Abstencoes | Primeiro checkpoint de 5% liberado? |
|---|---:|---:|---|
| Fortaleza 2024 | 13/19 | 6/19 | Nao |
| Pelotas 2024 | 5/19 | 14/19 | Nao |
| Natal 2024 | 6/19 | 13/19 | Nao |
| Sao Paulo 2020 | 19/19 | 0/19 | Sim |
| Presidencial 2022 | 19/19 | 0/19 | Sim |

Portanto, o modo conservador **reduz o risco de divulgar previsoes instaveis, mas frequentemente se abstem em pleitos municipais**. Nao satisfaz o requisito anterior de emitir estimativas em todos os 19 pontos nem no checkpoint de 5% desses tres casos de 2024. A media de erros apenas nas previsoes liberadas sofre vies de selecao; nao pode ser comparada como melhora de acuracia total.

## Proximos gates obrigatorios para certificacao

1. Registrar antes da avaliacao novos casos historicos *nao usados* para desenvolver V4, V5 ou V6, incluindo casos com disputas apertadas e diferentes topologias territoriais.
2. Congelar codigo, hashes de dados, criterios de bloqueio e selecao dos casos; evitar ajuste a posteriori dos limites de 20% e 1 pp.
3. Validar proveniencia, tempos reais de disponibilidade e reconciliacao com o TSE. Dados de seccoes finais com horarios internos reconstituidos **nao** demonstram snapshots publicos contemporaneos.
4. Aferir erros, enviesamento, acertos de vencedor, cobertura do mecanismo de abstencao e atrasos com cenarios reais. Comparar baseline observado e V4 sem alterar regras.
5. Avaliar amostras independentes no nivel de eleicao, nao tratar checkpoints correlacionados como observacoes independentes.
6. Nao divulgar probabilidades ou alegacao de 99,9% ate haver avaliacao de calibracao e base estatistica apropriada.

**Conclusao:** a V6 foi protegida contra falhas de entrada e submetida a um gate de engenharia mais rigoroso. A deficiencia preditiva e a instabilidade territorial permanecem problemas cientificos em aberto, e a opcao conservadora troca disponibilidade por seguranca. **Certificacao integral nao atingida.**
