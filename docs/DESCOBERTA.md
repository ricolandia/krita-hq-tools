# Descoberta técnica (Krita 5.3.4)

Registro do que foi confirmado sobre a API e os recursos do Krita 5.3.4 durante
a construção do HQ Tools. Fonte primária: código-fonte do Krita (branch master
do repo KDE/krita, via espelho GitHub, setembro de 2026) e inspeção do
AppImage `krita-6.0.x`/`5.3.4` (conteúdo de `usr/lib/kritaplugins` e
`usr/lib/krita-python-libs/PyKrita/krita.pyi`).

## Ambiente

- Krita em uso: `~/.local/share/applications/krita.desktop` aponta para
  `~/APP/APPIMAGE/krita.appimage`, que é o **Krita 5.3.4** (Qt5, PyQt5,
  Python 3.13). O sysinfo confirma `Appimage build: Yes`.
- `~/APP/krita-6.0.3/6.0.4-x86_64.AppImage` são o Krita 6 (Qt6, **PyQt6**,
  sem PyQt5): os plugins não são binariamente compatíveis entre as duas
  linhas; daí o `core/compat.py`.
- Plugins Python embutidos no AppImage: CPMT (comics_project_management_tools),
  batch_exporter, colorspace, krita_script_starter, scripter, tenbrushes,
  palette_docker, entre outros.

## Gerador Screentone (fill layer)

- Plugin: `kritascreentonegenerator.so`; id do gerador: `screentone`
  (`KisScreentoneGeneratorConfiguration::defaultName()`), versão 2.
- Fonte de referência: `plugins/generators/screentone/` (Krita master).
- Chaves do XML de configuração (valores por `getInt/getDouble/getBool/getColor`):

| Chave | Tipo | Padrão |
|---|---|---|
| `pattern` | int (0 pontas, 1 linhas) | 0 |
| `shape` | int (ver tabela abaixo) | 0 |
| `interpolation` | int (0 Linear, 1 Sinusoidal) | 0 |
| `equalization_mode` | int (0 Nenhuma, 1 Função, 2 Template) | 2 |
| `foreground_color` / `background_color` | cor (hex ou XML) | preto / branco |
| `foreground_opacity` / `background_opacity` | int 0-100 | 100 |
| `invert` | bool | false |
| `brightness` / `contrast` | qreal 0-100 | 50 / 95 |
| `size_mode` | int (0 resolução, 1 pixels) | 0 |
| `units` | int (0 polegadas, 1 cm) | 0 |
| `resolution` | qreal | 300 |
| `frequency_x` / `frequency_y` | qreal (linhas por unidade) | 30 |
| `constrain_frequency` | bool | true |
| `position_x` / `position_y` | qreal | 0 |
| `size_x` / `size_y` | qreal | 10 |
| `keep_size_square` | bool (nota: chave é `keep_size_square`, não `constrain_size`) | true |
| `shear_x` / `shear_y` | qreal | 0 |
| `rotation` | qreal (graus) | 45 |
| `align_to_pixel_grid` | bool | true |
| `align_to_pixel_grid_x` / `y` | int | 1 |

- Formas de pontos (`shape`): 0 Redondo, 1 Elipse (legado), 2 Losango,
  3 Quadrado, 4 Elipse.
- Formas de linhas: 0 Reta, 1 Senoide, 2 Onda triangular, 3 Serra, 4 Cortina.
- Cores: `InfoObject.properties()` devolve a cor em XML; ao *gravar* via
  `setProperty`, `KisPropertiesConfiguration::getColor` aceita string hex
  (caminho `QColor`) e também XML de cor. Confirmado no código-fonte
  (`libs/image/kis_properties_configuration.cc`).

## Filtro Halftone

- Plugin: `kritahalftone.so`; id do filtro: `halftone` (ação
  `krita_filter_halftone`).
- Fonte: `plugins/filters/halftone/` (Krita master).
- Chaves raiz: `color_model_id` (ex.: `RGBA`), `mode`
  (`intensity` | `independent_channels` | `alpha`).
- Opções com prefixo do modo: `{mode}_generator` (id do gerador),
  `{mode}_hardness`, `{mode}_invert`, `{mode}_foreground_color`,
  `{mode}_background_color`, `{mode}_foreground_opacity`,
  `{mode}_background_opacity`.
- Opções do gerador aninhado com prefixo duplo:
  `{mode}_generator_screentone_{chave}` (ex.:
  `intensity_generator_screentone_frequency_x`). O `KisHalftoneFilterConfiguration`
  monta o gerador com `getPrefixedProperties(fullGeneratorId + "_", config)` e
  invalida o cache quando uma propriedade desse padrão é gravada.
- Modo independente por canal usa prefixos `{color_model_id}_channel0_` ...

## API Python confirmada no krita.pyi 5.3.4

- `Document.createFillLayer(name, generatorName, configuration, selection)`
  devolve nó **órfão** (fonte: `libs/libkis/Document.cpp`): a inserção é sempre
  `parent.addChildNode(node, above)`.
- `Document.createFilterMask(name, filter, selection)` (com `Selection`) e
  `(name, filter, node)` (com `Node`, inicializa a máscara pela camada).
- `Document.createSelectionMask(name)` + `SelectionMask.setSelection(selection)`.
- `Selection()` cria seleção vazia; `Selection.select(x, y, w, h, 255)` vira
  seleção total (usada quando não há seleção ativa).
- `VectorLayer.addShapesFromSvg(svg)` aceita SVG com retângulos e `<text>`
  (fonte: `libs/libkis/VectorLayer.cpp`; o parser é o SvgParser do Krita).
- `Krita.instance().resources("preset")` e `("palette")` listam recursos;
  `View.activateResource(resource)` troca o pincel ativo (uso do tenbrushes
  embutido).
- `ManagedColor.fromQColor(QColor)` para aplicar cor de frente/fundo
  (`View.setForeGroundColor` / `setBackGroundColor`).
- `InfoObject`: `properties()`, `setProperties(dict)`, `property(key)`,
  `setProperty(key, value)`; cores lidas voltam como XML.
- `Filter.configuration()` / `setConfiguration(InfoObject)`; `Krita.instance().filter(name)`
  e `.filters()`.

## CPMT (comicConfig.json)

- Chaves usadas: `projectName`, `pagesLocation`, `pages` (lista de caminhos
  relativos), `pageNumber` (contador), além de `exportLocation`,
  `templateLocation`, `translationsLocation`.
- Nome de página: `projectName` com espaços virados em `_`, mais `_` extra
  apenas quando o nome termina em dígito, mais 3 dígitos + `.kra`
  (ex.: `Meu_Projeto001.kra`, `Projeto2_001.kra`). Confirmado no
  `comics_project_manager_docker.py`.
- Abrir página: `Application.openDocument(absurl)` + `activeWindow().addView(page)`.
- Miniaturas: cada `.kra` guarda `preview.png` (pequena) e `mergedimage.png`
  (grande); o CPMT usa `preview.png` para a lista.
- CPMT lê camadas vetoriais chamadas `panels` (retângulos = frames) e `text`
  (textos) na exportação ACBF/EPUB; os nomes são configuráveis no diálogo de
  exportação.
- Templates de página do Krita (`templates/comics/BD-EuroTemplate.kra`):
  grupo `Page0` com `Mask clone-outline` (clone, multiply), `Ink`, `Color`,
  `Sketch` e a camada vetorial `Mask` (retângulos dos painéis), mais fundo
  branco fora do grupo. Estrutura replicada pelo gerador de páginas (com
  `panels` no lugar de `Mask` para o CPMT).

## Descobertas da v0.2

- **Gerador Pattern** (id `pattern`): a propriedade da tela é o nome do recurso
  (`pattern` = nome, ex.: `Stars_Sized.png`). O filtro Halftone aceita qualquer
  gerador de preenchimento como tela; o Krita traz 112 padrões (Stripes,
  Squares, Zigzag, Stars, hexacolBW...). Chave na config do filtro:
  `{mode}_generator_pattern_pattern`.
- **Meio-tom por canal**: modo `independent_channels` usa prefixos
  `{color_model_id}_channel{i}_` (i = 0..3), cada um com `generator`,
  `hardness`, `invert`, cores e a tela própria. Ângulos clássicos de impressão:
  ciano 15°, magenta 75°, amarelo 0°, preto 45° (evita moiré).
- **Posição do padrão**: o gerador Screentone guarda `position_x`/`position_y`
  (px), que deslocam a tela sem mover a camada (equivalente ao "mover padrão
  do tom" do CSP).
- **Preview de pincel**: os `.kpp` são PNGs 200×200 com o preview (a doc do
  Krita confirma); `Resource.image()` devolve essa imagem, usada nas
  miniaturas do módulo de pincéis. Pincéis MyPaint usam `<nome>_prev.png`.
- **Conjuntos de pincéis**: os presets do bundle Krita 4 têm prefixos por
  categoria (`c)` lápis, `d)` tintas, `f)`/`g)` bristles secos, `i)` molhados,
  `j)` aquarela, `y)` screentones...); a busca por nome (normalizado, sem
  pontuação) casa cada conjunto com o que está instalado.
- **Bibliotecas de símbolos**: SVG na pasta `symbols` dos recursos; cada
  símbolo é `<symbol id="...">` ou `<g id="...">`. O Krita 5.3.4 não expõe
  símbolos pela API Python, então o plugin faz a extração por XML
  (`xml.etree`) e insere via `addShapesFromSvg`, com viewBox calculada por
  `QSvgRenderer.boundsOnElement`. Bibliotecas que vêm com o Krita:
  `BalloonSymbols.svg` (8 balões, domínio público de Martin Owens e Tavmjong
  Bah) e `pepper_carrot_speech_bubbles.svg` (CC-BY-SA 4.0, David Revoy).
- **Bundles de pincel**: arquivos `.bundle` na pasta de recursos do Krita são
  carregados na inicialização; o instalador do plugin copia o arquivo e pede
  reinício.

## Decisões resultantes

- Cores dos presets são hex; o filtro/generador converte.
- A retícula usa `size_mode = 0` (resolução) com `resolution = DPI do documento`
  e `frequency = LPI`, dando células exatas `DPI / LPI` em pixels.
- Frequência limitada a `DPI / 2` (célula mínima de 2 px), evitando moiré e
  perda do ponto.
- O meio-tom usa `mode = intensity` e o mesmo preset da retícula com
  `brightness/contrast` suaves (50/50) conforme a recomendação da documentação
  do Screentone para uso com o filtro Halftone.