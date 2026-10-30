# Revisão técnica do algoritmo de transferências — 2026-10-30

## Código inspecionado
- transferencias.js: decomposição exata de variação de votos, limites de Fréchet, construção de matrizes viáveis e três cadeias exploratórias.
- transferencias.html: build-up por seção com rateio contábil, apresentado como cenário e não observação individual.
- dados/2026/auditar_pesquisas.py: confronto com resultado e exigência de documentação original.

## Melhorias prioritárias

### P0 — Garantias e consistência
1. Testar invariantes em todos os níveis: soma das linhas = origens; colunas = destinos; células inteiras não negativas; igualdade de comparecimento, brancos e nulos por turno.
2. A função matrix(r,c,reverse) percorre a mesma ordem para linhas e colunas. Adicionar testes para cada dimensão, incluindo 0, 1 e casos extremos.
3. A categoria 'ajuste de universo' não é eleitor observado; separar explicitamente da matriz comportamental e documentar os casos em que aptos diferem.
4. Desacoplar cálculo puro de manipulação do DOM, permitindo testes automatizados sem navegador.

### P1 — Inferência estatística
5. Os 1500 registros visitados pelas cadeias NÃO são amostras de comportamento eleitoral; preservar o rótulo exploratório. Percentis e médias não constituem probabilidades eleitorais.
6. A proposta de movimento 2x2 com escolha uniforme de incremento não assegura amostragem uniforme sobre tabelas de contingência; avaliar distribuição estacionária e viés da proposta antes de fazer inferências.
7. Implementar diagnósticos de convergência (R-hat, ESS, autocorrelação) apenas após estabelecer um alvo probabilístico explícito. Sem isso, mostrar sensibilidade a sementes e pontos iniciais.
8. Para migração por candidato eliminado, aplicar modelo ecológico hierárquico por seção/município/UF com regularização, intervalos e análise de sensibilidade; validar por predição fora da amostra e dados externos.
9. Reportar identificabilidade e limites inferiores/superiores; evitar porcentagens de migração com falsa precisão.

### P2 — Engenharia e desempenho
10. Usar Web Worker para simulação e progressão, evitar travamento da interface móvel.
11. Cachear agregações por UF/município, em vez de filtrar toda a base em cada atualização.
12. Incluir metadados de versão, fonte, data, SHA-256, filtros e parâmetros em cada JSON exportado.
13. Exibir alertas quando fontes forem provisórias, dados ausentes ou não comparáveis.

### P3 — Auditoria de pesquisas e apuração
14. auditar_pesquisas.py não calcula erro amostral, efeito de desenho, não resposta, datas de campo nem correlação entre institutos. Implementar apenas com dados metodológicos originais.
15. Comparar resultado de seções com BU e registros independentes, sinalizando divergências materiais e mantendo rastreabilidade.
16. Não interpretar desvio de pesquisa como evidência de manipulação da apuração.

## Critério de aceite
- Testes de propriedades e casos sintéticos passam.
- Reconciliação exata por seção, município, UF e Brasil, com relatório de exceções.
- Modelo de migração distingue limites, cenário e inferência estimada.
- Qualquer inferência vem acompanhada de sensibilidade, validação e incerteza.
