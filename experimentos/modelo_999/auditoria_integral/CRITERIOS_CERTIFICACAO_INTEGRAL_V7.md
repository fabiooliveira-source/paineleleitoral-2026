# Critérios para buscar certificação técnica integral — modelo de projeção V7

Atualização: 2026-10-31. `main` não pode ser alterada.
Este documento NÃO certifica o modelo e NÃO autoriza divulgar confiança
numérica calibrada de vencedor.

## Interpretar corretamente o objetivo 100%

A meta legítima **100% de itens obrigatórios de certificação cumpridos**
é diferente de **100% de acurácia preditiva em eleições incompletas**.
A segunda não pode ser prometida: em eleições competitivas há
variabilidade irredutível de quais seções chegam primeiro e de sua
composição. O placar definitivo aos 100% é **apuração**, não
projeção antecipada. Nunca converter 100% de checkpoints processados
em 100% de confiança estatística.

O status geral é `NOT_CERTIFIED` até a aprovação de TODOS os itens:

| Gate | Requisito objetivo | Critério de sucesso |
|---|---|---|
| A. Fonte | Dados TSE originais, hashes SHA-256 e CRC, contagem de votos por seção | 100% integridade, sem exclusões não reportadas |
| B. Temporal | `generated_at<=available_at<=cutoff` para cada registro histórico | 100% dos snapshots com disponibilidade pública demonstrável |
| C. Algoritmo | Código, hiperparâmetros, seletor de casos e regras congelados ANTES da prova | 100% hashes coincidentes |
| D. Segurança | Bloqueio seguro de duplicação conflitante, futuro, ordem incorreta, falha territorial | 0 regressões nos testes adversariais |
| E. Holdout temporal | Eleições não usadas no desenvolvimento; todos os 18 casos 2020 preregistrados, sem substituição após falha | critérios predefinidos, 18/18; qualquer falha deve permanecer publicada |
| F. Comparadores | V4, V6, proporção observada e margens de error por cidade/checkpoint | apresentar ganhos e perdas sem seleção oportunista |
| G. Estabilidade | atrasos reais, revisões, ordens e cobertura territorial | reportar erro máximo e abstenções, limites fixos antes de testar |
| H. Estatística | erro, viés, ganho por eleição, intervalos, calibração de probabilidades se houver | nunca tratar checkpoints correlacionados como eleições independentes |
| I. Avaliação externa | auditor independente com dados e scripts reproduzidos de forma separada | parecer reproduzível e assinado, inclusive resultados negativos |
| J. Validação prospectiva | fluxo de snapshots públicos reais, registrado sem conhecimento futuro | aprovação em eleições futuras e rastreamento de revisões |

**Falhar em um item impede certificação integral.** Passar uma execução
no GitHub Actions, ou atingir 18/18 em um holdout histórico,
NÃO satisfaz automaticamente as etapas B, I e J.

## Evidências já disponíveis

- V6: integridade matemática, mas apenas **5/15 cidades** aprovadas no
  desafio histórico nacional de 2024; portanto **REPROVADA**.
- V7 experimental: fórmula diferente e separada, aprendendo swing
  A/B em escala log-odds, com shrinkage de zonas pouco amostradas
  e volume de votos válidos modelado separadamente.
- Na avaliação de **desenvolvimento já conhecida de 2024**,
  V7 apresentou menor MAE que V6 em 10/15 casos, mas
  só 7/15 passaram uma seleção dos critérios históricos.
  O procedimento inteiro está identificado como desenvolvimento,
  e NÃO foi utilizado como evidência independente.
- A integridade adversarial V7 é testada separadamente.
- Código V7 congelado pelo Git blob
  `f5701acc902a3d420030737196fcbf6b8dcb0a1e`.
- Holdout temporal **18 eleições municipais de 2020 em 18 UFs**,
  preregistradas antes da pontuação, com o mesmo modelo fixo.
  A seção São Paulo/SP 2020 foi excluída previamente por ter
  sido usada durante o desenvolvimento V4; nenhuma substituição
  de cidades é permitida.

## Limitações técnicas ainda abertas

1. Nenhum replay com horários internos reconstituídos substitui
   snapshots públicos reais coletados quando disponibilizados.
2. A transferência individual de votos entre turnos não pode ser
   identificada a partir de totais agregados por seção;
   inferência ecológica fornece cenários, não rastreamento nominal.
3. A geometria/raio/krigagem exige coordenadas historicamente
   válidas e validação espacial que não utilize seções futuras.
4. O modelo ainda não inclui integralmente, de forma identificável,
   o papel dos candidatos eliminados, brancos/nulos, abstenções
   e mudança de comparecimento.
5. Evidências de desempenho em 18 municípios não permitem
   afirmar probabilidade de acerto de 99%, 99,9% ou 100%.

## Decisão operacional

Manter V6 e V7 como **experimentos separados**. Divulgar
`provisional_leader` e `winner_call` distintos e
`probability=None` até haver calibração validada.
Se o holdout 2020 falhar, a V7 NÃO deve ser corrigida
a posteriori e reavaliada nos mesmos 18 casos como se
fosse nova prova externa. Uma V8 precisa de outro conjunto
temporal/territorial ainda não usado.

**A certificação integral é uma condição de evidências, não uma
pontuação que se aumenta forçando aprovação.**
