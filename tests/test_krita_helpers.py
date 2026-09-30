"""Testes dos utilitários de Krita que não dependem do Krita de verdade.

``krita_helpers`` importa ``krita`` e o ``compat`` (que precisa de Qt) no topo,
então este arquivo instala um ``krita`` falso e usa o Qt falso de
``tests/qt_falso.py``, instalado em ``tests/__init__.py``.
"""

import sys
import types
import unittest

import qt_falso


class DocumentoFalso:
    def __init__(self, com_macro=True):
        self.com_macro = com_macro
        self.macros = []
        self.fim = 0

    def beginMacro(self, nome):
        if not self.com_macro:
            raise RuntimeError("sem macro")
        self.macros.append(nome)

    def endMacro(self):
        self.fim += 1


def importar_helpers():
    qt_falso.instalar()
    if "krita" not in sys.modules:
        modulo = types.ModuleType("krita")
        modulo.Krita = type("K", (), {"instance": staticmethod(lambda: None)})
        modulo.Selection = object
        modulo.InfoObject = object
        sys.modules["krita"] = modulo
    for nome in list(sys.modules):
        if nome.startswith("hq_tools"):
            del sys.modules[nome]
    import hq_tools.core.krita_helpers as helpers

    return helpers


class TestMacro(unittest.TestCase):
    def setUp(self):
        self.helpers = importar_helpers()

    def tearDown(self):
        sys.modules.pop("krita", None)

    def test_encerra_a_macro_mesmo_com_erro(self):
        document = DocumentoFalso()

        def explode():
            raise ValueError("deu ruim")

        with self.assertRaises(ValueError):
            self.helpers.run_in_macro(document, explode)
        # Macro aberta no histórico trava o Ctrl+Z do autor até o fim da
        # sessão, então o endMacro não pode ficar depois da chamada.
        self.assertEqual(document.macros, ["explode"])
        self.assertEqual(document.fim, 1)

    def test_usa_o_nome_da_funcao(self):
        document = DocumentoFalso()
        self.helpers.run_in_macro(document, lambda: None)
        self.assertEqual(document.macros, ["<lambda>"])

    def test_sem_documento_executa_direto(self):
        self.assertEqual(self.helpers.run_in_macro(None, lambda: "ok"), "ok")

    def test_documento_sem_macro_nao_derruba(self):
        # Krita mais velho ou documento já fechado: executa e avisa, em vez de
        # perder a ação.
        document = DocumentoFalso(com_macro=False)
        self.assertEqual(self.helpers.run_in_macro(document, lambda: "ok"), "ok")
        self.assertEqual(document.fim, 0)

    def test_end_macro_que_falha_nao_mascara_o_erro_da_acao(self):
        class Ruim(DocumentoFalso):
            def endMacro(self):
                raise RuntimeError("fim de macro falhou")

        def explode():
            raise ValueError("deu ruim")

        with self.assertRaises(ValueError):
            self.helpers.run_in_macro(Ruim(), explode)


class TestCursorEspera(unittest.TestCase):
    def setUp(self):
        self.helpers = importar_helpers()
        self.app = self.helpers.QtWidgets.QApplication
        self.app.pilha[:] = []

    def tearDown(self):
        self.app.pilha[:] = []
        sys.modules.pop("krita", None)

    def test_roda_a_acao(self):
        with self.helpers.cursor_espera():
            self.assertEqual(1, 1)

    def test_desativa_passa_direto(self):
        with self.helpers.cursor_espera(ativo=False):
            self.assertEqual([], self.app.pilha)

    def test_marca_e_desmarca_o_cursor(self):
        with self.helpers.cursor_espera():
            self.assertEqual(1, len(self.app.pilha))
        self.assertEqual([], self.app.pilha)

    def test_nao_trava_quando_a_acao_erra(self):
        # Sem o finally, o cursor de espera ficava ligado e o Krita inteiro
        # continuava travado até reiniciar.
        with self.assertRaises(ValueError):
            with self.helpers.cursor_espera():
                raise ValueError("deu ruim")
        self.assertEqual([], self.app.pilha)


class TestLeituraDeTexto(unittest.TestCase):
    def setUp(self):
        self.helpers = importar_helpers()
        import os
        import tempfile

        self.pasta = tempfile.mkdtemp(prefix="hq_tools_helpers_")
        self.os = os

    def tearDown(self):
        import shutil

        shutil.rmtree(self.pasta, ignore_errors=True)
        sys.modules.pop("krita", None)

    def escrever(self, nome, dados):
        caminho = self.os.path.join(self.pasta, nome)
        with open(caminho, "wb") as handle:
            handle.write(dados)
        return caminho

    def test_aceita_utf8(self):
        caminho = self.escrever("a.svg", "<svg>ção</svg>".encode("utf-8"))
        self.assertEqual(self.helpers.read_text_file(caminho), "<svg>ção</svg>")

    def test_tira_o_bom_do_utf8_sig(self):
        caminho = self.escrever("b.svg", b"\xef\xbb\xbf<svg/>")
        self.assertEqual(self.helpers.read_text_file(caminho), "<svg/>")

    def test_le_latin1_em_vez_de_estourar(self):
        # SVG exportado por editor antigo: byte solto não pode virar erro de
        # leitura, que antes impedia o autor de usar o próprio kit.
        caminho = self.escrever("c.svg", b"<svg>caf\xe9</svg>")
        self.assertIn("caf", self.helpers.read_text_file(caminho))

    def test_arquivo_inexistente_levanta_oserror(self):
        with self.assertRaises(OSError):
            self.helpers.read_text_file(self.os.path.join(self.pasta, "nao-existe"))


if __name__ == "__main__":
    unittest.main()
