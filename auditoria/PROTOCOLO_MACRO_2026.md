# Auditoria macro 2026 — protocolo de detecção de anomalias

Status: protocolo metodológico; **não representa execução nem prova de irregularidade**.

## Fontes primárias
- https://dadosabertos.tse.jus.br/ — Resultados 2026; BUs por UF; arquivos transmitidos para totalização; correspondências esperadas/efetivadas; logs GEDAI; comparecimento.
- https://www.tse.jus.br/eleicoes/eleicoes-2026-content/boletim-de-urna-2o-turno — relatórios operacionais.
- Base de referência histórica: eleições presidenciais de 2022 (mesma granularidade e chaves harmonizadas).

## Etapa 0 — integridade e proveniência
Registrar URL, data/hora da coleta, SHA-512/SHA-256, tamanho, schema, codificação, número de linhas e chave (turno, UF, município TSE, zona, seção). Reconciliar somas por seção, município, UF e Brasil. Não excluir seções com alteração de aptos sem reportar o impacto; usar chaves e mapas de correspondência.

## Etapa 1 — detecção
1. Comparecimento: comparecimento/aptos, abstenção, brancos e nulos, com estratificação por UF, município e tamanho da seção; sinalizar extremos com intervalos binomiais/beta-binomiais e correção de múltiplos testes (Benjamini–Hochberg).
2. Variação entre turnos: diferenças absolutas e relativas por seção, ajustadas por aptos, comparecimento, voto em trânsito e alteração de seções; não atribuir transferências individuais com base apenas em totais agregados.
3. Biometria: separar ausência de cadastro, falha de reconhecimento, liberação por ano de nascimento e outros modos; exigir denominadores e horários de habilitação.
4. Integridade: BU versus RDV versus totalização, hash/assinaturas e correspondência efetivada; distinguir divergência de ausência de arquivo.
5. Tempo: reproduzir instantâneos da totalização, diferenças entre versões e janelas deslizantes de 84,7 s; distinguir horário de publicação, recepção e incorporação de BU, e versões de cache.
6. Forense: dígitos e Benford somente como análise exploratória, com testes de adequação e controles sintéticos/históricos; nenhum teste isolado comprova fraude.

## Etapa 2 — classificação
- A: divergência contábil reproduzida, com arquivo, hash e seção.
- B: anomalia estatística robusta após estratificação, controles e FDR.
- C: padrão atípico explicado por composição, logística, cache, mudança cadastral ou efeito demográfico.
- D: inconclusivo por insuficiência de dados.
Cada achado deve conter ID, UF, município, zona, seção, fonte, estatística, denominador, comparação, p/q-value quando aplicável, hipótese alternativa, impacto em votos e grau de confiança fundamentado.

## Pendências prioritárias
- Baixar e validar os CSVs oficiais por UF e executar reconciliação nacional.
- Reproduzir as 310/327 parciais históricas com carimbos temporais verificáveis.
- Verificar a alegada diferença de 4.352 versus 4.864 seções com locais alterados: datas, filtros e critérios de extração.
- Validar com dados de 2022 e controles negativos; publicar tabela de achados, inclusive resultados nulos.

**Não alterar a branch main.** Não afirmar auditoria certificada ou irregularidade sem cálculos reproduzidos.
