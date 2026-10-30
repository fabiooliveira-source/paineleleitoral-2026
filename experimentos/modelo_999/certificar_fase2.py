#!/usr/bin/env python3
"""Portao de certificacao: criterios verificaveis e impeditivos explicitos."""
import json,pathlib,hashlib,datetime
base=pathlib.Path("experimentos/modelo_999/resultados")
load=lambda name:json.loads((base/name).read_text(encoding="utf8"))
compare=load("comparacao_modelos_fase2.json")
stress=load("stress_disponibilidade_uf_fase2.json")
gate=load("portao_qualidade_nowcast.json")
checks={
 "reprodutibilidade_backtest_2026":compare["snapshots"]==19 and stress["status"]=="STRESS_EXECUTADO",
 "melhoria_mae_retrospectiva":compare["historico_primeiro_turno_mae_pp"]<compare["baseline_mae_pp"],
 "robustez_sete_cenarios":len(stress["cenarios"])==7 and stress["todos_cenarios_superam_baseline"],
 "ausencia_uso_alvo_futuro":None,
 "validacao_fora_amostra_eleicoes_independentes":False,
 "incerteza_calibrada_por_eleicoes_independentes":False,
 "integridade_criptografica_cadeia_origem":None,
 "revisao_independente_replicada":False
}
# None = nao demonstrado, False = requisito nao atendido, True = evidenciado.
report={"estado":"CERTIFICACAO_INTEGRAL_NAO_CONCEDIDA",
 "criterios":checks,
 "n_criterios_atendidos":sum(v is True for v in checks.values()),
 "n_criterios":len(checks),
 "evidencias":{"baseline_mae_pp":compare["baseline_mae_pp"],
 "modelo_mae_pp":compare["historico_primeiro_turno_mae_pp"],
 "reducao_erro_pct":compare["melhoria_relativa_pct"],
 "pior_stress":stress["pior_cenario"],
 "pior_stress_mae_pp":stress["cenarios"][stress["pior_cenario"]]["mae_pp"]},
 "proximas_acoes":["Obter snapshots temporais oficiais de eleicoes anteriores comparaveis, com proveniencia e hashes.",
 "Congelar hiperparametros antes da validacao externa.",
 "Reexecutar backtest cronologico sem usar informacao posterior ao instante de previsao.",
 "Avaliar cobertura e calibracao de intervalos de confianca em multiplas eleicoes.",
 "Auditoria independente de codigo, fonte, autenticidade e reproducao."],
 "fontes_institucionais":["https://dadosabertos.tse.jus.br/dataset/resultados-2026",
 "https://dadosabertos.tse.jus.br/dataset/resultados-2022",
 "https://www.tse.jus.br/eleicoes/eleicoes-2026-content/arquivos/divulgacao-de-resultados"],
 "nota":"O teste de estresse perturba apenas disponibilidade de UFs; nao simula ordem alternativa real de totalizacao nacional."}
(base/"certificacao_fase2.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(report,ensure_ascii=False))
