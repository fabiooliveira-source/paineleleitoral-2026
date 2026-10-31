# V6 — fechamento tecnico dos tres casos municipais de 2024

**Data:** 2026-10-31  
**Branch:** `experimento/modelo-territorial-999`. A `main` permanece inalterada.

## Conclusao sem ambiguidades

A V6 com limite de 20% **passou os criterios historicos existentes nos tres casos**:
Fortaleza, Pelotas e Natal (3/3). O ensaio foi executado novamente com **95
falhas injetadas por municipio (285 ao todo)**, sem permitir previsoes a partir
de entradas inconsistentes. Hashes Git de nove arquivos (codigo e entradas)
foram conferidos contra a manifestacao de congelamento.

**Isso NAO representa certificacao externa independente.** Esses tres casos
e seus resultados ja eram conhecidos ao desenvolver a V6. A regra foi
ajustada posteriormente a falha da V4.1; assim, a aplicacao dos criterios
originais da V4.1 e um ensaio retrospectivo de desenvolvimento.

## Evidencias executadas

1. V6 congelada e gate de tres cidades:
   https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41249300493
2. Painel seguro, 57 estimativas, com lideranca projetada separada de
   chamada de vencedor condicional:
   https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41249363274
3. Auditoria V6 adversarial (cinco casos, 3.895 controles):
   https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41248914738

## Precisao e criterios

| Caso | MAE V4 (pp) | MAE V6 (pp) | MAE baseline observado (pp) | Maximo V6 (pp) | Gate historico |
|---|---:|---:|---:|---:|---|
| Fortaleza 2024 | 0,115497 | 0,115497 | 0,174847 | 0,437375 | PASSA |
| Pelotas 2024 | 0,326510 | 0,378985 | 2,581757 | 1,278373 | PASSA |
| Natal 2024 | 0,267260 | 0,207731 | 0,257574 | 0,661358 | PASSA |

Nos primeiros 5%:
- Fortaleza: candidato A previsto em **50,372780%**, vencedor correto.
- Pelotas: candidato A previsto em **51,640864%**, vencedor correto.
- Natal: candidato A previsto em **44,762621%**, vencedor correto.

A V6 atende aos limites originais de MAE <= baseline, maximo <= baseline,
MAE <= 1 pp, P95 <= 2 pp, maximo <= 3 pp, vencedor correto em 5%,
limites fisicos e ausencia de chamada condicional incorreta, nos tres casos.

## Problema residual: lideranca provisoria ainda pode errar

O requisito original verificava acertar o vencedor nos 5% iniciais,
**nao** exigia que a lideranca prevista estivesse correta em todos os
19 checkpoints. Foram identificadas inversoes temporarias:

- **Fortaleza:** dois checkpoints incorretos (25%, 30%);
- **Pelotas:** seis (15%, 20%, 25%, 35%, 40%, 90%);
- **Natal:** nenhum.

Esse problema **nao foi eliminado pela regra V6** e nao deve ser ocultado.

## Tratamento de risco para painel experimental

O modulo `preditor_v6_painel_seguro.py` devolve a estimativa nos 19 pontos
sem supressao, mas distingue explicitamente:

- `provisional_leader`: lider estimado (pode estar errado).
- `winner_call`: somente vencedor demonstravel pelos limites fisicos
  deterministas de votos restantes, sob a hipotese de ausencia de revisoes.
- `territorial_alert`: sinal de mudanca de lideranca, sensibilidade superior
  a 1 ponto percentual ou falta de identificabilidade quando uma zona e
  hipoteticamente retirada.
- `probability=None`: nenhuma probabilidade de vitoria e inventada.

Em 57 checkpoints avaliados: **57 estimativas presentes**, **0 chamadas
condicionais erradas**, **1 chamada condicional emitida (em Natal)**,
e **8 liderancas provisorias incorretas**, preservadas no relatorio.

Alertas de sensibilidade territorial: Fortaleza 6, Pelotas 14, Natal 13
checkpoints. A interface nao foi implantada em producao; e apenas uma API
experimental validada no CI.

## Decisao e proxima barreira cientifica

- **APROVADA:** integridade de software e reproducao do benchmark de
  desenvolvimento das tres cidades.
- **NAO DEMONSTRADA:** precisao em outras eleicoes, imunidade a atrasos
  reais, acerto de todas as liderancas temporarias e calibracao
  probabilistica.
- **CERTIFICACAO EXTERNA INDEPENDENTE:** pendente. Selecionar outros
  municipios ainda nao utilizados, congelar a V6 antes de abrir suas
  projecoes e confrontar todos os criterios historicos, registrando casos
  desfavoraveis e a disponibilidade real de cada fonte.
- **APURACAO PRESIDENCIAL 2026:** sem certificacao implicita a partir de
  tres eleições municipais retrospectivas.

Os dados e horarios dos checkpoints sao retrospectivamente reconstruidos,
sem comprovacao de snapshots publicos de cada instante. Os 19 marcos de um
municipio nao equivalem a 19 eleicoes independentes. Nenhuma estimativa
autoriza alegacao de 99,9% de confiabilidade.

**Status final: os tres casos satisfazem o gate historico, com ressalvas
explicitas; nenhuma certificacao integral ou implementacao em producao.**
