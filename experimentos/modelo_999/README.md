# Modelo eleitoral 99,9% — experimento isolado

## Estado
A meta de 99,9% é aspiracional. Nenhuma precisão foi certificada. A branch não modifica a main.

## Dados verificados
CSV `observacoes_nacional_uf.csv`: 4.892 linhas; CSV `observacoes_municipais.csv`: 47.139 linhas.
Colunas: timestamp, scope, uf, municipio_tse, secoes_contabilizadas, eleitores_secoes_contabilizadas, comparecimento, brancos, nulos, votos_13, votos_22.

## Executar
`python3 experimentos/modelo_999/backtest_baseline_nacional.py`

Resultado esperado: `experimentos/modelo_999/resultados/backtest_baseline_nacional.json`.

## Critérios de auditoria
- Conferir se cada timestamp representa um snapshot genuinamente histórico.
- Verificar monotonicidade e duplicatas; não ocultar correções.
- Avaliar erros a cada 5% das seções contabilizadas.
- Diferenciar erro em pontos percentuais de probabilidade de acerto.
- Não usar resultado final como variável preditiva.
- Comparar com modelos simples antes de incorporar correção territorial.
- Validar 99,9% em várias eleições e amostras independentes; uma eleição não basta.

## Limitações
O baseline de votos já apurados pode ser enviesado pela ordem territorial de totalização. O arquivo final é usado apenas como alvo de avaliação e para definir percentuais de seções em retrospectiva. Para validação por seção é necessário histórico temporal de chegada das seções.
