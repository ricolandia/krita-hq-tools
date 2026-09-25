"""HQ Tools: ferramentas de quadrinhos para o Krita.

O pacote registra a extensão em ``plugin.py``. O bloco ``try/except`` existe
para que os módulos de núcleo possam ser importados e testados fora do Krita
(por exemplo, em ``python3 -m unittest``).
"""

try:
    from .plugin import *  # noqa: F401,F403
except ImportError:
    pass
