"""V4: razões por candidato sobre o MESMO conjunto de seções entre turnos.
Sem parâmetros ajustados. Ledger completo e sincronizado é obrigatório.
Limites determinísticos são condicionais à autenticidade de A/B/R e ausência
 de revisão futura; não são probabilidades nem intervalos de confiança.
"""
from datetime import datetime
import math

def _time(x):
    t = datetime.fromisoformat(x.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('timezone obrigatorio')
    return t

def _count(x):
    if isinstance(x, bool) or not isinstance(x, int) or x < 0:
        raise ValueError('inteiro nao negativo obrigatorio')
    return x

def deterministic_bounds(a, b, remaining):
    a, b, remaining = map(_count, (a, b, remaining))
    denominator = a + b + remaining
    if not denominator:
        return {'lower_a': 0., 'upper_a': 1., 'conditional_winner': None}
    return {'lower_a': a / denominator,
            'upper_a': (a + remaining) / denominator,
            'conditional_winner': 'a' if a > b + remaining else ('b' if b > a + remaining else None)}

def predict(current, reference, ledger):
    """current: timestamp/available_at, votes_a/b, electorate_total/counted.
    reference[scope]: votes_a/b, available_at (primeiro turno inteiro).
    ledger: scope, timestamp/available_at iguais ao cutoff atual; votes_a/b
    (segundo turno observado), matched_first_a/b (primeiro turno das MESMAS
    seções observadas). Exige um registro por estrato e totais conciliados.
    """
    now = _time(current['timestamp'])
    if _time(current['available_at']) > now:
        raise ValueError('nacional indisponivel')
    a, b = _count(current['votes_a']), _count(current['votes_b'])
    total, counted = _count(current['electorate_total']), _count(current['electorate_counted'])
    if counted > total or a + b > counted:
        raise ValueError('eleitorado ou votos inconsistentes')
    remaining = total - counted
    bounds = deterministic_bounds(a, b, remaining)
    result = {**bounds, 'estimate_a': None, 'remaining_electorate': remaining,
              'probability': None, 'status': 'ABSTAIN', 'reason': None,
              'bounds_conditional_on_no_future_revisions': True}
    if remaining == 0 and a + b:
        return {**result, 'estimate_a': a / (a + b), 'status': 'CLOSED', 'reason': None}
    if not a + b:
        return {**result, 'reason': 'no_observed_valid_votes'}
    if not reference:
        return {**result, 'reason': 'missing_reference'}
    refs = {}
    for scope, r in sorted(reference.items()):
        if _time(r['available_at']) > now:
            return {**result, 'reason': 'reference_unavailable'}
        refs[scope] = (_count(r['votes_a']), _count(r['votes_b']))
    latest = {}
    for row in ledger:
        scope = row['scope']
        if scope not in refs:
            return {**result, 'reason': 'unknown_scope'}
        generated, available = _time(row['timestamp']), _time(row['available_at'])
        if available < generated:
            raise ValueError('disponibilidade anterior a geracao')
        if generated > now or available > now:
            continue
        values = tuple(_count(row[k]) for k in ('votes_a', 'votes_b', 'matched_first_a', 'matched_first_b'))
        key = generated, available
        if scope in latest and key == latest[scope][0] and values != latest[scope][1]:
            return {**result, 'reason': 'conflicting_ledger'}
        if scope not in latest or key > latest[scope][0]:
            latest[scope] = (key, values)
    if set(latest) != set(refs):
        return {**result, 'reason': 'incomplete_ledger'}
    if any(key[0] != now or key[1] != now for key, v in latest.values()):
        return {**result, 'reason': 'unsynchronized_ledger'}
    if sum(v[1][0] for v in latest.values()) != a or sum(v[1][1] for v in latest.values()) != b:
        return {**result, 'reason': 'national_territorial_mismatch'}
    if any(v[2] > refs[u][0] or v[3] > refs[u][1] for u, (_, v) in latest.items()):
        return {**result, 'reason': 'matched_reference_exceeds_total'}
    observed_first = [sum(v[1][2+j] for v in latest.values()) for j in range(2)]
    if not all(observed_first):
        return {**result, 'reason': 'global_ratio_unidentifiable'}
    global_ratio = [a / observed_first[0], b / observed_first[1]]
    unseen = [0., 0.]
    for scope in sorted(refs):
        _, values = latest[scope]
        for j in range(2):
            local_ratio = values[j] / values[2+j] if values[2+j] else global_ratio[j]
            unseen[j] += (refs[scope][j] - values[2+j]) * local_ratio
    # Número físico de votos ainda possíveis limita a extrapolação.
    if sum(unseen) > remaining:
        scale = remaining / sum(unseen)
        unseen = [v * scale for v in unseen]
    estimate = (a + unseen[0]) / (a + b + sum(unseen))
    if not math.isfinite(estimate) or estimate < bounds['lower_a'] - 1e-12 or estimate > bounds['upper_a'] + 1e-12:
        raise ValueError('estimativa fora do limite fisico')
    return {**result, 'estimate_a': estimate, 'status': 'ESTIMATED', 'reason': None,
            'estimated_unseen_a': unseen[0], 'estimated_unseen_b': unseen[1]}
