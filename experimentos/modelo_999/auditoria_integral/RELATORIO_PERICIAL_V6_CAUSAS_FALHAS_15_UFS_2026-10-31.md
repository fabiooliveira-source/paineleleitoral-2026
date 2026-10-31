# RELATÓRIO PERICIAL — V6 | Investigação profunda das falhas em 15 UFs

**Data:** 31/10/2026. **Branch:** `experimento/modelo-territorial-999`.
**A `main` e o código congelado da V6 não foram modificados.**

## 1. Diagnóstico executivo

**A V6 é uma implementação numericamente coerente de uma regra preditiva
estatisticamente frágil.** O problema principal não é um erro de Python,
nem uma falha nos ZIPs do TSE. É a **suposição de que as taxas de conversão
de votos do 1º turno para o 2º turno, estimadas nas seções já apuradas,
representam as seções ainda não apuradas**, especialmente quando a
composição por zonas difere fortemente.

O ajuste da V6 nas zonas sem amostra pode piorar o problema:
- **Belo Horizonte:** aos 5%, 72,91% dos votos do 1º turno dos
  finalistas estavam em zonas ainda sem amostra; a regra V6 deslocou
  a previsão em **+5,8729 pontos percentuais** em relação à V4.
  A V4 projetava A em **44,8991%**; a V6 projetou A em **50,7720%**,
  contra **46,2729%** no resultado final. A V6 inverteu o vencedor
  projetado, errando com **+4,4992 pp**.
- **Olinda:** 32,88% da referência do 1º turno estavam em zona
  sem amostra aos 5%. A V6 deslocou +1,0069 pp a estimativa da V4,
  projetou A em 51,9827%, ante 48,6193% ao final (erro +3,3633 pp).
  A V4 também estava errada (+2,3564 pp).
- **São Paulo:** mesmo aprovada no gate geral, aos 5% a V6
  piorou a projeção da V4 em 1,9242 pp de deslocamento;
  a V6 errou -1,6378 pp, contra +0,2864 pp da V4.
- **Porto Velho e Aracaju:** nenhuma zona estava sem amostra
  aos 5%, portanto **V6 = V4**, mas as projeções continuaram piores
  que a proporção observada da própria apuração. Logo, o mecanismo
  de zona vazia **não explica todas as falhas**.

Essa conclusão distingue: uma contribuição algébrica **demonstrada**
(V6 versus V4 sob entradas iguais) de mecanismos de formação da
votação ainda **hipotéticos** (transferência de votos, comparecimento e
viés territorial não identificado causalmente).

## 2. Evidências e integridade

- [Execução nacional 15 UFs / 1.500 checkpoints](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41251355639):
  reconstrução e auditoria aritmética aprovadas, **gate científico reprovado**.
- [Investigação por zonas e estresse ampliado](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41251800731):
  **success**, sem alterar V6 ou seus parâmetros.
- [Auditoria da cronologia TSE](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41251666010):
  **success**.
- [Síntese cruzada das evidências](https://github.com/fabiooliveira-source/paineleleitoral-2026/actions/runs/41251856994):
  **success**.
- [Fontes primárias TSE 2024](https://dadosabertos.tse.jus.br/tl/dataset/resultados-2024)
  e [notas técnicas de divulgação](https://www.tse.jus.br/eleicoes/informacoes-tecnicas-sobre-a-divulgacao-de-resultados-2024).

Parâmetros, código original, insumos e manifesto permaneceram
congelados. Foram analisadas **55.924 seções eleitorais**, de 15
municípios em 15 estados, nas cinco regiões, mais os
**285 checkpoints primários (19 por cidade)** e **1.500 checkpoints
granulares** (1% a 100%). A aritmética foi conferida em **1.484
checkpoints não encerrados**, por implementação independente com frações.

**Resultado oficial original: 5/15 aprovações; 10/15 reprovações.**
Essa taxa (33,33%) é a fração de eleições que passaram em TODOS os
critérios estabelecidos, não é uma taxa de acerto de vencedor.

## 3. Formulação da V6: ponto estrutural vulnerável

A V6 mantém as projeções V4 para zonas que já possuem alguma
seção pareada. Para zonas **sem nenhuma seção pareada**, aplica:

`coverage = votos_1T_finalistas_secoes_2T_ja_apuradas / votos_1T_finalistas_todas_secoes`

`alpha = min(1, coverage / 0.20)`

`rate_A_global = votos_2T_A_observados / votos_1T_A_nas_mesmas_secoes`

`rate_common = (votos_2T_A + votos_2T_B)_observados / (votos_1T_A + votos_1T_B)_nas_mesmas_secoes`

`rate_A_zona_vazia = alpha * rate_A_global + (1-alpha) * rate_common`

Regra análoga para B; as estimativas são multiplicadas pelo
remanescente histórico de cada candidato, por zona, e somadas
aos votos já apurados.

**Problemas de modelagem identificados:**

1. A taxa comum elimina parte da distinção entre finalistas
   justamente em zonas onde a informação é inexistente; quanto
   menor a cobertura, maior o peso imposto à taxa comum.
2. O remanescente de votos do 1º turno de cada finalista não
   captura explicitamente o tamanho e a distribuição territorial
   dos votos dos demais candidatos, dos brancos/nulos, da abstenção
   e das mudanças de comparecimento do 2º turno.
3. A taxa estimada em uma zona com poucas seções pode ser
   pouco representativa do conjunto ainda pendente, mesmo quando
   nenhuma zona esteja completamente vazia.
4. Há apenas 1 a 57 zonas por município; o suporte territorial
   efetivo varia muito. Por exemplo, Palmas tem uma única zona
   no modelo: não existe informação sobre diferenciação
   **intra**zona nas entradas atuais.
5. A restrição física `votos_est_restantes <= eleitorado_nao_contado`
   é válida, mas pouco informativa: **em nenhum dos 285
   checkpoints primários ela foi ativada**. Portanto, ela NÃO
   causou nem impediu os erros observados.

A V6 não possui coordenadas espaciais, distância, raio em quilômetros,
IDW ou krigagem. A expansão para 15 estados foi de **escopo de
validação**, não aumento do raio de interpolação espacial do modelo.

## 4. Confronto entre modelos por cidade

MAE em **pontos percentuais (pp)**, 19 checkpoints 5%-95%.

| Município | V6 | V4 | Proporção observada | Critério original |
|---|---:|---:|---:|---|
| Manaus/AM | 0,1932 | 0,2299 | 0,6280 | PASSA |
| Belém/PA | 0,0733 | 0,0733 | 0,1723 | PASSA |
| Porto Velho/RO | 0,6148 | 0,6148 | 0,4065 | **FALHA** |
| Palmas/TO | 0,1045 | 0,1045 | 0,7157 | PASSA |
| Camaçari/BA | 0,1454 | 0,1454 | 0,2556 | PASSA |
| João Pessoa/PB | 0,2494 | 0,1986 | 0,1808 | **FALHA** |
| Aracaju/SE | 0,5610 | 0,5610 | 0,3597 | **FALHA** |
| Olinda/PE | 1,0215 | 0,9297 | 1,4600 | **FALHA** |
| Goiânia/GO | 0,1378 | 0,1826 | 0,1659 | **FALHA** |
| Cuiabá/MT | 0,2857 | 0,2857 | 0,2806 | **FALHA** |
| Campo Grande/MS | 0,2632 | 0,2685 | 0,1438 | **FALHA** |
| Belo Horizonte/MG | 0,4881 | 0,2523 | 0,2144 | **FALHA** |
| Niterói/RJ | 0,9491 | 0,9670 | 0,5425 | **FALHA** |
| São Paulo/SP | 0,1628 | 0,0792 | 0,8268 | PASSA |
| Curitiba/PR | 1,2071 | 1,4686 | 0,5981 | **FALHA** |

**Comparação cidade a cidade** (média dos 19 erros):
- V6 **pior que V4 em 4**, melhor em **5**, **idêntica em 6**.
- V6 pior que simples proporção observada em **8 das 15** cidades.
- Não houve demonstração de superioridade estatística uniforme.
- O gate também falha por excesso de erro máximo e/ou
  vencedor incorreto aos 5%, mesmo quando MAE é baixo:
  **Goiânia** reprovou pelo máximo 0,4561 pp (V6)
  versus 0,3680 pp (observado); **Cuiabá** pela diferença
  de MAE de apenas 0,0051 pp, mostrando a rigidez da regra.

## 5. Causalidade matemática versus inferência histórica

Foram reconstruídos, retrospectivamente, os votos finais ainda
pendentes por zona. Esse futuro é usado **SOMENTE para auditoria
ex post**. Jamais poderá alimentar o preditor ao vivo.

Para cada instante:
- Previsão A/B remanescente por zona foi confrontada com a
  votação A/B efetivamente finalizada naquela zona.
- Uma decomposição contrafactual troca **somente** o volume
  total futuro de votos válidos pelo volume efetivo,
  mantendo a composição A/B prevista. Isso separa uma
  contribuição aproximada de **composição do voto**
  da contribuição de **volume de votos remanescentes**.
- As duas contribuições somam o erro de projeção;
  NÃO são efeitos causais dos indivíduos nem efeitos
  de um experimento de intervenção.

**Evidência particularmente clara aos 5%:**

| Cidade | Erro V6 | Componente composição A/B (oráculo) | Componente volume remanescente (oráculo) |
|---|---:|---:|---:|
| Belo Horizonte | +4,4992 pp | +4,5018 pp | -0,0027 pp |
| Olinda | +3,3630 pp | +3,3481 pp | +0,0149 pp |
| Porto Velho | -1,8465 pp | -1,8480 pp | +0,0015 pp |
| Aracaju | +0,9123 pp | +0,9117 pp | +0,0006 pp |
| João Pessoa | +0,6956 pp | +0,6955 pp | +0,0001 pp |
| São Paulo | -1,6378 pp | -1,6342 pp | -0,0036 pp |

**Conclusão:** nos maiores desvios iniciais observados, a falha
principal está na **fração A/B dos votos ainda pendentes**,
não no volume total de comparecimento estimado. Essa é uma
constatação matemática para estes casos reconstruídos, não
prova de fluxo individual de eleitores entre candidatos.

## 6. Diagnóstico especial de Belo Horizonte

Checkpoint de 5%:
- Cobertura real do 1º turno de finalistas nas seções já apuradas:
  aproximadamente 5,26%; `alpha=0,2631`.
- Votos de referência em zonas sem amostra: **72,91%**.
- Votos válidos que de fato ainda estavam nessas zonas:
  cerca de **76,36% dos votos 2º turno ainda pendentes**.
- Estimativa A V4: **44,8991%**.
- Estimativa A V6: **50,7720%**.
- A final: **46,2729%**.
- Efeito isolado da regra V6 versus V4: **+5,8729 pp**.
- Os dois modelos calculam razões A/B a partir de poucas zonas
  observadas, mas a V6 dá demasiado peso ao ajuste comum
  em um conjunto maciço de zonas sem cobertura.

Isso não indica fraude ou anomalia eleitoral. É um
**erro na previsão do algoritmo** em uma configuração de
cobertura territorial desfavorável.

## 7. Estresse de atraso territorial: limites observados

Repeti **2.623 perturbações determinísticas** em 15 cidades,
removendo hipoteticamente zonas observadas
(individualmente, os dois/três maiores estratos e sorteios com
semente fixa), em checkpoints de 1% a 95%.

- **139 bloqueios/abstenções** quando o problema deixou
  de ser identificável após a remoção.
- **12 inversões de líder projetado** em cenários de remoção
  de zona única (não representam 12 eleições).
- Maior variação absoluta: **15,5231 pp**, em cenário
  sintético de remoção múltipla em Porto Velho.
- Maior variação com uma única zona em Porto Velho:
  **5,8377 pp**.
- João Pessoa: até **5,3754 pp** com múltiplas zonas.
- Belo Horizonte: até **4,0154 pp** com múltiplas zonas.
- São Paulo, apesar da grande dimensão, apresentou
  no conjunto testado até **0,5590 pp** com múltiplas zonas.

**Limitação importante:** o ledger não possui comparecimento
local exato por zona. As simulações retiram votos válidos A/B e
usam esses votos como **limite inferior para o eleitorado
contabilizado removido**. Assim, são testes de integridade/
sensibilidade, **não replays reais de atraso do TSE**.
Alterações em outras zonas simultâneas, correções de dados,
votos brancos/nulos e abstenções não são completamente
modelados.

## 8. Cronologia e possibilidade de vazamento temporal

Consultei os campos do CSV oficial por seção nas 15 UFs.
Ele contém:
- `DT_RECEBIMENTO_BU_HOR_TSE`: recepção do boletim;
- `DT_PRIM_TOT_PARCIAL_HOR_TSE`: primeira totalização
  parcial da seção.

Na amostra, a **mediana das medianas municipais** entre
recebimento e primeira totalização foi **29 segundos**
(as medianas por cidade variaram aproximadamente entre
23 e 39 segundos).

**O arquivo não possui campo de última totalização por
seção** na estrutura auditada. Tampouco preserva os
instantes efetivos de divulgação pública de todas as
parciais e revisões intermediárias.

Logo, associar o **resultado final de uma seção** ao seu
horário histórico de **primeira totalização** permite uma
reconstrução retrospectiva útil, mas **não prova que todos
esses votos já estavam publicados ao usuário nesse exato
segundo**. É a maior limitação metodológica remanescente
para certificação causal em tempo real.

A documentação do TSE explica que as totalizações e
comparecimentos vão sendo divulgados à medida que os
dados chegam, mas não transforma o campo de primeiro
processamento histórico em recibo de publicação no
aplicativo público.

## 9. Estatística: não fabricar confiança por checkpoint

Os **1.500 pontos não são observações independentes**.
A unidade de validação é a eleição/município; os marcos
de 1%-100% repetem os mesmos votos e dependem da mesma
composição territorial. Alguns marcos são exatamente
o mesmo instante de totalização.

Reamostrei **15 cidades**, não checkpoints, em
6.000 bootstraps de caráter **descritivo**:

| Comparação de MAE média por cidade | Diferença média (pp) | Intervalo percentil descritivo 2,5%-97,5% |
|---|---:|---:|
| V6 menos V4 | **+0,00637** | **[-0,04435; +0,05435]** |
| V6 menos proporção observada | **-0,03294** | **[-0,21396; +0,14563]** |

Ambos os intervalos incluem zero. Isso **não demonstra**
superioridade da V6. A escolha das 15 cidades não é aleatória,
e o bootstrap **não é intervalo de confiança populacional**
nem probabilidade de acerto eleitoral.

Não há base para alegar **95%, 99% ou 99,9% de certeza do
vencedor**. Um placar projetado de 51% não significa 51%
de chance de vitória. `probability=None` continua correto.

## 10. Diagnóstico por mecanismo e prioridade

**A. Erro da regra V6 em zona sem amostra — comprovado:**
MG/5%, PE/5%, SP/5% e outros episódios apresentam diferenças
numéricas grandes entre V6 e V4 nas mesmas entradas. Prioridade alta.

**B. Falha estrutural compartilhada V4/V6 — comprovada no
resultado, mecanismo individual não identificado:**
RO, SE e MT não tinham zona inteiramente vazia aos 5%,
mas ficaram piores que a proporção observada. Prioridade alta.

**C. Composição A/B das seções remanescentes — dominante
matematicamente nos maiores erros iniciais:**
Decomposição por volume futuro real identifica a maior parcela
do desvio. Prioridade máxima.

**D. Falta de fontes em tempo real autenticadas — fato:**
Horários internos do TSE e votos finais não equivalem
automaticamente a snapshots públicos contemporâneos.
Prioridade crítica para a auditoria científica.

**E. Excesso de confiança por reamostragem de checkpoints
correlacionados — risco metodológico:**
Usar as 1.500 séries como 1.500 eleições seria incorreto.
Prioridade alta.

## 11. Próxima arquitetura de pesquisa — V7, ainda NÃO aprovada

A investigação sustenta explorar **uma nova versão V7 em
arquivos separados da V6**, mantendo os resultados negativos
do holdout como dados **de desenvolvimento**, não de prova.

1. **Modelar separadamente volume e composição**:
   proporção de votos válidos versus eleitorado restante;
   depois, parcela A/B entre os votos válidos esperados.
   Tratar a primeira rodada inteira: votos dos finalistas,
   dos demais candidatos, brancos, nulos e participação.
2. **Hierarquia de suporte territorial e amostral**:
   seção/local de votação → zona → município, com
   regularização dependente do tamanho efetivo da
   amostra e da concentração de seções pendentes.
3. **Zona vazia e zona fracamente amostrada como
   dois riscos diferentes**: nunca atribuir confiança
   só porque uma zona recebeu sua primeira seção.
4. **Diagnosticar autocorrelação espacial antes** de
   tentar IDW, krigagem ou raio variável. Coordenadas
   precisam ser contemporâneas a 2024; o cadastro
   de locais de votação de 2026 não pode ser usado
   indiscriminadamente para 2024.
5. **Separar previsão provisória e chamada irreversível**:
   reportar incerteza e `ABSTAIN` quando critérios
   de estabilidade falharem, com cobertura de
   previsões no denominador.
6. **Novo conjunto não visto de municípios/anos**
   previamente registrado, usando eleições de 2016 e
   2020 não incluídas no desenvolvimento, e
   avaliador/revisor independente. Confrontar V7,
   V6 congelada, V4 e proporção observada com os
   critérios fixos ANTES de executar.
7. **Coletar snapshots efetivamente públicos** com
   horário de recepção e integridade verificada.
   Só então executar testes causais estritos de
   disponibilidade e calibração probabilística.

Qualquer ganho de V7 dentro destas mesmas 15 cidades
é **ganho de desenvolvimento**, nunca certificação externa.

## 12. Confiança, limitações e decisão

- **Confiança de engenharia nos cálculos e cruzamentos:
  alta (avaliação técnica aproximadamente 97/100).**
  1.484 verificações aritméticas independentes, hashes
  congelados e reprodução em GitHub sustentam isso.
- **Confiança no mecanismo ALGÉBRICO V6-versus-V4
  nos casos de zona sem amostra: alta.**
  A fórmula de mistura é observável e isolável por
  comparação com a mesma entrada.
- **Confiança de que todas as causas SOCIAIS das
  migrações eleitorais foram identificadas: baixa.**
  Dados agregados não permitem inferência individual.
- **Confiabilidade prospectiva em %: não estimada**,
  pois as eleições foram selecionadas historicamente
  e a disponibilidade pública real não foi provada.
- **Certificação integral da V6: NÃO CONCEDIDA.**

**Recomendação de auditoria:** manter o gate científico
vermelho, não promover V6 para previsões eleitorais
como solução certificada e separar estritamente
diagnóstico retrospectivo de experimentos futuros.
