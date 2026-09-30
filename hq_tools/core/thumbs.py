"""Extração de miniaturas internas dos arquivos ``.kra``.

Todo ``.kra`` guarda ``preview.png`` (miniatura) e ``mergedimage.png`` (imagem
final). O preview é pequeno e suficiente para a grade do gerenciador.
"""

import collections
import os
import threading
import zipfile

from .compat import KEEP_ASPECT, QImage, QPixmap, SMOOTH_TRANSFORMATION

PREVIEW_NAMES = ("preview.png", "mergedimage.png")

# O gerenciador de páginas chama refresh() a cada troca de pasta, ordenação,
# criação e exclusão, e a grade pede uma miniatura por item. Sem cache, um
# projeto de 40 páginas abria 40 zips e decodificava 40 PNGs a cada refresh,
# tudo na thread da interface. A chave inclui mtime e tamanho, então salvar a
# página de novo invalida a entrada sozinho.
_LIMITE = 256
_bytes = collections.OrderedDict()
_pixmaps = collections.OrderedDict()
_trava = threading.Lock()


def _chave(kra_path):
    try:
        info = os.stat(kra_path)
    except OSError:
        return None
    return (os.path.abspath(kra_path), info.st_mtime_ns, info.st_size)


def _guardar(cache, chave, valor, limite):
    cache[chave] = valor
    cache.move_to_end(chave)
    while len(cache) > limite:
        cache.popitem(last=False)


def limpar_cache():
    """Esvazia os dois caches (usado nos testes e por quem quiser)."""
    with _trava:
        _bytes.clear()
        _pixmaps.clear()


def preview_bytes(kra_path, usar_cache=True):
    """Devolve os bytes do preview embutido, ou ``None``."""
    if not os.path.isfile(kra_path):
        return None
    chave = _chave(kra_path) if usar_cache else None
    if chave is not None:
        with _trava:
            dados = _bytes.get(chave)
            if dados is not None:
                _bytes.move_to_end(chave)
                return dados
    dados = None
    try:
        with zipfile.ZipFile(kra_path) as archive:
            names = set(archive.namelist())
            for candidate in PREVIEW_NAMES:
                if candidate in names:
                    dados = archive.read(candidate)
                    break
    except (OSError, zipfile.BadZipFile, KeyError):
        return None
    if dados is not None and chave is not None:
        with _trava:
            _guardar(_bytes, chave, dados, _LIMITE)
    return dados


def thumbnail_pixmap(kra_path, size=160):
    """Devolve um ``QPixmap`` com a miniatura da página, ou ``None``.

    O ``QPixmap`` também é memoizado: decodificar o PNG é a parte cara, e
    refazer o ``scaled`` a cada refresh gastaria o mesmo tempo.
    """
    chave = _chave(kra_path)
    if chave is not None:
        with _trava:
            chave_pixmap = chave + (size,)
            pixmap = _pixmaps.get(chave_pixmap)
            if pixmap is not None:
                _pixmaps.move_to_end(chave_pixmap)
                return pixmap
    data = preview_bytes(kra_path)
    if not data:
        return None
    image = QImage.fromData(data)
    if image.isNull():
        return None
    pixmap = QPixmap.fromImage(image).scaled(
        size, size, KEEP_ASPECT, SMOOTH_TRANSFORMATION
    )
    if chave is not None:
        with _trava:
            _guardar(_pixmaps, chave + (size,), pixmap, _LIMITE)
    return pixmap
