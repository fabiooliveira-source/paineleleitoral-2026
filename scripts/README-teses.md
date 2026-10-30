# Teses aplicadas — validação espacial e cobertura

A página `teses.html` utiliza apenas arquivos estáticos do repositório. Não consulta APIs em tempo de navegação e não utiliza entrevistas. Dados eleitorais e indicadores IBGE são os congelamentos já documentados em `estudos-territoriais.html`. Simulações são identificadas separadamente dos resultados observados.

## Reprodução

Requer Python com numpy/scipy/pandas e Node para a preparação existente.

1. Reproduza `scripts/build-estudos-territoriais.py` conforme `README-estudos-territoriais.md` e preserve o pacote resultante com o hash da versão publicada.
2. `python scripts/build-teses-espaciais.py` produz `dados/teses_espaciais_pacote.json`. O núcleo `spatial_validation_core.py` é compartilhado com os testes de separação treino/teste.
3. `node scripts/prepare-model-input.cjs` prepara as composições por seção em `../model-input.json.gz`, conforme o estudo de comparação já existente. A simulação também usa as taxas do pacote existente `dados/2026/inferencia-resultados.json`; hashes estão no resultado.
4. `python scripts/build-cobertura-intervalos.py` executa os experimentos e produz `dados/cobertura_intervalos.json`. São 100 bases por cenário e 100 bootstraps por base. O processamento pode levar alguns minutos.
5. `python tests/test_spatial_validation.py` e `node tests/teses.cjs`.

## Universo e validação espacial

Base comum de 5.555 municípios brasileiros: quatro eleições (2º turno), quatro indicadores IBGE positivos e coordenadas eleitorais válidas. A vizinhança é reconstruída nessa base com oito vizinhos em esfera, pesos iguais e soma por linha um. Posições são médias de locais de votação de 2026, não centroides de limites municipais. Essa é uma seleção de casos completos, com exclusões explícitas, não preenchimento de ausências.

Indicadores locais: log10 da população de 2022, log10 da densidade de 2022, alfabetização 15+ em 2022 e log10 do PIB por habitante calculado de 2021. PIB por habitante não é renda familiar. Modelo IBGE + UF inclui indicadores locais e efeitos fixos de UF. O espacial SLX acrescenta as médias dessas quatro covariáveis nos vizinhos. Nenhum resultado eleitoral de vizinho é uma covariável. Características IBGE dos locais ocultos são consideradas conhecidas; são predições retrospectivas com covariáveis estáticas disponíveis, não previsões prospectivas históricas.

Regressões lineares ponderadas pelo denominador: votos válidos para parcela PT, aptos para abstenção. Padronização estimada somente no treino. Efeitos de UF e coeficientes recebem penalização numérica 1e-6, intercepto não penalizado. Predições limitadas a [0,1]. O ajuste integral gera coeficientes e Moran dos resíduos; esses resultados são separados das predições fora do ajuste. UF sem treino tem coeficiente específico zero e usa o componente comum; isso é informado na auditoria.

Três protocolos, cinco rodadas cada: CRC32(chave + `|20261029`) módulo cinco. No primeiro a chave é o município. Nos demais a chave é um bloco: floor(R cos(-15°) longitude/200), floor(R latitude/200), com R=6371 km e ângulos em radianos. A grade é aproximadamente de 200 km, não uma malha oficial. No terceiro protocolo, retiram-se ainda todas as posições de treino a menos de 100 km de qualquer posição de teste, por distância esférica. Cada município é previsto uma vez fora do treino, incluindo quando sua UF não foi vista.

RMSE, erro absoluto médio e erro agregado ponderados pelos denominadores do teste. O peso do teste não entra no ajuste; só na avaliação. O pacote armazena predições e observações arredondadas a 0,001 p.p. (inteiros em milésimos de ponto percentual). Métricas são calculadas antes de arredondar. Os testes aceitam somente o erro numérico correspondente à precisão divulgada. Escores por UF mantêm os ajustes nacionais das rodadas, sem reajuste na UF selecionada.

A validação espacial adapta a questão abordada por Tiago Pinho da Silva (USP, 2023); não reproduz integralmente as duas técnicas da tese. O SLX é uma adaptação com covariáveis espaciais da questão tratada por Kevin Horan (Maynooth, 2025), não implementação de seu modelo hierárquico autorregressivo. Referência da especificação SLX: https://pysal.org/spreg/generated/spreg.OLS.html .

## Experimento de cobertura dos intervalos

Adapta o diagnóstico de cobertura discutido por André Klima (LMU, 2016) ao nosso estimador WLS restrito existente, com 16 origens e cinco destinos. Não implementa um novo modelo bayesiano ou híbrido.

Amostra fixa: 150 municípios brasileiros com pelo menos oito seções elegíveis, oito seções sorteadas sem reposição por município. Os municípios também são sorteados sem reposição; semente 20261029. São 1.200 seções, não a base nacional inteira. As origens são composições reais e os destinos de cada repetição são gerados artificialmente por multinomiais. Os totais de origem e aptos são preservados em cada seção.

Cenário homogêneo: P0 = 0,8 × matriz WLS publicada + 0,2 × uniforme. Essa suavização define uma verdade artificial interior ao simplex, sem afirmar novas taxas reais. Cenário heterogêneo: marcador = participação inicial de Lula nos aptos, centralizado/padronizado na amostra e truncado a [−1,5,+1,5]. Adiciona-se a log(P0) o produto 0,8 × marcador × [1; −1; 0,15; −0,1; 0,05], em seguida normaliza-se cada origem por softmax. É heterogeneidade artificial associada à composição, não coeficiente político causal estimado.

Em cada um dos 100 conjuntos sintéticos por cenário, o núcleo `solve` de `inferencia_eleitoral.py` é reajustado sem ridge; depois 100 bootstraps reamostram municípios inteiros com reposição. Os percentis 2,5% e 97,5% definem intervalos nominais de 95%. Origem sem votos em uma reamostragem fica não estimável naquele bootstrap. Células só têm intervalo avaliado com pelo menos 80 ajustes finitos. Falhas e denominadores válidos são informados; não se imputam intervalos ausentes.

Verdade para cobertura: taxa geradora esperada, ponderada pelos totais da própria origem. No cenário homogêneo é P0; no heterogêneo, soma(X_ir P_ird) / soma(X_ir). Não é a taxa realizada aleatória dos fluxos ocultos em cada repetição. Os destinos sintéticos e a verdade não substituem as inferências reais do painel.

Cobertura por célula = repetições em que intervalo contém a taxa geradora / repetições com intervalo válido. Wilson 95% é a incerteza Monte Carlo dessa proporção, não intervalo de taxa de transferência. A média reúne células dependentes; seu erro-padrão Monte Carlo usa a dispersão entre repetições, não trata 8.000 células/repetições como independentes.

Resultados não calibram automaticamente os intervalos de todo o Brasil, não identificam migrações de eleitores e não fornecem chance de vitória. Não há garantia de 99%. As três referências de doutorado estão ligadas na página, com distinção entre método original e adaptação.
