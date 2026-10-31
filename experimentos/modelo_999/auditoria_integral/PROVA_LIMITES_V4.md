# Limites determinísticos condicionais da participação de A

Sejam A e B os votos válidos já contabilizados, e R um limite superior verdadeiro para o total de votos válidos ainda possíveis. Para qualquer conclusão da apuração, x votos adicionais para A e y para B satisfazem x >= 0, y >= 0 e x + y <= R.

A participação final é (A + x) / (A + B + x + y). Se A + B + R > 0:

limite inferior = A / (A + B + R)
limite superior = (A + R) / (A + B + R)

## Limite inferior

O numerador final é pelo menos A e o denominador final é no máximo A + B + R. Portanto, a participação final é pelo menos A / (A + B + R). Equivalentemente, a diferença dos produtos cruzados é A * (R - y) + x * (B + R), não negativa.

## Limite superior

A diferença entre os produtos cruzados do limite superior e da participação final é:

B * (R - x) + (A + R) * y

Ela é não negativa porque x <= R e A, B, R e y são não negativos. Logo, a participação final não supera (A + R) / (A + B + R).

## Indicação condicional de vencedor

Se A > B + R, então A + x > B + y para toda conclusão admissível. O raciocínio é simétrico para B > A + R. Empate no limite não permite indicação de vencedor. O código usa esses testes inteiros, evitando uma chamada baseada em arredondamento de porcentagens.

## Condições essenciais

A e B devem estar corretos e não podem ser revistos posteriormente de forma que invalide a desigualdade. R deve realmente limitar votos futuros: pode ser calculado por eleitorado total menos eleitorado das seções já contabilizadas somente quando os dois cadastros são consistentes, autênticos e contemporâneos. Contagens intermediárias, anulações, recursos ou alterações cadastrais podem exigir reabrir a verificação.

Esses limites não são intervalos de confiança, não têm probabilidade associada e não certificam a qualidade da projeção pontual. A prova refere-se ao contrato matemático sob as condições declaradas, não à autenticidade dos dados nem à impossibilidade de revisões eleitorais.

## Verificações do código

Além da demonstração algébrica, o teste exaustivo pequeno percorre A, B e R de 0 a 7 e todas as conclusões admissíveis, totalizando 7.672 casos com denominador final não nulo. Confere inclusão da participação final nos limites e ausência de indicação matemática errada. Isso não substitui a prova para números arbitrários nem uma revisão técnica independente.
