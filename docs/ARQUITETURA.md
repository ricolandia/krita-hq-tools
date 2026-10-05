# Arquitetura do HQ Tools

Plugin do Krita (Python) para produção de quadrinhos, com dez módulos
habilitáveis e um núcleo compartilhado. Alvo: Krita 5.3.4 (AppImage, PyQt5,
Python 3.13); o núcleo de compatibilidade prepara a migração para o Krita 6
(PyQt6).

## Estrutura

```
Krita-Comics-Plugin/
├── hq_tools/                    # pasta do plugin (pykrita)
│   ├── __init__.py              # importa plugin.py; falha sem críticas fora do Krita
│   ├── plugin.py                # Extension: registra dockers e ações de pincel
│   ├── hq_tools_manual.html     # manual mostrado no gerenciador de plugins
│   ├── core/                    # núcleo compartilhado
│   │   ├── compat.py            # PyQt5/PyQt6 e constantes de enum
│   │   ├── config.py            # config.json do usuário (caminho com pontos)
│   │   ├── paths.py             # pastas do plugin e do usuário
│   │   ├── krita_helpers.py     # documento/seleção/grupo/inserção/mensagens
│   │   ├── cpmt.py              # leitura/escrita do comicConfig.json
│   │   ├── gpl.py               # paletas GIMP (.gpl)
│   │   ├── thumbs.py            # miniaturas internas dos .kra
│   │   └── version.py           # __version__
│   ├── resources/               # kit do plugin
│   │   ├── fonts/               # 12 famílias OFL de HQ + licenças
│   │   ├── balloons-cc0/        # 2 balões de domínio público
│   │   ├── patterns/            # 11 padrões/texturas próprios (MIT)
│   │   └── brushes/             # packs da comunidade (Deevad, Vasco Basqué)
│   └── modules/
│       ├── screentone/          # retículas e hachuras (+ linhas de efeito)
│       ├── balloons/            # balões (+ botão do docker de símbolos do Krita)
│       ├── onomatopeias/        # onomatopeias
│       ├── palettes/            # paletas e templates
│       ├── pages/               # gerenciador de páginas
│       ├── brushes/             # slots de pincel com atalhos
│       └── biblioteca/          # biblioteca do projeto (balões, painéis, onomatopeias)
├── hq_tools.desktop             # registro do plugin
├── hq_tools.action              # atalhos das 16 ações de pincel
├── scripts/                     # install-dev, build-zip, snippets de validação
├── tests/                       # testes do núcleo (fora do Krita)
└── docs/                        # arquitetura, sintaxe, descoberta, validação
```

## Fluxo de dados

- Configuração em `~/.local/share/krita/hq_tools/config.json` (chaves por
  módulo, presets do usuário, pastas, slots de pincel). Escrita atômica
  (arquivo temporário + `os.replace`).
- Presets de retícula do usuário em `~/.local/share/krita/hq_tools/
  screentone_presets.json`; os de fábrica ficam no pacote
  (`modules/screentone/presets.json`).
- Balões: pasta configurável, padrão
  `~/.local/share/krita/hq_tools/balloons/`, com amostras copiadas na primeira
  execução.
- Paletas: templates `.gpl` no pacote; "Instalar no Krita" copia para
  `~/.local/share/krita/palettes/`.
- Páginas: o gerenciador lê `comicConfig.json` (lista `pages` de caminhos
  relativos, `pageNumber`); o gerador grava os `.kra` e registra as páginas.

## Como cada módulo usa a API do Krita

| Módulo | API usada |
|---|---|
| Retículas | `Document.createFillLayer` com o gerador `screentone`; `Filter` `halftone` + `Document.createFilterMask` (overloads por `Selection` e por `Node`); `InfoObject.setProperties`; `Selection.select` para seleção total; `Node.addChildNode` para posicionar dentro do grupo ativo |
| Balões | `Document.createVectorLayer` + `VectorLayer.addShapesFromSvg`; miniaturas com `QSvgRenderer` (PyQt5.QtSvg) |
| Paletas | `Krita.instance().resources("palette")`, `Palette`, `PaletteView`, `ManagedColor.fromQColor`, `View.setForeGroundColor`/`setBackGroundColor` |
| Páginas | `createDocument`, `createGroupLayer`, `createVectorLayer`, `createNode("paintlayer")`, `createCloneLayer`, `createFillLayer("color")` para o fundo; `Document.saveAs`; `openDocument` + `Window.addView` |
| Pincéis | `Krita.instance().resources("preset")`, `View.activateResource`, ações de `Window.createAction` com atalhos via `.action` |

## Convenções importantes

- `addChildNode(child, None)` insere no topo da pilha (o documento lista as
  camadas de baixo para cima). Por isso a ordem de criação dos filhos de uma
  página é: fundo branco, grupo, painéis, Sketch, Color, Ink, contorno, texto.
- `createFillLayer`/`createFilterMask` devolvem nós órfãos; a inserção é sempre
  explícita.
- Cores em configurações de filtro aceitam strings hex (`"#000000"`): o
  `KisPropertiesConfiguration::getColor` do Krita converte strings (QColor).
- A máscara de meio-tom usa a seleção ativa quando existir; sem seleção, usa o
  nó ativo como origem (initSelection por camada).
- Os módulos podem ser desligados em `config.json` (`modules.*`); a mudança
  exige reiniciar o Krita.

## Extensibilidade

Para adicionar um módulo:

1. criar `hq_tools/modules/<nome>/docker.py` com uma classe filha de `DockWidget`;
2. registrar em `plugin.py` um `DockWidgetFactory` atrás da chave
   `modules.<nome>` da configuração;
3. colocar a lógica pura em um módulo sem importar `krita` (testável com
   `python3 -m unittest`);
4. adicionar testes em `tests/`.

## Compatibilidade PyQt5/PyQt6

`core/compat.py` centraliza imports e constantes de enum (PyQt6 usa enums
escopados). O código dos módulos usa apenas os nomes reexportados ali. A
migração para o Krita 6 passa por: trocar o AppImage, testar cada docker e
ajustar pontos de enum que faltarem.

## Limitações conhecidas

- O texto importado de SVG pode chegar como shape e não como texto editável na
  5.3.4; ver `docs/VALIDACAO.md` (bloco 5) e, se necessário, ajustar as falas
  com a ferramenta de texto do Krita.
- Criar paletas novas pela API (`Palette(None)` + `save()`) não foi validado no
  Krita 5.3.4; por isso os templates são arquivos `.gpl` instalados na pasta de
  paletas.
- O gerador de páginas não desenha a forma do balão (só posiciona o texto); a
  forma entra pelo módulo de balões ou na mão.
- Exportação em lote e renomeação de páginas ficam no CPMT (fora do escopo).