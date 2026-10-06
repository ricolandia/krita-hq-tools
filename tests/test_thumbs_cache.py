"""Testes do cache de miniaturas dos ``.kra``.

O ``QPixmap`` vem do Qt, então o teste instala o falso de ``tests/qt_falso.py``
e cobre a parte que decide: a chave (mtime/tamanho), o descarte do limite, a
leitura do zip e a devolução do mesmo objeto na segunda chamada.
"""

import os
import shutil
import sys
import tempfile
import unittest
import zipfile

try:  # do repositório (unittest discover, pytest ou arquivo direto)
    from tests import qt_falso
    from tests.qt_falso import instalar as instalar_qt
except ImportError:  # rodando de dentro de tests/: python3 test_x.py
    import qt_falso
    from qt_falso import instalar as instalar_qt


def instalar_thumbs():
    """Qt falso + hq_tools.core.thumbs recién importado com ele."""
    restaurar = instalar_qt()
    from hq_tools.core import thumbs

    assert sys.modules["hq_tools.core.compat"].QPixmap is qt_falso.QPixmap, (
        "o compat não pegou o Qt falso; o teste ia passar ou falhar por acaso"
    )
    return thumbs, restaurar


def kra_com_preview(caminho, conteudo=b"png-de-mentira", nome="preview.png"):
    with zipfile.ZipFile(caminho, "w") as archive:
        archive.writestr(nome, conteudo)
    return caminho


class TestCacheDeMiniaturas(unittest.TestCase):
    def setUp(self):
        self.thumbs, restaurar = instalar_thumbs()
        self.pasta = tempfile.mkdtemp(prefix="hq_tools_thumbs_")
        self.abertos = []
        real = zipfile.ZipFile

        def contando(*args, **kwargs):
            modo = args[1] if len(args) > 1 else kwargs.get("mode", "r")
            if modo == "r":  # as fixtures também abrem zip, em modo escrita
                self.abertos.append(args[0])
            return real(*args, **kwargs)

        zipfile.ZipFile = contando

        def restaurar_zip():
            zipfile.ZipFile = real

        self.addCleanup(restaurar_zip)
        self.addCleanup(restaurar)
        self.addCleanup(shutil.rmtree, self.pasta, True)
        self.addCleanup(self.thumbs.limpar_cache)

    def test_le_o_preview_do_zip(self):
        caminho = kra_com_preview(os.path.join(self.pasta, "a.kra"))
        self.assertEqual(self.thumbs.preview_bytes(caminho), b"png-de-mentira")

    def test_segunda_leitura_nao_abre_o_zip(self):
        caminho = kra_com_preview(os.path.join(self.pasta, "b.kra"))
        self.thumbs.preview_bytes(caminho)
        self.thumbs.preview_bytes(caminho)
        self.assertEqual(len(self.abertos), 1)

    def test_salvar_de_novo_invalida(self):
        # O ponto do mtime na chave: o autor salva a página e a miniatura da
        # grade precisa mudar, sem ninguém pedir para limpar nada.
        caminho = kra_com_preview(os.path.join(self.pasta, "c.kra"), b"antigo")
        self.assertEqual(self.thumbs.preview_bytes(caminho), b"antigo")
        kra_com_preview(caminho, b"novo")
        self.assertEqual(self.thumbs.preview_bytes(caminho), b"novo")

    def test_cache_ignorado_para_ler_sempre(self):
        caminho = kra_com_preview(os.path.join(self.pasta, "d.kra"))
        self.thumbs.preview_bytes(caminho)
        self.thumbs.preview_bytes(caminho, usar_cache=False)
        self.assertEqual(len(self.abertos), 2)

    def test_pixmap_tambem_e_memoizado(self):
        caminho = kra_com_preview(os.path.join(self.pasta, "e.kra"))
        primeiro = self.thumbs.thumbnail_pixmap(caminho)
        segundo = self.thumbs.thumbnail_pixmap(caminho)
        self.assertIs(primeiro, segundo)
        self.assertEqual(len(self.abertos), 1)

    def test_tamanhos_diferentes_sao_entradas_separadas(self):
        caminho = kra_com_preview(os.path.join(self.pasta, "f.kra"))
        self.assertIsNot(
            self.thumbs.thumbnail_pixmap(caminho, size=160),
            self.thumbs.thumbnail_pixmap(caminho, size=320),
        )

    def test_limite_descarta_as_mais_antigas(self):
        self.thumbs._LIMITE = 3
        caminhos = []
        for indice in range(5):
            caminho = kra_com_preview(
                os.path.join(self.pasta, "g{0}.kra".format(indice))
            )
            caminhos.append(caminho)
            self.thumbs.preview_bytes(caminho)
        self.assertEqual(len(self.thumbs._bytes), 3)
        # A mais antiga foi descartada: pedir de novo reabre o zip (5 leituras
        # iniciais + 1 releitura).
        self.thumbs.preview_bytes(caminhos[0])
        self.assertEqual(len(self.abertos), 6)

    def test_zip_corrompido_nao_levanta(self):
        caminho = os.path.join(self.pasta, "ruim.kra")
        with open(caminho, "wb") as handle:
            handle.write(b"nao e zip")
        self.assertIsNone(self.thumbs.preview_bytes(caminho))
        self.assertIsNone(self.thumbs.thumbnail_pixmap(caminho))

    def test_arquivo_inexistente(self):
        self.assertIsNone(self.thumbs.preview_bytes(os.path.join(self.pasta, "nao.existe.kra")))

    def test_usa_mergedimage_quando_falta_preview(self):
        caminho = os.path.join(self.pasta, "h.kra")
        with zipfile.ZipFile(caminho, "w") as archive:
            archive.writestr("mergedimage.png", b"final")
        self.assertEqual(self.thumbs.preview_bytes(caminho), b"final")

    def test_zip_sem_preview(self):
        caminho = os.path.join(self.pasta, "i.kra")
        with zipfile.ZipFile(caminho, "w") as archive:
            archive.writestr("mainwindow.xml", "<xml/>")
        self.assertIsNone(self.thumbs.preview_bytes(caminho))


if __name__ == "__main__":
    unittest.main()
