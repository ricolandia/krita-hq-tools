<p align="center"><img src="assets/icon-light-128.png" width="96" alt="HQ Tools icon"></p>

# HQ Tools: comics tools for Krita

[Português](README.md) · **English**

Krita plugin with screentones and hatching, vector speech balloons and sound
effects, an asset library, a page manager, brush shortcuts, a 3D viewer, a
perspective line library and a hub to open and close the modules. Built for
Krita 5.3.4 (AppImage, PyQt5) with preparation for Krita 6 (PyQt6). The
project documentation is written in Portuguese; this file is the English
overview.

The four original context documents of the project are in `docs/contexto/`
(Portuguese).

## Demo

**3D viewer over the page:** pick the body and pose, draw a rectangular selection over the target panel (the preview adopts its aspect ratio and shows the exact crop, with up to 12x zoom for details), use "Float on page" to see it over the panel and "Insert as layer" or "as reference": the layer lands at the selection size, below the sketch, and the selection is cleared.

[<img src="Screenshots/09-3d-na-pagina.png" width="720" alt="Click to watch the short video 'Krita tools - update 3Dfloat'">](https://youtu.be/0rfDIr2QTDE)

▶ **Short video:** [Krita tools - update 3Dfloat](https://youtu.be/0rfDIr2QTDE) (the 3D float flow in action).

[<img src="Screenshots/08-demo.png" width="720" alt="Click to watch the short video 'All features' (first release)">](https://youtu.be/B9KYYyLdHF0)

▶ **Short video:** [All features](https://youtu.be/B9KYYyLdHF0) (the first release demo).

## Screenshots

<img src="Screenshots/01-baloes.png" width="380" alt="Balloons docker with the author's hand-drawn kit">

| Pages | Library | Brushes |
|---|---|---|
| ![Page manager](Screenshots/00-paginas.png) | ![Project library](Screenshots/02-biblioteca.png) | ![Brushes docker with the set cards, the 8 slots and the Clear slots button](Screenshots/03-pinceis.png) |

| Screentones and action lines | Onomatopoeia | Palettes |
|---|---|---|
| ![Screentones and action lines](Screenshots/04-reticulas.png) | ![Onomatopoeia](Screenshots/05-onomatopeias.png) | ![Palettes](Screenshots/06-paletas.png) |

| 3D viewer | Hub |
|---|---|
| ![3D docker with the Pose, Camera and Insert tabs, a running mannequin and the joint sliders](Screenshots/07-3d.png) | ![Hub docker with the buttons that open and close all ten modules, including Moodboard](Screenshots/10-hub.png) |

| Perspective library | Hub and 3D in Krita |
|---|---|
| ![Perspective docker with the grid gallery, the enlarged preview and the insert-into-selection buttons](Screenshots/11-perspectiva.png) | ![Krita with the hub and the 3D docker open (14 mm perspective camera, blue mannequin) and the mannequin already inserted into a page](Screenshots/12-hub-e-3d.png) |

| Moodboard |
|---|
| ![Moodboard docker with the project references folder, the list of linked references and the add, insert-into-selection, rename and delete buttons](Screenshots/13-Moodboard.png) |

## Modules

| Module | What it does |
|---|---|
| Screentones and hatching | Screentone presets with real LPI (cell computed from the document DPI), applied as a non-destructive fill layer inside the panel group, halftone as a Halftone filter mask over painted tone, tone with Krita patterns, CMYK per-channel color halftone, editing the applied screentone, empty mask to reveal by painting, show area, reuse of identical tones, pattern position and effect/speed lines (with an active selection, the lines use its area). |
| Balloons | Catalog of SVG vector balloons (the author's hand-drawn kit and CC0 samples on first run, own folder), one-click insert into the active group, `text` layer option for CPMT, a button that opens the native "Symbol Libraries" docker and installs the included comic fonts. |
| Onomatopoeia | Catalog of SVG sound effects (3 samples, own folder), inserted as vectors; draw your own in Inkscape. |
| Project library | Create your own balloons, panels and onomatopoeia inside Krita: "Create new resource" opens a 15 x 15 cm document at 300 dpi; "Save resource from document" exports the active layer as SVG (vector) or transparent PNG (painting, trimmed by the layer) to the library; double-click inserts it into the active group; Rename, Duplicate and Delete organize the folder. |
| Palettes | Comic and artistic templates (tones, ink, skin, sky, vegetation, flat colors, Zorn, portrait, landscape, dawn, night, earth, pastel, watercolor, gouache, acrylic, retro, BD, superhero, manga, sepia), applied to the foreground/background color, installed into Krita and previewed from the installed palettes. |
| Pages | Manager with internal `.kra` thumbnails: "New project..." uses the saved page folder (writes comicConfig.json and creates the project library), "Open project..." reads a CPMT `comicConfig.json` and "Folder..." opens any folder; "Create next page" opens a dialog (A4/A5/A3/strip format, DPI and strip panels), generates the page with automatic margin guides and refreshes the grid; "Set page template" uses the current page or a Krita comic template (BD, US, manga...) as the model; "Reference layer" marks the selected layer and "Import reference (PNG)" inserts a locked reference into the active group. New pages come with the "Arte" group and the "Panel mask" (paint only inside; hide the mask to paint outside). |
| Brushes | Suggested sets (Sketching, Inking, Watercolor/Gouache, Acrylic/Oil, Screentones) with thumbnail + name cards built from the brush presets installed in Krita; 8 slots with configurable shortcuts (right-click a slot to clear one or all, and the "Clear slots" button empties them); "Packs" tab with community brushes with verified licenses (one-click install and license display) and the brush bundle installer. |
| 3D viewer | Posable low-poly mannequin (MakeHuman + Auto-Rig Pro) as reference, with model choice (Man/Woman) and a pose library split into body (Idle, Fly, Walk, Run and Pose A) and hands (Closed, Open and Holding, authored for the right hand, with the Hand: selector for right, mirrored left or both): drag to orbit; the mouse wheel or the −/+ buttons zoom; Shift+drag, the middle mouse button or the Move button pan the framing, and "Fit" recenters; click a region (head, torso, arm, leg) to open Bend/Open/Twist sliders for that joint. The controls live in tabs (Pose, Camera and Insert), with the preview always visible; the camera can be orthographic (default) or perspective with 14/28/35 mm lenses (the lens changes only the convergence, without spilling out of the frame), and the mannequin color is selectable (beige, blue, ice or graphite). Draw a selection over the panel and the preview adopts its aspect ratio (WYSIWYG, camera zoom and pan included); "Float on page" only opens with a selection and appears over it (drag/resize, opacity and lock mode), and the insertion lands at the exact selection size, below the sketch, clearing the selection. |
| Perspective | Library of 9 perspective grids (one-point, two-point, three-point, bird's and worm's eye in two levels, 4- and 5-point curvilinear) with thumbnails and a preview that adopts the selection aspect ratio: "Float on page" shows the grid over the selection (drag and wheel); the insertion lands as an editable vector layer (each line with two nodes) at the exact selection size, below the sketch, as a layer or a locked reference, inside a macro (one Ctrl+Z undoes it) and clearing the selection. |
| Moodboard | Project reference board, light because it stores only links: "Add references..." resizes (max side 1600 px) and saves the images as JPG in the project's `moodboard/` folder (the originals stay untouched) and inserts them into `moodboard.kra` as file layers on a grid that grows; double-click (or "Insert into selection") brings the reference to the selected panel, locked and fitted to the selection, for tracing over; Rename and Delete manage the folder (with the board open, the layer is updated along). |
| Production | Script checklist: paste the text (the same syntax as the pages, with the optional character on the line, e.g. `fala p1 joao: ...`) and use Ctrl+Enter; each page becomes a node with the layout panels and each panel has three states (sketch, art and final; click the State column to cycle, right-click sets it directly), with the lines and characters in view; the weekly panel goal shows what is left and the expected date, the progress sits on top, double-click opens the `pagina_NNN.kra` and "Export .md" saves the checklist as Markdown; `roteiro.txt` and `producao.json` live in the project folder, and the "Syntax..." button shows the full format. |
| Hub | Control center to open and close the modules: one button per docker, checked while the dock is open (click again to close); the "Close the current one when opening another" option toggles between one module at a time and docks living together; a module disabled in the settings gets a disabled button with a warning. |

## Comic kit (fonts and free balloons)

The plugin ships a kit with licenses documented in `CREDITS.md`:

- **Fonts** (SIL OFL 1.1): Bangers, Comic Relief (Regular/Bold), Patrick
  Hand, Comic Neue (Regular/Bold), the full Londrina family (Solid, Shadow,
  Outline, Sketch), Nanum Pen Script, Gaegu and Boogaloo, installable with one
  click in the balloons docker;
- **Public-domain balloons** (CC0/PD): copied to the default folder on first
  run;
- **Own patterns and textures** (11 tiles: papers, extra screentones, manga
  hatch, hatching, grain), installable in the screentones docker and used by
  the "tone with pattern" mode;
- **Page templates** generated by the plugin (A4, A3, 1-3 strips, 2x2 and 3x3
  grids) in "Set page template";
- **Community brushes** ("Packs" tab in the brushes docker): Deevad v8.2
  (David Revoy, CC-BY 4.0) and Krita Watercolor Set (Vasco Basqué, CC-0),
  one-click install, each with license and credits.

## Installation

Complete end-user guide (ZIP, manual, Flatpak, uninstall and troubleshooting):
**`INSTALL.en.md`**.

Development mode (edit and test straight from the repository):

```bash
bash scripts/install-dev.sh
```

Distribution (ZIP for Tools > Scripts > Import Python Plugin from File):

```bash
bash scripts/build-zip.sh
# result in dist/hq_tools-<version>.zip
```

Then: enable **HQ Tools** in the Python Plugin Manager and restart Krita. If
you installed from the ZIP, copy `hq_tools.action` (inside the ZIP) to
`~/.local/share/krita/actions/` to get the default brush shortcuts in
Configure Krita > Shortcuts (the `install-dev.sh` script does that for you).
The dockers live in Settings > Dockers with the "HQ Tools" prefix; to group
them as tabs of one panel, drag one docker over another (Krita merges them
automatically, and you can ungroup whenever you want).

## Quick start

1. **Screentone**: "HQ Tools: screentones" docker, pick a preset (e.g. medium
   shadow 60 LPI) and "Apply screentone". The plugin uses the document DPI for
   the cell math; check "Use active selection" to limit it to the panel. After
   applying, select the layer and use "Edit selected" to adjust LPI, angle and
   position without recreating anything.
2. **Halftone**: paint the tone on a layer and apply "Halftone (filter mask)";
   the preset becomes dots or lines reactive to the painted tone. In a CMYKA
   document, the "Color per channel" mode uses the printing angles (15/75/0/45).
3. **Balloon**: double-click the model; the balloon enters the active group as
   a vector. Install the comic fonts with one click and, if you want, create
   your own balloons in the "Project library" docker.
4. **Pages**: save the current page to a folder and "New project..." uses that
   folder (creates comicConfig.json and the project library); "Create next
   page" asks for format/DPI (A3, strip, free...) and is born with margin
   guides; "Set page template" lets you use the current page or a Krita comic
   template as the base; references come in through "Reference layer" or
   "Import reference (PNG)".
5. **Brushes**: browse the sets (Sketching, Inking, Watercolor/Gouache,
   Acrylic/Oil, Screentones), click the card to activate; right-click assigns
   to a slot. Shortcuts in Configure Krita > Shortcuts > Scripts > HQ Tools.
6. **Effect lines**: in the screentones docker, "Effect lines" tab: choose
   focus or parallel and insert as vectors.
7. **Project library**: choose "Vector" or "Painting", "Create new resource"
   opens the 15 x 15 cm document at 300 dpi; draw, "Save resource from
   document" and insert with a double-click. Paintings come out as transparent
   PNG trimmed by the active layer. Rename, Duplicate and Delete organize the
   list.
8. **3D viewer**: in the "HQ Tools: 3D" docker, choose the model (Man or
   Woman) and the body and hand poses (default: Idle + Closed; the Hand:
   selector mirrors to the left or applies to both); drag to orbit, use
   Shift+drag (or the Move button) to pan, the wheel or the −/+ buttons to
   zoom and "Fit" to recenter; click a body region to pose. Draw a rectangular
   selection over the panel: the preview shows exactly the crop (use zoom for
   details, like a hand) and "Float on page" appears over the selection.
   "Insert as layer" or "as reference" places it at the selection size, below
   the sketch, and clears the selection.

## Development

```bash
python3 -m unittest discover -s tests -v   # core tests (outside Krita)
```

- Architecture: `docs/ARQUITETURA.md`
- Technical discovery (Krita API, configuration keys): `docs/DESCOBERTA.md`
- Validation inside Krita: `docs/VALIDACAO.md`

The pure core (script parser, screentone presets, comicsConfig, GPL palettes)
does not import `krita` and runs on any Python. The interface modules import
`krita` and only run inside Krita.

## Configuration

Everything in `~/.local/share/krita/hq_tools/`:

- `config.json` (enabled modules, presets, folders, brush slots);
- `screentone_presets.json` (user screentone presets);
- `balloons/` (balloon models, with samples on first run).

The interface follows the system language: a Portuguese locale uses
Portuguese, everything else uses English; the environment variable
`HQ_TOOLS_IDIOMA=pt|en` forces a language. The manual and the install guide
have English versions (`hq_tools_manual.en.html`, `INSTALL.en.md`).

## License

MIT. Uses native Krita resources: the Screentone generator and the Halftone
filter (Deif Lou) and the Comics Project Management Tools (Krita team). See
`LICENSE`.
