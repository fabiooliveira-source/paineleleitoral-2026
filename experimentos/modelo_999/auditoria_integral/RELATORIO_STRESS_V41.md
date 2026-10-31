# Stress ampliado: V4.1 protegida

## Resultado

ACEITA NO ESCOPO DOS CRITÉRIOS DE STRESS PRÉ-REGISTRADOS:1.710/1.710 controles de entrada e36/36 cenários artificiais de ordem/composição passaram após acrescentar uma camada de proteção. A fórmula e os parâmetros da V4 congelada foram preservados, com as57 previsões dos replays originais numericamente idênticas. Não é certificação probabilística ou operacional integral.

A decisão refere-se a segurança de entrada, preservação de invariantes e desempenho relativo ao baseline nos cenários definidos. Não foi exigido nem demonstrado limite absoluto universal de erro,99% de acerto ou superioridade em toda eleição possível.

## Critérios fixados antes dos testes

Protocolo: commit feeae17ed7a4a6777c923c5c321945bd330896c0, protocolo_stress_ampliado_v4.json.

- Falhas de contrato: suspender estimativa em vez de conservar projeção inválida.
- Informação futura e permutações válidas: não mudar o resultado atual.
- Referências: manter previsões e comportamento dos replays válidos.
- Ordens artificiais: em cada cenário, MAE e máximo absoluto não superiores ao baseline observado,19 estimativas disponíveis e nenhum alvo fora dos limites sob as hipóteses do cenário.
- Disponibilidade: reportar abstinência separadamente; não contabilizá-la como erro zero.
- Reparo: criar camada nova preservando a versão congelada e repetir a mesma bateria; não reduzir critérios depois da execução.

## Problemas encontrados e correção

Na primeira avaliação, a V4 respondeu a1.596/1.710 controles conforme a exigência ampliada. As114 falhas foram57 casos de metadados com recebimento anterior à geração declarada e57 casos de revisão decrescente entre snapshots.

Essas verificações ampliam o contrato anterior: a V4 original não possuía estado entre chamadas nem campo explícito generated_at. Não alteram retroativamente os resultados dos testes anteriores; evidenciam funções de proteção que ainda precisavam ser acrescentadas para o contrato ampliado.

O teste temporal foi refinado para não confundir cutoff de avaliação e geração. Receber uma versão antes do cutoff é legítimo e não é falha. O caso inválido informa generated_at explicitamente posterior ao recebimento. Foi acrescentado teste que aceita recebimento anterior ao cutoff quando a ordem geração/recepção é válida. Quando generated_at não é fornecido, essa parte da proveniência não pode ser autenticada pelo software.

A camada preditor_v4_guardado.py:

1. Verifica disponibilidade no cutoff e, quando informado, generated_at <= available_at.
2. Usa o agregado anterior para detectar snapshots fora de ordem, conflitos no mesmo instante, redução dos votos/eleitorado contabilizado e mudança do cadastro total.
3. Suspende projeção e indicação condicional, com clear_prior_forecast=true, quando detecta revisão ou inconsistência.
4. Preserva o cálculo original nas entradas válidas.

executar_v41.py acrescenta arquivo --state para persistir o agregado anterior em execução de instante único. O estado não avança quando a projeção é suspensa. No replay, pode usar o marco anterior já disponível, sem acessar marcos futuros. Caminhos de entrada, saída e estado devem ser distintos. Estado perdido ou omitido indevidamente pelo integrador impede garantir detecção de revisões anteriores.

Congelamento de código e hashes: congelamento_guard_v41.json. A fórmula preditor_causal_v4.py conserva o SHA-256 original.

## Bateria de controle

Os1.710 controles distribuem-se pelos57 marcos dos replays2018/2022/São Paulo2020. Incluem dez permutações por marco, duplicatas, perdas de estratos, atrasos de1/5/15/30 minutos, dados futuros, conflitos, contagens negativas/fracionárias/booleanas, eleitorado inválido, referência indisponível ou inflada, metadados temporais e revisões decrescentes.

Após o reparo:1.710 aprovados, zero falhas. Também passaram74 testes unitários/integração existentes e novos, incluindo57 comparações exatas com as previsões originais. São verificações de software, não1.710 novas eleições.

A proteção adicional pode suspender o serviço durante inconsistência ou revisão. Isso melhora segurança, mas não comprova disponibilidade contínua nem precisão com dados ausentes. O integrador deve retirar a projeção anterior quando clear_prior_forecast=true.

## Ordem e composição: cenários artificiais

Foram construídos440 blocos de2018 e553 de2022 a partir de coortes pareadas já documentadas, mais o restante final porUF. Os totais por candidato e referência foram preservados. Blocos e entradas de referência têm SHA-256 fixados em manifesto_blocos_stress_v4.json.

Por eleição: dez embaralhamentos com sementes0..9; UFs em ordem crescente e decrescente; Nordeste primeiro e por último; perfil de primeiro turno deA baixo/alto primeiro; ordem das coortes históricas e sua inversa. Total:36 cenários e684 projeções pontuais.

Não são outras gravações oficiais de apuração. Os cortes de5..95% usam massa de votos de primeiro turno dos dois finalistas coberta pelos blocos, e não percentual real de seções. O eleitorado contabilizado sintético foi definido igual aos votos válidos observados; assim,R é conservador e os limites são amplos. A ordem artificial pode reunir blocos que, na história, foram totalizados em datas distintas. Nenhuma data foi modificada no replay original.

## Precisão sob stress

| Eleição de desenvolvimento | Cenários | Maior MAE de cenário | Maior erro absoluto | P95 do erro absoluto dos pontos artificiais |
|---|---:|---:|---:|---:|
| 2018 |18|4,0019 pp|7,7755 pp|3,2966 pp|
| 2022 |18|0,3092 pp|0,6017 pp|0,3752 pp|

Os36 cenários passaram no critério relativo ao próprio baseline, mas o máximo de7,78 pp em2018 continua relevante. Ser melhor que um baseline muito enviesado não implica precisão absoluta elevada. O maior erro do baseline em qualquer cenário2018 foi32,9199 pp; em2022,25,2810 pp. Não se utilizam esses números para esconder os erros da V4.

### Acerto observado do vencedor pela projeção pontual

Foram677 acertos em684 projeções artificiais:98,9766%, ou98,98% arredondados. Essa frequência supera98%, mas fica abaixo de99%. Os sete erros ocorreram nos cenários de2018;2022 teve zero nesses pontos.

Isso é uma FREQUÊNCIA DESCRITIVA DO STRESS, não probabilidade calibrada nem certificação de98% de acerto presidencial. São pontos correlacionados, sementes artificiais e somente duas eleições de desenvolvimento. Nenhuma eleição externa nova foi acrescentada por esses embaralhamentos.

### Indicação matemática condicional

Não houve indicação matemática errada; nesses cenários artificiais também não houve indicação matemática alguma, porque os limites conservadores permaneceram amplos. Portanto, zero indicações erradas é aqui uma abstenção completa, não uma demonstração de precisão de chamadas. As projeções pontuais e as indicações matemáticas são campos distintos. Nos replays originais, as indicações condicionais anteriormente documentadas permanecem inalteradas.

## Uso da versão protegida

Na pasta experimentos/modelo_999/auditoria_integral:

```sh
# Replay: referência anterior automática, sem modificar a V4
python executar_v41.py --input entradas_pareadas_v4_2020.json --checkpoint 5 --output saida-v41.json

# Instantes sucessivos: persistência obrigatória para detectar revisões
python executar_v41.py --input snapshot-pareado.json --state estado-v41.json --output saida-v41.json

# Reproduzir o stress com os blocos versionados
python stress_ampliado_v4.py v4
python stress_ampliado_v4.py v41
python -m unittest discover -s . -p 'test_*.py' -v
```

O fluxo não coleta dados nem se conecta sozinho ao TSE. O snapshot deve obedecer ao contrato pareado, com origem e horários verificáveis. Não apagar o estado para contornar uma revisão ou forçar aprovação. Revalidar a fonte e reconciliar versões antes de reiniciar o fluxo.

## Estado final

A V4.1 atende aos critérios de stress publicados para segurança e comparação com baseline. Não houve retuning estatístico para melhorar as sementes, implantação na main ou concessão de taxa de acerto comprovada.

Para uma aceitação absoluta mais exigente, por exemplo máximo de1pp em toda ordem adversarial, esta bateria NÃO demonstra aprovação: o próprio contraexemplo2018 tem7,78pp. Os requisitos quantitativos devem ser estabelecidos antes de outro ciclo; não se deve renomear esse extremo como erro aceitável sem decisão explícita sobre o uso.

A certificação integral continua dependendo de dados contemporâneos autenticados, integração operacional, avaliação externa comparável e revisão independente. Os resultados e contraexemplos desta rodada foram preservados para essa avaliação.

## Reprodução CI concluída

A execução [41152022365](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41152022365), commit61613eebe3259406308ead30b77c7b140400b327, concluiu com SUCESSO. O job stress-regressao reproduziu74 testes, a comparação antes/depois, os1.710 controles e os36 cenários. Hashes da camada e identidade do núcleo V4 foram confrontados. Evidência em evidencia_ci_stress_v41.json. Isso não altera as limitações quantitativas ou probabilísticas descritas acima.
