"""Testes do cache de miniaturas dos ``.kra``.

O ``QPixmap`` vem do Qt, que não está instalado na máquina de teste. Estes
casos cobrem a parte que decide: a chave (mtime/tamanho), o descarte do limite
e a leitura do zip, com o ``QPixmap`` de mentira.
"""

import io
import os
import shutil
import sys
import tempfile
import types
import unittest
import zipfile


class _Pixmap:
    def __init__(self, nome):
        self.nome = nome

    def scaled(self, *args, **kwargs):
        return self

    def __repr__(self):
        return "Pixmap({0})".format(self.nome)


class _QImage:
    @staticmethod
    def fromData(data):
        return _QImage()

    def isNull(self):
        return False


class _MetaQt(type):
    """Enum do Qt falso: ``QImage.Format_RGBA8888`` precisa existir."""

    def __getattr__(cls, nome):
        return _Qualquer()


class _Qualquer(metaclass=_MetaQt):
    """Objeto que aceita qualquer atributo, para o PyQt falso."""

    def __getattr__(self, nome):
        return _Qualquer()

    def __call__(self, *args, **kwargs):
        return _Qualquer()

    def __repr__(self):
        return "<qt-falso>"


def instalar_qt_falso():
    """Registra PyQt5 e PyQt6 falsos, com QPixmap observável.

    ``compat`` importa PyQt de verdade no topo, então o jeito de testar a
    miniatura fora do Krita é dar a ele um Qt falso. O QPixmap precisa
    devolver objetos comparáveis, por isso sai do genérico.

    Os dois nomes são registrados porque ``qt_probe`` escolhe PyQt6 sempre que
    ele já estiver carregado no processo (é o que a suíte faz ao rodar outros
    testes antes): se só o PyQt5 fosse falso, o compat usaria o PyQt6 de
    verdade, leria bytes que não são PNG e devolveria None.
    """
    qtcore = types.ModuleType("QtCore")
    qtgui = types.ModuleType("QtGui")
    qtwidgets = types.ModuleType("QtWidgets")
    qtsvg = types.ModuleType("QtSvg")

    for modulo in (qtcore, qtgui, qtwidgets, qtsvg):
        modulo.__getattr__ = lambda nome: _Qualquer()

    class QPixmap(_Qualquer):
        def __init__(self, nome="imagem"):
            self.nome = nome

        def scaled(self, *args, **kwargs):
            return self

    class QImage(_Qualquer):
        @staticmethod
        def fromData(data):
            return QImage()

        def isNull(self):
            return False

    qtgui.QPixmap = QPixmap
    qtgui.QImage = QImage
    qtcore.QImage = QImage

    def limpar():
        for nome in list(sys.modules):
            if nome == "PyQt5" or nome == "PyQt6" or nome.startswith("PyQt5."):
                del sys.modules[nome]
            elif nome.startswith("PyQt6."):
                del sys.modules[nome]

    for raiz_nome in ("PyQt5", "PyQt6"):
        raiz = types.ModuleType(raiz_nome)
        raiz.__getattr__ = lambda nome: _Qualquer()
        raiz.QtCore = qtcore
        raiz.QtGui = qtgui
        raiz.QtWidgets = qtwidgets
        raiz.QtSvg = qtsvg
        sys.modules[raiz_nome] = raiz
        for parte, modulo in (
            ("QtCore", qtcore),
            ("QtGui", qtgui),
            ("QtWidgets", qtwidgets),
            ("QtSvg", qtsvg),
        ):
            sys.modules["{0}.{1}".format(raiz_nome, parte)] = modulo

    for nome in list(sys.modules):
        if nome.startswith("hq_tools"):
            del sys.modules[nome]
    import hq_tools.core.thumbs as thumbs

    assert sys.modules["hq_tools.core.compat"].QPixmap is QPixmap, (
        "o compat não pegou o Qt falso; o teste ia passar/failar por acaso"
    )
    return thumbs, limpar


def kra_com_preview(caminho, conteudo=b"png-de-mentira", nome="preview.png"):
    with zipfile.ZipFile(caminho, "w") as archive:
        archive.writestr(nome, conteudo)
    return caminho


class TestCacheDeMiniaturas(unittest.TestCase):
    def setUp(self):
        self.thumbs, restaurar = instalar_qt_falso()
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
