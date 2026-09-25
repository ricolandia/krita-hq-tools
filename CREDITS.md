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

## Projeto e contato

HQ Tools, por Ricardo Graça. Repositório:
`31_APPS_GITHUB/Krita-Comics-Plugin` (pasta de projetos locais).