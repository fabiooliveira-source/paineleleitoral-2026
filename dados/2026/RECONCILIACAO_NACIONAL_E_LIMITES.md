# Auditoria eleitoral 2026 — reconciliação e limites inferenciais

Data da revisão: 2026-10-30.

## Totais registrados em dados/2026/validacao.json

| Métrica | Primeiro turno | Segundo turno | Variação |
|---|---:|---:|---:|
| Comparecimento | 125275835 | 128236074 | +2960239 |
| Votos válidos | 119300788 | 124082273 | +4781485 |
| Lula | 53879538 | 64256232 | +10376694 |
| Flávio | 56104503 | 59826041 | +3721538 |
| Brancos | 2300798 | 1430496 | -870302 |
| Nulos | 3674249 | 2723305 | -950944 |

Votos dos demais candidatos no primeiro turno = 119300788 - 53879538 - 56104503 = 9316747.
A soma dos ganhos líquidos dos dois finalistas = 14098232.
Diferença = 14098232 - 9316747 = 4781485, exatamente o crescimento dos votos válidos.

Checagens:
- Primeiro turno: 119300788 + 2300798 + 3674249 = 125275835.
- Segundo turno: 124082273 + 1430496 + 2723305 = 128236074.
- Lula + Flávio no segundo turno = 124082273.
- A base informa divergencias_municipio_secoes = 0 e duplicatas principais = 0.

## Limites do que se pode concluir

Essas igualdades são reconciliações contábeis e não provam, isoladamente, correspondência independente com boletins de urna individuais.
Os ganhos líquidos de Lula e Flávio NÃO equivalem a transferências dos eleitores dos candidatos eliminados: novos comparecimentos, abstenções, votos inválidos e mudanças entre finalistas podem produzir os mesmos totais.

## Pendências para conclusão independente

1. Confrontar seção por seção com boletins de urna assinados/publicados e registros de totalização independentes.
2. Extrair registros e questionários das pesquisas dos ZIPs originais, validar instituto, número de registro, campo, amostra e ponderações.
3. Estimar transferências via modelo ecológico com incerteza, sem apresentar fluxo individual como observado.
4. Executar testes de anomalia pré-especificados com controles por UF, porte, comparecimento e composição geográfica; revisar manualmente casos extremos.
5. Verificar a conclusão do GitHub Actions e manifesto SHA-256/CRC antes de afirmar download completo.

Fonte interna: dados/2026/validacao.json (gerado em 2026-10-28).