# V6 — primeiro holdout histórico de cinco cidades (2024): gate reprovado

**Data:** 2026-10-31. Branch: `experimento/modelo-territorial-999`; `main` não alterada.

## Decisão

**O workflow acusou `failure` CORRETAMENTE: apenas 3 de 5 cidades
cumpriram todos os critérios definidos antes do teste.** Não é falha de
infraestrutura ou aritmética; é reprovação do **gate de desempenho**.

- Execução original e artefato integral: https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41249875043
- Auditoria aritmética independente da implementação (frações exatas):
  https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41249973049
- Diagnóstico de checkpoints e zonas:
  https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41250110358

## Desenvolvimento do teste

- Protocolo de cinco cidades e critérios congelado em commit
  `e5161ff62edd153b1cb82cd2cba4348e7b0ca33f` antes da primeira
  execução dessas novas cidades.
- Cinco cidades 2024, 100 checkpoints reconstruídos por cidade (1% a
  100%); 19 checkpoints primários por cidade, 5%, 10%, ... 95%.
- Fontes oficiais TSE ZIP com hashes SHA-256 previamente fixados, CRC
  íntegro e totais finais conferidos. Os horários são de **primeira
  totalização interna das seções, reconstituídos**, e não snapshots
  públicos de tempo real autenticados.
- Comparação sem reajuste da fórmula V6 (limite de 20%), V4 protegida
  e proporção observada.
- 495 verificações por implementação matemática alternativa com
  `fractions.Fraction` corresponderam à V6 com erro numérico máximo
  de cerca de 1,11e-14 pp; cinco marcos de 100% tratados como
  fechamento aritmético.
- **5/5 fontes reconstruídas, 5/5 testes aritméticos compatíveis,
  apenas 3/5 cidades passaram o gate predefinido.**

## Resultado do holdout, MAE em pontos percentuais

| Município | V6 | V4 | Proporção observada | Gate |
|---|---:|---:|---:|---|
| Canoas | 0,111049 | 0,111049 | 1,652159 | PASSA |
| Caxias do Sul | 0,350123 | 0,350123 | 0,630633 | **FALHA:** vencedor errado aos 5% |
| Porto Alegre | 0,076588 | 0,049851 | 0,925064 | PASSA |
| Santa Maria | 0,715740 | 0,171998 | 1,781512 | **FALHA:** vencedor errado aos 5%, P95 e erro máximo |
| Caucaia | 0,327135 | 0,327135 | 0,709746 | PASSA |

Em Caxias do Sul, aos 5% a V6 previu 49,3725% para A enquanto
o resultado final foi 51,3763%; erro -2,0038 pp. V4 apresentou
a mesma previsão, portanto é falha compartilhada.

Em Santa Maria, aos 5% a V6 previu 48,3699% para A enquanto
o resultado final foi 54,5027%; erro -6,1328 pp. A V4 previu
54,4818%, com erro de somente -0,0209 pp. O primeiro checkpoint
de Santa Maria continha **51,27% dos votos de referência do 1º turno
em uma zona sem amostra**, ativando a regra de mistura V6. Esta
correspondência é um forte indício de que a regra de tratamento de
zona sem dados pode piorar projeções mesmo quando a fórmula está correta.
É um diagnóstico, não identificação causal definitiva.

## Por que não alterar silenciosamente os limites

Esses cinco municípios agora foram avaliados e deixam de ser uma amostra
independente para quaisquer modificações futuras. Escolher entre V4 e
V6 usando o resultado final dessas cidades invalidaria o teste externo,
por vazamento de informação e sobreajuste.

A implementação **não** deve ser promovida a um painel de previsão
sem novos testes. Não declarar que a V6 está certificada. O workflow
de gate científico deve permanecer vermelho até que um modelo
**novo e previamente congelado** enfrente outra seleção de eleições
não analisadas. Não usar os próprios cinco casos reprovados para
declarar aprovação prospectiva.

## Próximas atividades tecnicamente legítimas

1. Estudar as causas da falha, sobretudo cobertura territorial
   aos 5%, sem ajustar a V6 congelada.
2. Comparar com outros municípios/regiões e ciclos sem acesso ao
   resultado futuro na etapa de modelagem; preregistrar antes.
3. Separar projeção do placar (`estimate_a`) de previsão categórica
   de vencedor e de chamada matematicamente irreversível.
4. Modelar dados de `available_at` reais em vez de assumir que
   horário interno de totalização equivale à publicidade dos votos.
5. Se desenvolver V7, tratar cinco cidades recém-testadas como
   **desenvolvimento**, exigindo um holdout adicional distinto,
   com critérios e modelos congelados.

**Conclusão: erro do GitHub Actions é o bloqueio científico esperado.
Integridade técnica aprovada, precisão externa histórica não aprovada;
certificação integral ainda pendente.**
