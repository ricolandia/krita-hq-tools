"""Conjuntos de pincéis sugeridos, montados com presets que o Krita já traz.

Cada conjunto é uma lista de "pistas" de nome (pedaços do nome original do
preset, ex.: ``Pencil-1``). Na hora de montar a interface, cada pista procura
o primeiro preset instalado cujo nome, normalizado, contenha a pista.
"""

import re

# Oito slots (2 fileiras de 4) para a doca não ficar comprida; o plugin cria um
# atalho por slot em Configurar Krita > Atalhos. Configurações antigas com mais
# slots são truncadas na leitura.
SLOT_COUNT = 8
PER_SET = 4

BRUSH_SETS = (
    (
        "Rascunho",
        ("Pencil-1", "Pencil-2", "Pencil-3", "Pencil-5", "Sketching-1",
         "Charcoal Pencil Medium", "Sketching-3"),
    ),
    (
        "Contornos",
        ("Ink-1", "Ink-2", "Ink-3", "Ink-4", "Ink-7", "Ink-8", "Marker Chisel"),
    ),
    (
        "Aquarela/Guache",
        ("Watercolor Fringe", "Watercolor Texture", "Waterpaint Hard",
         "Waterpaint Soft", "Wet Bristles", "Wet Paint", "Wet Textured Soft",
         "Wet Circle"),
    ),
    (
        "Acrílico/Óleo",
        ("Bristles-1", "Bristles-2", "Bristles-3", "Bristles-4", "Bristles-5",
         "Dry Bristles", "Dry Brushing", "Wet Knife"),
    ),
    (
        "Retículas",
        ("Screentone",),
    ),
)


def normalize(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def match_preset(installed_names, hint):
    """Primeiro preset instalado cujo nome contém a pista normalizada."""
    wanted = normalize(hint)
    if not wanted:
        return ""
    for name in installed_names:
        if wanted in normalize(name):
            return name
    return ""


def suggest_sets(installed_names):
    """Mapeia cada conjunto para a lista de presets instalados encontrados."""
    installed_names = list(installed_names)
    result = []
    for label, hints in BRUSH_SETS:
        matched = []
        for hint in hints:
            preset = match_preset(installed_names, hint)
            if preset:
                matched.append(preset)
        result.append((label, matched))
    return result


def slot_suggestions(installed_names, per_set=PER_SET):
    """16 sugestões de slots: os primeiros ``per_set`` de cada conjunto."""
    suggestions = []
    for label, matched in suggest_sets(installed_names):
        suggestions.extend(matched[:per_set])
    suggestions = suggestions[:SLOT_COUNT]
    while len(suggestions) < SLOT_COUNT:
        suggestions.append("")
    return suggestions