# Executar a V4 na branch experimental

A V4 está implementada em preditor_causal_v4.py, congelada e qualificada no escopo dos replays pareados. executar_v4.py fornece um adaptador executável para gerar JSON que uma integração do painel poderá consumir. Nenhuma alteração foi feita na main; a página pública continua com seu modelo atual.

## Reprodução imediata

Na pasta experimentos/modelo_999/auditoria_integral:

```sh
python executar_v4.py --input entradas_pareadas_v4_2020.json --checkpoint 5 --output saida_v4.json
python -m unittest discover -s . -p test_integracao_v4.py -v
```

O exemplo é um replay identificado: São Paulo2020, Boulos50 como A, Covas45 como B, marco de5%. Não é previsão atual nem uma captura pública contemporânea autenticada.

## Entrada de um único instante

Também é aceito um documento JSON com:

- current: timestamp, available_at, votes_a, votes_b, electorate_total, electorate_counted;
- reference: objeto por estrato, com votes_a/votes_b do primeiro turno inteiro e available_at;
- ledger: um registro por estrato, com scope, timestamp, available_at, votes_a/votes_b atuais e matched_first_a/matched_first_b do primeiro turno das MESMAS seções já observadas;
- config opcional: a e b com identificadores dos candidatos e municipality com código TSE; year opcional.

Para esse documento, executar sem --checkpoint. As contagens devem ser inteiros não negativos e timestamps devem incluir fuso. Não atribuir datas fictícias a dados recebidos depois: a hipótese de disponibilidade dos replays não pode ser convertida em comprovação operacional de um feed real.

O ledger deve estar completo, sincronizado no instante atual e conciliado com o total agregado. Um arquivo com totais somente por UF não permite fabricar matched_first_a/b. A referência depende das identidades das seções efetivamente observadas.

## Saída v4-panel-1

- observed: votos observados, eleitorado e eleitores restantes;
- projection: participação estimada de A/B, ou null quando não há estimativa admissível;
- conditional_bounds: limites físicos e eventual vencedor condicional;
- model_sha256: confrontado com congelamento_v4.json antes de executar;
- source_document_sha256: identidade do documento de entrada inteiro; não é atributo utilizado na projeção;
- contest: ano e identificadores declarados de A/B, quando disponíveis;
- operational_approved=false e certification_integral=false;
- probabilidades sempre null: os limites determinísticos não são probabilidades calibradas.

Estados: ESTIMATED, ABSTAIN, CLOSED ou ERROR. CLOSED significa que o contrato informa eleitorado restante zero; não é, por si, uma homologação institucional do resultado.

Em ABSTAIN, a integração deve retirar a projeção pontual da tela e pode mostrar apenas os limites condicionais identificados como tais. Não substituir null por zero, não manter o último percentual como se fosse atualizado e não rotular um conditional_winner como vencedor oficial.

Em erro de leitura, esquema, timestamp ou integridade, o CLI grava ERROR com projeções nulas e retorna código2. A escrita é atômica para evitar arquivos JSON parciais. Entrada e saída não podem ser o mesmo caminho. Falhas de permissão ou armazenamento que impeçam a gravação devem ser tratadas pelo integrador; não presumir atualização apenas por existir um arquivo antigo.

## Verificação feita nesta entrega

Nove testes de integração: comparação com o resultado já qualificado, marco explícito, exclusão de marcos posteriores da previsão selecionada, rejeição de marco duplicado, abstinência por ledger incompleto, execução CLI, remoção de projeção antiga em erro de JSON ou timestamp e proteção do arquivo de entrada. O preditor congelado não foi alterado.

A próxima conexão operacional exige um coletor real por seção e a validação de origem, recepção, revisão e cadastro. Este adaptador deixa pronta a execução e a interface de dados; não representa implantação no painel público nem certificação integral.
