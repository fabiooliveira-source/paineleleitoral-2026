#!/usr/bin/env node
'use strict';
/* Servidor MCP (stdio, JSON-RPC 2.0 delimitado por linha) sem dependências.
 * Expõe os motores do painel como ferramentas para Claude Code, Claude Desktop
 * ou qualquer cliente MCP. Opcional: AGENTE_LOG=<arquivo.jsonl> registra cada
 * chamada (entrada, saída, horário) para auditoria e reprodutibilidade.
 */
const fs = require('node:fs');
const readline = require('node:readline');
const { executar, listar } = require('./ferramentas.cjs');

const VERSOES = ['2025-06-18', '2025-03-26', '2024-11-05'];
const INSTRUCOES = fs.readFileSync(require('node:path').join(__dirname, 'prompt-sistema.md'), 'utf8');

const enviar = m => process.stdout.write(JSON.stringify(m) + '\n');
const erro = (id, code, message) => enviar({ jsonrpc: '2.0', id, error: { code, message } });

function registrar(envelope, entrada) {
  const arq = process.env.AGENTE_LOG;
  if (!arq) return;
  try { fs.appendFileSync(arq, JSON.stringify({ ...envelope, entrada }) + '\n'); }
  catch (e) { process.stderr.write('Falha ao gravar log: ' + e.message + '\n'); }
}

function tratar(m) {
  if (!m || m.jsonrpc !== '2.0' || typeof m.method !== 'string') {
    if (m && m.id !== undefined) erro(m.id, -32600, 'Requisição inválida');
    return;
  }
  const notificacao = m.id === undefined || m.id === null;
  if (notificacao) return; // notifications/initialized, cancelled etc.
  switch (m.method) {
    case 'initialize': {
      const pedida = m.params && m.params.protocolVersion;
      return enviar({ jsonrpc: '2.0', id: m.id, result: {
        protocolVersion: VERSOES.includes(pedida) ? pedida : VERSOES[0],
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: 'painel-eleitoral-2026', version: '1.0.0' },
        instructions: INSTRUCOES
      } });
    }
    case 'ping': return enviar({ jsonrpc: '2.0', id: m.id, result: {} });
    case 'tools/list': return enviar({ jsonrpc: '2.0', id: m.id, result: { tools: listar() } });
    case 'tools/call': {
      const p = m.params || {};
      if (typeof p.name !== 'string') return erro(m.id, -32602, 'name obrigatório');
      const env = executar(p.name, p.arguments);
      registrar(env, p.arguments);
      return enviar({ jsonrpc: '2.0', id: m.id, result: {
        content: [{ type: 'text', text: JSON.stringify(env, null, 2) }],
        structuredContent: env,
        isError: false // ABSTAIN é resultado válido, não falha de transporte
      } });
    }
    default: return erro(m.id, -32601, 'Método não suportado: ' + m.method);
  }
}

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on('line', linha => {
  if (!linha.trim()) return;
  let m;
  try { m = JSON.parse(linha); } catch { return erro(null, -32700, 'JSON inválido'); }
  if (Array.isArray(m)) return m.forEach(tratar);
  tratar(m);
});
