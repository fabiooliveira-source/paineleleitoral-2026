'use strict';
/* Registro de ferramentas para agentes de IA.
 * Cada ferramenta embrulha um motor puro já existente e testado no painel.
 * Nenhuma ferramenta reimplementa fórmula: apenas valida, chama o motor e
 * devolve um envelope auditável (versão, hash da entrada, avisos obrigatórios).
 * ABSTAIN do motor é repassado intacto; o agente não pode completá-lo.
 */
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const crypto = require('node:crypto');

const ROOT = path.resolve(__dirname, '..');
const req = f => require(path.join(ROOT, f));
const TeoriaJogos = req('teoria-jogos.js');
const Negociacao = req('negociacao-eleitoral.js');
const TransfNegociacao = req('transferencias-negociacao.js');
const Sensibilidade = req('probabilidade-transferencias.js');
const Limites = req('limites-por-urna.js');
const Rateio = req('rateio-core.js');
const V7 = req('v7-engine.js');

const FONTE_MUNICIPIOS = 'dados/2026/municipios.json.gz';
// Totais nacionais conferidos (mesma verificação de monte-carlo.js).
const TOTAIS_CONFERIDOS = { lula_1t: 53879538, flavio_1t: 56104503, lula_2t: 64256232, flavio_2t: 59826041 };
const CAMPOS = ['aptos_1t', 'comparecimento_1t', 'abstencoes_1t', 'validos_1t', 'brancos_1t', 'nulos_1t', 'lula_1t', 'flavio_1t',
  'aptos_2t', 'comparecimento_2t', 'abstencoes_2t', 'validos_2t', 'brancos_2t', 'nulos_2t', 'lula_2t', 'flavio_2t'];

let cacheMunicipios = null;
function municipios() {
  if (cacheMunicipios) return cacheMunicipios;
  const bruto = fs.readFileSync(path.join(ROOT, FONTE_MUNICIPIOS));
  const dados = JSON.parse(zlib.gunzipSync(bruto).toString('utf8'));
  for (const [k, v] of Object.entries(TOTAIS_CONFERIDOS)) {
    const s = dados.reduce((a, x) => a + x[k], 0);
    if (s !== v) throw Error('Base municipal diverge do consolidado nacional conferido em ' + k);
  }
  cacheMunicipios = { dados, sha256: crypto.createHash('sha256').update(bruto).digest('hex') };
  return cacheMunicipios;
}

const normalizar = s => String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toUpperCase();

/* Resolve um território em linhas municipais. Lança erro (=> ABSTAIN) se ambíguo. */
function territorio(t) {
  if (!t || typeof t !== 'object') throw Error('Território ausente');
  const { dados } = municipios();
  const nivel = t.nivel;
  if (nivel === 'BR') return { rotulo: 'Brasil, incluindo exterior', linhas: dados };
  const uf = normalizar(t.uf);
  if (!uf) throw Error('UF obrigatória para nível ' + nivel);
  const daUF = dados.filter(x => x.uf === uf);
  if (!daUF.length) throw Error('UF sem dados: ' + uf);
  if (nivel === 'UF') return { rotulo: uf === 'ZZ' ? 'Exterior (ZZ)' : 'UF ' + uf, linhas: daUF };
  if (nivel !== 'MUN') throw Error('Nível deve ser BR, UF ou MUN');
  let achados;
  if (t.codigo_municipio_tse) achados = daUF.filter(x => x.codigo_municipio_tse === String(t.codigo_municipio_tse).padStart(5, '0'));
  else if (t.municipio) achados = daUF.filter(x => normalizar(x.municipio) === normalizar(t.municipio));
  else throw Error('Informe municipio ou codigo_municipio_tse');
  if (achados.length !== 1) throw Error(achados.length ? 'Município ambíguo; informe codigo_municipio_tse' : 'Município não encontrado em ' + uf);
  return { rotulo: achados[0].municipio + ' / ' + uf, linhas: achados };
}

function somar(linhas) {
  const s = Object.fromEntries(CAMPOS.map(k => [k, 0]));
  for (const x of linhas) for (const k of CAMPOS) s[k] += x[k];
  return s;
}

const esquemaTerritorio = {
  type: 'object',
  description: 'Recorte territorial da base oficial TSE conferida (cópia datada, sem atualização automática).',
  properties: {
    nivel: { type: 'string', enum: ['BR', 'UF', 'MUN'] },
    uf: { type: 'string', description: 'Sigla da UF; ZZ = exterior' },
    municipio: { type: 'string', description: 'Nome do município (sem distinção de acentos)' },
    codigo_municipio_tse: { type: 'string', description: 'Código TSE de 5 dígitos; prevalece sobre o nome' }
  },
  required: ['nivel']
};

const abstain = (motivo, extra = {}) => Object.assign({ status: 'ABSTAIN', reason: motivo, probability: null }, extra);

const FERRAMENTAS = [
  {
    name: 'totais_territorio',
    modelo: 'BASE_OFICIAL_TSE_CONFERIDA_2026',
    description: 'Totais oficiais conferidos do 1º e 2º turnos (Presidência 2026) para Brasil, UF ou município. Única fonte de números observados para o agente.',
    aviso: 'Cópia datada da base oficial TSE conferida (dados/2026); não é apuração em tempo real.',
    inputSchema: { type: 'object', properties: { territorio: esquemaTerritorio }, required: ['territorio'] },
    run(i) {
      const t = territorio(i.territorio);
      const s = somar(t.linhas);
      return {
        status: 'OK', territorio: t.rotulo, localidades: t.linhas.length, totais: s,
        vantagem_lula_menos_flavio_1t: s.lula_1t - s.flavio_1t,
        vantagem_lula_menos_flavio_2t: s.lula_2t - s.flavio_2t,
        share_lula_validos_2t: s.validos_2t ? s.lula_2t / s.validos_2t : null,
        fonte: FONTE_MUNICIPIOS, fonte_sha256: municipios().sha256, probability: null
      };
    }
  },
  {
    name: 'decisao_robusta',
    modelo: TeoriaJogos.VERSION,
    description: 'Decisão minimax na apuração: CALL_A, CALL_B ou WAIT dados votos observados, eleitorado restante e intervalo de cenários para a fração final de A. Não produz probabilidade.',
    aviso: 'Chamada robusta é condicional ao intervalo de cenários informado; só mathematical_winner é garantia física.',
    inputSchema: {
      type: 'object',
      properties: {
        observedA: { type: 'integer', minimum: 0 }, observedB: { type: 'integer', minimum: 0 },
        remainingElectors: { type: 'integer', minimum: 0 },
        scenarioLow: { type: 'number', minimum: 0, maximum: 1 }, scenarioHigh: { type: 'number', minimum: 0, maximum: 1 },
        abstentionCost: { type: 'number', exclusiveMinimum: 0, exclusiveMaximum: 1 }
      },
      required: ['observedA', 'observedB', 'remainingElectors', 'scenarioLow', 'scenarioHigh']
    },
    run: i => TeoriaJogos.compute(i)
  },
  {
    name: 'barganha_nash',
    modelo: Negociacao.VERSION,
    description: 'Solução de barganha de Nash sobre fronteira de utilidades hipotéticas de duas partes.',
    aviso: 'Utilidades e fronteira são hipóteses do usuário; não representam votos reais nem transferência observada.',
    inputSchema: {
      type: 'object',
      properties: {
        frontier: { type: 'array', items: { type: 'array', items: { type: 'number' }, minItems: 2, maxItems: 2 }, maxItems: 10000 },
        disagreement: { type: 'array', items: { type: 'number' }, minItems: 2, maxItems: 2 }
      },
      required: ['frontier', 'disagreement']
    },
    run: i => Negociacao.nash(i)
  },
  {
    name: 'valor_shapley',
    modelo: Negociacao.VERSION,
    description: 'Valor de Shapley para 1 a 8 grupos; coalitionValues tem 2^n valores indexados por máscara de bits (bit i = grupo i), com coalizão vazia = 0.',
    aviso: 'Valor marginal da função de coalizão assumida; não é causalidade nem migração individual.',
    inputSchema: {
      type: 'object',
      properties: { groups: { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 8 }, coalitionValues: { type: 'array', items: { type: 'number' } } },
      required: ['groups', 'coalitionValues']
    },
    run: i => Negociacao.shapley(i)
  },
  {
    name: 'matriz_transferencia_neutra',
    modelo: 'INDEPENDENCE_NEUTRAL_BASELINE_HAMILTON',
    description: 'Matriz inteira de referência (independência) entre origens e destinos com margens exatas e limites de Fréchet por célula.',
    aviso: 'Linha de base neutra de independência; não é migração observada nem inferência causal.',
    inputSchema: {
      type: 'object',
      properties: {
        origins: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, votes: { type: 'integer', minimum: 0 } }, required: ['name', 'votes'] } },
        destinations: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, votes: { type: 'integer', minimum: 0 } }, required: ['name', 'votes'] } }
      },
      required: ['origins', 'destinations']
    },
    run: i => TransfNegociacao.compute(i)
  },
  {
    name: 'sensibilidade_pesos',
    modelo: 'CONDITIONAL_USER_SUPPLIED_WEIGHTS',
    description: 'Aplica pesos condicionais fornecidos pelo usuário (cada origem soma 100%) e opcionalmente compara com destinos observados.',
    aviso: 'Pesos são hipóteses do usuário, não probabilidades estimadas.',
    inputSchema: {
      type: 'object',
      properties: {
        origins: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, votes: { type: 'integer', minimum: 0 }, weights: { type: 'array', items: { type: 'number', minimum: 0, maximum: 1 } } }, required: ['name', 'votes', 'weights'] } },
        destinations: { type: 'array', items: { type: 'string' } },
        observedDestinations: { type: 'array', items: { type: 'integer', minimum: 0 } }
      },
      required: ['origins', 'destinations']
    },
    run: i => Sensibilidade.calculate(i)
  },
  {
    name: 'limites_transferencia',
    modelo: 'SECTIONWISE_FRECHET_PARTIAL_IDENTIFICATION',
    description: 'Limites de identificação parcial (Fréchet) entre 1º e 2º turnos, calculados por unidade e somados. Aceita linhas fornecidas ou um território da base municipal.',
    aviso: 'Com território, a unidade é o MUNICÍPIO, não a seção: os limites ficam mais largos que os da página por seção. Não são probabilidades; extremos por célula não são simultâneos.',
    inputSchema: {
      type: 'object',
      properties: {
        territorio: esquemaTerritorio,
        linhas: { type: 'array', description: 'Linhas por seção com campos lula/flavio/validos/brancos/nulos/abstencoes/aptos de _1t e _2t', items: { type: 'object' } }
      }
    },
    run(i) {
      if (Array.isArray(i.linhas)) return Object.assign(Limites.evaluate(i.linhas), { unidade: 'linhas fornecidas' });
      if (!i.territorio) return abstain('Informe territorio ou linhas');
      const t = territorio(i.territorio);
      const r = Limites.evaluate(t.linhas);
      if (r.status !== 'OK') return r;
      // O motor conta "sections"; aqui cada unidade é um município: renomear evita citação errada.
      const { sections, ...resto } = r;
      return { ...resto, municipios_validados: sections, unidade: 'município', territorio: t.rotulo };
    }
  },
  {
    name: 'rateio_buildup_territorio',
    modelo: 'RATEIO_URNAS_TRANSPORT',
    description: 'Matriz de build-up do painel (rateio-core.transport) aplicada aos totais agregados de um território: retenção máxima, demais candidatos rateados na proporção do 2º turno.',
    aviso: 'Heurística contábil de rateio aplicada ao agregado do território (não por urna); não identifica migração individual.',
    inputSchema: { type: 'object', properties: { territorio: esquemaTerritorio }, required: ['territorio'] },
    run(i) {
      const t = territorio(i.territorio);
      const r = Rateio.transport(somar(t.linhas));
      return { status: 'OK', territorio: t.rotulo, unidade: 'agregado territorial', ...r, probability: null };
    }
  },
  {
    name: 'v7_checkpoint',
    modelo: V7.model && (V7.model.version || V7.model.name || V7.model) || 'V7',
    description: 'Modelo V7 experimental. Exige contrato completo {current, reference, ledger, previous?} com seções pareadas e horários; caso contrário ABSTAIN.',
    aviso: 'V7 experimental, NÃO certificada para 2026 (4/10 requisitos em 31/10/2026). Nunca fornece probabilidade de vitória.',
    inputSchema: {
      type: 'object',
      properties: { current: { type: 'object' }, reference: { type: 'object' }, ledger: { type: 'array' }, previous: { type: 'object' } },
      required: ['current', 'reference', 'ledger']
    },
    run: i => V7.predict(i)
  }
];

const hash = x => crypto.createHash('sha256').update(JSON.stringify(x === undefined ? null : x)).digest('hex');

/* Executa uma ferramenta e devolve o envelope auditável. Nunca lança. */
function executar(nome, entrada) {
  const f = FERRAMENTAS.find(x => x.name === nome);
  const inicio = new Date().toISOString();
  let saida;
  if (!f) saida = abstain('Ferramenta desconhecida: ' + nome);
  else {
    try {
      if (entrada !== undefined && (entrada === null || typeof entrada !== 'object' || Array.isArray(entrada))) throw Error('Entrada deve ser objeto JSON');
      saida = f.run(entrada || {});
      if (!saida || typeof saida !== 'object') saida = abstain('Motor não retornou objeto');
    } catch (e) { saida = abstain(e.message || 'Erro na entrada'); }
  }
  const avisos = [f && f.aviso, saida.warning, saida.assumptions].filter(Boolean);
  return {
    ferramenta: nome,
    modelo: f ? f.modelo : null,
    status: saida.status || 'ABSTAIN',
    executado_em: inicio,
    entrada_sha256: hash(entrada),
    saida,
    avisos_obrigatorios: avisos,
    regra: saida.status === 'OK'
      ? 'Citar números somente desta saída e repassar avisos_obrigatorios.'
      : 'ABSTAIN: informar o motivo ao usuário e não estimar o resultado por outros meios.'
  };
}

function listar() {
  return FERRAMENTAS.map(f => ({ name: f.name, description: f.description + ' Aviso: ' + f.aviso, inputSchema: f.inputSchema }));
}

module.exports = { executar, listar, FERRAMENTAS, _territorio: territorio };
