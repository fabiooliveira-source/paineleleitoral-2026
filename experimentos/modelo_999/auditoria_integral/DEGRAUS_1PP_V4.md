# Metas em passos de um ponto percentual

Confirmada a redução em passos de1 ponto percentual:99%,98%,97%,96%,95%,94% e assim por diante, até1%. Esta política substitui o piso anterior de95% a pedido do usuário. Não altera o preditor, seus parâmetros nem a população-alvo presidencial.

Foram avaliadas99 metas. Nenhuma meta positiva foi demonstrada para a população presidencial nacional com os dados externos elegíveis atuais. Os casos presidenciais2018/2022 foram utilizados no desenvolvimento; São Paulo2020 é municipal. Não se reclassificaram esses casos para produzir aprovação.

O método mantém confiança estatística unilateral de95%, distinta da taxa-alvo de acerto. Reduzir a taxa-alvo não reduz silenciosamente esse nível de confiança nem transforma ausência de evidência em certificação.

O teste matemático de1 sucesso em1 tentativa produz limite inferior de5% sob hipóteses binomiais, mas não autoriza atribuir5% ao algoritmo presidencial ou tratar o caso municipal como amostra presidencial. Ele serve apenas para conferir a implementação da rotina.

Execução:

```sh
python avaliar_degraus_1pp_v4.py
python -m unittest discover -s . -p test_degraus_1pp_v4.py -v
```

Resultado completo: resultado_degraus_1pp_v4.json. Cinco testes passaram. A main e o modelo congelado permanecem intactos. Não há nova certificação ou probabilidade calibrada.
