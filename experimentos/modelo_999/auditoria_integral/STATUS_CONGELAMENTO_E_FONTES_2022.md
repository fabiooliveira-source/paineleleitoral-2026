# Atualização: bloqueio contornado para reconstrução territorial

Foi executado um backtest territorial reconstruído de 2022. A curva resultante coincide exatamente com os 5.286 registros nacionais oficiais em votos dos dois candidatos, brancos, nulos e seções.

Leia o [relatório atualizado](STATUS_RECONSTRUCAO_TERRITORIAL_2022.md), que detalha os sete cenários e as limitações. A base é uma reconstrução por primeira totalização, não captura dos snapshots estaduais originais. Certificação integral continua não concedida.

---

## Registro anterior da investigação (preservado)

# Preditor identificado e busca temporal UF — 2022

## Resultado

Código causal audit-v2 identificado, testado e congelado no commit 419593081c7178a9b4e293cb0b13befe1808fe1a. Histórico temporal contemporâneo por UF de 2022 não foi obtido nas fontes consultadas. Validação territorial externa continua bloqueada por dados, não está em execução e não foi certificada.

Todo o trabalho deste registro está na branch experimento/modelo-territorial-999. main não foi modificada.

## Identificação e correção

O manifesto anterior foi preservado integralmente. Seu hash não coincide com os 27 arquivos Python examinados em experimentos/modelo_999, cujos bytes foram confrontados com os identificadores dos blobs Git. Outros arquivos Python da árvore também foram examinados sem coincidência, mas a evidência reproduzível anexada limita-se aos 27 arquivos do experimento. Não foi possível recuperar e autenticar um preditor audit-v1 a partir daquele manifesto.

A versão v2 deriva explicitamente de backtest_primeiro_turno_uf.py. Mantém os parâmetros de 300 segundos de idade máxima e 600 segundos de decaimento, assim como a fórmula de ponderação e swing. Foi extraída para uma função sem acesso ao resultado final. A cobertura exige numerador e denominador contemporâneos: deixou de usar o total de seções do último snapshot. Também distingue horário de geração e disponibilidade ao consumidor e rejeita histórico indisponível.

Isso constitui nova versão, não identificação retroativa do hash antigo. O desempenho retrospectivo anteriormente publicado (MAE 0,827 pp) pertence à implementação anterior; não pode ser atribuído automaticamente à v2. Não houve ajuste de parâmetros por desempenho de 2022.

congelamento_v2.json registra caminhos, SHA-256, parâmetros, commit de origem, critérios e limitações. O código, os testes e o manifesto publicados foram relidos no commit fixo e confrontados com o conteúdo local. O congelamento do código está concluído; o congelamento das entradas de validação territorial permanece pendente.

## Verificação realizada

10 testes unitários passaram: informação futura; chegada tardia; registro vencido; histórico futuro; fechamento em 100%; denominador inválido; equivalência numérica de controle com a fórmula anterior; invariância à ordem de entrada; conflito no mesmo instante; indisponibilidade nacional. Os testes verificam a função, não certificam toda a cadeia de aquisição, disponibilização pública ou calibração estatística.

Reprodução:

```sh
python -m unittest discover -s experimentos/modelo_999/auditoria_integral -p test_preditor_causal_v2.py -v
```

## Fontes procuradas

- Catálogo oficial: https://dadosabertos.tse.jus.br/dataset/resultados-2022
- API do catálogo: https://dadosabertos.tse.jus.br/api/3/action/package_show?id=resultados-2022
- Documentação: https://www.tse.jus.br/eleicoes/eleicoes-2022/arquivos/interessados

O catálogo consultado contém 34 recursos. Os dois recursos identificados como histórico temporal são BR, primeiro e segundo turnos. Os recursos por seção e município não são apresentados como captura integral de parciais temporais por UF.

Consultadas 29 URLs EA13 de evolução (BR, 27 UFs e ZZ) e 3 índices (BR, SP, BA), conforme nomenclatura da documentação oficial. Todas as 32 retornaram HTTP 404. A consulta ao catálogo retornou HTTP 200. URLs e resultados estão em disponibilidade_uf_2022.json. Esses resultados não provam que nenhum acervo exista em outro endereço, instituição ou coletor.

O script buscar_historico_uf_2022.py permite repetir a busca e preserva bytes e hashes dos retornos bem-sucedidos. Seu JSON de execução registra a situação observada nesta consulta; uma execução futura pode retornar situação diferente.

Foi ainda consultada https://numerosdaeleicao.com.br/fontes. A própria página descreve o acervo 2022 como reconstrução com BUs finais, sem gravação das parciais originais e sem recuperação de correções intermediárias. Não foi aceito como substituto de snapshots contemporâneos para certificar causalidade territorial. Nenhum voto final foi retrodatado nesta etapa.

## Condições para desbloquear

Obter um acervo de parciais UF de 2022 com proveniência verificável, identificação de versão, horários de geração e disponibilidade, hashes e referência de primeiro turno. Não preencher horário de recebimento desconhecido com horário de totalização como se fossem o mesmo evento. Em ausência de registro de disponibilidade pública, delimitar o resultado a simulação informacional por horário de totalização.

Se esse acervo não puder ser recuperado, manter a avaliação real de 2022 limitada ao nacional. Reconstruções ou ordens simuladas podem ser usadas como testes de estresse explicitamente identificados, sem elevar o status para validação temporal territorial independente.

Certificação integral permanece NÃO CONCEDIDA. Não houve nova estimativa de probabilidade de acerto.
