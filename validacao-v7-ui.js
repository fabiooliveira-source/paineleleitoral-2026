/* Interface exclusivamente laboratorial para V7. Nenhum acesso automático ao TSE.
 * Não associa arquivos sintéticos ou do usuário ao resultado oficial.
 */
(function() {
  'use strict';
  const byId = id => document.getElementById(id);
  const out = byId('v7Result');
  const pct = n => (n * 100).toLocaleString('pt-BR', {
    minimumFractionDigits: 3, maximumFractionDigits: 3
  }) + '%';
  const sample = {
    current: {
      timestamp:'2026-10-31T20:00:00-03:00',
      available_at:'2026-10-31T19:59:50-03:00',
      votes_a:170, votes_b:150,
      electorate_total:2000, electorate_counted:400
    },
    reference: {
      '01':{votes_a:450,votes_b:550,available_at:'2026-10-01T00:00:00-03:00'},
      '02':{votes_a:350,votes_b:650,available_at:'2026-10-01T00:00:00-03:00'}
    },
    ledger:[
      {scope:'01',timestamp:'2026-10-31T19:59:00-03:00',available_at:'2026-10-31T19:59:00-03:00',votes_a:170,votes_b:150,matched_first_a:100,matched_first_b:100},
      {scope:'02',timestamp:'2026-10-31T19:59:00-03:00',available_at:'2026-10-31T19:59:00-03:00',votes_a:0,votes_b:0,matched_first_a:0,matched_first_b:0}
    ]
  };
  function present(payload, label) {
    if (!window.V7Electoral || typeof window.V7Electoral.predict !== 'function') {
      out.textContent = 'Motor V7 não carregado. A projeção permanece bloqueada.';
      return;
    }
    const res = window.V7Electoral.predict(payload);
    if (res.status === 'ABSTAIN') {
      out.textContent = label + '\n\n⛔ SEM PROJEÇÃO (ABSTAIN)\nMotivo: ' +
        String(res.reason || 'entrada inválida') +
        '\nUma projeção anterior deve ser desconsiderada.\nConfiança de vitória: NÃO CALIBRADA.';
      return;
    }
    const leader = res.provisional_leader === 'a' ? 'Candidato A' :
      res.provisional_leader === 'b' ? 'Candidato B' : 'Empate projetado';
    const determined = res.winner_call === 'a' ? 'Candidato A' :
      res.winner_call === 'b' ? 'Candidato B' : 'NÃO DETERMINADO';
    const covered = res.first_round_coverage;
    out.textContent = label + '\n\n' +
      'Modelo: V7 experimental • ' + res.status + '\n' +
      'Proporção estimada A: ' + pct(res.estimate_a) + '\n' +
      'Proporção estimada B: ' + pct(1 - res.estimate_a) + '\n' +
      'Liderança PROVISÓRIA: ' + leader + '\n' +
      'Vencedor matematicamente determinado, sob ausência de revisões: ' + determined + '\n' +
      'Limites físicos A: [' + pct(res.lower_a) + '; ' + pct(res.upper_a) + ']\n' +
      'Cobertura pareada de referência: ' + pct(covered) + '\n' +
      'Zonas fracamente identificadas: ' + res.weak_zone_count + '\n\n' +
      'Probabilidade calibrada de vitória: INDISPONÍVEL.\n' +
      'Fonte/horários de divulgação pública: NÃO AUTENTICADOS NESTE LABORATÓRIO.\n' +
      'Resultado oficial da eleição 2026: NÃO ALTERADO.';
  }
  byId('runSynthetic').addEventListener('click', () =>
    present(sample, 'EXEMPLO SINTÉTICO • sem dados eleitorais reais'));
  byId('clearV7').addEventListener('click', () => {
    byId('v7File').value = '';
    out.textContent = 'Aguardando um checkpoint JSON com seções pareadas. Nenhuma projeção gerada.';
  });
  byId('v7File').addEventListener('change', async event => {
    const file = event.currentTarget.files && event.currentTarget.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      out.textContent = 'Arquivo acima de 5 MB. Projeção bloqueada.';
      return;
    }
    try {
      const payload = JSON.parse(await file.text());
      present(payload, 'JSON LOCAL • não autenticado como publicação pública do TSE');
    } catch (err) {
      out.textContent = '⛔ Arquivo JSON inválido. Projeção bloqueada: ' + (err && err.message || err);
    }
  });
})();
