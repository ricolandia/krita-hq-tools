# Perspectivas: pesquisa e conjuntos de linhas

Pesquisa feita em 05/10/2026 para a biblioteca de linhas de perspectiva
(ideia registrada no `IDEIAS-FUTURAS.md`). Os SVGs estão em
`hq_tools/resources/perspectivas/` e são gerados por
`scripts/gerar-perspectivas.py`.

## O que os quadrinhos mais usam

- **1, 2 e 3 pontos (cônica)** é o sistema dominante. O nível dos olhos
  (horizonte no meio do quadro) é o mais comum, porque cria identificação com
  o leitor; a cena de quina em 2 pontos é a mais versátil; o 3º ponto entra
  para drama.
- **Pássaro e verme** são o 3º ponto levado ao extremo: olhar de cima
  (horizonte alto, verticais convergindo para baixo, sensação de mapa) e de
  baixo (horizonte baixo, verticais para cima, sensação de opressão). Ficam
  para momentos dramáticos, não para o fluxo normal da página.
- **Curvilíneas (4 e 5 pontos)** são o recurso de vertigem e velocidade: a
  cena é projetada numa esfera, as retas viram arcos e só as linhas que passam
  pelo centro da visão continuam retas. Popularizadas nos quadrinhos por
  David Chelsea, em *Extreme Perspective! for Artists*; o clássico do básico é
  o mesmo autor em *Perspective! for Comic Book Artists* (as "cheat sheets" do
  livro são citadas até hoje como referência prática).

Referências principais: David Chelsea (*Perspective!* e *Extreme
Perspective!*), Scott McCloud (*Making Comics*), o material do Clip Studio
Paint sobre régua de perspectiva, e as construções de 4/5 pontos
(Flocon/Barre; descrições modernas em perspectivegrids.com e gridmypic.com).

## Construção usada nos SVGs

Cada linha tem **exatamente dois nós**, um em cada ponta (pedido do autor,
para o desenho continuar editável quando importado como vetor):

- **1/2/3 pontos**: famílias de retas; cada guia é um `<line>` recortado de
  borda a borda do quadro, mesmo com o ponto de fuga fora dele.
- **Pássaro/verme**: 3 pontos com o horizonte deslocado; o nível 2 aproxima o
  3º ponto de fuga (convergência mais forte) e o nível 1 afasta.
- **4 pontos**: dois VPs no horizonte (esquerda/direita) e zênite/nadir. As
  verticais são arcos de círculos que passam por zênite e nadir; as
  horizontais, arcos que passam por esquerda e direita; o horizonte e a
  vertical central ficam retos (são o limite da família). Cada arco é um
  `<path>` com um único `M` e um único `A`: dois nós e as alças do arco.
- **5 pontos**: a de 4 pontos mais o VP central; a família de profundidade é
  reta, porque as linhas que passam pelo centro da visão não curvam.

## Catálogo (9 conjuntos)

| Arquivo | Perspectiva | Uso típico |
|---|---|---|
| `01-frontal.svg` | 1 ponto | corredor, rua, cena simétrica |
| `02-dois-pontos.svg` | 2 pontos | cenário de quina, o mais versátil |
| `03-tres-pontos.svg` | 3 pontos neutro | drama moderado |
| `04-passaro-nivel-1.svg` | pássaro suave (horizonte a 30%) | visão geral |
| `05-passaro-nivel-2.svg` | pássaro forte (horizonte a 15%) | altura, vertigem |
| `06-verme-nivel-1.svg` | verme suave (horizonte a 70%) | imponência |
| `07-verme-nivel-2.svg` | verme forte (horizonte a 85%) | opressão |
| `08-curvilinea-4-pontos.svg` | curvilínea 4 pontos | grande angular, sonho |
| `09-curvilinea-5-pontos.svg` | curvilínea 5 pontos (fisheye) | vertigem extrema |

Cores (uma família por cor, legenda no comentário de cada arquivo):
**azul** = família vertical (ou do 3º VP); **laranja** = profundidade/VP
esquerdo (nas curvilíneas, os eixos retos e a família central); **cinza** =
VP direito, horizontais de apoio e horizonte.

## Como regenerar

    python3 scripts/gerar-perspectivas.py [--largura N --altura N] [--destino DIR]

Padrão 900x1200 (3:4). O docker `modules/perspectiva/` (mesmo fluxo do 3D:
seleção, preview WYSIWYG, flutuante para arrastar e dar zoom, inserir como
raster abaixo do esboço) gera na proporção da seleção; o script grava os
assets de referência.

## Testes

`tests/test_perspectivas.py` garante que cada elemento tem exatamente dois
nós, que só há `<line>` e `<path>`, que as cores são da paleta e que os SVGs
versionados batem byte a byte com o gerador.
