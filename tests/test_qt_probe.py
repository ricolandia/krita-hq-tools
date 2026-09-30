"""Escolha do binding de Qt, testada sem PyQt instalado.

O teste que importa :mod:`hq_tools.core.compat` não roda nesta máquina (não há
PyQt5 nem PyQt6), então a decisão foi puxada para ``qt_probe`` e testada aqui
com as dependências injetadas.
"""

import sys
import types
import unittest

from hq_tools.core import qt_probe


class _KritaModulo(types.ModuleType):
    pass


class TestEscolhaDeQt(unittest.TestCase):
    def setUp(self):
        sys.modules.pop("krita", None)

    def tearDown(self):
        sys.modules.pop("krita", None)

    def instalar_krita(self, versao):
        modulo = _KritaModulo("krita")
        if versao is not None:
            modulo.QT_VERSION = versao
        sys.modules["krita"] = modulo

    def test_o_krita_manda(self):
        self.instalar_krita("5")
        self.assertEqual(qt_probe.escolher(), 5)
        self.instalar_krita("6")
        self.assertEqual(qt_probe.escolher(), 6)
        # 5.15.2 e "6.0.0" são strings, não inteiros.
        self.instalar_krita("5.15.2")
        self.assertEqual(qt_probe.escolher(), 5)
        self.instalar_krita("6.0.0")
        self.assertEqual(qt_probe.escolher(), 6)

    def test_krita_ignora_versao_invalida(self):
        self.instalar_krita("desconhecido")
        self.assertIsNone(qt_probe.versao_do_krita())

    def test_sem_krita_usa_o_que_esta_no_processo(self):
        # Isto aqui é o caso dos testes e scripts: com PyQt5 já importado,
        # fixar PyQt6 criava widgets de um Qt que o processo não usa.
        self.assertEqual(qt_probe.escolher(versao_krita=None, no_processo=5), 5)
        self.assertEqual(qt_probe.escolher(versao_krita=None, no_processo=6), 6)

    def test_o_que_esta_no_processo_ganha_do_que_esta_instalado(self):
        self.assertEqual(
            qt_probe.escolher(versao_krita=None, no_processo=5, disponivel=6), 5
        )

    def test_krita_ganha_do_que_esta_no_processo(self):
        # Krita 5 com PyQt6 instalado por fora (pip, outra distro): o
        # processo manda, senão o Krita cai ao abrir o docker.
        self.assertEqual(
            qt_probe.escolher(versao_krita=5, no_processo=6, disponivel=6), 5
        )

    def test_sem_nada_instalado_usa_pyqt6(self):
        self.assertEqual(
            qt_probe.escolher(versao_krita=None, no_processo=None, disponivel=5), 5
        )
        self.assertEqual(
            qt_probe.escolher(versao_krita=None, no_processo=None, disponivel=6), 6
        )
        self.assertEqual(
            qt_probe.escolher(versao_krita=None, no_processo=None, disponivel=None), 6
        )


if __name__ == "__main__":
    unittest.main()
