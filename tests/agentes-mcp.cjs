'use strict';
/* Contrato das ferramentas do agente, protocolo MCP e validador de saída. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { executar, listar } = require('../agentes/ferramentas.cjs');
const { validarResposta } = require('../agentes/validador.cjs');

let n = 0;
const ck = (ok, msg) => { assert.ok(ok, msg); n++; };

// 1. Registro: nomes únicos, esquemas de objeto, avisos presentes.
const tools = listar();
ck(tools.length === 9, '9 ferramentas');
ck(new Set(tools.map(t => t.name)).size === tools.length, 'nomes únicos');
for (const t of tools) ck(t.inputSchema.type === 'object' && /Aviso:/.test(t.description), 'esquema e aviso: ' + t.name);

// 2. Dados observados reconciliados com totais conferidos.
const br = executar('totais_territorio', { territorio: { nivel: 'BR' } });
ck(br.status === 'OK' && br.saida.localidades === 5757, 'Brasil com 5.757 localidades');
ck(br.saida.totais.lula_2t === 64256232 && br.saida.totais.flavio_2t === 59826041, 'totais 2º turno conferidos');
ck(br.saida.vantagem_lula_menos_flavio_2t === 64256232 - 59826041, 'vantagem 2º turno');
ck(/^[0-9a-f]{64}$/.test(br.saida.fonte_sha256) && /^[0-9a-f]{64}$/.test(br.entrada_sha256), 'hashes de auditoria');
const ufs = [...new Set(require('node:zlib').gunzipSync(require('node:fs').readFileSync(path.join(__dirname, '../dados/2026/municipios.json.gz'))).toString().match(/"uf":"[A-Z]{2}"/g))].map(s => s.slice(6, 8));
const somaUF = ufs.reduce((a, uf) => a + executar('totais_territorio', { territorio: { nivel: 'UF', uf } }).saida.totais.lula_2t, 0);
ck(ufs.length === 28 && somaUF === 64256232, '27 UFs + ZZ somam o Brasil');
const mun = executar('totais_territorio', { territorio: { nivel: 'MUN', uf: 'ac', municipio: 'bujari' } });
ck(mun.status === 'OK' && mun.saida.totais.lula_2t === 2454, 'município por nome sem acento/caixa');
ck(executar('totais_territorio', { territorio: { nivel: 'MUN', uf: 'AC', codigo_municipio_tse: '1007' } }).saida.totais.lula_2t === 2454, 'código com zero à esquerda');

// 3. Falha fechada: tudo que é inválido vira ABSTAIN, nunca exceção.
for (const [nome, ent] of [
  ['totais_territorio', { territorio: { nivel: 'MUN', uf: 'AC', municipio: 'Inexistente' } }],
  ['totais_territorio', { territorio: { nivel: 'XX' } }],
  ['totais_territorio', {}],
  ['decisao_robusta', { observedA: 51000, observedB: 49000, remainingElectors: 10000, scenarioLow: 0.1, scenarioHigh: 0.6 }],
  ['v7_checkpoint', {}],
  ['limites_transferencia', {}],
  ['ferramenta_inexistente', {}],
  ['barganha_nash', null]
]) {
  const e = executar(nome, ent);
  ck(e.status === 'ABSTAIN' && e.saida.reason && /ABSTAIN/.test(e.regra), 'ABSTAIN: ' + nome);
}

// 4. Repasse fiel dos motores (nada reimplementado).
const tj = executar('decisao_robusta', { observedA: 100, observedB: 50, remainingElectors: 20, scenarioLow: 100 / 170, scenarioHigh: 120 / 170 });
ck(tj.saida.action === 'CALL_A' && tj.saida.mathematical_winner === 'A' && tj.saida.probability === null, 'minimax repassado');
const sh = executar('valor_shapley', { groups: ['A', 'B'], coalitionValues: [0, 1, 1, 3] });
ck(sh.status === 'OK' && sh.saida.contributions.every(c => c.marginal_value === 1.5), 'Shapley simétrico');
const lim = executar('limites_transferencia', { territorio: { nivel: 'UF', uf: 'AC' } });
ck(lim.status === 'OK' && lim.saida.municipios_validados === 22 && !('sections' in lim.saida), 'unidade municipal rotulada');
ck(lim.avisos_obrigatorios.some(a => /MUNICÍPIO/.test(a)), 'aviso de granularidade');
const rb = executar('rateio_buildup_territorio', { territorio: { nivel: 'UF', uf: 'DF' } });
ck(rb.status === 'OK' && rb.saida.rest === 0, 'rateio reconciliado');

// 5. Validador de saída.
const env = [br];
ck(validarResposta('Lula teve 64.256.232 votos no 2º turno; vantagem de 4.430.191.', env).ok, 'números rastreáveis aceitos');
ck(!validarResposta('Lula teve 64.300.000 votos.', env).ok, 'número inventado bloqueado');
ck(!validarResposta('Lula tem 87% de chance de vitória.', env).ok, 'probabilidade bloqueada');
ck(!validarResposta('A probabilidade de vencer é alta.', env).ok, 'probabilidade textual bloqueada');
const pct = (100 * br.saida.share_lula_validos_2t).toFixed(2).replace('.', ',');
ck(validarResposta('Lula obteve ' + pct + '% dos válidos em 2026.', env).ok, 'percentual derivado aceito');
const ab = executar('v7_checkpoint', {});
ck(!validarResposta('A V7 indica liderança de Lula.', [ab]).ok, 'ABSTAIN ignorado bloqueado');
ck(validarResposta('A V7 se absteve: faltam seções pareadas.', [ab]).ok, 'ABSTAIN reconhecido');
ck(!validarResposta('Eleitores migraram de Flávio para Lula.', [rb]).ok, 'migração individual bloqueada');

// 6. Protocolo MCP via stdio.
const srv = spawn(process.execPath, [path.join(__dirname, '../agentes/mcp-server.cjs')], { stdio: ['pipe', 'pipe', 'inherit'] });
const pend = new Map(); let buf = '';
srv.stdout.on('data', d => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const m = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1); pend.get(m.id)?.(m); pend.delete(m.id); } });
let id = 0;
const rpc = (method, params) => new Promise(r => { const k = ++id; pend.set(k, r); srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: k, method, params }) + '\n'); });
(async () => {
  const init = await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'teste', version: '0' } });
  ck(init.result.protocolVersion === '2025-06-18' && init.result.capabilities.tools && /ABSTAIN/.test(init.result.instructions), 'initialize');
  srv.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  const lst = await rpc('tools/list', {});
  ck(lst.result.tools.length === 9, 'tools/list');
  const call = await rpc('tools/call', { name: 'totais_territorio', arguments: { territorio: { nivel: 'UF', uf: 'DF' } } });
  ck(call.result.isError === false && call.result.structuredContent.status === 'OK' && JSON.parse(call.result.content[0].text).ferramenta === 'totais_territorio', 'tools/call');
  const bad = await rpc('metodo/inexistente', {});
  ck(bad.error && bad.error.code === -32601, 'método desconhecido');
  srv.stdin.end();
  console.log(n + ' agent/MCP assertions PASS');
})().catch(e => { console.error(e); process.exit(1); });
