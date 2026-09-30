"""Snippets de descoberta/validação para rodar no Scripter do Krita.

Uso: abra o Krita 5.3.4 (AppImage), vá em Ferramentas > Scripts > Scripter,
cole um bloco por vez (Ctrl+Enter para executar) e guarde as saídas. O roteiro
de validação completo está em docs/VALIDACAO.md.

Os blocos não alteram arquivos do usuário; o bloco 6 cria um documento novo
(não salvo) e o 7 cria uma paleta em memória.
"""

# 1. Identificação do ambiente
def bloco_1():
    from krita import Krita
    instance = Krita.instance()
    print("Versão do Krita:", instance.version())
    print("Filtros com 'halftone':", [f for f in instance.filters() if "halftone" in f.lower()])
    print("Tipo do recurso 'preset' (amostra):", sorted(list((instance.resources("preset") or {}).keys()))[:5])
    print("Paletas (amostra):", sorted(list((instance.resources("palette") or {}).keys()))[:5])


# 2. Config real de uma camada de preenchimento Screentone criada na mão
#    Crie uma camada de preenchimento > Screentone na interface, selecione-a
#    e rode:
def bloco_2():
    from krita import Krita
    node = Krita.instance().activeDocument().activeNode()
    print("Tipo:", node.type())
    print("Gerador:", node.generatorName())
    print("Config:", node.filterConfig().properties())


# 3. Config real de um filtro Halftone configurado na interface
#    Aplique Filtros > Artísticos > Halftone em uma camada, com o gerador
#    Screentone escolhido, e rode:
def bloco_3():
    from krita import Krita
    node = Krita.instance().activeDocument().activeNode()
    filters = node.childNodes()
    for child in filters:
        if child.type() == "filtermask":
            print("Máscara:", child.name())
            f = child.filter()
            print("Config:", f.configuration().properties())


# 4. Criação de camada de preenchimento por script
def bloco_4():
    from krita import InfoObject, Krita, Selection
    doc = Krita.instance().activeDocument()
    selection = Selection()
    selection.select(0, 0, doc.width(), doc.height(), 255)
    info = InfoObject()
    info.setProperties({
        "pattern": 0,
        "shape": 0,
        "equalization_mode": 2,
        "size_mode": 0,
        "units": 0,
        "resolution": doc.xRes(),
        "frequency_x": 60.0,
        "frequency_y": 60.0,
        "brightness": 50.0,
        "contrast": 95.0,
        "rotation": 45.0,
        "align_to_pixel_grid": True,
        "foreground_color": "#000000",
        "background_color": "#ffffff",
    })
    layer = doc.createFillLayer("Teste retícula", "screentone", info, selection)
    print("Camada criada:", layer is not None)
    if layer is not None:
        doc.rootNode().addChildNode(layer, None)
        doc.refreshProjection()


# 5. Texto vindo de SVG em camada vetorial
def bloco_5():
    from krita import Krita
    doc = Krita.instance().activeDocument()
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="200pt" height="100pt" '
        'viewBox="0 0 200 100">'
        '<rect x="10" y="10" width="180" height="80" fill="#ffffff" stroke="#000000" stroke-width="2"/>'
        '<text x="100" y="55" font-family="sans-serif" font-size="14" text-anchor="middle">Teste</text>'
        '</svg>'
    )
    layer = doc.createVectorLayer("Teste SVG")
    shapes = layer.addShapesFromSvg(svg)
    doc.rootNode().addChildNode(layer, None)
    doc.refreshProjection()
    print("Formas importadas:", [(shape.type(), shape.name()) for shape in shapes])


# 6. Seleção e máscara de filtro Halftone
def bloco_6():
    from krita import Krita
    doc = Krita.instance().activeDocument()
    halftone = Krita.instance().filter("halftone")
    print("Filtro:", halftone is not None)
    if halftone is None:
        return
    config = halftone.configuration()
    props = {
        "color_model_id": doc.colorModel(),
        "mode": "intensity",
        "intensity_generator": "screentone",
        "intensity_hardness": 80.0,
        "intensity_generator_screentone_pattern": 0,
        "intensity_generator_screentone_size_mode": 0,
        "intensity_generator_screentone_units": 0,
        "intensity_generator_screentone_resolution": doc.xRes(),
        "intensity_generator_screentone_frequency_x": 60.0,
        "intensity_generator_screentone_frequency_y": 60.0,
        "intensity_generator_screentone_brightness": 50.0,
        "intensity_generator_screentone_contrast": 50.0,
        "intensity_generator_screentone_rotation": 45.0,
    }
    config.setProperties(props)
    halftone.setConfiguration(config)
    node = doc.activeNode()
    mask = doc.createFilterMask("Teste meio-tom", halftone, node)
    node.addChildNode(mask, None)
    doc.refreshProjection()
    print("Máscara criada:", mask is not None)


# 7. Paleta em memória (não salva)
def bloco_7():
    import importlib
    import os
    import sys
    # O binding do Qt muda entre Krita 5 e 6, então perguntar ao qt_probe do
    # plugin é o que evita o ImportError do PyQt5 fixo aqui.
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if raiz not in sys.path:
        sys.path.insert(0, raiz)
    from hq_tools.core.qt_probe import escolher
    qtgui = importlib.import_module(escolher() + ".QtGui")
    from krita import ManagedColor, Palette, Swatch
    QColor = qtgui.QColor
    palette = Palette(None)
    palette.addGroup("Teste")
    for name, hex_color in (("Preto", "#000000"), ("Cinza", "#808080"), ("Branco", "#ffffff")):
        swatch = Swatch()
        swatch.setName(name)
        swatch.setColor(ManagedColor.fromQColor(QColor(hex_color)))
        palette.addEntry(swatch, "Teste")
    print("Cores na paleta:", palette.colorsCountTotal())
