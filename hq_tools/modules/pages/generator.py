"""Geração de páginas ``.kra`` a partir do roteiro, integrada ao CPMT.

Cada página vira um documento em 300 dpi (configurável) com a mesma estrutura
dos templates de HQ do Krita: grupo da página, camada vetorial ``panels`` com os
retângulos dos painéis, camadas Sketch/Color/Ink, contorno multiplicado e uma
camada ``text`` com as falas e narrações. As camadas ``panels`` e ``text`` são
lidas pelo CPMT na exportação ACBF/EPUB.
"""

import os

from krita import Krita

from ...core import krita_helpers as helpers
from . import roteiro


def _escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _panels_svg(page, width_px, height_px, dpi):
    scale = 72.0 / float(dpi)
    width_pt = width_px * scale
    height_pt = height_px * scale
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0:.4f}pt" '
        'height="{1:.4f}pt" viewBox="0 0 {0:.4f} {1:.4f}">'.format(
            width_pt, height_pt
        )
    ]
    for x, y, w, h in page["panels"]:
        parts.append(
            '<rect x="{0:.4f}" y="{1:.4f}" width="{2:.4f}" height="{3:.4f}" '
            'fill="#ffffff" stroke="#000000" stroke-width="2"/>'.format(
                x * width_pt, y * height_pt, w * width_pt, h * height_pt
            )
        )
    parts.append("</svg>")
    return "".join(parts)


def _text_svg(page, width_px, height_px, dpi):
    if not page["balloons"]:
        return ""
    scale = 72.0 / float(dpi)
    width_pt = width_px * scale
    height_pt = height_px * scale
    format_name = page.get("format", roteiro.DEFAULT_FORMAT)
    width_mm = roteiro.FORMATS.get(format_name, roteiro.FORMATS["A4"])[0]
    font_pt = max(8.0, width_mm * 0.055)
    line_height = font_pt * 1.25
    font_px = font_pt / scale

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0:.4f}pt" '
        'height="{1:.4f}pt" viewBox="0 0 {0:.4f} {1:.4f}">'.format(
            width_pt, height_pt
        )
    ]

    for balloon in page["balloons"]:
        index = balloon["panel"] - 1
        if index < 0 or index >= len(page["panels"]):
            continue
        x, y, w, h = page["panels"][index]
        panel_x = x * width_px
        panel_y = y * height_px
        panel_w = w * width_px
        panel_h = h * height_px
        wrapped = roteiro.wrap_text(
            balloon["text"], max(6, int(panel_w * 0.8 / (font_px * 0.55)))
        )
        if balloon["kind"] == "narracao":
            text_x = panel_x + panel_w * 0.08
            text_y = panel_y + panel_h * 0.16
            anchor = "start"
        else:
            text_x = panel_x + panel_w * 0.5
            text_y = panel_y + panel_h * 0.42
            anchor = "middle"
        x_pt = text_x * scale
        y_pt = text_y * scale
        parts.append(
            '<text x="{0:.4f}" y="{1:.4f}" font-family="sans-serif" '
            'font-size="{2:.4f}" text-anchor="{3}" fill="#000000">'.format(
                x_pt, y_pt, font_pt, anchor
            )
        )
        for line_index, line in enumerate(wrapped):
            dy = 0.0 if line_index == 0 else line_height
            parts.append(
                '<tspan x="{0:.4f}" dy="{1:.4f}">{2}</tspan>'.format(
                    x_pt, dy, _escape(line)
                )
            )
        parts.append("</text>")

    parts.append("</svg>")
    return "".join(parts)


def _build_document(page, title, panel_svg, text_svg, width_px, height_px, dpi):
    document = Krita.instance().createDocument(
        width_px, height_px, title, "RGBA", "U8", "sRGB built-in", float(dpi)
    )
    if document is None:
        raise RuntimeError("Não foi possível criar o documento da página.")

    root = document.rootNode()
    selection = helpers.full_selection(document)

    background = document.createFillLayer(
        "Background", "color", helpers.make_info_object({"color": "#ffffff"}), selection
    )
    if background is not None:
        root.addChildNode(background, None)
        background.setLocked(True)

    group = document.createGroupLayer("Page{0:02d}".format(page["index"]))
    if group is None:
        raise RuntimeError("Não foi possível criar o grupo da página.")
    root.addChildNode(group, None)

    panels = document.createVectorLayer("panels")
    if panels is None:
        raise RuntimeError("Não foi possível criar a camada de painéis.")
    group.addChildNode(panels, None)
    panels.addShapesFromSvg(panel_svg)

    for name in ("Sketch", "Color", "Ink"):
        layer = document.createNode(name, "paintlayer")
        if layer is not None:
            group.addChildNode(layer, None)

    outline = document.createCloneLayer("panels contorno", panels)
    if outline is not None:
        outline.setBlendingMode("multiply")
        group.addChildNode(outline, None)

    if text_svg:
        text_layer = document.createVectorLayer("text")
        if text_layer is not None:
            text_layer.addShapesFromSvg(text_svg)
            group.addChildNode(text_layer, None)

    document.refreshProjection()
    return document


def _save_document(document, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not document.saveAs(path):
        raise RuntimeError("Não foi possível salvar {0}".format(path))
    document.setModified(False)
    document.close()


def generate(script_text, target_dir=None, project=None, format_override=None,
             dpi_override=None, name_prefix="pagina"):
    """Gera as páginas do roteiro.

    ``project`` é um ``CPMTProject`` opcional: quando informado, as páginas são
    criadas dentro do projeto e registradas no ``comicsConfig.json``.
    """
    pages = roteiro.parse_script(script_text)
    created = []
    relatives = []

    for page in pages:
        dpi = float(dpi_override or page["dpi"])
        width_px, height_px = roteiro.page_pixels(page, format_override, dpi)
        panel_svg = _panels_svg(page, width_px, height_px, dpi)
        text_svg = _text_svg(page, width_px, height_px, dpi)

        if project is not None:
            filename = project.next_page_name(offset=len(created) + 1)
            path = os.path.join(project.pages_dir(), filename)
            if project.pages_location:
                relatives.append(os.path.join(project.pages_location, filename))
            else:
                relatives.append(filename)
            title = "{0} - pagina {1}".format(project.project_name, page["index"])
        else:
            if not target_dir:
                raise ValueError("Informe uma pasta de destino ou um projeto CPMT.")
            os.makedirs(target_dir, exist_ok=True)
            filename = "{0}_{1:03d}.kra".format(name_prefix, len(created) + 1)
            path = os.path.join(target_dir, filename)
            title = "{0} - pagina {1}".format(name_prefix, page["index"])

        document = _build_document(
            page, title, panel_svg, text_svg, width_px, height_px, dpi
        )
        _save_document(document, path)
        created.append(path)

    if project is not None and relatives:
        project.register_pages(relatives)
    return created


# API pública estável (usada pelo docker de páginas): os nomes privados
# históricos continuam como aliases para não quebrar importações externas.
panels_svg = _panels_svg
text_svg = _text_svg
build_page_document = _build_document
save_page = _save_document
