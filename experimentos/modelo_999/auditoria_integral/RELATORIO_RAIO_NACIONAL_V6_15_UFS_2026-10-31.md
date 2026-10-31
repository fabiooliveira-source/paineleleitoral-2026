# V6 — expansão nacional do holdout histórico, 15 UFs, 1.500 checkpoints

Data: 2026-10-31. Branch: `experimento/modelo-territorial-999`.
**A `main` não foi modificada.**

## Decisão inequívoca

**A V6 REPROVOU no teste nacional ampliado.** Somente **5/15 municípios**
atenderam todos os critérios anteriores ao teste (33,33% de casos).
Concluir a execução no GitHub Actions com `failure` é o comportamento
correto do *gate científico*: isso não quer dizer que a implementação
aritmética falhou.

**NÃO existe certificação integral, probabilística, prospectiva ou
independente do algoritmo com os dados atuais.** A seleção de cidades e
a reconstrução foram realizadas pelo mesmo projeto, com dados históricos
de resultados já potencialmente conhecidos.

## Evidências diretamente executadas

- Preparação independente de previsão, 15 estados:
  https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41250338824
  — `success`.
- Congelamento dos 15 insumos por hashes antes da previsão:
  https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41250436125
  — `success`. Manifesto `congelamento_raio_nacional_v6_2024.json`.
- Auditoria corrigida e projeção final:
  https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41251355639
  — reprodução e aritmética `success`, gate de desempenho `failure`.
- Um teste anterior marcou `TO` incorretamente porque assumiu que
  o estado `CLOSED` só poderia ocorrer quando 100% das seções tivessem
  sido totalizadas. O contrato correto é **eleitorado restante igual a
  zero**; algumas seções podem não ter eleitorado apto. A correção
  afetou apenas o verificador; **não mudou fórmulas, critérios ou fontes
  da V6**. A execução corrigida passou integralmente na aritmética.

## Resultados: 19 checkpoints primários por cidade (5%...95%)

MAE e máximo em pontos percentuais.

| UF | Município | MAE V6 | MAE V4 | MAE proporção observada | Gate |
|---|---|---:|---:|---:|---|
| AM | Manaus | 0,1932 | 0,2299 | 0,6280 | PASSOU |
| PA | Belém | 0,0733 | 0,0733 | 0,1723 | PASSOU |
| RO | Porto Velho | 0,6148 | 0,6148 | 0,4065 | **FALHOU** |
| TO | Palmas | 0,1045 | 0,1045 | 0,7157 | PASSOU |
| BA | Camaçari | 0,1454 | 0,1454 | 0,2556 | PASSOU |
| PB | João Pessoa | 0,2494 | 0,1986 | 0,1808 | **FALHOU** |
| SE | Aracaju | 0,5610 | 0,5610 | 0,3597 | **FALHOU** |
| PE | Olinda | 1,0215 | 0,9297 | 1,4600 | **FALHOU** |
| GO | Goiânia | 0,1378 | 0,1826 | 0,1659 | **FALHOU** |
| MT | Cuiabá | 0,2857 | 0,2857 | 0,2806 | **FALHOU** |
| MS | Campo Grande | 0,2632 | 0,2685 | 0,1438 | **FALHOU** |
| MG | Belo Horizonte | 0,4881 | 0,2523 | 0,2144 | **FALHOU** |
| RJ | Niterói | 0,9491 | 0,9670 | 0,5425 | **FALHOU** |
| SP | São Paulo | 0,1628 | 0,0792 | 0,8268 | PASSOU |
| PR | Curitiba | 1,2071 | 1,4686 | 0,5981 | **FALHOU** |

**Principais falhas no marco de 5%:** Olinda e Belo Horizonte
projetaram provisoriamente o vencedor incorreto. Várias outras cidades
foram reprovadas mesmo sem errar o vencedor, porque a V6 produziu
erros médios e/ou máximos superiores à proporção observada ou excedeu
limites de erro fixados.

A demonstração da V6 em dados anteriores de Fortaleza, Pelotas e Natal
não elimina essas reprovações em localidades distintas. Tampouco uma
cidade aprovada comprova robustez futura.

## Granularidade e unidades estatísticas

- **15 eleições municipais**, distribuídas em 15 UFs e cinco regiões,
  constituem o conjunto de desafio, não 1.500 eleições independentes.
- **1.500 checkpoints** de seções (1% a 100%) foram calculados,
  dos quais **285** são checkpoints primários (19 × 15).
- **1.484 comparações aritméticas com frações exatas** foram concluídas.
  Marcos com encerramento aritmético foram tratados separadamente.
- Dados TSE oficiais de seção e votação com integridade ZIP e SHA-256,
  revisados por manifesto.
- Os horários são da **primeira totalização interna de cada seção**,
  retroativamente reconstituídos de dados finais: não equivalem a
  fluxos públicos autenticados disponíveis a cada instante de 2024.
- A revisão não foi conduzida por um auditor externo independente.

## Falha de execução transitória resolvida

O preparo demorou em **São Paulo**, que depende de um ZIP estadual de
votação por seção de **475.818.561 bytes (~476 MB)** e da leitura de
muitos registros. O processamento terminou em `success`: 15/15 estados.
O congelamento só prosseguiu depois da conclusão da coleta de todas
as UFs, para impedir a substituição posterior de dados.

Na primeira avaliação nacional, o verificador aritmético rejeitou
indevidamente um fechamento antecipado do eleitorado de Palmas (`TO`)
antes do marco nominal de 100% das seções. Esse falso positivo foi
corrigido e o pipeline executado novamente. Na segunda execução,
**a implementação aritmética passou e a validação de desempenho reprovou**.

## Decisão para desenvolvimento futuro

1. Preservar o congelamento V6, os resultados negativos e os critérios
   originais. Não recalibrar a V6 usando dados que eram holdout e chamar
   isso de validação externa.
2. Tratar este conjunto de 15 como diagnóstico de desenvolvimento
   caso seja criado um modelo **V7**.
3. Investigar erro por concentração territorial, estratos sem amostra,
   taxa de votos válidos e momentos de entrada das zonas. A regra V6
   não usa distância geográfica, IDW ou krigagem; não alegar expansão
   de raio de interpolação espacial.
4. Pré-registrar outro conjunto de eleições não usado na V7; manter
   janelas temporais rigorosas e verificar disponibilidade dos dados.
5. Publicar cobertura, erros máximos, vieses, acerto e estabilidade
   das chamadas de vencedor com **abstenções** quando a evidência for
   insuficiente. O nível de confiança de um resultado só pode ser
   interpretado como probabilidade após calibração.

**Status final: V6 falhou no gate nacional, apesar de integridade de dados
e implementação aritmética validadas nessa bateria.**
