# Painel Eleitoral 2026

Monitor independente, sem vínculo com a Justiça Eleitoral. Publicado pelo GitHub Pages na raiz de main.

## Arquivos

- index.html: monitor conectado diretamente ao ambiente oficial do TSE; Presidência, 2º turno, ciclo ele2026. Eleição identificada no arquivo oficial ele-c.json (6258 na revisão de 25/10/2026).
- simulador.html: ambiente explicitamente fictício com os dez parâmetros herdados do simulador do usuário, velocidade de reprodução, navegação temporal, mapa offline incorporado do IBGE e exportação. Bases e distribuição territorial do simulador não são dados oficiais validados.

## Fontes e atualização

Configuração EA11 e municípios EA12; resultados nacionais, estaduais, exterior e municipais EA20; acompanhamento municipal EA15. Base fixa: https://resultados.tse.jus.br/oficial. Consulta nacional e 28 abrangências a cada 60 segundos enquanto a página estiver aberta. As consultas são espaçadas a no máximo 5 por segundo. Arquivos municipais são buscados em segundo plano após mudanças na totalização; a fila e sua cobertura são visíveis. Uma rodada grande pode exigir mais de 60 segundos para carregar todos os municípios. A CDN do TSE pode atualizar arquivos em momentos diferentes.

O monitor valida eleição, turno, ambiente oficial, abrangência, cargo, candidatos, votos válidos, contagens e correspondência entre EA15 e EA20. Não substitui falhas por dados simulados. Um arquivo com zero votos é distinto de um arquivo ausente. Os resultados nacionais informam a data/hora de geração da fonte; a hora de consulta aparece separadamente.

## Estimativa ponderada para 100%

Por município: votos observados do candidato + (eleitorado total − eleitorado de seções totalizadas) × votos observados/eleitorado de seções totalizadas. Somam-se as estimativas municipais para estado, região e Brasil, incluindo ZZ (exterior).

Municípios sem amostra usam a taxa observada da UF; na ausência, região; por último, Brasil. A parcela do eleitorado com taxa emprestada é exibida. Sem amostra alguma, não existe projeção. Sem cobertura das 27 UFs e exterior, a projeção nacional é suspensa. Não se faz média simples dos percentuais locais e não se aplica uma amostra de uma localidade a todo o país silenciosamente.

Essa razão incorpora implicitamente comparecimento e votos não válidos da amostra. Assume comportamento semelhante no eleitorado restante. A ordem de chegada das urnas não é aleatória e pode enviesar fortemente a estimativa, sobretudo no início. Não há margem de erro validada ou declaração de vencedor. Não é uma pesquisa eleitoral.

Granularidade: consolidados municipais com eleitorado das seções totalizadas, não decodificação individual de boletins de urna. O ETA usa variações recentes de seções totalizadas e é independente da projeção de votos. Seções não são necessariamente urnas físicas.

## Gráficos e mapa

Linhas temporais de percentuais oficiais e projetados, curva junto ao mapa, diferença acumulada oficial e projetada e barras de novas seções entre gerações oficiais. Histórico observado nesta sessão, sem reconstrução artificial de períodos anteriores. Lula em vermelho, Flávio em verde; mapa oficial cinza sem dados ou empate. Cartografia IBGE, fotos online Wikimedia Commons com créditos e opção de incorporar arquivos escolhidos pelo usuário.

## Validação em 25/10/2026

Conexão direta no navegador: 59 respostas TSE válidas, 28/28 abrangências e 5.757 localidades incluindo exterior, eleitorado total 158.745.502 conforme arquivos consultados. Na consulta de teste não havia seções totalizadas nos arquivos recebidos. Nenhum gráfico ou percentual de projeção foi preenchido com números fictícios.

Testes: esquema real do TSE, rejeição de outra eleição, candidatos por número estável (sem inversão por liderança local), exemplo ponderado 2.800/3.200 votos, convergência a 100%, taxa emprestada identificada, ausência de amostras, layout em 1440/768/390/320px e controles. Simulador com dez parâmetros, 27 UFs, mapa offline, limites extremos não negativos e conservação de comparecimento = votos dos candidatos + brancos + nulos.

Documentação: https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados

## Comparação oficial dos turnos — 28/10/2026

comparativo.html utiliza a base oficial TSE conferida em dados/2026: 5.757 localidades (5.571 brasileiras e 186 no exterior), 499.248 seções. Filtros por região, UF, município, perda de votos, maior comparecimento e zeros. Seções são carregadas por UF sob demanda em JSON gzip (DecompressionStream em navegadores modernos). Valores ausentes permanecem indisponíveis. A base é uma cópia datada, sem atualização automática. Votos de Lula e Flávio e comparecimento reconciliados entre municípios e seções; 85 registros seção/turno segregados. Ver dados/2026/LEIA-ME.md, validacao.json e downloads.json para critérios, datas, URLs e SHA-256. Simulador e monitor ao vivo mantêm seus respectivos modos.
