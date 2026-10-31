# Parecer técnico — V7, validação histórica temporal, 18 municípios (2020)

**Data da execução:** 2026-10-31. **Branch:** `experimento/modelo-territorial-999`.
**Resultado do protocolo retrospectivo: APROVADO 18/18.**
**Certificação integral e prospectiva: NÃO CONCEDIDA.**

## Origem e congelamento

A V7 foi escrita em arquivo novo e o código original da V6 não foi alterado.
O Git blob da V7 foi congelado antes da primeira pontuação do holdout:
`f5701acc902a3d420030737196fcbf6b8dcb0a1e`.

O protocolo selecionou 18 municípios de 18 estados, resultados de 2020,
sem substituir nenhuma cidade após o teste. Os insumos foram construídos
num workflow **somente de dados** e congelados com SHA-256 em separado,
ANTES de executar os estimadores.

- [Preparação dos 18 arquivos oficiais e checkpoints](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41252574828): **success**, 18/18 UFs.
- [Congelamento dos 18 arquivos, antes da primeira pontuação](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41252610671): **success**.
- [V7 versus V6/V4/baseline — gate científico retrospectivo](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41253079566): **success**.
- [V7 — mutações adversariais de software](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41252705722): **success**, 2.565 verificações sobre 285 checkpoints de desenvolvimento.
- [Parecer formal da certificação integral](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41253114992): relatório reproduzido com sucesso, mas **gate de certificado integral corretamente BLOQUEADO** por ausência de outras evidências.

## Resultados da V7 no holdout temporal de 2020

- **18/18 municípios aprovaram todos os nove critérios predefinidos por município.**
- **342/342 checkpoints primários** (5%, 10%, ..., 95%) tiveram estimativa da V7.
- **342/342 projeções de liderança provisória** estavam corretas nesse recorte.
  Isso NÃO é 342 eleições independentes nem 100% de chance futura de acerto.
- **1.800/1.800 checkpoints** (1% a 100%) foram reconstruídos e avaliados
  como diagnósticos, incluindo marcos de apuração concluída.
- MAE médio **por município**, em pontos percentuais, com pesos iguais
  para os 18 municípios:
  - V7: **0,185720 pp**.
  - V6 congelada: **0,202257 pp**.
  - Proporção simples observada: **0,787033 pp**.
- MAE V7 foi menor que V6 em **11 municípios**, maior em **7**.
  Portanto, **não houve dominância uniforme**, apesar da melhora média.
- Maior erro absoluto da V7 entre as 18 cidades e os checkpoints primários:
  **1,595378 pp** (Maceió).
- Rio de Janeiro teve pico de **1,030764 pp**.

## Por que 100% de aprovação no holdout NÃO concede 100% de certificação

Esses resultados são fortes **para o recorte histórico estudado**, mas
existem limitações independentes do desempenho:

1. **Disponibilidade temporal:** o timestamp de primeira totalização TSE
   foi associado retrospectivamente ao resultado final da seção.
   Não se verificou, com snapshots públicos capturados em tempo real,
   que cada voto estava publicamente disponível nesse instante.
2. **Autenticidade de parciais:** o TSE informa que o repositório de dados
   consolidados pode refletir retotalizações posteriores.
   São necessários snapshots originais com origem, hash de arquivo
   e horário de recebimento do painel contemporâneo.
3. **Amostra não cega e não probabilística:** o mesmo projeto selecionou
   os 18 casos (antes da pontuação V7), codificou, reconstruiu e avaliou.
   O resultado histórico era potencialmente conhecido, embora não
   utilizado diretamente no código V7. Auditoria de terceiro permanece
   necessária.
4. **Dependência estatística:** cada eleição é uma unidade estatística;
   os 19 checkpoints por cidade não são ensaios independentes.
5. **Sem calibração:** `estimate_a=0.51` é percentual projetado de
   votos válidos do candidato A, **não** 51% de probabilidade de vitória.
6. **Sem validação prospectiva:** nenhuma coleta independente de
   snapshots públicos futuros testou a V7.
7. **Limites do escopo:** vitória categórica e precisão da margem não são
   equivalentes; testes com disputas mais apertadas, mudanças adversas na
   ordem territorial, falhas e revisões reais são necessários.

## Checklist mecanizado (não confundir com acurácia)

O parecer `emitir_parecer_certificacao_v7.py` verificou 10 requisitos
de evidência para **certificação integral**.
**4/10 requisitos estão atualmente comprovados (40% do checklist).**
Os demais 6 não podem ser dados como cumpridos só com código próprio:

| Gate | Resultado atual |
|---|---|
| A. Integridade de dados e hashes | APROVADO |
| B. Cronologia pública autenticada | PENDENTE |
| C. Congelamento modelo/protocolo/dados | APROVADO |
| D. Verificação externa independente da engenharia | PENDENTE (embora testes internos adversariais tenham passado) |
| E. Holdout histórico preregistrado 18/18 | APROVADO |
| F. Comparação obrigatória com V4/V6/baseline | APROVADO |
| G. Testes com atrasos e revisões REAIS da fonte | PENDENTE |
| H. Calibração estatística e incerteza prospectiva | PENDENTE |
| I. Auditor externo independente assina e reproduz | PENDENTE |
| J. Dados prospectivos autenticados em eleição futura | PENDENTE |

**40% significa fração de requisitos comprovados**, NÃO 40% de acerto,
NÃO 40% de confiança preditiva.

## Conclusão técnica

**Aprovamos 100% do protocolo histórico de 2020**, um avanço real e
reproduzível. **Não podemos emitir certificado de 100% de confiança
preditiva, nem certificar integralmente a V7**, pois faltam provas
externas, cronologia pública real e validação prospectiva.

Nenhuma regra, parâmetro ou cidade desse teste foi ajustado depois
de conhecer o resultado para forçar a aprovação. `main` intacta.

**Recomendação:** manter V7 como candidata experimental em branch
isolada. Oferecer pacote de hashes, relatórios e testes para revisão
de terceiros. Para o próximo ciclo, armazenar assinadamente os
snapshots públicos durante a apuração, com relógio UTC e as revisões.

## Adendo — segunda implementação aritmética independente

Nova execução GitHub Actions:
https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41253315254

Foi reproduzida a fórmula V7 em Python `decimal.Decimal` com precisão
48 dígitos, separadamente dos cálculos `float` da V7 original,
sem alterações no código congelado:

- **1.769 checkpoints preditivos** conferidos entre duas implementações;
- **31 checkpoints de encerramento** verificados separadamente;
- **zero divergências aritméticas acima de 10^-9 pp**;
- **zero abstenções não explicadas** e **zero falhas do gate**.

O êxito reforça a **reprodutibilidade matemática** e NÃO comprova
calibração futura, disponibilidade de parciais públicas ou revisão
por uma instituição externa.

**Cautela com amostra de margens:** entre os 18 municípios selecionados,
o menor diferencial final entre os dois finalistas foi aproximadamente
**2,294 pp (Cuiabá)**. A capacidade de acertar casos com diferença
inferior a 1 pp permanece não avaliada nesse conjunto de 2020.
