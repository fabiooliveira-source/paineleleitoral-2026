# V4.1 — validação externa municipal 2024

Decisão: **não promover ao painel**. Apenas 1 dos 3 casos satisfez todos os critérios registrados antes da avaliação. Modelo e critérios não foram reajustados. A branch main permanece intacta.

Protocolo: commit 537cc770f07855a3bef0a5febe3ac719dcb427dd.

| Caso | MAE (pp) | P95 absoluto (pp) | Máximo (pp) | Resultado |
|---|---:|---:|---:|---|
| Fortaleza | 0,115497 | 0,395164 | 0,437375 | Passou |
| Pelotas | 0,326510 | 0,620469 | 0,757171 | Errou vencedor no checkpoint de 5% |
| Natal | 0,267260 | 0,718257 | 1,230356 | MAE e máximo piores que baseline |

Pelotas estimou 49,605320% para A no primeiro checkpoint, contra resultado final de 50,362491%. Natal teve MAE de 0,267260 pp contra 0,257574 pp da proporção observada; máximo de 1,230356 contra 0,922796 pp. Fortaleza acertou o vencedor em 17 dos 19 pontos: passou o critério previamente fixado de acerto em 5%, mas errou em 25% e 30%. Não significa acerto durante toda a apuração.

Foram reconstruídos 19 checkpoints por caso, com pareamento das mesmas seções entre turnos: Fortaleza 5.274 seções/17 zonas, Pelotas 753/3 e Natal 1.407/5. Sem registros tardios nesses três recortes. Os arquivos normalizados reproduziram exatamente os hashes da primeira execução. As quatro fontes TSE tiveram SHA-256 e integridade ZIP verificados. Os diagnósticos preservam conciliação, duplicidades e hipóteses temporais.

Os 285 controles de falha passaram (95 por caso). Uma implementação independente com frações exatas confirmou as 57 projeções, os limites determinísticos e as chamadas condicionais; diferença máxima de 1,43e-14 pp. Os sete novos testes de regressão passaram. Isso verifica execução e aritmética, sem anular as reprovações de desempenho.

As escolhas foram registradas antes das projeções, mas resultados históricos públicos eram conhecidos. Esta amostra de desafio não é aleatória nem representativa. Os dados usam votos finais por seção e horários internos de primeira totalização; não constituem snapshots públicos autenticados nem comprovam disponibilidade pública naquele instante. A disponibilidade da referência do primeiro turno é assumida. Casos municipais não certificam desempenho presidencial nacional. Checkpoints correlacionados não são eleições independentes. P95 de erro não é probabilidade de vitória; probability permanece ausente.

Reprodução: obter_fontes_2024_v41.py; preparar_caso_externo_2024.py para 13897, 87912 e 17612; avaliar_externos_v41_2024.py; verificar_externos_2024_fracoes.py. O workflow separa reprodução técnica do gate científico; este deve reprovar enquanto menos de três casos satisfizerem o protocolo. Não baixar critérios após observar os resultados. Qualquer novo modelo deverá ser congelado antes de enfrentar novos casos externos.
