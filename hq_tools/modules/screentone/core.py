"""Núcleo do módulo de retículas e hachuras (sem dependência do Krita).

Reúne as constantes do gerador Screentone do Krita, o cálculo de LPI para
pixels e a montagem das configurações usadas em:

- camada de preenchimento com o gerador ``screentone``;
- máscara de filtro com o filtro ``halftone`` usando o gerador como tela.
"""

import json
import os

PATTERN_DOTS = 0
PATTERN_LINES = 1

DOT_SHAPES = [
    ("Redondo", 0),
    ("Elipse (legado)", 1),
    ("Losango", 2),
    ("Quadrado", 3),
    ("Elipse", 4),
]
LINE_SHAPES = [
    ("Reta", 0),
    ("Senoide", 1),
    ("Onda triangular", 2),
    ("Serra", 3),
    ("Cortina", 4),
]
INTERPOLATIONS = [
    ("Linear", 0),
    ("Sinusoidal", 1),
]
EQUALIZATIONS = [
    ("Nenhuma", 0),
    ("Por função", 1),
    ("Por template", 2),
]
UNITS = [
    ("Linhas por polegada (LPI)", 0),
    ("Linhas por centímetro (LPC)", 1),
]

SIZE_MODE_RESOLUTION = 0
SIZE_MODE_PIXEL = 1

GENERATOR_ID = "screentone"
PATTERN_GENERATOR_ID = "pattern"
HALFTONE_FILTER_NAMES = ("halftone", "krita_filter_halftone")

DEFAULT_PRESET = {
    "name": "Nova retícula",
    "pattern": PATTERN_DOTS,
    "shape": 0,
    "interpolation": 0,
    "equalization": 2,
    "lpi": 60.0,
    "units": 0,
    "rotation": 45.0,
    "align": True,
    "align_x": 1,
    "align_y": 1,
    "brightness": 50.0,
    "contrast": 95.0,
    "invert": False,
    "fg": "#000000",
    "bg": "#ffffff",
    "fg_opacity": 100,
    "bg_opacity": 100,
    "hardness": 80.0,
    "constrain_frequency": True,
}


def shapes_for_pattern(pattern):
    return LINE_SHAPES if int(pattern) == PATTERN_LINES else DOT_SHAPES


def lpi_to_cell_px(frequency, dpi):
    """Tamanho da célula da retícula em pixels: ``dpi / frequência``."""
    frequency = float(frequency or 0)
    if frequency <= 0:
        return 0.0
    return float(dpi) / frequency


def max_frequency(dpi):
    """Frequência máxima útil: célula de pelo menos 2 pixels."""
    return float(dpi) / 2.0


def clamp_frequency(frequency, dpi):
    frequency = float(frequency)
    limit = max_frequency(dpi)
    if frequency > limit:
        return limit
    if frequency < 1.0:
        return 1.0
    return frequency


def normalize_preset(preset):
    """Completa e converte os campos de um preset vindo de JSON."""
    result = dict(DEFAULT_PRESET)
    result.update(preset or {})
    result["pattern"] = int(result["pattern"])
    result["shape"] = int(result["shape"])
    result["interpolation"] = int(result["interpolation"])
    result["equalization"] = int(result["equalization"])
    result["lpi"] = float(result["lpi"])
    result["units"] = int(result["units"])
    result["rotation"] = float(result["rotation"])
    result["align"] = bool(result["align"])
    result["align_x"] = max(1, int(result["align_x"]))
    result["align_y"] = max(1, int(result["align_y"]))
    result["brightness"] = float(result["brightness"])
    result["contrast"] = float(result["contrast"])
    result["invert"] = bool(result["invert"])
    result["fg_opacity"] = int(result["fg_opacity"])
    result["bg_opacity"] = int(result["bg_opacity"])
    result["hardness"] = float(result["hardness"])
    result["constrain_frequency"] = bool(result["constrain_frequency"])
    return result


def screentone_properties(preset, dpi):
    """Propriedades do gerador Screentone para a camada de preenchimento."""
    preset = normalize_preset(preset)
    frequency = clamp_frequency(preset["lpi"], dpi)
    properties = {
        "pattern": preset["pattern"],
        "shape": preset["shape"],
        "interpolation": preset["interpolation"],
        "equalization_mode": preset["equalization"],
        "foreground_color": preset["fg"],
        "background_color": preset["bg"],
        "foreground_opacity": preset["fg_opacity"],
        "background_opacity": preset["bg_opacity"],
        "invert": preset["invert"],
        "brightness": preset["brightness"],
        "contrast": preset["contrast"],
        "size_mode": SIZE_MODE_RESOLUTION,
        "units": preset["units"],
        "resolution": float(dpi),
        "frequency_x": frequency,
        "frequency_y": frequency,
        "constrain_frequency": preset["constrain_frequency"],
        "position_x": 0.0,
        "position_y": 0.0,
        "keep_size_square": True,
        "shear_x": 0.0,
        "shear_y": 0.0,
        "rotation": preset["rotation"],
        "align_to_pixel_grid": preset["align"],
        "align_to_pixel_grid_x": preset["align_x"],
        "align_to_pixel_grid_y": preset["align_y"],
    }
    return properties


def halftone_properties(preset, color_model_id, dpi, mode="intensity",
                        generator=GENERATOR_ID, pattern_name=None):
    """Propriedades do filtro Halftone com um gerador como tela.

    O filtro guarda cada opção com prefixo do modo (``intensity_``, ``alpha_``)
    e as opções do gerador com o prefixo adicional ``generator_<id>_``. Com
    ``generator="pattern"`` e ``pattern_name``, a tela passa a ser um padrão
    instalado do Krita (estrelas, listras, quadrados...).
    """
    preset = normalize_preset(preset)
    prefix = "{0}_".format(mode)
    properties = {
        "color_model_id": color_model_id,
        "mode": mode,
        prefix + "generator": generator,
        prefix + "hardness": preset["hardness"],
        prefix + "invert": preset["invert"],
        prefix + "foreground_color": preset["fg"],
        prefix + "background_color": preset["bg"],
        prefix + "foreground_opacity": preset["fg_opacity"],
        prefix + "background_opacity": preset["bg_opacity"],
    }
    if generator == PATTERN_GENERATOR_ID:
        if pattern_name:
            properties[prefix + "generator_pattern_pattern"] = pattern_name
        return properties
    generator_prefix = prefix + "generator_{0}_".format(generator)
    for key, value in screentone_properties(preset, dpi).items():
        properties[generator_prefix + key] = value
    return properties


def halftone_cmyk_properties(preset, color_model_id, dpi, angles=(15.0, 75.0, 0.0, 45.0)):
    """Meio-tom colorido por canal (modo independent_channels do Halftone).

    Cada canal recebe a própria tela com um ângulo clássico de impressão:
    ciano 15°, magenta 75°, amarelo 0° e preto 45° (evita moiré).
    """
    preset = normalize_preset(preset)
    properties = {
        "color_model_id": color_model_id,
        "mode": "independent_channels",
    }
    for index, angle in enumerate(angles):
        channel_preset = dict(preset)
        channel_preset["rotation"] = float(angle)
        properties.update(
            halftone_properties(
                channel_preset, color_model_id, dpi,
                mode="{0}_channel{1}".format(color_model_id, index),
                generator=GENERATOR_ID,
            )
        )
    properties["mode"] = "independent_channels"
    properties["color_model_id"] = color_model_id
    return properties


def pattern_fill_properties(pattern_name):
    """Propriedades de uma camada de preenchimento com o gerador Pattern."""
    return {"pattern": str(pattern_name)}


TONE_FINGERPRINT_KEYS = (
    "pattern",
    "shape",
    "interpolation",
    "equalization_mode",
    "units",
    "frequency_x",
    "frequency_y",
    "rotation",
    "brightness",
    "contrast",
    "invert",
    "foreground_color",
    "background_color",
    "foreground_opacity",
    "background_opacity",
    "align_to_pixel_grid",
)


def tone_fingerprint(properties):
    """Identificador canônico das opções que definem uma retícula igual."""
    items = []
    for key in TONE_FINGERPRINT_KEYS:
        if key in properties:
            items.append((key, repr(properties[key])))
    return tuple(sorted(items))


def color_xml_to_hex(value):
    """Converte a cor vinda da API (XML de KoColor) em hex ``#rrggbb``.

    A API devolve cores de configuração como ``<color .../>``; o que já vier
    como hex passa direto.
    """
    if value is None:
        return None
    text = str(value).strip()
    if text.startswith("#"):
        return text[:7]
    if "<" not in text:
        return None
    try:
        import xml.etree.ElementTree as ET

        element = ET.fromstring(text)
    except (ET.ParseError, ValueError):
        return None
    red = element.get("r")
    green = element.get("g")
    blue = element.get("b")
    if red is None or green is None or blue is None:
        return None
    try:
        return "#{0:02x}{1:02x}{2:02x}".format(
            int(round(float(red))), int(round(float(green))), int(round(float(blue)))
        )
    except (TypeError, ValueError):
        return None


def load_presets(path):
    """Carrega uma lista de presets de um arquivo JSON."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("presets") or []
    presets = []
    for item in data:
        if isinstance(item, dict):
            presets.append(normalize_preset(item))
    return presets


def save_presets(path, presets):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {"presets": [normalize_preset(item) for item in presets]},
            handle,
            indent=2,
            ensure_ascii=False,
        )
