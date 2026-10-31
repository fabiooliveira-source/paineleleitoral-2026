# Metas de acerto V4: 99% até o piso95%

A política foi alterada a pedido do usuário: avaliar 99%,98%,97%,96%,95%, nessa ordem, sem reduzir abaixo de95%. O preditor V4 e seus parâmetros permanecem inalterados. A maior meta sustentada pela evidência é selecionada; se nenhuma passar, o resultado é meta não demonstrada, e não aprovação automática no piso.

## Definições

Acerto: identificar corretamente o vencedor pela estimativa pontual no marco de5% de seções apuradas. Empate ou ausência de estimativa conta como insucesso. Esta definição mantém o objetivo original de projeção precoce; não significa erro de participação inferior a1% ou5% e não é uma probabilidade atribuída a uma eleição específica.

População-alvo: segundo turno presidencial nacional. Unidade de teste: eleição independente comparável. Os19 marcos de uma eleição e suas simulações não são19 novas eleições.

Foi adotado nível de confiança estatística unilateral de95% para avaliar as metas de acerto. Confiança estatística e taxa de acerto são conceitos distintos. O método é o limite inferior binomial exato de Clopper-Pearson, sujeito a independência, comparabilidade, representatividade e plano amostral de tamanho previamente definido. Não é um procedimento de parada opcional para acrescentar dados até passar.

Referência institucional: https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm

## Resultado com a evidência atual

| Meta de acerto | Resultado |
|---|---|
| 99% | Não demonstrada |
| 98% | Não demonstrada |
| 97% | Não demonstrada |
| 96% | Não demonstrada |
| 95% | Não demonstrada |

A V4 acertou o vencedor nos três casos examinados no marco de5%. Porém,2018 e2022 são desenvolvimento, e São Paulo2020 não é um teste externo presidencial nacional. Não há, neste conjunto, eleições presidenciais externas elegíveis para comprovar a taxa pretendida.

Mesmo tratando ilustrativamente o caso municipal como uma tentativa de uma população mais ampla, um acerto em uma tentativa não demonstraria95% de acerto. Sob um modelo binomial independente, o limite inferior unilateral de95% para1/1 seria5%. Isso não estima que o algoritmo tenha apenas5% de acerto; mostra a falta de informação para um limite inferior elevado.

## Planejamento ilustrativo

Com zero erros e amostra fixa de eleições independentes, comparáveis e representativas, o número mínimo de sucessos necessário para o limite inferior unilateral de95% atingir cada meta seria:

| Meta | Casos independentes, todos corretos |
|---|---:|
| 99% | 299 |
| 98% | 149 |
| 97% | 99 |
| 96% | 74 |
| 95% | 59 |

Cálculo para zero falhas: limite inferior = 0,05 elevado a(1/n); n mínimo = arredondar para cima[ln(0,05)/ln(meta)]. Estes números são condições de planejamento do modelo binomial, não garantia de certificação, nem autorização para contar checkpoints ou replays repetidos como eleições independentes. Uma estratégia com erros observados ou dependência entre casos exige outro tamanho e/ou desenho.

O mesmo limite inferior é confrontado com as cinco metas aninhadas; não são cinco modelos reajustados. A redução da meta não elimina as pendências de integração, dados contemporâneos autenticados e revisão especializada independente.

## Arquivos e execução

- politica_taxa_acerto_v4.json: política de metas e piso.
- avaliar_taxa_acerto_v4.py: cálculo e avaliação sem retuning.
- resultado_metas_acerto_v4.json: resultado atual auditável.
- test_metas_acerto_v4.py: oito testes das fronteiras e das exclusões.

```sh
python avaliar_taxa_acerto_v4.py
python -m unittest discover -s . -p test_metas_acerto_v4.py -v
```

Main preservada. Nenhuma taxa probabilística do painel foi substituída por um número escolhido na política.
