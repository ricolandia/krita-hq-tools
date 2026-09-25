"""Extração de miniaturas internas dos arquivos ``.kra``.

Todo ``.kra`` guarda ``preview.png`` (miniatura) e ``mergedimage.png`` (imagem
final). O preview é pequeno e suficiente para a grade do gerenciador.
"""

import os
import zipfile

from .compat import KEEP_ASPECT, QImage, QPixmap, SMOOTH_TRANSFORMATION

PREVIEW_NAMES = ("preview.png", "mergedimage.png")


def preview_bytes(kra_path):
    """Devolve os bytes do preview embutido, ou ``None``."""
    if not os.path.isfile(kra_path):
        return None
    try:
        with zipfile.ZipFile(kra_path) as archive:
            names = set(archive.namelist())
            for candidate in PREVIEW_NAMES:
                if candidate in names:
                    return archive.read(candidate)
    except (OSError, zipfile.BadZipFile, KeyError):
        return None
    return None


def thumbnail_pixmap(kra_path, size=160):
    """Devolve um ``QPixmap`` com a miniatura da página, ou ``None``."""
    data = preview_bytes(kra_path)
    if not data:
        return None
    image = QImage.fromData(data)
    if image.isNull():
        return None
    pixmap = QPixmap.fromImage(image)
    return pixmap.scaled(size, size, KEEP_ASPECT, SMOOTH_TRANSFORMATION)
