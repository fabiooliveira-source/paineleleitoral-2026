# TSE — Presidencial 2026: dados oficiais e comparação

Verificação e download em 28/10/2026. Fonte exclusiva: https://dadosabertos.tse.jus.br/dataset/resultados-2026

Os quatro ZIPs originais estão preservados sem alteração. Total: 949.574.426 bytes. Todos retornaram HTTP 200, tamanho compatível com Content-Length e passaram na verificação CRC. downloads.json registra URLs, cabeçalhos e SHA-256; integridade_zip.json registra a integridade dos membros.

## Arquivos organizados

- comparacao_municipios.csv: uma linha por UF e código municipal TSE, votos nominais e válidos de Lula e Flávio, aptos, comparecimento, abstenções, brancos, nulos, percentuais válidos e diferenças entre turnos.
- comparacao_secoes.csv: uma linha por UF, município, zona e seção, valores de ambos os turnos, situação, local de votação e transições de zero.
- secoes_com_zero.csv: recorte de seções com zero conferido para ao menos um dos dois candidatos em algum turno.
- pendencias_secoes.csv: situações que impedem classificar o voto ausente como zero conferido.
- divergencias_municipio_secoes.csv: diferenças entre a soma das seções e a publicação municipal mais recente, sem ajuste artificial.
- validacao.json: contagens, cobertura, candidatos, datas de geração e resultados dos controles.

CSV em UTF-8 com BOM e separador ponto e vírgula. Importe códigos como texto: codigo_municipio_tse tem cinco dígitos; não é código IBGE. A comparação por seção é feita pela chave UF + município + zona + seção; a coluna mesmo_local_votacao indica se o identificador do local permaneceu igual. Igualdade de chave não comprova identidade do eleitorado entre turnos.

## Cobertura e definição

Cargo 1 (Presidente), ano 2026, eleição 6257 (primeiro turno) e 6258 (segundo turno). Lula: 13, LUIZ INÁCIO LULA DA SILVA; Flávio: 22, FLAVIO NANTES BOLSONARO. Identidades confirmadas nos próprios arquivos.

Utilizados somente os membros terminados em _BR.csv, que contêm o recorte federal presidencial. Não foram somadas suas cópias por UF nem BRASIL.csv. Zonas e registros distintos de voto em trânsito foram agregados por município. Quantidades municipais: 5757, sendo 186 unidades do exterior (UF ZZ). Não chamar os registros ZZ de municípios brasileiros.

Seções distintas: 499248. Os registros de seção e turno conferidos somam 998411. Uma seção entra no recorte de zeros conferidos quando está instalada, não anulada, tem registros de votação e a soma de todos os votáveis coincide com nominais + brancos + nulos + anulados em separado. Nessas condições, candidato ausente da lista esparsa de votos é interpretado como zero; fora delas a ausência permanece em branco. O valor zero explícito é preservado, mas só entra nas contagens de zeros se a situação for conferido. Seções sem qualquer votação registrada são pendências e não entram nesse universo.

Para Flávio: 81 zeros no primeiro turno, 106 no segundo; 50 zero→zero; 56 positivo→zero; 30 zero→positivo. Uma seção zerada no primeiro turno, Trípoli/ZZ, município 30686, zona 1, seção 443, ficou sem registros de votação e com comparecimento zero no segundo, permanecendo fora das transições conferidas. Para Lula: 8 zeros no primeiro e 4 no segundo. Contagens incluem exterior e excluem situações não conferidas. Zero voto não demonstra irregularidade.

Diferença = segundo menos primeiro turno. Percentual municipal = 100 × votos nominais válidos do candidato / total de votos válidos para Presidente. Campos vazios significam indisponível ou não comparável, nunca zero imputado indiscriminadamente.

## Limitações concretas e atualização

Datas de geração gravadas nos CSVs:
- detalhe_votacao_munzona_2026: 28/10/2026 05:32:36
- votacao_candidato_munzona_2026: 28/10/2026 12:32:58
- detalhe_votacao_secao_2026: 26/10/2026 09:49:06
- votacao_secao_2026_BR: 26/10/2026 12:07:25

Os arquivos municipais são mais recentes que os de seção. A reconciliação resultou em 0 combinações município/turno/medida com diferenças: votos de Lula, votos de Flávio e comparecimento coincidiram em todos os cruzamentos. O CSV de divergências contém apenas o cabeçalho. Os votos municipais usam a publicação municipal; o estudo de zeros usa a publicação por seção. Os horários diferentes são preservados como metadados, apesar da reconciliação bem-sucedida destas três medidas.

Há 82 registros seção/turno não instalados ou anulados e 3 sem votação, separados em pendencias_secoes.csv. No catálogo, o TSE informa 39 registros de eleitores duplicados por transferência temporária: aptos publicados 158.745.502; total efetivo informado 158.745.463. Aptos foram preservados como publicados, sem distribuir a correção por município sem evidência. Aptos, comparecimento e abstenções não necessariamente fecham por simples soma quando há seções não instaladas.

Não houve impedimento de acesso ou download. As limitações são as pendências e a ressalva do eleitorado acima; as datas de geração diferentes não produziram divergências nas três medidas reconciliadas. Os números da conversa anterior só podem ser considerados confirmados onde reproduzidos nesta extração.

## Reprodução

organizar.py contém as transformações e controles. Execute da pasta de trabalho original, que contém outputs/tse_2026, com Python 3 e biblioteca padrão. Os ZIPs originais devem permanecer em outputs/tse_2026. O script lê CSVs dentro dos ZIPs sem expandir todas as cópias. A soma dos membros descompactados é muito maior que os arquivos baixados. Não é necessário abrir as bases brutas inteiras no Excel.
