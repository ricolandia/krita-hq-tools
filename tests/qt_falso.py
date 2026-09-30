"""PyQt falso para testar o plugin fora do Krita.

O ``hq_tools.core.compat`` importa PyQt5 ou PyQt6 no topo, e eles não existem
na máquina de CI (e existem em qualidade variável na máquina do autor). Sem um
falso, o comportamento dos testes passa a depender do que estiver instalado: foi
o que fez o cache de miniaturas "passar" na máquina do autor e falhar no CI.

A escolha de binding é feita por ``qt_probe``: PyQt6 ganha quando já está
carregado no processo. Por isso o falso é registrado nos dois nomes, senão o
compat pega o PyQt de verdade e os bytes de teste viram uma imagem nula.
"""

import sys
import types


class _MetaQt(type):
    """Enum do Qt falso: ``QImage.Format_RGBA8888`` precisa existir."""

    def __getattr__(cls, nome):
        return _Qualquer()


class _Qualquer(metaclass=_MetaQt):
    """Objeto que aceita qualquer atributo e qualquer chamada."""

    def __getattr__(self, nome):
        return _Qualquer()

    def __call__(self, *args, **kwargs):
        return _Qualquer()

    def __mro_entries__(self, bases):
        # Os dockers do Krita herdam de ``DockWidget`` e companhia, que aqui
        # são o falso. O Python exige uma tupla neste ponto; sem isso, a classe
        # nem chega a ser criada ("__mro_entries__ must return a tuple").
        return ()

    def __bool__(self):
        return True

    def __repr__(self):
        return "<qt-falso>"


class QPixmap(_Qualquer):
    """Pixmap comparável, para o teste ver se o cache devolveu o mesmo objeto."""

    def __init__(self, nome="imagem"):
        self.nome = nome

    def scaled(self, *args, **kwargs):
        return self

    def __repr__(self):
        return "Pixmap({0})".format(self.nome)


class QImage(_Qualquer):
    """Imagem que sempre decodifica, para não depender de PNG de verdade."""

    @staticmethod
    def fromData(data):
        return QImage()

    def isNull(self):
        return False


class QApplication(_Qualquer):
    """QApplication falso que anota o cursor em uso.

    O ``cursor_espera`` mexe em ``QApplication.overrideCursor()``; sem este
    registro o teste não tem como provar que o cursor volta ao normal.
    """

    pilha = []

    @staticmethod
    def setOverrideCursor(cursor):
        QApplication.pilha.append(cursor)

    @staticmethod
    def restoreOverrideCursor():
        if QApplication.pilha:
            QApplication.pilha.pop()

    @staticmethod
    def overrideCursor():
        return QApplication.pilha[-1] if QApplication.pilha else None

    @staticmethod
    def instance():
        return QApplication()


_instalado = False


def instalar(sobrescrever=True):
    """Registra PyQt5/PyQt6 falsos e devolve a função de restauração.

    ``sobrescrever=False`` não mexe se já houver um PyQt de verdade no
    processo (é o que os testes que precisam de Qt real, como os do cursor de
    espera, preferem). Chamar duas vezes não empilha nenhuma troca: a segunda
    devolve uma restauração que não faz nada.
    """
    global _instalado
    if _instalado and not _tem_pyqt_real():
        def ja_instalado():
            pass

        return ja_instalado
    if not sobrescrever and _tem_pyqt_real():
        def deixar_como_esta():
            pass

        return deixar_como_esta

    qtcore = types.ModuleType("QtCore")
    qtgui = types.ModuleType("QtGui")
    qtwidgets = types.ModuleType("QtWidgets")
    qtsvg = types.ModuleType("QtSvg")
    for modulo in (qtcore, qtgui, qtwidgets, qtsvg):
        modulo.__getattr__ = lambda nome: _Qualquer()

    qtgui.QPixmap = QPixmap
    qtgui.QImage = QImage
    qtcore.QImage = QImage
    qtwidgets.QApplication = QApplication

    salvos = {
        nome: modulo
        for nome, modulo in sys.modules.items()
        if nome == "PyQt5" or nome == "PyQt6" or nome.startswith("PyQt5.") or nome.startswith("PyQt6.")
    }
    for raiz_nome in ("PyQt5", "PyQt6"):
        raiz = types.ModuleType(raiz_nome)
        raiz._hq_tools_falso = True
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

    def restaurar():
        global _instalado
        for nome in list(sys.modules):
            if (
                nome == "PyQt5"
                or nome == "PyQt6"
                or nome.startswith("PyQt5.")
                or nome.startswith("PyQt6.")
            ):
                del sys.modules[nome]
        sys.modules.update(salvos)
        limpar_hq_tools()
        _instalado = False

    _instalado = True
    return restaurar


def _tem_pyqt_real():
    """Diz se há um PyQt de verdade importado (e não o falso daqui)."""
    for nome in ("PyQt5", "PyQt6"):
        modulo = sys.modules.get(nome)
        if modulo is not None and not getattr(modulo, "_hq_tools_falso", False):
            return True
    try:
        import PyQt5  # noqa: F401
    except Exception:
        return False
    return True


def limpar_hq_tools():
    """Esquece o pacote, para o próximo import pegar o Qt escolhido agora."""
    for nome in list(sys.modules):
        if nome == "hq_tools" or nome.startswith("hq_tools."):
            del sys.modules[nome]
