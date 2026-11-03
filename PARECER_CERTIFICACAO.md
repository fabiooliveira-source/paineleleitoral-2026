# Parecer de certificação técnica — 30/10/2026

**Status: APROVAÇÃO PARCIAL. NÃO CERTIFICADO PARA CONCLUSÕES ELEITORAIS.**

## Evidência reproduzida
- `python -m unittest test_validar_modelo.py -v`: 6 testes aprovados (execução local em 30/10/2026).
- `python stress_validacao.py` (arquivo de testes local, ainda não versionado): 11/11 cenários aprovados, incluindo 100.000 linhas sintéticas em 0,193 s.
- Essas execuções testam apenas `validar_modelo.py`, não a integridade do resultado eleitoral nem a acurácia preditiva.

## Bloqueios de certificação
1. **Integridade**: refazer hashes dos ZIPs oficiais, validar CRC, schema, chaves, votos por categoria, seções excluídas, reconciliação seção/município/UF/BR. A documentação `dados/2026/LEIA-ME.md` registra números, mas isso não substitui reexecução independente.
2. **Inferência ecológica**: demonstrar ausência de dupla contagem de candidaturas nas origens; verificar conservação `sum(X)=sum(Y)=aptos`; testar matrizes de rank deficiente, bootstrap sem convergência, sensibilidade de agrupamentos e generalização por municípios não vistos.
3. **Previsão**: o módulo `previsao_territorial.py` utiliza votos finais ordenados pelo primeiro horário parcial; isso **não** é replay de snapshots históricos. Não usar a saída para afirmar calibração temporal ou acerto com 5% de apuração.
4. **Proveniência temporal**: cada snapshot precisa de fonte, instante de disponibilidade, SHA-256 e trilha de processamento verificável; conferir que treino não contém resultados posteriores ao instante previsto.
5. **Calibração**: Brier, MAE, RMSE, cobertura de intervalos e comparação com baselines simples em amostras realmente independentes. Um pleito isolado não valida probabilidade de vitória de 99%.
6. **Anomalias**: implementar controle de multiplicidade, estratificação territorial, inspeção documental e investigação de falsos positivos; desvios não são prova de fraude.
7. **Operacional**: testes de integração e regressão do dashboard, estabilidade, acessibilidade e segurança de publicação.

## Critérios de aceite
- Testes unitários e de integração reproduzidos em CI com versões fixadas.
- Zero divergências **não justificadas** nos controles contábeis, com cobertura e exceções publicadas.
- Nenhuma duplicidade de origens ou vazamento temporal.
- Métricas prospectivas publicadas com baseline, incerteza e análise de sensibilidade.
- Parecer de auditoria independente para afirmações de certificação externa.

**Observação**: este parecer é uma auditoria técnica interna, não uma certificação emitida pelo TSE ou entidade independente.
