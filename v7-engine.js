/* V7 experimental — adaptação JS da fórmula Python congelada (2026-10-31).
 * A V7 NÃO está certificada para a eleição presidencial de 2026.
 * Este módulo exige dados por zona e seções pareadas 1º/2º turno.
 * NÃO é conectado automaticamente ao EA20 municipal, que não os fornece.
 * Uso: V7Electoral.predict({current, reference, ledger, previous?}).
 * Nunca retorna uma probabilidade de vitória.
 */
(function(root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.V7Electoral = api;
})(typeof globalThis === 'object' ? globalThis : this, function() {
  'use strict';
  const MODEL = 'V7-EXPERIMENTAL-LOGODDS-VOLUME-2026-10-31';
  const PRIOR_VALID = 1000;
  const PSEUDOCOUNT = 0.5;
  const MAX_SWING = Math.log(4);
  const EPS = 1e-10;

  function abstain(reason) {
    return {
      model_version: MODEL, status: 'ABSTAIN', reason,
      estimate_a: null, provisional_leader: null, winner_call: null,
      probability: null, clear_prior_forecast: true,
      is_certified: false, public_timing_authenticated: false
    };
  }
  function integer(value, label) {
    if (!Number.isSafeInteger(value) || value < 0)
      throw new Error('Contagem inválida: ' + label);
    return value;
  }
  function date(value, label) {
    if (typeof value !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value))
      throw new Error('Horário ISO com fuso obrigatório: ' + label);
    const t = Date.parse(value);
    if (!Number.isFinite(t)) throw new Error('Horário inválido: ' + label);
    return t;
  }
  function timeline(record, now, label) {
    if (!record || typeof record !== 'object' || Array.isArray(record))
      throw new Error('Registro inválido: ' + label);
    const cutoff = date(record.timestamp, label + '.timestamp');
    const avail = date(record.available_at, label + '.available_at');
    if (cutoff > now || avail > cutoff)
      throw new Error('Informação futura/inacessível em ' + label);
    if (record.generated_at != null && date(record.generated_at, label + '.generated_at') > avail)
      throw new Error('Recebimento anterior à geração em ' + label);
    return cutoff;
  }
  function logRatio(a, b) {
    return Math.log((a + PSEUDOCOUNT) / (b + PSEUDOCOUNT));
  }
  function sigmoid(x) {
    if (x >= 0) return 1 / (1 + Math.exp(-x));
    const e = Math.exp(x);
    return e / (1 + e);
  }
  function predict(input) {
    try {
      if (!input || typeof input !== 'object' || Array.isArray(input))
        return abstain('Contrato de entrada ausente');
      const current = input.current, reference = input.reference, ledger = input.ledger;
      if (!current || !reference || typeof reference !== 'object' ||
          Array.isArray(reference) || !Array.isArray(ledger) || !ledger.length)
        return abstain('Informe agregado, referências e ledger territorial pareado');
      const now = date(current.timestamp, 'current.timestamp');
      timeline(current, now, 'current');
      const a = integer(current.votes_a, 'current.votes_a');
      const b = integer(current.votes_b, 'current.votes_b');
      const total = integer(current.electorate_total, 'current.electorate_total');
      const counted = integer(current.electorate_counted, 'current.electorate_counted');
      if (counted > total || a + b > counted ||
          !Number.isSafeInteger(a + b))
        throw new Error('Agregado incompatível com eleitorado contabilizado');
      if (input.previous) {
        const old = input.previous;
        const then = timeline(old, now, 'previous');
        if (then > now) throw new Error('Regressão cronológica');
        for (const k of ['votes_a','votes_b','electorate_total','electorate_counted'])
          integer(old[k], 'previous.' + k);
        if (old.electorate_total !== total ||
            old.votes_a > a || old.votes_b > b ||
            old.electorate_counted > counted)
          throw new Error('Revisão de votos/eleitorado: retirar projeção anterior');
        if (then === now && (old.votes_a !== a || old.votes_b !== b ||
            old.electorate_counted !== counted))
          throw new Error('Snapshots conflitantes com o mesmo horário');
      }
      const scopes = Object.keys(reference);
      if (!scopes.length || scopes.length !== ledger.length)
        throw new Error('Cobertura de todas as zonas não demonstrada');
      let allFirst = 0;
      for (const scope of scopes) {
        const ref = reference[scope];
        if (!ref || typeof ref !== 'object' || Array.isArray(ref))
          throw new Error('Referência inválida para zona ' + scope);
        const ava = date(ref.available_at, 'reference[' + scope + '].available_at');
        if (ava > now ||
            (ref.generated_at && date(ref.generated_at, 'reference.generated_at') > ava))
          throw new Error('Referência do 1º turno indisponível no corte');
        const ra = integer(ref.votes_a, 'reference.a');
        const rb = integer(ref.votes_b, 'reference.b');
        allFirst += ra + rb;
        if (!Number.isSafeInteger(allFirst))
          throw new Error('Soma histórica imprecisa');
      }
      if (!allFirst) throw new Error('Referência de finalistas vazia');
      const byScope = new Map();
      let sumA = 0, sumB = 0, matchedA = 0, matchedB = 0;
      for (const row of ledger) {
        if (!row || typeof row !== 'object' || row.scope == null)
          throw new Error('Zona ausente no ledger');
        const scope = String(row.scope);
        if (byScope.has(scope) || !Object.prototype.hasOwnProperty.call(reference, scope))
          throw new Error('Zona duplicada ou fora da referência: ' + scope);
        timeline(row, now, 'ledger[' + scope + ']');
        const ra = integer(row.votes_a, 'ledger.a');
        const rb = integer(row.votes_b, 'ledger.b');
        const ma = integer(row.matched_first_a, 'ledger.matched_first_a');
        const mb = integer(row.matched_first_b, 'ledger.matched_first_b');
        if (ma > reference[scope].votes_a || mb > reference[scope].votes_b)
          throw new Error('Pareamento excede 1º turno na zona ' + scope);
        byScope.set(scope, row);
        sumA += ra; sumB += rb; matchedA += ma; matchedB += mb;
      }
      if (!Number.isSafeInteger(sumA + sumB) ||
          !Number.isSafeInteger(matchedA + matchedB) ||
          sumA !== a || sumB !== b || byScope.size !== scopes.length)
        throw new Error('Ledger por zona não reconcilia com agregado');
      if (a + b === 0 || matchedA === 0 || matchedB === 0)
        throw new Error('Insuficiência de amostra pareada dos dois finalistas');
      const remaining = total - counted;
      const observed = a + b;
      const lower = a / (observed + remaining);
      const upper = (a + remaining) / (observed + remaining);
      const winnerCall = a > b + remaining ? 'a' : b > a + remaining ? 'b' : null;
      if (remaining === 0) {
        const exact = a / observed;
        return {
          model_version: MODEL, status:'CLOSED', reason:null,
          estimate_a:exact, lower_a:exact, upper_a:exact,
          provisional_leader:exact > .5 ? 'a' : exact < .5 ? 'b' : null,
          winner_call:winnerCall, probability:null, is_certified:false,
          clear_prior_forecast:false, public_timing_authenticated:false,
          first_round_coverage:(matchedA + matchedB) / allFirst,
          expected_valid_remaining:0, weak_zone_count:0
        };
      }
      const swing = logRatio(a, b) - logRatio(matchedA, matchedB);
      const volume = (a + b) / (matchedA + matchedB);
      if (!Number.isFinite(volume) || volume <= 0)
        throw new Error('Taxa de volume não identificável');
      let unseenA = 0, unseenB = 0, emptyFirst = 0, weakZones = 0, support = 0;
      for (const scope of scopes.sort()) {
        const ref = reference[scope], row = byScope.get(scope);
        const leftA = ref.votes_a - row.matched_first_a;
        const leftB = ref.votes_b - row.matched_first_b;
        const left = leftA + leftB;
        if (!left) continue;
        const valid = row.votes_a + row.votes_b;
        const weak = row.matched_first_a === 0 ||
                     row.matched_first_b === 0 || valid === 0;
        let localWeight = 0, localSwing = swing;
        if (!weak) {
          localWeight = valid / (valid + PRIOR_VALID);
          localSwing = logRatio(row.votes_a, row.votes_b) -
                       logRatio(row.matched_first_a, row.matched_first_b);
        }
        const deviation = Math.max(-MAX_SWING, Math.min(MAX_SWING, localSwing - swing));
        const posterior = swing + localWeight * deviation;
        const share = sigmoid(logRatio(leftA, leftB) + posterior);
        const amount = left * volume;
        unseenA += amount * share;
        unseenB += amount * (1 - share);
        support += localWeight;
        if (weak) { weakZones++; emptyFirst += left; }
      }
      const estimatedValid = unseenA + unseenB;
      const cap = estimatedValid > remaining && estimatedValid > 0 ?
                  remaining / estimatedValid : 1;
      unseenA *= cap; unseenB *= cap;
      const forecastValid = observed + unseenA + unseenB;
      if (!(forecastValid > 0)) throw new Error('Votos válidos inexistentes');
      const estimate = (a + unseenA) / forecastValid;
      if (!Number.isFinite(estimate) || estimate < lower - EPS ||
          estimate > upper + EPS)
        throw new Error('Estimativa fora dos limites físicos');
      return {
        model_version:MODEL, status:'ESTIMATED', reason:null,
        estimate_a:estimate, lower_a:lower, upper_a:upper,
        provisional_leader:estimate>.5?'a':estimate<.5?'b':null,
        winner_call:winnerCall, probability:null, is_certified:false,
        clear_prior_forecast:false, public_timing_authenticated:false,
        first_round_coverage:(matchedA+matchedB)/allFirst,
        weak_zone_reference_fraction:emptyFirst/allFirst,
        weak_zone_count:weakZones, effective_zones:support,
        expected_valid_remaining:unseenA+unseenB,
        volume_conversion:volume, volume_scale:cap
      };
    } catch (error) {
      return abstain(error && error.message ? error.message : 'Dados incompatíveis');
    }
  }
  return Object.freeze({ model: MODEL, predict });
});
