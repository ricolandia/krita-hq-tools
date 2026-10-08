"""Parser da sintaxe de roteiro do HQ Tools, sem dependência do Krita.

Sintaxe (uma página por bloco, palavras-chave sem acento e sem maiúsculas):

    # comentário
    pagina 1
    formato A4
    dpi 300
    layout grade2x2
    direcao ltr
    margem 5%
    sarjeta 2%
    fala p1: primeira fala do painel 1
    fala p1 joao: fala do painel 1 dita pelo Joao (personagem opcional)
    narracao p1: texto de narração do painel 1

Layouts aceitos: ``quadro``, ``splash``, ``duplo-h``, ``duplo-v``,
``grade2x2``, ``grade3x2``, ``grade2x3``, ``tira3``, ``tira4``,
``gradeRxC`` (ex.: ``grade3x3``) ou ``RxC`` (ex.: ``3x2``), até 6 em cada
eixo.
"""

import re

from ...core import i18n

FORMATS = {
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "A3": (297.0, 420.0),
    "tirinha": (297.0, 210.0),
    "americano": (168.0, 259.0),
    "tankobon": (128.0, 182.0),
    "quadrado": (210.0, 210.0),
}

LAYOUTS = {
    "quadro": (1, 1),
    "splash": (1, 1),
    "duplo-h": (1, 2),
    "duplo-v": (2, 1),
    "grade2x2": (2, 2),
    "grade3x2": (3, 2),
    "grade2x3": (2, 3),
    "tira3": (3, 1),
    "tira4": (4, 1),
}

DEFAULT_FORMAT = "A4"
DEFAULT_DPI = 300
DEFAULT_LAYOUT = "grade2x2"
DEFAULT_MARGIN = 0.05
DEFAULT_GUTTER = 0.02
DEFAULT_DIRECTION = "ltr"

BALLOON_PATTERN = re.compile(
    r"^(fala|narracao|narração|legenda)\s+p?(\d+)\s*(?:([^:]+?)\s*)?:\s*(.*)$",
    re.IGNORECASE,
)
PLANO_PATTERN = re.compile(r"^plano\s+p?(\d+)\s*:?\s*(.*)$", re.IGNORECASE)
LAYOUT_PATTERN = re.compile(r"^(\d+)\s*[x×]\s*(\d+)$")


class RoteiroError(ValueError):
    """Erro de sintaxe com a linha do roteiro."""


def new_page():
    return {
        "index": 0,
        "format": DEFAULT_FORMAT,
        "dpi": DEFAULT_DPI,
        "layout": DEFAULT_LAYOUT,
        "direction": DEFAULT_DIRECTION,
        "margin": DEFAULT_MARGIN,
        "gutter": DEFAULT_GUTTER,
        "balloon_lines": [],
        "planos": {},
    }


def parse_fraction(value):
    text = str(value).strip().replace("%", "")
    number = float(text.replace(",", "."))
    if number > 1.0:
        number /= 100.0
    return max(0.0, min(0.45, number))


def parse_layout(value):
    key = str(value).strip().lower()
    if key in LAYOUTS:
        return LAYOUTS[key]
    # O prefixo "grade" é opcional: grade3x3, grade 4x2 e 3x2 valem igual.
    sem_grade = key[5:].strip() if key.startswith("grade") else key
    match = LAYOUT_PATTERN.match(sem_grade)
    if match:
        rows = max(1, min(6, int(match.group(1))))
        cols = max(1, min(6, int(match.group(2))))
        return (rows, cols)
    raise RoteiroError(
        i18n.t(
            "Layout desconhecido: {0}. Use gradeRxC (ex.: grade3x3), LxC (ex.: 3x2) "
            "ou um nome: quadro, splash, duplo-h, duplo-v, tira3, tira4."
        ).format(value)
    )


def parse_direction(value):
    key = str(value).strip().lower()
    if key in ("rtl", "manga", "japones", "japonês"):
        return "rtl"
    return "ltr"


def parse_script(text):
    """Converte o texto do roteiro em uma lista de páginas prontas para gerar."""
    pages = []
    current = None
    for line_number, raw in enumerate(str(text).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lower = line.lower()

        if lower.startswith("pagina") or lower.startswith("página"):
            current = new_page()
            pages.append(current)
            continue

        if current is None:
            current = new_page()
            pages.append(current)

        if lower.startswith("formato"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[7:].strip()
            for name in FORMATS:
                if name.lower() == value.lower():
                    current["format"] = name
                    break
            else:
                raise RoteiroError(
                    i18n.t("Linha {0}: formato desconhecido '{1}'.").format(line_number, value)
                )
        elif lower.startswith("dpi"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[3:].strip()
            try:
                current["dpi"] = max(72, min(1200, int(float(value))))
            except ValueError:
                raise RoteiroError(i18n.t("Linha {0}: DPI inválido.").format(line_number))
        elif lower.startswith("layout"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[6:].strip()
            try:
                current["layout"] = "{0}x{1}".format(*parse_layout(value))
            except RoteiroError:
                raise RoteiroError(
                    i18n.t("Linha {0}: layout desconhecido '{1}'.").format(line_number, value)
                )
        elif lower.startswith("direcao") or lower.startswith("direção"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[7:].strip()
            current["direction"] = parse_direction(value)
        elif lower.startswith("margem"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[6:].strip()
            current["margin"] = parse_fraction(value)
        elif lower.startswith("sarjeta"):
            value = line.split(":", 1)[-1].strip() if ":" in line else line[7:].strip()
            current["gutter"] = parse_fraction(value)
        elif lower.startswith("plano"):
            match = PLANO_PATTERN.match(line)
            if match is None:
                raise RoteiroError(
                    i18n.t("Linha {0}: plano sem o número do painel: {1}.").format(
                        line_number, line
                    )
                )
            valor = match.group(2).strip()
            if not valor:
                raise RoteiroError(
                    i18n.t("Linha {0}: plano sem valor: {1}.").format(line_number, line)
                )
            current["planos"][int(match.group(1))] = valor
        else:
            match = BALLOON_PATTERN.match(line)
            if match:
                kind = match.group(1).lower()
                if kind in ("narracao", "narração", "legenda"):
                    kind = "narracao"
                current["balloon_lines"].append(
                    {
                        "kind": kind,
                        "panel": int(match.group(2)),
                        "character": (match.group(3) or "").strip(),
                        "text": match.group(4).strip(),
                    }
                )
            else:
                raise RoteiroError(
                    i18n.t("Linha {0}: comando não reconhecido: {1}").format(line_number, line)
                )

    for position, page in enumerate(pages, 1):
        page["index"] = position
        finalize_page(page)
    return pages


def finalize_page(page):
    rows, cols = parse_layout(page["layout"])
    page["rows"] = rows
    page["cols"] = cols
    page["panels"] = build_panels(
        rows, cols, page["margin"], page["gutter"], page["direction"]
    )
    total = len(page["panels"])
    balloons = []
    for entry in page["balloon_lines"]:
        index = entry["panel"]
        if index < 1 or index > total:
            raise RoteiroError(
                i18n.t("Página {0}: fala aponta para o painel {1}, mas há {2} painéis.").format(
                    page["index"], index, total
                )
            )
        balloons.append(
            {
                "kind": entry["kind"],
                "panel": index,
                "character": entry.get("character", ""),
                "text": entry["text"],
            }
        )
    page["balloons"] = balloons
    planos = {}
    for index, valor in page["planos"].items():
        if index < 1 or index > total:
            raise RoteiroError(
                i18n.t("Página {0}: plano aponta para o painel {1}, mas há {2} painéis.").format(
                    page["index"], index, total
                )
            )
        planos[index] = valor
    page["planos"] = planos
    return page


def build_panels(rows, cols, margin, gutter, direction="ltr"):
    """Calcula retângulos normalizados (0 a 1) na ordem de leitura."""
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    margin = max(0.0, float(margin))
    gutter = max(0.0, float(gutter))

    available_w = 1.0 - 2.0 * margin
    available_h = 1.0 - 2.0 * margin
    cell_w = max(0.0, (available_w - (cols - 1) * gutter) / cols)
    cell_h = max(0.0, (available_h - (rows - 1) * gutter) / rows)

    panels = []
    for row in range(rows):
        columns = list(range(cols))
        if direction == "rtl":
            columns = list(reversed(columns))
        for column in columns:
            x = margin + column * (cell_w + gutter)
            y = margin + row * (cell_h + gutter)
            panels.append((x, y, cell_w, cell_h))
    return panels


def page_pixels(page, format_override=None, dpi_override=None):
    """Dimensões da página em pixels."""
    name = format_override or page["format"]
    width_mm, height_mm = FORMATS.get(name, FORMATS[DEFAULT_FORMAT])
    dpi = float(dpi_override or page["dpi"])
    width = int(round(width_mm * dpi / 25.4))
    height = int(round(height_mm * dpi / 25.4))
    return width, height


def build_strip_panels(count, margin=DEFAULT_MARGIN, gutter=DEFAULT_GUTTER):
    """Painéis de tirinha: ``count`` retângulos iguais numa linha horizontal."""
    count = max(1, min(8, int(count)))
    margin = max(0.0, float(margin))
    gutter = max(0.0, float(gutter))
    available_w = 1.0 - 2.0 * margin
    panel_w = max(0.0, (available_w - (count - 1) * gutter) / count)
    panel_h = 1.0 - 2.0 * margin
    return [
        (margin + index * (panel_w + gutter), margin, panel_w, panel_h)
        for index in range(count)
    ]


def wrap_text(text, max_chars):
    """Quebra o texto em linhas de até ``max_chars`` caracteres."""
    max_chars = max(4, int(max_chars))
    words = str(text).split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = "{0} {1}".format(current, word)
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
