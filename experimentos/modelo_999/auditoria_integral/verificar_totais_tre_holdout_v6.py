"""Independent aggregate cross-check against 2024 TRE/TSE published 2T tallies.

Official election pages are cited in the holdout report. These totals are
used ONLY to verify reconstruction after it is complete; NEVER model inputs.
"""
import json
import pathlib
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"holdout_v6_2024"

# Counts in candidate_a/candidate_b order registered in the external holdout protocol.
OFFICIAL_2024_2T={
    "85898":{"name":"Canoas","a":75688,"b":69518,"blank":10434,"null":11229},
    "85995":{"name":"Caxias do Sul","a":116730,"b":110476,"blank":8861,"null":11676},
    "88013":{"name":"Porto Alegre","a":406467,"b":254128,"blank":27249,"null":26811},
    "88412":{"name":"Santa Maria","a":76803,"b":64113,"blank":3149,"null":2865},
    "13730":{"name":"Caucaia","a":109835,"b":72014,"blank":5544,"null":10425}
}
SOURCES={
    "85898":"https://resultados.tre-rs.jus.br/eleicoes/2024/620/RS85898.html",
    "85995":"https://resultados.tre-rs.jus.br/eleicoes/2024/620/RS85995.html",
    "88013":"https://resultados.tre-rs.jus.br/eleicoes/2024/620/RS88013.html",
    "88412":"https://resultados.tre-rs.jus.br/eleicoes/2024/620/RS88412.html",
    "13730":"https://www.tre-ce.jus.br/eleicao/eleicoes-anteriores/eleicoes-2024/relatorios-de-resultados-da-totalizacao"
}
def run():
    comparisons=[]
    for code,official in OFFICIAL_2024_2T.items():
        data=json.loads((OUT/(code+"_checkpoints_1_100.json")).read_text())
        final=data["final_votes"]
        expected={"candidate_a":official["a"],"candidate_b":official["b"],
                  "blank":official["blank"],"null":official["null"]}
        ok=expected==final
        comparisons.append({"code":code,"name":official["name"],
                            "reference_url":SOURCES[code],
                            "expected_official":expected,
                            "reconstructed":final,"match":ok})
        print(json.dumps({"municipality":code,"crosscheck_match":ok},flush=True))
    result={"status":"INDEPENDENT_AGGREGATE_RECONCILIATION",
            "cases":comparisons,"all_match":all(x["match"] for x in comparisons),
            "not_independent_model_certification":True}
    (OUT/"totais_oficiais_conciliados.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    if not result["all_match"]:raise SystemExit("Official final-vote reconciliation FAILED")
    print(json.dumps({"official_aggregates_all_match":True,"cases":len(comparisons)}),flush=True)
if __name__=="__main__":run()
