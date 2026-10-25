# Painel Eleitoral 2026

Site independente, em português, publicado pelo GitHub Pages a partir de `main` e da pasta raiz.

## Conteúdo

- `index.html`: página autônoma, responsiva, sem dependências externas.
- Seleção de Brasil e 27 UFs, turno e mapa esquemático acessível.
- Links para os portais oficiais do TSE.
- Simulador educativo com duas candidaturas fictícias, separado da consulta oficial.

## Situação dos dados

**Não há importação de resultados eleitorais nem atualização automática.** Os filtros organizam a seleção local, mas não filtram os links externos. Nenhum valor do simulador deve ser apresentado como pesquisa, previsão ou dado oficial.

Para integrar apuração, verificar a documentação e os arquivos atuais do TSE; validar eleição, turno, cargo, território e horário de geração; exibir a origem exata, a atualização e o estado de falha. Dados ausentes nunca devem aparecer como zero votos. Não reutilizar resultados de outra eleição ou simulados como fallback.

Fontes: https://resultados.tse.jus.br/oficial/app/index.html e https://dadosabertos.tse.jus.br/ .

## Verificação da primeira publicação

Em 25/10/2026: HTTP 200 e conteúdo publicado idêntico ao arquivo revisado; layout verificado nas larguras 1440, 768, 390 e 320 px, sem rolagem horizontal; mapa e filtros sincronizados; simulação testada para arredondamento, empate, restauração e entradas inválidas; nenhum erro JavaScript observado.

## Publicação

Editar `index.html` na branch `main`. O GitHub Pages recompila após cada alteração. Confirmar a implantação e testar o endereço público antes de anunciar uma nova versão.
