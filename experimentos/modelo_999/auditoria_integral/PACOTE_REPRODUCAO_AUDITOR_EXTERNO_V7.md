# Pacote de reprodução para auditor externo — V7 (2020)

**Este pacote NÃO é parecer de auditor independente.** É uma preparação
para que terceiro sem envolvimento no desenvolvimento reproduza e
questione os resultados. Deve guardar o próprio relatório, data,
identificação e assinatura, sem usar um resultado de GitHub Actions
como substituto de independência.

## Referências congeladas

- Branch: `experimento/modelo-territorial-999`
- Commit que introduziu o lock dos insumos ANTES da primeira pontuação:
  `5759e10396385ddfb72bf0d4b7a9ec8a06f4f018`
- Git blob do modelo V7:
  `f5701acc902a3d420030737196fcbf6b8dcb0a1e`
- Protocolo: `protocolo_v7_holdout_temporal_2020_v1.json`
- Lock de 18 municípios, TSE ZIP SHA-256 e insumos reconstituídos:
  `congelamento_v7_holdout_temporal_2020.json`
- Preparação sem pontuação: GitHub Actions `41252574828`
- Congelamento pré-resultado: `41252610671`
- Primeiro teste V7 2020: `41253079566`
- Gate de integridade V7, 2.565 mutações: `41252705722`
- Checklist integral honesto: `41253114992` (gate de certificado bloqueado por evidência externa ausente)

## Reprodução com ambiente Python 3.11

Execute os comandos após clonar o repositório (o revisor deve
guardar o próprio hash do clone, requisitos do ambiente, logs e
resultados e também reproduzir ao menos um cálculo de modo independente).

```bash
git checkout 5759e10396385ddfb72bf0d4b7a9ec8a06f4f018
cd experimentos/modelo_999/auditoria_integral
git hash-object preditor_v7_experimental.py
python verificar_congelamento_v6.py
for uf in SE PA RR MT CE GO PB AL AM RS RO PE AC RJ MA PI ES BA; do
    python preparar_holdout_temporal_v7_2020.py --uf "$uf"
done
python agregar_v7_insumos_2020.py
python avaliar_v7_holdout_temporal_2020.py
python emitir_parecer_certificacao_v7.py
```

O comando `git hash-object` deve imprimir o blob
`f5701acc902a3d420030737196fcbf6b8dcb0a1e`.
As tabelas e arquivos reconstituídos devem coincidir com todos
os 18 hashes presentes em
`congelamento_v7_holdout_temporal_2020.json`. Abortar em qualquer
diferença; não substituir município ou dados.

Ao usar o commit pré-pontuação, o código do avaliador e parecer
já está presente, mas os arquivos de entrada são derivados dos ZIPs
originais. O download de arquivos do TSE é pesado; a auditoria deve
preservar o manifesto com URL e SHA-256 de cada arquivo.

## Ensaios independentes mínimos de terceiro

1. Reimplementar em outra biblioteca ou linguagem a fórmula V7
   (swing de log-odds com pseudo-contagens e regularização da zona)
   e comparar os 1.800 checkpoints até tolerância numérica publicada.
2. Refazer agregação de votos do TSE a partir dos CSVs originais
   por eleição/seção/candidato, sem reaproveitar as entradas derivadas.
3. Conferir se o campo usado como timestamp corresponde ao instante
   REAL de disponibilidade pública; se não houver prova, registrar
   `NOT_VERIFIABLE`, não converter em certeza.
4. Validar limites físicos e tratar revisões, duplicatas conflitantes,
   cortes de disponibilidade, checkpoints faltantes e inversão de
   ordem, reportando todos os casos de abstenção.
5. Refazer métricas por MUNICÍPIO, sem usar os 342 checkpoints como
   342 amostras independentes. Preservar resultados negativos.
6. Auditar desempenho em disputas apertadas: no conjunto de 18
   eleições o menor diferencial final entre os dois candidatos foi
   aproximadamente **2,29 pontos percentuais** (Cuiabá 2020).
   Não há prova do desempenho em disputa com margem menor que 1 pp.
7. Não ajustar a V7 nos próprios 18 municípios e reutilizá-los
   para alegar validação externa novamente.
8. Registrar assinatura e identidade institucional do revisor,
   integridade de sua cópia, data, discrepâncias e limitações.

## Situação técnica real

18/18 municípios passaram no protocolo HISTÓRICO de 2020. V7 melhorou
MAE média por cidade em relação à V6 nesse conjunto: 0,185720 pp
contra 0,202257 pp, mas foi pior que V6 em sete dos dezoito.

**Pendente:** disponibilidade pública contemporânea de cada snapshot,
cobertura de eleições com margem <1 pp, teste prospectivo, calibração
de probabilidades e parecer assinado de auditor verdadeiramente externo.

Uma assinatura só é válida se emitida pelo revisor independente
efetivo. O assistente ou workflow do próprio projeto NÃO pode
autocertificar independência.
