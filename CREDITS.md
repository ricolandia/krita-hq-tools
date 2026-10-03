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

As 19 amostras de balão em `modules/balloons/samples/` e as 3 onomatopeias em
`modules/onomatopeias/samples/` (WHOOSH!, POW! e CRASH!) são o kit handdrawn do
autor (Ricardo Graça), desenhado no Inkscape em outubro de 2026 sob a licença
MIT do plugin. As paletas `.gpl`, os presets de retícula e os ícones gerados
foram criados para o projeto e seguem a mesma licença.

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
os arquivos são os originais do autor, sem alteração, salvo registro no
`FONTE.md` do pack; cada pack traz `LICENSE.txt` e `FONTE.md` (autor, origem,
licença, alterações).

A única alteração já feita é a remoção de três presets que citavam uma textura
que os autores nunca distribuíram: `deevad 2d expressive thin` e `deevad 6n
stamp floor particles` (Deevad v8.2) e `X9AI_WC_Scattered_Sharp` (Watercolor
Set). Conferido em 2026-09-30 no histórico inteiro dos dois repositórios acima:
os arquivos citados (`deevad_bristle.png`, `flat-tip-dirty.gbr`,
`T_Texture_7.gih`) não existem em versão alguma, então não há o que
redistribuir. O `FONTE.md` de cada pack registra a remoção e a contagem
corrigida.

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
- Paletas, presets de retícula e ícones: criados para o projeto.
- Kit handdrawn de balões e onomatopeias (19 amostras em
  `modules/balloons/samples/` e 3 em `modules/onomatopeias/samples/`; fonte
  local do autor fora do repositório): desenhado à mão por Ricardo Graça no
  Inkscape em 02 e 03/10/2026 (MIT).
- Ícone do plugin (`assets/`; cópia em `hq_tools/resources/`): grade de
  retícula em papel `#F4EFE6` e tinta `#141414`, desenhado no Penpot para o
  projeto (MIT).

## Modelo 3D do visualizador (em teste)

- `hq_tools/modules/viewer3d/modelos/homem.json` (68 ossos, 1591 vértices,
  1570 faces) e `mulher.json` (68 ossos, 1605 vértices, 1584 faces): dados
  derivados dos FBX do autor. Malha do MakeHuman (CC0); rig gerado com
  Auto-Rig Pro (addon de terceiros) e exportado pelo autor. Os JSON são
  redistribuídos para o visualizador 3D do plugin; os FBX originais ficam
  fora do repositório.
- `hq_tools/modules/viewer3d/poses/`: poses extraídas dos FBX animados do
  autor (rotações locais por osso). Hoje: `idle_maos_fechadas.json` (padrão dos
  dois corpos) e `idle_maos_abertas.json` (dedos no repouso, mãos abertas).

## Pastas fora do repositório

Estas pastas são material de trabalho local do autor e ficam no `.gitignore`
(não entram no repositório nem no pacote):

- `Referencias/`: pranchas de referência, o lote fonte dos vetores e imagens
  de estudo. **Origem a declarar pelo autor** (desenho próprio, material de
  terceiros ou imagem gerada por IA); o que é redistribuído são as amostras
  já embarcadas em `hq_tools/`.
- `Novas_ideias/`: implementações em estudo, fora do CI e do pacote.

O pacote distribuído (`dist/hq_tools-<versão>.zip`) leva só `hq_tools/`,
`hq_tools.desktop`, `hq_tools.action` e os documentos.

## Projeto e contato

HQ Tools, por Ricardo Graça. Repositório público:
https://github.com/ricolandia/krita-hq-tools