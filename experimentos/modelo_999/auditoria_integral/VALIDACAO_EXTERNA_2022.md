# Validação externa 2022 — controle nacional

Fonte oficial: https://dadosabertos.tse.jus.br/dataset/resultados-2022

Foi executado replay cronológico do histórico BR do segundo turno: 5286 registros, 19 marcos (5..95%). Cobertura calculada com QT_SECOES_TOTAL da própria linha. Nenhuma diminuição nos votos acumulados dos candidatos ou seções acumuladas. ZIP com CRC válido e SHA-256 1f12128fbcfacab755e0e83d9c0a350ed99ae68ea3d024aaa7bc58fe0c1dda3c.

Baseline observado: MAE 1.4975301436535073 pp; máximo absoluto 4.1874835473893555 pp; viés -1.4975301436535073 pp. Estes resultados NÃO são do modelo territorial. Arquivo obtido contém apenas BR; histórico contemporâneo de UF ainda não obtido.

## Pendência do congelamento

Manifesto no commit ff42daf66f92d4bed425420ae5793af7dc11507a registra predictor_sha256=422c6020e9ef66aaab090c5fbbd1cf99aa0cbc9ee999f96865fe40a462beda07, mas não identifica o caminho do preditor. O arquivo backtest_primeiro_turno_uf.py no mesmo commit tem SHA-256 a2b1ee31784e7710d62aa7a7ebce5915747ce8accd15accefac7b52ddcc3b0b8. Não afirmar que são o mesmo arquivo nem que o congelamento está validado. O script também calcula cobertura com seções do snapshot final, contrariando a política de entrada contemporânea do manifesto; precisa de versão causal identificada e congelada antes do teste territorial externo.

O congelamento original foi preservado. Nenhum ajuste do preditor territorial foi realizado nesta etapa. O controle nacional não deve ser usado para calibrar o modelo e não certifica probabilidade. Próximos passos: identificar preditor audit-v1, confrontar hash/código, obter histórico UF e executar modelo sem alterações por desempenho externo. Se UF não disponível, limitar conclusão ao modo nacional degradado.

Reprodução: python experimentos/modelo_999/auditoria_integral/replay_baseline_2022.py (requer acesso à fonte oficial; saída JSON em /tmp/backtest2022_resultado.json).
