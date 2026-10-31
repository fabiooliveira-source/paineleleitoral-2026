// Testes Node para motor V7 experimental, sem rede nem TSE live.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const V7 = require('../v7-engine.js');

const fixture = () => ({
  current: {
    timestamp:'2026-10-31T20:00:00-03:00',
    available_at:'2026-10-31T19:59:50-03:00',
    votes_a:170, votes_b:150,
    electorate_total:2000, electorate_counted:400
  },
  reference:{
    '01':{votes_a:450,votes_b:550,available_at:'2026-10-01T00:00:00-03:00'},
    '02':{votes_a:350,votes_b:650,available_at:'2026-10-01T00:00:00-03:00'}
  },
  ledger:[
    {scope:'01',timestamp:'2026-10-31T19:59:00-03:00',available_at:'2026-10-31T19:59:00-03:00',votes_a:170,votes_b:150,matched_first_a:100,matched_first_b:100},
    {scope:'02',timestamp:'2026-10-31T19:59:00-03:00',available_at:'2026-10-31T19:59:00-03:00',votes_a:0,votes_b:0,matched_first_a:0,matched_first_b:0}
  ]
});
let assertions = 0;
function check(ok, message) {
  assert.ok(ok, message); assertions++;
}
function rejected(changer, label) {
  const f = fixture();
  changer(f);
  const r = V7.predict(f);
  check(r.status === 'ABSTAIN', label + ': expected fail-closed');
  check(r.estimate_a === null && r.probability === null && r.clear_prior_forecast, label + ': not cleared');
}
const base = V7.predict(fixture());
check(base.status === 'ESTIMATED', 'valid synthetic fixture estimated');
check(Math.abs(base.estimate_a - 0.4375381151273609) < 1e-12, 'matches independently calculated Python reference including remaining-electorate cap');
check(base.provisional_leader === 'b', 'provisional leader B');
check(base.winner_call === null, 'no unearned definitive call');
check(base.probability === null && !base.is_certified, 'no confidence fabrication');
check(base.lower_a <= base.estimate_a && base.upper_a >= base.estimate_a, 'physical bounds');
check(base.weak_zone_count === 1, 'missing zone counted');
check(Math.abs(base.first_round_coverage - 0.1) < 1e-12, 'matched first round coverage');
const reversed = fixture();
reversed.ledger.reverse();
check(Math.abs(V7.predict(reversed).estimate_a - base.estimate_a) < 1e-12, 'order-invariant');
rejected(f => { f.current.available_at = '2026-11-01T20:00:00-03:00'; }, 'future national data');
rejected(f => { f.ledger[1].available_at = '2026-11-01T20:00:00-03:00'; }, 'future zone');
rejected(f => { f.reference['02'].available_at = '2026-11-01T00:00:00-03:00'; }, 'future reference');
rejected(f => { f.current.votes_a++; }, 'national vs ledger mismatch');
rejected(f => { f.ledger[1].votes_a++; }, 'zone vs national mismatch');
rejected(f => { f.ledger[1].scope = '01'; }, 'duplicate zone');
rejected(f => { f.ledger.pop(); }, 'missing zone');
rejected(f => { f.ledger[0].matched_first_a = 451; }, 'matched exceeds reference');
rejected(f => { f.current.electorate_counted = 250; }, 'observed valid more than counted electors');
rejected(f => { f.current.votes_b = -1; }, 'negative votes');
rejected(f => { f.current.votes_a = '170'; }, 'must not accept string votes');
rejected(f => { f.current.timestamp = '2026-10-31T20:00:00'; }, 'timezone required');
rejected(f => { f.ledger[0].generated_at = '2026-11-01T00:00:00-03:00'; }, 'future generation');
rejected(f => { f.previous = {
 timestamp:'2026-10-31T19:59:00-03:00',available_at:'2026-10-31T19:59:00-03:00',
 votes_a:171,votes_b:150,electorate_total:2000,electorate_counted:400
}; }, 'revision blocked');
const end = fixture();
end.current.electorate_counted = 2000;
const closed = V7.predict(end);
check(closed.status === 'CLOSED', 'closed by electorate even with hypothetical section lag');
check(closed.estimate_a === 170/320, 'closed uses observed share only');
check(closed.probability === null, 'closed not converted to probability');
const locked = fixture();
locked.current.votes_a = 400;
locked.current.votes_b = 50;
locked.current.electorate_total = 500;
locked.current.electorate_counted = 450;
locked.ledger[0].votes_a = 400;
locked.ledger[0].votes_b = 50;
const called = V7.predict(locked);
check(called.status === 'ESTIMATED', 'mathematical lock input valid');
check(called.winner_call === 'a', 'winner only if observed lead exceeds remaining electorate');
const html = fs.readFileSync(path.join(__dirname, '..', 'validacao-v7.html'),'utf8');
const landing = fs.readFileSync(path.join(__dirname,'..','acompanhar.html'),'utf8');
const main = fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
check(html.includes('v7-engine.js') && html.includes('validacao-v7-ui.js'), 'lab JS wired');
check(landing.includes('validacao-v7.html'), 'landing links lab');
check(main.includes('validacao-v7.html'), 'monitor links lab');
check(html.includes('NÃO CERTIFICADO') && html.includes('7 / 15'), 'honest historical label');
console.log('V7 engine and panel links: '+assertions+' assertions PASS.');
