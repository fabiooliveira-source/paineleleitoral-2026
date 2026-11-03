# Investigação de versões dos dados oficiais TSE 2026

## Evidência preservada
Execução GitHub Actions #14, ID 40993959893, commit 86b9c01cb37942ace941dfca8a87841b6c119939: quatro jobs de download, verificação CRC e upload de artefatos concluídos com sucesso. Artefatos retidos por 90 dias.

- detalhe_votacao_munzona_2026.zip: artifact 12950940431
- votacao_candidato_munzona_2026.zip: artifact 12949819696
- detalhe_votacao_secao_2026.zip: artifact 12950381844
- votacao_secao_2026_BR.zip: artifact 12950935495

## Divergências entre 28 e 30/10
Comparação preliminar de tamanho e SHA-256 de arquivos brutos, não de votos:
- votacao_candidato_munzona_2026.zip: 470170707 bytes antes, 466183381 bytes agora; SHA-256 anterior faaa2fd0b199c018a7f6148c62cbe9fcc65a551e6fd68e27b8a4bf0d815fa3b6, atual 6e7c7e1f79c1bbb4c00ecc804fe3b11ef4f36b0169b1f887d539ce1e85eb0e7e.
- detalhe_votacao_munzona_2026.zip: 3154863 bytes antes, 4193757 bytes agora; SHA-256 anterior 52b9926a71851a6371a2be2ce30543868c04ae4ad933b09bacc297010d944393, atual 71e14672de70199b46472b158aed4dca24467a143d3ac52da900080a0b269ae0.

Essas alterações de arquivo não comprovam alteração de votos. CRC aprovado demonstra integridade interna do ZIP, não autenticidade nem correção eleitoral.

## Próxima etapa de auditoria
1. Extrair somente membros _BR.csv dos ZIPs atuais, mantendo os arquivos originais imutáveis.
2. Reprocessar com mesmo código e critérios do levantamento de 28/10.
3. Comparar totais nacionais, 27 UFs e exterior, municípios, seções e candidatos.
4. Distinguir mudança de registros, mudança de abrangência e mudança de votos.
5. Recuperar ZIPs históricos de 28/10 para diff registro a registro; o manifesto antigo sozinho não permite reconstruí-los.
6. Documentar mudanças e horários de geração. Não inferir fraude de diferenças entre publicações.

Status: preservação confirmada; comparação dos votos ainda não executada.
