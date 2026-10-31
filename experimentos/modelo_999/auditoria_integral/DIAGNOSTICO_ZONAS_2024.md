# Diagnóstico quantitativo de cobertura inicial — V4.1 (2024)

Revisão descritiva dos dados congelados, sem alteração de parâmetros ou inferência individual.

| Município | Zona sem votos no checkpoint 5% | Referência de votos 1T da zona | Total de referência 1T | Fração sem amostra |
|---|---:|---:|---:|---:|
| Pelotas | 60 | 56.426 | 123.179 | 45,81% |
| Natal | 3 | 67.904 | 281.629 | 24,11% |

Pelotas: no checkpoint de 5%, zonas 164 e 34 somam 9.229 votos observados e a zona 60 ainda não contribui. Erro V4.1 de -0,757171 pp e classificação do vencedor incorreta. Em 19 checkpoints, o erro tem sinal negativo; 11 classificações corretas. MAE V4.1 0,326510 pp contra 2,581757 pp do baseline.

Natal: no checkpoint de 5%, zonas 1, 2, 4 e 69 somam 21.421 votos observados, com zero na zona 3. Erro V4.1 de +1,230356 pp contra +0,922796 pp do baseline. MAE V4.1 0,267260 pp contra 0,257574 pp do baseline.

Os percentuais de cobertura acima têm denominador de votos do primeiro turno por zona, não de seções ou eleitores; são medidas retrospectivas. A ausência de amostra local indica uso potencial de fallback, mas **não demonstra** que o fallback causou os erros.

Testes seguintes: (1) decomposição da contribuição por zona e fallback; (2) ablação por zona; (3) validação com novas cidades congeladas previamente; (4) auditoria de disponibilidade temporal. V4.1 permanece reprovada para promoção. Main não deve ser alterada.
