"""Testes do registro do plugin (rodam fora do Krita, com um ``krita`` falso).

O ponto é o isolamento entre módulos: um erro em um docker não pode impedir
os outros de aparecer, porque a versão anterior importava tudo dentro de um
bloco só e qualquer exceção derrubava o plugin inteiro.
"""

import importlib
import sys
import types
import unittest

try:  # do repositório (unittest discover, pytest ou arquivo direto)
    from tests import qt_falso
except ImportError:  # rodando de dentro de tests/: python3 test_x.py
    import qt_falso


class _Sinal:
    def connect(self, *args, **kwargs):
        pass


class _Acao:
    triggered = _Sinal()


class _Janela:
    def __init__(self):
        self.acoes = []

    def createAction(self, nome, texto, caminho):
        self.acoes.append((nome, texto, caminho))
        return _Acao()


class _Krita:
    def __init__(self):
        self.fabricas = []
        self.extensoes = []

    def instance(self):
        return self

    def addDockWidgetFactory(self, fabrica):
        self.fabricas.append(fabrica)

    def addExtension(self, extensao):
        self.extensoes.append(extensao)

    def activeDocument(self):
        return None


class _No:
    pass


class _Extension:
    def __init__(self, parent=None):
        self.parent = parent


class _FabricaBase:
    class DockRight:
        pass


def instalar_stub():
    """Registra um módulo ``krita`` mínimo em ``sys.modules``."""
    modulo = types.ModuleType("krita")
    instancia = _Krita()
    modulo.QT_VERSION = "5"
    modulo.Krita = instancia
    modulo.DockWidget = _No
    modulo.DockWidgetFactory = lambda nome, lado, tipo: (nome, lado, tipo)
    modulo.DockWidgetFactoryBase = _FabricaBase
    modulo.Extension = _Extension
    modulo.InfoObject = object
    modulo.Selection = object
    sys.modules["krita"] = modulo
    return instancia


class TestRegistroDoPlugin(unittest.TestCase):
    def setUp(self):
        self.instancia = instalar_stub()
        # Antes do recarregamento: o compat escolhe o PyQt na importação, e sem
        # o falso o plugin não importa na máquina de CI.
        qt_falso.instalar()
        # Recarrega o pacote a cada teste: hq_tools/__init__.py importa o
        # plugin, que registra a extensão no import, então o estado do registro
        # vive em sys.modules.
        for nome in list(sys.modules):
            if nome == "hq_tools" or nome.startswith("hq_tools."):
                del sys.modules[nome]

    def tearDown(self):
        for nome in list(sys.modules):
            if nome == "hq_tools" or nome.startswith("hq_tools."):
                del sys.modules[nome]
        # O krita falso não pode vazar: outros testes (qt_probe) descobrem a
        # versão do Qt por ele e passariam a achar que o processo é um Krita 5.
        sys.modules.pop("krita", None)

    def carregar(self):
        """Importa o plugin e roda ``setup`` como o Krita faria."""
        modulo = importlib.import_module("hq_tools.plugin")
        for extensao in self.instancia.extensoes:
            extensao.setup()
        return modulo


    def test_registra_os_modulos(self):
        modulo = self.carregar()
        self.assertEqual(len(self.instancia.fabricas), 12)
        self.assertEqual(len(self.instancia.extensoes), 1)
        self.assertEqual(modulo.HQTools.__name__, "HQTools")

    def test_modulo_quebrado_nao_derruba_os_outros(self):
        modulo = importlib.import_module("hq_tools.plugin")
        # Um caminho de import inexistente simula o arquivo do módulo com erro:
        # a versão anterior parava no primeiro e não registrava nenhum.
        quebrado = (
            ("screentone", "hq_tools_screentone", "ScreentoneDocker", "x.que.nao.existe"),
        ) + tuple(m for m in modulo.MODULOS if m[0] != "screentone")
        modulo.MODULOS = quebrado
        extension = self.instancia.extensoes[0]
        extension.setup()
        ids = [fabrica[0] for fabrica in self.instancia.fabricas]
        self.assertEqual(len(ids), 11)
        self.assertNotIn("hq_tools_screentone", ids)
        self.assertIn("hq_tools_pages", ids)
        self.assertIn("hq_tools_brushes", ids)
        self.assertEqual(
            [nome for nome, _ in extension.modulos_com_erro], ["screentone"]
        )

    def test_modulo_desabilitado_nao_e_registrado(self):
        self.carregar()
        # Desliga pelo objeto de configuração já construído: o que está em
        # teste é o registro, e o arquivo em disco é coberto por
        # tests/test_data_integrity.py. Escrever um config de teste exigiria
        # trocar CONFIG_PATH antes de qualquer import de hq_tools (o
        # __init__.py importa o plugin, que já cria a extensão na importação).
        extension = self.instancia.extensoes[0]
        extension.config.data["modules"]["pages"] = False
        self.instancia.fabricas = []
        extension.setup()
        ids = [fabrica[0] for fabrica in self.instancia.fabricas]
        self.assertEqual(len(ids), 11)
        self.assertNotIn("hq_tools_pages", ids)

    def test_atalhos_criam_as_oito_acoes(self):
        modulo = self.carregar()
        janela = _Janela()
        self.instancia.extensoes[0].createActions(janela)
        self.assertEqual(len(janela.acoes), 8)
        self.assertEqual(janela.acoes[0][0], "hq_tools_brush_1")
        self.assertEqual(janela.acoes[-1][0], "hq_tools_brush_8")

    def test_atalhos_somem_quando_pinceis_desligado(self):
        self.carregar()
        extension = self.instancia.extensoes[0]
        extension.config.data["modules"]["brushes"] = False
        janela = _Janela()
        extension.createActions(janela)
        self.assertEqual(janela.acoes, [])


if __name__ == "__main__":
    unittest.main()
