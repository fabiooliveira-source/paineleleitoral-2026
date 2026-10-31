# Comparação metodológica — Inferência espacial e análises existentes

Data de integração: 2026-10-31. Documento de auditoria preliminar, sem certificação estatística.

## Componentes
- `inferencia.html`: inferência ecológica exploratória por seção, taxas estimadas, intervalos bootstrap por reamostragem de municípios e limites matemáticos sob hipóteses de pareamento.
- `transferencias.html`: reconciliação dos totais e build-up contábil determinístico. O rateio compatível com margens não identifica transferências individuais.
- `comportamento.html`: mudanças observadas, distribuições de Monte Carlo e leitura territorial/histórica.
- `mudanca.html`: variações territoriais e rankings de contribuições entre turnos.
- `inferencia-espacial-brasil.html`: pseudoverossimilhança multinomial agregada, ajuste nacional/UF, composição de origens, vizinhança, interpolação IDW² e krigagem ordinária de coeficientes ecológicos locais, com separação treino/seleção/teste descrita no próprio painel.

## O que comparar quantitativamente
1. **Mesmas unidades e margens**: UF, município e seção; votos válidos, brancos, nulos, abstenção, eleitores aptos, comparecimento e votos dos finalistas. Confirmar cobertura e exclusões antes de comparar erros.
2. **Reprodução dos resultados**: erro absoluto e percentual por candidato, MAE ponderado por votos, máximo, viés por UF e região, e fechamento contábil. Erro pequeno de reconstrução não é evidência de migração individual correta.
3. **Generalização**: validação territorial bloqueada por município/UF, sem vazamento de seções vizinhas, e teste temporal com dados disponíveis apenas no instante da previsão. Seleção de hiperparâmetros não pode usar o conjunto de teste.
4. **Sensibilidade espacial**: comparar modelo sem espaço, IDW² e krigagem; testar raio, quantidade de vizinhos, variograma, ausência de coordenadas e bordas de UF. Não interpretar interpolação como causalidade.
5. **Incerteza e identificação**: limites factíveis das matrizes de transição, intervalos bootstrap por blocos territoriais, estabilidade das taxas por candidato e identificabilidade. Comparar taxas apenas sob as mesmas definições de origem/destino.
6. **Proveniência**: versão e hash dos dados, regras de pareamento, mudanças de eleitorado, voto em trânsito, seção agregada e consistência com totalizações oficiais.

## Conclusão preliminar
O painel espacial amplia a modelagem com dependência geográfica e descreve separação treino/seleção/teste. Isso é avanço metodológico potencial, mas **não demonstra** que as taxas de migração individual estejam corretas. O painel de transferências apresenta uma solução contábil; a inferência ecológica apresenta estimativas condicionadas a hipóteses; os totais por seção são observações agregadas. São objetos estatísticos diferentes e não devem ser apresentados como confirmação mútua.

**Status**: integração de navegação realizada. Auditoria quantitativa de métricas, amostras e reprodutibilidade pendente; nenhuma certificação integral foi emitida.
