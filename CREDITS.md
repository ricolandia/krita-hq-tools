# Créditos e licenças

O código do plugin HQ Tools é MIT (ver `LICENSE`). O kit de HQ acompanha
arquivos de terceiros, todos com licenças livres; as atribuições estão abaixo.
Os arquivos de licença das fontes acompanham o pacote em
`hq_tools/resources/fonts/`.

## Fontes de HQ (SIL Open Font License 1.1)

Instaláveis pelo botão "Instalar fontes de HQ" no docker de balões
(destino: `~/.local/share/fonts/hq_tools`).

| Fonte | Autor | Licença |
|---|---|---|
| Bangers | The Bangers Project Authors (googlefonts/bangers) | SIL OFL 1.1 (`OFL-Bangers.txt`) |
| Comic Relief (Regular e Bold) | The Comic Relief Project Authors (loudifier/Comic-Relief) | SIL OFL 1.1 (`OFL-ComicRelief.txt`) |
| Patrick Hand | Patrick Wagesreiter | SIL OFL 1.1 (`OFL-PatrickHand.txt`) |
| Comic Neue (Regular e Bold) | The Comic Neue Project Authors (crozynski/comicneue) | SIL OFL 1.1 (`OFL-Comicneue.txt`) |
| Londrina Solid | The Londrina Solid Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-Londrinasolid.txt`) |
| Londrina Shadow | The Londrina Shadow Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaShadow.txt`) |
| Londrina Outline | The Londrina Outline Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaOutline.txt`) |
| Londrina Sketch | The Londrina Sketch Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaSketch.txt`) |
| Nanum Pen Script | NHN Corporation | SIL OFL 1.1 (`OFL-Nanumpenscript.txt`) |
| Gaegu | The Gaegu Project Authors | SIL OFL 1.1 (`OFL-Gaegu.txt`) |
| Boogaloo | John Vargas Beltrán | SIL OFL 1.1 (`OFL-Boogaloo.txt`) |

A SIL OFL permite uso, modificação e redistribuição, incluindo uso comercial;
o nome das fontes não pode ser usado para vender as fontes sozinhas. O texto
completo da licença acompanha cada fonte.

## Balões de domínio público (kit CC0/PD)

Copiados para a pasta padrão de balões na primeira execução
(`hq_tools/resources/balloons-cc0/`).

| Arquivo | Origem | Licença |
|---|---|---|
| `balao-fala-amada44.svg` | "Speech bubble.svg", Amada44, Wikimedia Commons, 2008 | Domínio público (dedicado pelo autor) |
| `balao-talk-to-me-cc0.svg` | "Talk to Me - speech bubble.svg", SupremeLordBagel, Wikimedia Commons, 2024 | CC0 1.0 Universal |

Mais balões livres podem ser baixados em:
- Openclipart (domínio público): `https://openclipart.org` (busca "speech bubble");
- Wikimedia Commons (licenças por arquivo): `https://commons.wikimedia.org`.

## Amostras do plugin

Os SVGs de exemplo (6 balões em `modules/balloons/samples/`, 8 onomatopeias
em `modules/onomatopeias/samples/`), as paletas `.gpl`, os presets de retícula
e os ícones gerados foram criados para o projeto e seguem a licença MIT do
plugin.

## Bibliotecas de símbolos do Krita (referência, não redistribuídas)

O Krita já traz estas bibliotecas na pasta `symbols` dos recursos; o plugin
apenas abre o docker nativo para usá-las:

| Biblioteca | Autor | Licença |
|---|---|---|
| `BalloonSymbols.svg` | Martin Owens, Tavmjong Bah (2013) | Domínio público |
| `pepper_carrot_speech_bubbles.svg` | David Revoy (Pepper & Carrot) | CC-BY-SA 4.0 |

## Recursos do Krita usados (não redistribuídos)

O plugin configura recursos nativos do Krita, de autoria do projeto Krita:

- Gerador Screentone e filtro Halftone: Deif Lou, GPL-2.0-or-later;
- Comics Project Management Tools (CPMT): time do Krita, GPL-2.0-or-later;
- 112 padrões de preenchimento e presets de pincel dos bundles padrão:
  Krita team e contribuidores (licenças dos respectivos bundles).

## Pincéis da comunidade (kit, `hq_tools/resources/brushes/`)

| Pack | Autor | Origem | Licença |
|---|---|---|---|
| Deevad v8.2 (brushkit) | David Revoy | https://github.com/Deevad/deevad-krita-brushpresets | CC-BY 4.0 (atribuição a David Revoy em redistribuição) |
| Krita Watercolor Set | Vasco Basqué | https://github.com/vascoalexander/krita-watercolor-set | CC-0 (ícones de David Revoy/MyPaint também CC-0) |

Regra do kit: só entram packs com licença explícita que permita redistribuição;
os arquivos são os originais do autor, sem alteração; cada pack traz
`LICENSE.txt` e `FONTE.md` (autor, origem, licença, alterações).

Candidatos avaliados e **não incluídos** por falta de licença clara (podem
entrar após contato com o autor ou como link): Cityscape Brushes e Pesi's
Watercolors (packs locais do autor do plugin), packs do repo portnov/krita-brushes
(comics de Animtim, Ramon de Ramon Miranda, Gouache, pencils), Lilly_Mist
Comics pack e InkP/Expressive Inks.

## Itens próprios do plugin (MIT)

- Padrões e texturas (`hq_tools/resources/patterns/`): 11 tiles gerados por
  código (papéis, retículas de estrelas/corações/ruído, trama de manga,
  hachuras 45°/135° e granulado de nanquim), criados para o projeto.
- Modelos de página gerados pelo plugin (A4, A3, tirinhas 1-3, grades 2x2 e
  3x3), criados para o projeto.
- Paletas, presets de retícula, amostras de balões e onomatopeias: criadas
  para o projeto.

## Projeto e contato

HQ Tools, por Ricardo Graça. Repositório:
`31_APPS_GITHUB/Krita-Comics-Plugin` (pasta de projetos locais).