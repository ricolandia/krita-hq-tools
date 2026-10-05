"""Camada de idioma do plugin (PT-BR e EN).

O idioma sai do locale do sistema (o Krita segue o locale por padrão):
qualquer variante ``pt*`` usa português; o resto usa inglês. A variável de
ambiente ``HQ_TOOLS_IDIOMA`` (``pt`` ou ``en``) força um idioma, útil para
conferir as duas interfaces sem mexer no sistema.

As strings visíveis passam por :func:`t`; a chave é o próprio texto em
português e :data:`TRADUCOES` guarda a versão em inglês. Texto sem tradução
volta como está (a interface nunca quebra por falta de tradução), e o
``tests/test_i18n.py`` varre os dockers para exigir que toda string visível
tenha a sua entrada.
"""

import os

from .i18n_en import TRADUCOES

PT = "pt"
EN = "en"

_IDIOMA = None


def escolher_idioma(nome_locale):
    """``pt`` para qualquer variante de português; ``en`` para o resto."""
    if nome_locale is None:
        return EN
    return PT if str(nome_locale).strip().lower().startswith("pt") else EN


def _locale_do_sistema():
    try:
        from .compat import QtCore

        return QtCore.QLocale.system().name()
    except (ImportError, AttributeError, RuntimeError):
        return None


def idioma():
    global _IDIOMA
    if _IDIOMA is None:
        forcado = os.environ.get("HQ_TOOLS_IDIOMA", "").strip().lower()
        if forcado in (PT, EN):
            _IDIOMA = forcado
        else:
            _IDIOMA = escolher_idioma(_locale_do_sistema())
    return _IDIOMA


def definir_idioma(codigo):
    """Força o idioma (testes e conferência); ``None`` volta ao automático."""
    global _IDIOMA
    _IDIOMA = codigo


def t(texto):
    """Tradução da string visível; sem tradução, devolve o original."""
    if idioma() == PT:
        return texto
    return TRADUCOES.get(texto, texto)
