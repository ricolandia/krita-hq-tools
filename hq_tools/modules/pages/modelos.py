"""Modelos de página padrão do HQ Tools (specs puras, sem Krita).

Cada modelo tem nome, formato e um layout de painéis: painel único com
margem, grade (2x2 ou 3x3) ou tira de N painéis. A geração dos ``.kra``
acontece dentro do Krita (reusa o generator); aqui ficam só as specs
testáveis.
"""

from . import roteiro

MODELOS = (
    ("A4 padrão", "A4", "unico"),
    ("A3", "A3", "unico"),
    ("Tirinha 1 tira", "tirinha", "tira1"),
    ("Tirinha 2 tiras", "tirinha", "tira2"),
    ("Tirinha 3 tiras", "tirinha", "tira3"),
    ("Grade 2x2", "A4", "grade2x2"),
    ("Grade 3x3", "A4", "grade3x3"),
)

PAINEL_UNICO = [(0.05, 0.05, 0.9, 0.9)]


def layout_paineis(chave):
    """Painéis (frações) de um layout nomeado; None para o único padrão."""
    if chave == "unico":
        return list(PAINEL_UNICO)
    if chave.startswith("tira"):
        return roteiro.build_strip_panels(int(chave[4:]))
    if chave == "grade2x2":
        return roteiro.build_panels(2, 2, 0.05, 0.02)
    if chave == "grade3x3":
        return roteiro.build_panels(3, 3, 0.05, 0.02)
    return list(PAINEL_UNICO)


def slug(nome):
    import unicodedata
    import re as _re

    texto = unicodedata.normalize("NFKD", str(nome))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = _re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")
    return texto or "modelo"


def nome_por_slug():
    """Mapa slug -> nome amigável dos modelos padrão."""
    return {slug(nome): nome for nome, _, _ in MODELOS}