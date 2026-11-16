'use strict';
/* Validador de saída do agente: aplica em código as regras do prompt.
 * validarResposta(texto, envelopes) -> {ok, violacoes[]}
 *  - linguagem de probabilidade de vitória quando nenhuma ferramenta a forneceu;
 *  - ABSTAIN ignorado (texto não reconhece a abstenção);
 *  - números >= 1.000 ou percentuais que não aparecem em nenhuma saída;
 *  - avisos obrigatórios não repassados (verificação por palavras-chave).
 * Limitação: confere presença dos números, não o contexto em que são usados.
 */

const RE_PROB = /(probabilidade|chances?)\s+(de\s+|da\s+|do\s+)?(vit[oó]ria|vencer|ganhar|eleger)|\d+(?:[.,]\d+)?\s*%\s+de\s+chances?/i;
const RE_ABST = /abst(en[cç][aã]o|[eé]m|eve|ain)|ABSTAIN|n[aã]o\s+aplic[aá]vel|inconclusiv|sem\s+resultado|n[aã]o\s+(foi\s+)?poss[ií]vel/i;

function numerosDe(obj, acc = new Set()) {
  if (typeof obj === 'number' && Number.isFinite(obj)) acc.add(obj);
  else if (Array.isArray(obj)) obj.forEach(x => numerosDe(x, acc));
  else if (obj && typeof obj === 'object') Object.values(obj).forEach(x => numerosDe(x, acc));
  return acc;
}

// Converte número em formato pt-BR ("1.234.567", "51,37") ou en ("1234567", "51.37").
function lerNumero(s) {
  s = s.replace(/\s/g, '');
  if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(s)) return Number(s.replace(/\./g, '').replace(',', '.'));
  if (/^\d+,\d+$/.test(s)) return Number(s.replace(',', '.'));
  return Number(s);
}

function extrair(texto) {
  const out = [];
  const re = /(?<![\w.,])(-|−)?(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)(\s*%)?/g;
  let m;
  while ((m = re.exec(texto))) {
    const v = lerNumero(m[2]) * (m[1] ? -1 : 1);
    if (Number.isFinite(v)) out.push({ bruto: m[0].trim(), valor: v, pct: Boolean(m[3]) });
  }
  return out;
}

function validarResposta(texto, envelopes) {
  const violacoes = [];
  const envs = Array.isArray(envelopes) ? envelopes : [];
  if (typeof texto !== 'string') return { ok: false, violacoes: ['Texto ausente'] };

  const temProb = envs.some(e => e.saida && typeof e.saida.probability === 'number');
  if (!temProb && RE_PROB.test(texto))
    violacoes.push('Linguagem de probabilidade de vitória sem ferramenta que a forneça');

  const abst = envs.filter(e => e.status !== 'OK');
  if (abst.length && !RE_ABST.test(texto))
    violacoes.push('Resposta ignora ABSTAIN de: ' + abst.map(e => e.ferramenta).join(', '));

  const conhecidos = [...numerosDe(envs.map(e => e.saida))];
  const confere = (n) => {
    if (n.pct) return conhecidos.some(v => Math.abs(v * 100 - n.valor) <= 0.051 || Math.abs(v - n.valor) <= 0.051);
    if (Math.abs(n.valor) < 1000) return true; // contagens pequenas, ordinais, números de lista
    if (Number.isInteger(n.valor) && n.valor >= 1900 && n.valor <= 2100) return true; // anos
    return conhecidos.some(v => Math.abs(v - n.valor) < 0.5);
  };
  for (const n of extrair(texto)) if (!confere(n)) violacoes.push('Número sem origem nas ferramentas: ' + n.bruto);

  const usadas = new Set(envs.filter(e => e.status === 'OK').map(e => e.ferramenta));
  if (usadas.has('v7_checkpoint') && !/experimental|n[aã]o\s+certificad/i.test(texto))
    violacoes.push('V7 usada sem declarar que é experimental/não certificada');
  if ([...usadas].some(u => /transfer|rateio|limites/.test(u)) && /eleitores?\s+(migraram|trocaram|passaram)/i.test(texto))
    violacoes.push('Afirma migração individual de eleitores');

  return { ok: violacoes.length === 0, violacoes };
}

module.exports = { validarResposta, _extrair: extrair };
