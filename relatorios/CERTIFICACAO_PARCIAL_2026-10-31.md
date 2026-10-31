# Relatório parcial de certificação — 31/10/2026

## Escopo e rastreabilidade
- Execução auditada: GitHub Actions 41246261513 (conclusão **success**).
- Modelo testado: baseline nacional de proporção acumulada de votos válidos, **não** o algoritmo territorial principal.
- Evidência: logs do job 124670220954 e artefato 13059054412.
- Status: **CERTIFICAÇÃO INTEGRAL NÃO CONCEDIDA**.

## Resultados observados
| Seções apuradas | n observações | MAE (pontos percentuais) | Viés (pp) | Erro máximo absoluto (pp) |
|---|---:|---:|---:|---:|
| 1–5% | 42 | 0,379059 | -0,109432 | 1,395331 |
| 5–10% | 19 | 1,007483 | -1,007483 | 1,350055 |
| 10–25% | 39 | 1,945565 | -1,945565 | 2,297061 |
| 25–50% | 45 | 2,057546 | -2,057546 | 2,295225 |
| 50–75% | 38 | 1,167648 | -1,167648 | 1,645651 |
| 75–90% | 24 | 0,421058 | -0,421058 | 0,695563 |
| 90–99% | 16 | 0,096830 | -0,096830 | 0,205287 |

Os pontos representam observações temporais correlacionadas **de uma única apuração**, não amostras independentes. O erro não é monotônico: o viés entre 25–50% é pior do que entre 1–5%. Logo, não se deve extrapolar que mais seções sempre produzem projeções melhores.

## Crítica de certificação
1. O benchmark é a proporção corrente dos votos; não foi feita previsão de votos ainda não contabilizados por território.
2. A regra não usa o resultado final para calcular a previsão; o denominador final de seções é utilizado somente para estratificação ex post.
3. Um único pleito não fornece evidência de generalização; exigir validação externa, preferencialmente 2022, com parâmetros congelados.
4. O acervo tem integridade interna verificada, mas sua autenticidade oficial ainda não foi certificada independentemente.
5. A análise de transferência entre turnos é **inferência ecológica**: margens por seção não identificam trajetórias individuais. A conciliação com os totais finais é condição necessária, jamais prova de acerto das transferências.
6. Não confundir 100% de cobertura (inclusive imputada) com 100% de observação ou 99,9% de acerto preditivo.

## Próximos gates
- G1: reproduzir métricas de referência e publicar logs/artefatos (concluído para o baseline).
- G2: executar o algoritmo territorial sob os mesmos cortes temporais, registrar erros nacionais, estaduais e municipais (pendente).
- G3: simular reordenação e atraso territorial, falhas e indisponibilidade; proibir dados futuros (pendente).
- G4: processar seções excluídas, classificar observadas/imputadas/não estimáveis, reconciliar margens, medir incerteza (pendente).
- G5: backtest externo 2022 com parâmetros congelados e critérios de aceitação pré-registrados (pendente).
- G6: auditoria independente de proveniência e certificação final (pendente).

## Decisão
**Reprovado para certificação integral nesta etapa, por insuficiência de evidências**, não por comprovação de falha do algoritmo principal.
