"""Leitura e escrita de paletas no formato GIMP (``.gpl``), usado pelo Krita."""

import os
import tempfile


def parse_gpl(text):
    """Converte o texto de um ``.gpl`` em dicionário com nome e cores."""
    palette = {"name": "Paleta", "columns": 0, "colors": []}
    if not text:
        return palette
    lines = text.splitlines()
    if not lines or "GIMP Palette" not in lines[0]:
        raise ValueError("Arquivo não é uma paleta GIMP (.gpl)")
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.lower().startswith("name:"):
            palette["name"] = stripped.split(":", 1)[1].strip()
            continue
        if stripped.lower().startswith("columns:"):
            try:
                palette["columns"] = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                palette["columns"] = 0
            continue
        parts = stripped.split(None, 3)
        if len(parts) < 3:
            continue
        try:
            red, green, blue = (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            continue
        name = parts[3].strip() if len(parts) > 3 else ""
        palette["colors"].append(
            {"rgb": (red, green, blue), "name": name}
        )
    return palette


def write_gpl(palette):
    """Gera o texto de uma paleta ``.gpl`` a partir do dicionário."""
    name = palette.get("name") or "Paleta"
    colors = palette.get("colors") or []
    columns = palette.get("columns") or min(max(len(colors), 1), 10)
    lines = ["GIMP Palette", "Name: {0}".format(name), "Columns: {0}".format(columns)]
    for color in colors:
        red, green, blue = color["rgb"]
        label = color.get("name") or ""
        lines.append(
            "{0:3d} {1:3d} {2:3d}\t{3}".format(int(red), int(green), int(blue), label)
        )
    return "\n".join(lines) + "\n"


def load_gpl(path):
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return parse_gpl(handle.read())


def save_gpl(path, palette):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=directory, delete=False
    )
    try:
        with handle:
            handle.write(write_gpl(palette))
        os.replace(handle.name, path)
    except OSError:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
