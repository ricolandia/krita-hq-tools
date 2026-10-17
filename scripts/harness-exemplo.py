"""Exemplo de script para o ``scripts/harness-krita.sh``.

Mostra a convenção do harness: o repositório já está no ``sys.path``, o
caminho do log vem em ``HQ_HARNESS_LOG`` e o Krita é encerrado pelo próprio
harness (não chame ``quit``). Rode:

    scripts/harness-krita.sh scripts/harness-exemplo.py

Este exemplo monta o docker 3D e confere o manequim; para validadores de
verdade, ver ``scripts/validar-*.py``.
"""

import os

from hq_tools.core import paths
from hq_tools.modules.viewer3d.docker import Viewer3DDocker


def registrar(texto):
    with open(os.environ["HQ_HARNESS_LOG"], "a", encoding="utf-8") as arquivo:
        arquivo.write(texto + "\n")


paths.ensure_user_dirs()
docker = Viewer3DDocker()
registrar(
    "exemplo ok: modelo com %d ossos, %d vertices, %d faces"
    % (
        len(docker.modelo.ossos),
        len(docker.modelo.vertices),
        len(docker.modelo.faces),
    )
)
