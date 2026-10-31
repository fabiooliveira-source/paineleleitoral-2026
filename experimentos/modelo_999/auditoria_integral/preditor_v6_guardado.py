"""V6 guardada: conserva a regra congelada de 20% e os contratos temporais V4.1.

Nao certificada; dados retrospectivos nao comprovam disponibilizacao publica real.
Aplicacao: predict_v6_guarded(current, reference, ledger, previous=None).
"""
import math
from preditor_v4_guardado import predict_guarded

MODEL_VERSION = "v6-guarded-2026-10-31"
COVERAGE_THRESHOLD = 0.20

def predict_v6_guarded(current, reference, ledger, previous=None):
    """Valida invariantes via V4.1 antes de calcular o estimador V6.

    Retorna ABSTAIN (estimate_a=None) quando entradas temporais ou territoriais
    nao atendem ao contrato. Nao transforma estimativas em probabilidades.
    """
    verified = predict_guarded(current, reference, ledger, previous=previous)
    answer = dict(verified, model_version=MODEL_VERSION, coverage_threshold=COVERAGE_THRESHOLD)
    if verified["status"] != "ESTIMATED":
        return answer
    try:
        a = current["votes_a"]
        b = current["votes_b"]
        counted = current["electorate_counted"]
        remaining = current["electorate_total"] - counted
        by_scope = {str(r["scope"]): r for r in ledger
                    if r["timestamp"] == current["timestamp"]
                    and r["available_at"] == current["timestamp"]}
        # A validacao V4.1 ja exigiu todos os estratos e conciliou votos.
        # Rejeitar duplicacoes contraditorias tambem ja e responsabilidade V4.1.
        if len(by_scope) != len(reference):
            raise ValueError("ledger nao canonico")
        ordered = [by_scope[k] for k in sorted(reference)]
        matched = [sum(r["matched_first_" + k] for r in ordered) for k in ("a", "b")]
        if min(matched) <= 0:
            raise ValueError("denominador global zero")
        first_total = sum(reference[k]["votes_a"] + reference[k]["votes_b"] for k in reference)
        if first_total <= 0:
            raise ValueError("referencia sem votos")
        coverage = sum(matched) / first_total
        if not 0 <= coverage <= 1:
            raise ValueError("cobertura fora do intervalo fisico")
        alpha = min(1., max(0., coverage / COVERAGE_THRESHOLD))
        global_ratio = (a / matched[0], b / matched[1])
        common = (a + b) / sum(matched)
        unseen = [0., 0.]
        zero_scopes = []
        zero_votes_first = 0
        for scope in sorted(reference):
            row = by_scope[scope]
            ref = reference[scope]
            zero_both = row["matched_first_a"] + row["matched_first_b"] == 0
            if zero_both:
                zero_scopes.append(scope)
                zero_votes_first += ref["votes_a"] + ref["votes_b"]
            for i, k in enumerate(("a", "b")):
                m = row["matched_first_" + k]
                rate = row["votes_" + k] / m if m else global_ratio[i]
                if zero_both:
                    rate = alpha * global_ratio[i] + (1 - alpha) * common
                unseen[i] += (ref["votes_" + k] - m) * rate
        if not all(math.isfinite(x) and x >= 0 for x in unseen):
            raise ValueError("extrapolacao invalida")
        if sum(unseen) > remaining:
            factor = remaining / sum(unseen)
            unseen = [x * factor for x in unseen]
        den = a + b + sum(unseen)
        if den <= 0:
            raise ValueError("denominador de estimativa zero")
        estimate = (a + unseen[0]) / den
        if not math.isfinite(estimate) or not (0 <= estimate <= 1):
            raise ValueError("estimativa invalida")
        if estimate < answer["lower_a"] - 1e-12 or estimate > answer["upper_a"] + 1e-12:
            raise ValueError("fora dos limites fisicos")
        return dict(answer, estimate_a=estimate, model_version=MODEL_VERSION,
                    coverage_first_valid=coverage, shrinkage_alpha=alpha,
                    zero_sample_scopes=zero_scopes,
                    zero_sample_first_vote_share=zero_votes_first / first_total,
                    estimated_unseen_a=unseen[0], estimated_unseen_b=unseen[1],
                    comparison_v4_estimate_a=verified["estimate_a"],
                    probability=None)
    except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError):
        return dict(answer, estimate_a=None, status="ABSTAIN",
                    reason="v6_invalid_computation", clear_prior_forecast=True,
                    probability=None, model_version=MODEL_VERSION)
