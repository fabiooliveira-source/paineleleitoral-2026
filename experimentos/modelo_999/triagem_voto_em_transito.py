#!/usr/bin/env python3
"""Triagem documental da hipótese voto em trânsito; não confunde dados de aptos com habilitações."""
import json,pathlib
p=pathlib.Path("experimentos/modelo_999/resultados/redistribuicao_aptos_territorial.json")
d=json.loads(p.read_text());s=d["summary"]
# Números documentados pelo TSE, notícia publicada em outubro de 2026.
official={"total_2t":314519,"SP":52206,"BA":30841,"MG":29593,"RJ":24736}
state={x["key"]:x["delta"] for x in s["uf"]["top_unbalanced"]}
report={"status":"TRIAGEM_DOCUMENTAL_SEM_VINCULO_INDIVIDUAL",
 "fontes":[{"tipo":"TSE - voto em transito 2026","url":"https://www.tse.jus.br/eleicoes/eleicoes-2026-content/voto-em-transito-perguntas-e-respostas"},
 {"tipo":"TSE - resolucao 23.751/2026 art. 30","url":"https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-751-de-26-de-fevereiro-de-2026"},
 {"tipo":"TSE - habilitacoes 2 turno","url":"https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/faltam-9-dias-mais-de-314-mil-pessoas-solicitaram-voto-em-transito-para-o-2o-turno-das-eleicoes"}],
 "habilitacoes_voto_em_transito_2t":official,
 "dados_repositorio":{"aumento_bruto_aptos_secoes":37346,"reducao_bruta_aptos_secoes":37346,
 "saldo_liquido_aptos_uf":state,"soma_positiva_saldos_uf":s["uf"]["positive"]},
 "comparacao":{"habilitacoes_2t_dividido_aumento_bruto_secoes":official["total_2t"]/37346,
 "observacao":"Habilitações do TSE são grandeza distinta da variação de aptos entre turnos. Não há correspondência 1:1 nem base para subtração."},
 "veredito":"INDETERMINADO",
 "pendencias":["Obter seções oficiais com modalidade de transferência temporária por turno e identificadores de zona/seção.",
 "Obter quantitativos oficiais de habilitados por turno e seção para correspondência territorial.",
 "Conferir se os 55.722 registros decorrem de mudanças reais de aptos ou transformação de dados na construção do repositório.",
 "Não inferir voto em trânsito apenas por saldo positivo/negativo ou por mudança do local de votação."]}
out=pathlib.Path("experimentos/modelo_999/resultados/triagem_voto_em_transito_2026.json");out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"veredito":report["veredito"],"comparacao":report["comparacao"]},ensure_ascii=False))
