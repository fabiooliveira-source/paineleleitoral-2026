"""Audit-v3: swing atenuado; coeficiente selecionado apenas em 2022.
Nao reajustar pelo teste externo 2018. Frações em 0..1; tempos com timezone.
Entrada de cobertura deve vir da linha contemporânea; não usar snapshot final.
"""
import math
from datetime import datetime

MAX_AGE_SECONDS = 300
AGE_DECAY_SECONDS = 600
SWING_SHRINKAGE = 0.25

def _time(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('timestamp sem timezone')
    return t

def _count(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError('contagem deve ser inteiro nao negativo')
    return value

def predict(current, first_round, territorial=()):
    """Não aceita alvo final. first_round inclui available_at anterior ao instante.

    current: timestamp, available_at, votes_a/b, counted_sections, total_sections.
    first_round: scope -> votes_a/b, valid_votes, available_at.
    territorial: registros com scope, timestamp, available_at, votes_a/b.
    timestamp é geração; available_at é disponibilidade ao consumidor.
    Empates conflitantes de timestamps são rejeitados, sem escolher por ordem.
    """
    now = _time(current['timestamp'])
    if _time(current['available_at']) > now:
        raise ValueError('registro nacional ainda indisponivel')
    a, b = _count(current['votes_a']), _count(current['votes_b'])
    sections, total = _count(current['counted_sections']), _count(current['total_sections'])
    if total == 0 or sections > total or a + b == 0:
        raise ValueError('cobertura ou votos invalidos')
    if not first_round:
        raise ValueError('historico anterior obrigatorio')
    first = {}
    for scope, row in sorted(first_round.items()):
        if _time(row['available_at']) > now:
            raise ValueError('historico indisponivel no instante')
        aa, bb, valid = (_count(row[k]) for k in ('votes_a', 'votes_b', 'valid_votes'))
        if not aa + bb or valid < aa + bb:
            raise ValueError('historico inconsistente')
        first[scope] = {'share': aa/(aa+bb), 'weight': valid}
    latest = {}
    for row in territorial:
        scope = row['scope']
        if scope not in first:
            raise ValueError('territorio sem historico')
        generated, available = _time(row['timestamp']), _time(row['available_at'])
        if available < generated:
            raise ValueError('disponibilidade anterior a geracao')
        if generated > now or available > now:
            continue
        aa, bb = _count(row['votes_a']), _count(row['votes_b'])
        key = generated, available
        prior = latest.get(scope)
        if prior and key == prior[0] and (aa, bb) != prior[1]:
            raise ValueError('snapshots conflitantes no mesmo instante')
        if prior is None or key > prior[0]:
            latest[scope] = (key, (aa, bb))
    numerator = denominator = 0.0
    fresh = 0
    for scope in sorted(latest):
        (generated, _), (aa, bb) = latest[scope]
        age = (now-generated).total_seconds()
        if age > MAX_AGE_SECONDS or aa+bb == 0:
            continue
        weight = min(aa+bb, first[scope]['weight']) * max(0, 1-age/AGE_DECAY_SECONDS)
        numerator += weight * (aa/(aa+bb)-first[scope]['share'])
        denominator += weight
        fresh += 1
    raw_swing = numerator/denominator if denominator else 0.0
    swing = SWING_SHRINKAGE * raw_swing
    weight_total = sum(x['weight'] for x in first.values())
    unseen = sum(x['weight']/weight_total * max(0, min(1, x['share']+swing)) for x in first.values())
    coverage = sections/total
    forecast = coverage*a/(a+b) + (1-coverage)*unseen
    if not math.isfinite(forecast) or not 0 <= forecast <= 1:
        raise ValueError('previsao invalida')
    return {'forecast_a': forecast, 'baseline_a': a/(a+b), 'coverage': coverage,
            'swing': swing, 'raw_swing': raw_swing, 'fresh_territories': fresh,
            'mode': 'territorial' if fresh else 'degraded_no_fresh_territory'}
