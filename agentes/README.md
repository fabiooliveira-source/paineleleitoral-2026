# Agentes — motores do painel como ferramentas de IA

Fase 1: os motores puros do painel são expostos como ferramentas MCP para que um agente de IA (Claude Code, Claude Desktop ou outro cliente MCP) responda perguntas chamando os próprios modelos validados, sem reimplementar fórmulas.

Sem dependências: Node 22, arquivos `.cjs`, protocolo MCP stdio (JSON-RPC 2.0).

## Ferramentas

| Ferramenta | Motor | Observação |
|---|---|---|
| `totais_territorio` | `dados/2026/municipios.json.gz` | Única fonte de números observados. Valida os totais nacionais conferidos antes de responder |
| `decisao_robusta` | `teoria-jogos.js` | CALL_A / CALL_B / WAIT; sem probabilidade |
| `barganha_nash`, `valor_shapley` | `negociacao-eleitoral.js` | Utilidades hipotéticas |
| `matriz_transferencia_neutra` | `transferencias-negociacao.js` | Linha de base de independência |
| `sensibilidade_pesos` | `probabilidade-transferencias.js` | Pesos fornecidos pelo usuário |
| `limites_transferencia` | `limites-por-urna.js` | Com `territorio`, a unidade é o município (limites mais largos que por seção) |
| `rateio_buildup_territorio` | `rateio-core.js` → `transport` | Heurística aplicada ao agregado |
| `v7_checkpoint` | `v7-engine.js` | Experimental, não certificada |

Ainda **não** incluídos (fase 2): Monte Carlo (`monte-carlo.js`) e simulador de apuração (`simulador.html`), cuja lógica está acoplada ao DOM e precisa ser extraída com testes de equivalência.

## Envelope de resposta

Toda chamada devolve `{ferramenta, modelo, status, executado_em, entrada_sha256, saida, avisos_obrigatorios, regra}`. `ABSTAIN` é resultado válido (não erro de transporte) e deve encerrar aquela linha de análise.

## Salvaguardas

1. `prompt-sistema.md` é enviado como `instructions` no `initialize` do MCP.
2. `validador.cjs` aplica as regras em código: bloqueia linguagem de probabilidade de vitória, números sem origem nas saídas das ferramentas, ABSTAIN ignorado, V7 sem aviso e afirmações de migração individual. Limitação: verifica a presença dos números, não o contexto em que são usados.
3. `AGENTE_LOG=arquivo.jsonl` registra cada chamada para auditoria.

## Uso

Claude Code, na raiz do repositório: o arquivo `.mcp.json` já registra o servidor `painel-eleitoral` (aprovar na primeira execução).

Claude Desktop (`claude_desktop_config.json`):

```json
{ "mcpServers": { "painel-eleitoral": { "command": "node", "args": ["/caminho/paineleleitoral-2026/agentes/mcp-server.cjs"], "env": { "AGENTE_LOG": "/caminho/agente.jsonl" } } } }
```

Uso direto em scripts:

```js
const { executar } = require('./agentes/ferramentas.cjs');
executar('totais_territorio', { territorio: { nivel: 'UF', uf: 'MG' } });
```

Testes: `node tests/agentes-mcp.cjs` (também no CI: `.github/workflows/agentes-mcp.yml`).

O GitHub Pages é estático: um chat público exigiria um backend intermediário (a chave de API nunca vai para o navegador). Fora do escopo da fase 1.
