"""Leitura das bibliotecas de símbolos do Krita (SVG), sem dependência de Qt.

O Krita carrega bibliotecas de símbolos de arquivos SVG na pasta ``symbols``
dos recursos. Cada símbolo é um elemento ``<symbol id="...">`` ou um grupo
``<g id="...">``. Este módulo lista e extrai esses elementos para inserção
no documento como camada vetorial.
"""

import xml.etree.ElementTree as ET

SVG_NAMESPACE = "http://www.w3.org/2000/svg"

SKIP_IDS = {"svg", "defs", "title", "desc", "metadata", "namedview", "script", "style"}


def _local_name(tag):
    if tag is None:
        return ""
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.split("}", 1)[1]
    return str(tag)


def list_symbols(svg_text):
    """Lista os símbolos de um SVG: ``[{"id", "kind", "title"}]``."""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return []
    results = []
    for element in root.iter():
        element_id = element.get("id")
        if not element_id:
            continue
        if _local_name(element.tag) not in ("symbol", "g"):
            continue
        if element_id in SKIP_IDS or element_id.endswith("_transform"):
            continue
        title = element_id
        for child in element.iter():
            if _local_name(child.tag) == "title" and child.text and child.text.strip():
                title = child.text.strip()
                break
        results.append({"id": element_id, "kind": _local_name(element.tag), "title": title})
    return results


def _svg_element(root, element_id):
    for element in root.iter():
        if element.get("id") == element_id:
            return element
    return None


def extract_symbol_svg(svg_text, element_id, view_box=None):
    """Gera um SVG pequeno com o conteúdo do símbolo (para addShapesFromSvg).

    O elemento de origem vira um ``<g>``; o ``<defs>`` do arquivo original é
    preservado para manter estilos e gradientes. ``view_box`` opcional
    (``"x y w h"``) limita a janela ao símbolo, calculada em tempo de execução
    por ``QSvgRenderer.boundsOnElement``.
    """
    root = ET.fromstring(svg_text)
    target = _svg_element(root, element_id)
    if target is None:
        raise ValueError("Símbolo não encontrado: {0}".format(element_id))

    ET.register_namespace("", SVG_NAMESPACE)
    defs = None
    for element in root:
        if _local_name(element.tag) == "defs":
            defs = element
            break
    container = ET.Element(
        "{0}svg".format(SVG_NAMESPACE), {"xmlns": SVG_NAMESPACE}
    )
    if view_box:
        container.set("viewBox", view_box)
    if defs is not None:
        container.append(defs)
    group = ET.SubElement(container, "{0}g".format(SVG_NAMESPACE))
    group.set("id", element_id)
    for child in list(target):
        group.append(child)
    return ET.tostring(container, encoding="unicode")


def symbols_folder():
    """Pasta de símbolos do usuário, onde o Krita procura as bibliotecas."""
    import os

    return os.path.join(os.path.expanduser("~"), ".local", "share", "krita", "symbols")


def list_libraries(folder=None):
    """Devolve ``{arquivo: [símbolos]}`` para cada SVG da pasta de símbolos."""
    import os

    folder = folder or symbols_folder()
    libraries = {}
    if not os.path.isdir(folder):
        return libraries
    for name in sorted(os.listdir(folder)):
        if not name.lower().endswith(".svg"):
            continue
        path = os.path.join(folder, name)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                symbols = list_symbols(handle.read())
        except (OSError, ValueError):
            continue
        if symbols:
            libraries[name] = {"path": path, "symbols": symbols}
    return libraries