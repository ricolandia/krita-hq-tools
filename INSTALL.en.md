# HQ Tools installation (user guide)

Step by step to install the plugin on any machine with Krita. If you already
have the repository and want to develop, see `scripts/install-dev.sh` and
`README.md`; this guide is for users only.

## Requirements

- Krita 5.3.4 or newer (AppImage, Flatpak or distribution package).
- The plugin is tested on Krita 5.3.4; there is preparation for Krita 6
  (PyQt6), but full validation on 6 has not been done yet.
- A release ZIP (`hq_tools-<version>.zip`) downloaded from the releases page.
- **The 3D viewer has no extra dependencies**: the models and poses ship
  inside the ZIP and the plugin reads everything in pure Python (no numpy).
  Blender is used only by the author to generate the files from the FBX; you
  do not need to install it, nor to be online.

## Quick install (ZIP)

1. Download the `hq_tools-<version>.zip` file from the releases page.
2. In Krita: Tools > Scripts > **Import Python plugin from file...** and pick
   the ZIP.
3. In Configure Krita > **Python Plugin Manager**, check **HQ Tools**.
4. Close and reopen Krita.
5. The 10 dockers show up in Settings > Dockers with the "HQ Tools" prefix:
   screentones, balloons, sound effects, palettes, pages, brushes, library,
   3D, perspective and hub.
   To group them as tabs in a single panel, drag one docker over another
   (Krita groups them automatically; drag back to ungroup).
6. Brush shortcuts (optional): unpack the ZIP, copy the `hq_tools.action`
   file into Krita's `actions` folder (see the folder table below) and
   restart. The shortcuts show up in Configure Krita > Shortcuts > Scripts >
   HQ Tools (brush 1 to 16).
7. Plugin icon (optional, Linux): for the icon to show up in the Python
   Plugin Manager, copy the PNG from `<pykrita>/hq_tools/resources/icon-256.png`
   to `~/.local/share/icons/hicolor/256x256/apps/hq_tools.png` and restart
   Krita. On Windows and macOS the manager icon depends on the theme.

## Manual install (without the import dialog)

Copy into Krita's Python plugins folder:

- the `hq_tools` folder and the `hq_tools.desktop` file into the `pykrita`
  folder;
- the `hq_tools.action` file into the `actions` folder.

Then enable the plugin in the Python Plugin Manager and restart Krita.

## Krita folders by installation type

| Installation type | `pykrita` | `actions` |
|---|---|---|
| AppImage / regular package (Linux) | `~/.local/share/krita/pykrita/` | `~/.local/share/krita/actions/` |
| Flatpak | `~/.var/app/org.kde.krita/data/krita/pykrita/` | `~/.var/app/org.kde.krita/data/krita/actions/` |
| Windows | `%APPDATA%\krita\pykrita\` | `%APPDATA%\krita\actions\` |
| macOS | `~/Library/Application Support/krita/pykrita/` | `~/Library/Application Support/krita/actions/` |

## First steps

1. **Screentone**: in the "HQ Tools: screentones" docker, pick a preset and
   click "Apply screentone". The plugin uses the document DPI for the cell
   math; check "Use active selection" to limit it to the panel.
2. **Balloon**: double-click a model to insert it into the active group; the
   "Install comic fonts" button copies the kit fonts to the system.
3. **Pages**: save the page in a folder, use "New project..." and then
   "Create next page" to continue the sequence with margin guides.
4. **Brushes**: click the card to activate; right-click assigns it to a slot
   (16 slots with shortcuts).

The full user manual is in `hq_tools_manual.en.html` (shown in the plugin
manager itself) and in the project's `README.en.md`.

## Interface language

The dockers follow the system language (Krita follows the system locale by
default): any Portuguese locale uses Portuguese, everything else uses
English. To force a language, set the environment variable
`HQ_TOOLS_IDIOMA` to `pt` or `en` before starting Krita.

## Where the plugin stores data

In Krita's data folder, which changes per system:

| System | Base folder |
|---|---|
| Linux | `~/.local/share/krita/` (Flatpak: `~/.var/app/org.kde.krita/data/krita/`) |
| Windows | `%APPDATA%\krita\` |
| macOS | `~/Library/Application Support/krita/` |

Inside it:

| Data | Folder |
|---|---|
| User configuration and screentone presets | `hq_tools/` (`config.json`, `screentone_presets.json`) |
| Your own balloons and sound effects | `hq_tools/balloons/` and `hq_tools/onomatopeias/` |
| Page models | `hq_tools/modelos/` |
| Installed comic fonts | Linux: `~/.local/share/fonts/hq_tools/` · Windows: `%LOCALAPPDATA%\Microsoft\Windows\Fonts` (HKCU registry) · macOS: `~/Library/Fonts` |
| Kit patterns (tone with pattern) | `patterns/` |
| Installed palettes | `palettes/` |
| Community brush packs | `{paintoppresets,brushes,patterns,palettes}` |

## Kit shipped with the plugin

- 12 comic font families (SIL OFL 1.1), installable with one click;
- public domain balloons (CC0/PD) copied on first run;
- 11 own patterns and textures (papers, screentones, hatching), installable
  from the screentones docker;
- community brush packs (Deevad v8.2, CC-BY 4.0 and Krita Watercolor Set,
  CC-0), installable from the "Packs" tab of the brushes docker.

Full credits and licenses in `CREDITS.en.md`. Everything installed into Krita's
resources (fonts, patterns, palettes, packs) requires restarting the program
to show up.

## Uninstall

1. In Configure Krita > Python Plugin Manager, uncheck HQ Tools.
2. Remove the copied files: `hq_tools` and `hq_tools.desktop` from the
   `pykrita` folder, and `hq_tools.action` from the `actions` folder.
3. To delete the user data as well, remove
   `~/.local/share/krita/hq_tools/` (careful: it deletes presets, your own
   balloons, sound effects and models). Fonts, patterns and packs installed
   into Krita's resource folders can be removed by hand if you no longer want
   them.

## Troubleshooting

- **Docker does not show up in the list**: check that HQ Tools is enabled in
  the Python Plugin Manager and restart Krita. Import errors on startup show
  up in Tools > Scripts > Scripter (Python tab).
- **Brush shortcuts do not show up**: if you installed from the ZIP, copy
  `hq_tools.action` into the `actions` folder (step 6 of the quick install).
- **New fonts/patterns/palettes do not show up**: Krita reads resources on
  startup; restart after installing any kit item.
- **Pack brush does not show up**: check that the "Packs" tab marks
  "[installed]" and restart; the presets show up in Krita's brush list under
  the pack's internal name.
- **A preset that was in the list is gone**: three presets were removed from
  the kit (`deevad 2d expressive thin`, `deevad 6n stamp floor particles` and
  `X9AI_WC_Scattered_Sharp`). All three pointed to textures the pack authors
  never distributed, so the preset installed and the brush would not load.
  If you installed an earlier version you can delete them from the plugin's
  brush folder; the reason is in each pack's `FONTE.md`.
- **CPMT project does not open**: the plugin reads `comicConfig.json`
  (no "s") in UTF-16, the default of the Comics Project Management Tools
  bundled with Krita; the old `comicsConfig.json` variant (UTF-8) is also
  accepted.

## License

Code under MIT. Third-party resources (fonts, balloons, packs) have their own
licenses documented in `CREDITS.en.md`. The plugin uses Krita's native features
(the Screentone generator and Halftone filter by Deif Lou, and the Comics
Project Management Tools by the Krita team) without redistributing them.
