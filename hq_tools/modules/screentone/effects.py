"""Linhas de efeito e velocidade (estilo Clip Studio Paint), sem Krita.

Duas formas: linhas convergentes para um ponto de fuga (linhas de velocidade)
e linhas paralelas preenchendo uma região (linhas de efeito/chuva).
A saída é uma lista de segmentos com espessura própria, convertida em SVG.
"""

import math


def _ray_circle(cx, cy, angle, inner, outer):
    """Segmento de uma reta radial entre dois raios, centrada em (cx, cy)."""
    x1 = cx + math.cos(angle) * inner
    y1 = cy + math.sin(angle) * inner
    x2 = cx + math.cos(angle) * outer
    y2 = cy + math.sin(angle) * outer
    return x1, y1, x2, y2


def effect_lines_focus(width, height, cx, cy, count, inset=0.12, thickness=2.0,
                       jitter=0.35, outer=1.15):
    """Linhas radiais saindo de um foco até além das bordas do documento.

    ``cx``/``cy`` em pixels; ``inset`` é a fração da distância máxima que as
    linhas começam longe do foco (0 = todas passam pelo centro); ``jitter``
    varia a espessura entre linhas para um traço menos mecânico.
    """
    count = max(2, int(count))
    thickness = max(0.2, float(thickness))
    jitter = max(0.0, min(1.0, float(jitter)))
    max_distance = math.hypot(width, height) * float(outer) / 2.0
    inner = max_distance * max(0.0, min(0.9, float(inset)))

    lines = []
    for index in range(count):
        angle = 2.0 * math.pi * index / count
        x1, y1, x2, y2 = _ray_circle(cx, cy, angle, inner, max_distance)
        factor = 1.0 - jitter / 2.0 + jitter * float(index % 2)
        lines.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "width": thickness * factor,
            }
        )
    return lines


def _rect_line_bounds(x0, y0, dx, dy, rect_x, rect_y, rect_w, rect_h):
    """Intervalo de t para a reta ``(x0,y0)+t*(dx,dy)`` cruzando o retângulo."""
    epsilon = 1e-9
    t_min = float("-inf")
    t_max = float("inf")

    if abs(dx) < epsilon:
        if not (rect_x - epsilon <= x0 <= rect_x + rect_w + epsilon):
            return None
    elif dx > 0:
        t_min = max(t_min, (rect_x - x0) / dx)
        t_max = min(t_max, (rect_x + rect_w - x0) / dx)
    else:
        t_min = max(t_min, (rect_x + rect_w - x0) / dx)
        t_max = min(t_max, (rect_x - x0) / dx)

    if abs(dy) < epsilon:
        if not (rect_y - epsilon <= y0 <= rect_y + rect_h + epsilon):
            return None
    elif dy > 0:
        t_min = max(t_min, (rect_y - y0) / dy)
        t_max = min(t_max, (rect_y + rect_h - y0) / dy)
    else:
        t_min = max(t_min, (rect_y + rect_h - y0) / dy)
        t_max = min(t_max, (rect_y - y0) / dy)

    if t_min > t_max:
        return None
    return t_min, t_max


def effect_lines_parallel(width, height, x, y, w, h, spacing, angle_deg=0.0,
                          thickness=2.0):
    """Linhas paralelas preenchendo a região (x, y, w, h), em pixels.

    ``angle_deg`` orienta as linhas; ``spacing`` é o espaçamento entre elas.
    """
    spacing = max(1.0, float(spacing))
    thickness = max(0.2, float(thickness))
    angle = math.radians(float(angle_deg))
    dx = math.cos(angle)
    dy = math.sin(angle)
    nx = -dy
    ny = dx

    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    projections = [corner_x * nx + corner_y * ny for corner_x, corner_y in corners]
    start = min(projections)
    end = max(projections)

    lines = []
    offset = start
    while offset <= end + 0.5:
        x0 = nx * offset
        y0 = ny * offset
        bounds = _rect_line_bounds(x0, y0, dx, dy, x, y, w, h)
        if bounds is not None:
            t1, t2 = bounds
            lines.append(
                {
                    "x1": x0 + dx * t1,
                    "y1": y0 + dy * t1,
                    "x2": x0 + dx * t2,
                    "y2": y0 + dy * t2,
                    "width": thickness,
                }
            )
        offset += spacing
    return lines


def lines_to_svg(lines, width, height, dpi, color="#000000"):
    """Gera o SVG dos segmentos, com cada linha na própria espessura."""
    scale = 72.0 / float(dpi)
    width_pt = float(width) * scale
    height_pt = float(height) * scale
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0:.4f}pt" '
        'height="{1:.4f}pt" viewBox="0 0 {0:.4f} {1:.4f}">'.format(
            width_pt, height_pt
        )
    ]
    for line in lines:
        parts.append(
            '<line x1="{0:.2f}" y1="{1:.2f}" x2="{2:.2f}" y2="{3:.2f}" '
            'stroke="{4}" stroke-width="{5:.2f}" stroke-linecap="round"/>'.format(
                line["x1"] * scale,
                line["y1"] * scale,
                line["x2"] * scale,
                line["y2"] * scale,
                color,
                line["width"],
            )
        )
    parts.append("</svg>")
    return "".join(parts)