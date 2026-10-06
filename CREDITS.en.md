<p align="center"><img src="assets/icon-light-128.png" width="96" alt="HQ Tools icon"></p>

# Credits and licenses

[Português](CREDITS.md) · **English**

The HQ Tools plugin code is MIT (see `LICENSE`). The comics kit ships
third-party files, all under free licenses; the attributions are below. The
font license files ship with the package in `hq_tools/resources/fonts/`.

## Comics fonts (SIL Open Font License 1.1)

Installable with the "Install comics fonts" button in the balloons docker
(destination: `~/.local/share/fonts/hq_tools`).

| Font | Author | License |
|---|---|---|
| Bangers | The Bangers Project Authors (googlefonts/bangers) | SIL OFL 1.1 (`OFL-Bangers.txt`) |
| Comic Relief (Regular and Bold) | The Comic Relief Project Authors (loudifier/Comic-Relief) | SIL OFL 1.1 (`OFL-ComicRelief.txt`) |
| Patrick Hand | Patrick Wagesreiter | SIL OFL 1.1 (`OFL-PatrickHand.txt`) |
| Comic Neue (Regular and Bold) | The Comic Neue Project Authors (crozynski/comicneue) | SIL OFL 1.1 (`OFL-Comicneue.txt`) |
| Londrina Solid | The Londrina Solid Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-Londrinasolid.txt`) |
| Londrina Shadow | The Londrina Shadow Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaShadow.txt`) |
| Londrina Outline | The Londrina Outline Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaOutline.txt`) |
| Londrina Sketch | The Londrina Sketch Authors (marcelommp/Londrina-Typeface) | SIL OFL 1.1 (`OFL-LondrinaSketch.txt`) |
| Nanum Pen Script | NHN Corporation | SIL OFL 1.1 (`OFL-Nanumpenscript.txt`) |
| Gaegu | The Gaegu Project Authors | SIL OFL 1.1 (`OFL-Gaegu.txt`) |
| Boogaloo | John Vargas Beltrán | SIL OFL 1.1 (`OFL-Boogaloo.txt`) |

SIL OFL allows use, modification and redistribution, including commercial
use; the font names cannot be used to sell the fonts by themselves. The full
license text ships with each font.

## Public-domain balloons (CC0/PD kit)

Copied into the default balloons folder on first run
(`hq_tools/resources/balloons-cc0/`).

| File | Origin | License |
|---|---|---|
| `balao-fala-amada44.svg` | "Speech bubble.svg", Amada44, Wikimedia Commons, 2008 | Public domain (dedicated by the author) |
| `balao-talk-to-me-cc0.svg` | "Talk to Me - speech bubble.svg", SupremeLordBagel, Wikimedia Commons, 2024 | CC0 1.0 Universal |

More free balloons can be downloaded from:
- Openclipart (public domain): `https://openclipart.org` (search "speech bubble");
- Wikimedia Commons (per-file licenses): `https://commons.wikimedia.org`.

## Plugin samples

The 19 balloon samples in `modules/balloons/samples/` and the 3 sound effects
in `modules/onomatopeias/samples/` (WHOOSH!, POW! and CRASH!) are the author's
hand-drawn kit (Ricardo Graça), drawn in Inkscape in October 2026 under the
plugin's MIT license. The `.gpl` palettes, the screentone presets and the
generated icons were created for the project and follow the same license.

## Krita symbol libraries (reference, not redistributed)

Krita already ships these libraries in the resources `symbols` folder; the
plugin only opens the native docker to use them:

| Library | Author | License |
|---|---|---|
| `BalloonSymbols.svg` | Martin Owens, Tavmjong Bah (2013) | Public domain |
| `pepper_carrot_speech_bubbles.svg` | David Revoy (Pepper & Carrot) | CC-BY-SA 4.0 |

## Krita resources used (not redistributed)

The plugin configures native Krita resources, authored by the Krita project:

- Screentone generator and Halftone filter: Deif Lou, GPL-2.0-or-later;
- Comics Project Management Tools (CPMT): Krita team, GPL-2.0-or-later;
- 112 fill patterns and brush presets from the default bundles:
  Krita team and contributors (licenses of the respective bundles).

## Community brushes (kit, `hq_tools/resources/brushes/`)

| Pack | Author | Origin | License |
|---|---|---|---|
| Deevad v8.2 (brushkit) | David Revoy | https://github.com/Deevad/deevad-krita-brushpresets | CC-BY 4.0 (attribution to David Revoy on redistribution) |
| Krita Watercolor Set | Vasco Basqué | https://github.com/vascoalexander/krita-watercolor-set | CC-0 (icons by David Revoy/MyPaint also CC-0) |

Kit rule: only packs with an explicit license that allows redistribution are
included; the files are the authors' originals, unmodified, unless recorded in
the pack's `FONTE.md`; each pack ships `LICENSE.txt` and `FONTE.md` (author,
origin, license, changes).

The only change made so far is the removal of three presets that referenced a
texture the authors never distributed: `deevad 2d expressive thin` and
`deevad 6n stamp floor particles` (Deevad v8.2) and `X9AI_WC_Scattered_Sharp`
(Watercolor Set). Checked on 2026-09-30 across the entire history of the two
repositories above: the referenced files (`deevad_bristle.png`,
`flat-tip-dirty.gbr`, `T_Texture_7.gih`) do not exist in any version, so there
is nothing to redistribute. Each pack's `FONTE.md` records the removal and the
corrected count.

Candidates evaluated and **not included** for lack of a clear license (they
may enter after contacting the author or as links): Cityscape Brushes and
Pesi's Watercolors (local packs of the plugin author), packs from the
portnov/krita-brushes repo (Animtim's comics, Ramon by Ramon Miranda, Gouache,
pencils), Lilly_Mist Comics pack and InkP/Expressive Inks.

## Plugin's own items (MIT)

- Patterns and textures (`hq_tools/resources/patterns/`): 11 code-generated
  tiles (papers, star/heart/noise screentones, manga weave, 45°/135° hatches
  and ink grain), created for the project.
- Page templates generated by the plugin (A4, A3, strips 1-3, 2x2 and 3x3
  grids), created for the project.
- Palettes, screentone presets and icons: created for the project.
- Hand-drawn balloon and sound-effect kit (19 samples in
  `modules/balloons/samples/` and 3 in `modules/onomatopeias/samples/`; the
  author's local source stays outside the repository): hand-drawn by Ricardo
  Graça in Inkscape on 02 and 03/10/2026 (MIT).
- Plugin icon (`assets/`; copy in `hq_tools/resources/`): screentone grid on
  paper `#F4EFE6` and ink `#141414`, drawn in Penpot for the project (MIT).

## 3D viewer model (under test)

- `hq_tools/modules/viewer3d/modelos/homem.json` (68 bones, 1591 vertices,
  1570 faces) and `mulher.json` (68 bones, 1605 vertices, 1584 faces): data
  derived from the author's FBX files. MakeHuman mesh (CC0); rig generated
  with Auto-Rig Pro (third-party addon) and exported by the author. The JSON
  files are redistributed for the plugin's 3D viewer; the original FBX files
  stay outside the repository.
- `hq_tools/modules/viewer3d/poses/`: poses extracted from the author's
  animated FBX files (semantic values per bone), split into `corpo/` (Idle,
  Voa, Anda, Corre and Pose A) and `maos/` (Fechada, Abertas and Segura,
  authored for the right hand; the docker mirrors to the left).

## Folders outside the repository

These folders are the author's local working material and stay in
`.gitignore` (they do not enter the repository or the package):

- `Referencias/`: reference sheets, the source batch of vectors and study
  images. **Origin to be declared by the author** (own drawing, third-party
  material or AI-generated image); what is redistributed are the samples
  already embedded in `hq_tools/`.
- `Novas_ideias/`: implementations under study, outside the CI and the
  package.

The distributed package (`dist/hq_tools-<version>.zip`) carries only
`hq_tools/`, `hq_tools.desktop`, `hq_tools.action` and the documents.

## Development and transparency

The plugin code was developed with AI assistance (opencode + DeepSeek) in
the coding, with review and testing by the author. The plugin **has no AI
features** and the kit **includes no AI-generated art**: the assets are the
author's own or third-party under free licenses (see the sections above).

## Project and contact

HQ Tools, by Ricardo Graça. Public repository:
https://github.com/ricolandia/krita-hq-tools
