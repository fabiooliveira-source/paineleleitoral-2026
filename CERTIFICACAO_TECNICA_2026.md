# Parecer de certificação técnica — 30/10/2026

## Veredito
**APROVAÇÃO PARCIAL — CERTIFICAÇÃO INTEGRAL NÃO CONCEDIDA.**

Este parecer avalia somente integridade de arquivos, execução de testes, chaves municipais/zonais e reconciliação nacional. Não certifica a autenticidade de cada boletim de urna, o processo de totalização eleitoral, a ausência de irregularidades nem o algoritmo preditivo.

## Evidências reproduzíveis
- Workflow GitHub Actions ID **40994524681**, branch `melhorias-validacao-eleitoral-2026`, com cinco trabalhos concluídos com sucesso.
- Quatro ZIPs recebidos e aprovados em teste de CRC, preservados como artefatos temporários do Actions (retenção 90 dias).
- Arquivo municipal de candidatos gerado em **29/10/2026 19:31:43**.
- Script `comparar_munzona_tse_2026.py`: **25.168 linhas** filtradas (presidente, candidatos 13/22, turnos 1/2); **zero chaves duplicadas** segundo chave turno+UF+município+zona+candidato+trânsito.
- Totais nacionais apurados e conferidos com `dados/2026/validacao.json` (28/10):
  - 1º turno: Lula 53.879.538; Flávio 56.104.503.
  - 2º turno: Lula 64.256.232; Flávio 59.826.041.
  - Diferença nacional por candidato/turno: **zero**.
- Relatório detalhado atual por município/zona preservado como artefato `auditoria-munzona-2026`.

## Limites de inferência
- Igualdade de totais nacionais **não implica** igualdade de votos por UF, município, zona ou seção. Alterações locais podem se compensar.
- O processamento municipal/zonais não comparou as linhas da versão anterior: somente os totais nacionais anteriores estão disponíveis nesta etapa.
- ZIPs municipais antigos não foram recuperados; manifestos com SHA-256 não permitem reconstruir seu conteúdo.
- A diferença de SHA-256/tamanho entre versões pode decorrer de conteúdo, metadados ou compactação; não prova mudança de votos.
- CRC de ZIP não é prova de autenticidade criptográfica do TSE.
- Os testes não certificam previsões históricas sem snapshots com carimbo de tempo e validação livre de vazamento temporal.
- A publicação de artefatos no GitHub Actions tem retenção limitada; arquivamento durável e proveniência exigem procedimento adicional.

## Critérios para certificação integral
1. Recuperar versão antiga dos CSVs municipais e comparar chaves/valores de ambas as versões, gerando diff assinado por hash e totalização das diferenças.
2. Reconciliação por UF, município, zona e seção, para todos os candidatos e indicadores de comparecimento, votos válidos, brancos e nulos.
3. Comparar dados de seção com boletins e totalizadores independentes, documentando filtros e exceções.
4. Cobertura de testes de regressão, casos-limite, carga e stress, com logs e resultados reproduzíveis.
5. Para algoritmo de projeção: backtesting com snapshots efetivamente disponíveis em cada instante, sem acesso a dados futuros.
6. Revisor independente reproduzir o processo a partir das mesmas fontes e hashes.

## Conclusão
Aprovação **somente do escopo comprovado**: processamento executado com sucesso, integridade ZIP/CRC, unicidade das chaves selecionadas e igualdade dos totais nacionais selecionados. **Certificação integral: pendente**. Nenhum achado descrito neste parecer permite concluir fraude ou manipulação eleitoral.
