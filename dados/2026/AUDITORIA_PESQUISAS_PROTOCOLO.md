# Auditoria estatística eleitoral 2026 — protocolo documental (30/10/2026)

## Base existente — NÃO baixar novamente
- dados/2026/LEIA-ME.md descreve 4 ZIPs originais e controles de integridade (CRC, SHA-256), 499.248 seções distintas e 998.411 registros de seção/turno conferidos.
- dados/2026/downloads.json: proveniência, URLs, cabeçalhos, SHA-256.
- dados/2026/integridade_zip.json e validacao.json: controles existentes.
- dados/2026/candidatos-secao-*.json: arquivos por UF; formato compactado gzip+base64. Conferir esquema antes de inferir fluxos individuais.
- dados/2026/analise_microdados.json: indicadores municipais pré-computados.
- As contagens acima são as documentadas no repositório, não uma auditoria independente refeita nesta etapa.

## Fontes primárias sobre pesquisas
1. TSE Dados Abertos: https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026
   Recursos: pesquisas eleitorais CSV, contratantes, pagantes, notas fiscais, questionários e detalhamento bairro/município.
2. PesqEle: https://www.tse.jus.br/eleicoes/pesquisas-eleitorais/pesquisas-eleitorais
3. Norma: https://www.tse.jus.br/legislacao/compilada/res/2019/resolucao-no-23-600-de-12-de-dezembro-de-2019
4. Atualização metodológica 2026: https://www.tse.jus.br/comunicacao/noticias/2026/Setembro/tse-atualiza-sistema-de-pesquisas-eleitorais-e-amplia-transparencia-em-levantamentos

## Esquema de auditoria das pesquisas (uma linha por pesquisa)
registro_tse;instituto;contratante;data_inicio;data_fim;data_divulgacao;modo_coleta;n_planejado;n_efetivo;n_validos;confianca;margem_erro;efeito_desenho;ponderacao;fonte_populacional;taxa_resposta;recusas;substituicoes;questionario_url;relatorio_url;resultado_lula_validos;resultado_flavio_validos;resultado_lula_totais;resultado_flavio_totais;indecisos;bn_abstencao;status_documental;observacoes

## Procedimento
1. Obter registros e PDFs diretamente do TSE e dos próprios institutos; não preencher dados não verificados.
2. Normalizar votos válidos vs votos totais, respeitar datas reais de campo e arredondamentos.
3. Modelo hierárquico com efeito de instituto e método, tendência temporal e incerteza amostral/não amostral.
4. Comparar previsões à totalização, decompor erro por geografia e comparecimento.
5. Cruzar com seções existentes, controlar multiplicidade, e confirmar discrepâncias documentais com BU antes de inferir inconsistência.
6. Matriz por candidato eliminado: inferência ecológica com restrições de margens; resultados são intervalos/cenários, jamais migração individual comprovada.

## Critérios de qualidade
- Diferenciar erro de pesquisa, mudança de opinião e divergência de totalização.
- Evitar falsa precisão por urna para pesquisas com amostra nacional.
- Não atribuir fraude ou viés na apuração a partir de testes isolados, Benford ou diferenças de pesquisa.
- Publicar código, fonte, versão, data de coleta, controles e resultados reproduzíveis.

## Estado em 30/10/2026
- Fontes oficiais localizadas; estrutura da base eleitoral existente inspecionada.
- Relatórios individuais das pesquisas NÃO baixados nem auditados nesta etapa.
- Nenhuma conclusão sobre viés na apuração.
