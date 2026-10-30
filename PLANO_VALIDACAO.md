# Plano de validação — algoritmo eleitoral 2026

## Estado atual
- [x] Validador independente: `validar_modelo.py`.
- [x] Testes sintéticos: `test_validar_modelo.py`.
- [ ] Executar testes sintéticos e registrar saída.
- [ ] Produzir snapshots históricos com proveniência temporal comprovada.
- [ ] Validar previsões em eleições e cortes temporais independentes.
- [ ] Testar inferência ecológica por UF, estabilidade e cobertura.
- [ ] Implementar detecção de anomalias com ajuste para múltiplos testes.
- [ ] Confrontar totais e boletins oficiais, com chaves e hashes.
- [ ] Revisar interface e integrar somente após validação.

## Restrições metodológicas
1. A hora de emissão da previsão não comprova que as fontes eram conhecidas nessa hora. Cada snapshot deve preservar versão, data de obtenção, origem e hash do conteúdo.
2. Resultados finais não podem ser usados para reconstruir uma parcial histórica apresentada como previsão em tempo real.
3. Transferências individuais não são identificáveis apenas por dados agregados. Apresentar intervalos condicionais e limites matemáticos.
4. Uma anomalia estatística não comprova irregularidade; separar flags de integridade documental e desvios comportamentais.
5. O Brier Score requer múltiplos eventos independentes para avaliação robusta da calibração. Um único pleito nacional não basta.
6. Registrar quantidade de seções excluídas, motivos e cobertura geográfica.
7. Não divulgar percentuais de confiabilidade sem backtests independentes.

## Execução
```bash
python -m unittest test_validar_modelo.py -v
python validar_modelo.py --previsoes previsoes.csv --observados observados.csv --saida validacao.json
```

## Critério de aprovação
Todos os testes passam, entradas têm proveniência temporal auditável, e métricas e limitações são publicadas juntamente com os resultados.
