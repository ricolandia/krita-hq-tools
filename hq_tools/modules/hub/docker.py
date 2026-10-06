"""Docker de hub: central de abertura e fechamento dos módulos.

Um botão por módulo: clicar abre a doca; clicar de novo fecha, e o botão fica
marcado enquanto a doca está visível. A opção "Fechar o atual ao abrir outro"
torna a abertura exclusiva (um módulo por vez); desmarcada, as dockas vão
convivendo. O estado de cada botão acompanha o ``visibilityChanged`` da doca,
então fechar pelo X do Krita também desmarca.
"""

from krita import DockWidget

from ...core import krita_helpers as helpers
from ...core import registro, ui
from ...core import i18n
from ...core.compat import QtWidgets
from ...core.config import Config

ROTULOS = {
    "screentone": "Retículas",
    "balloons": "Balões",
    "onomatopeias": "Onomatopeias",
    "palettes": "Paletas",
    "pages": "Páginas",
    "biblioteca": "Biblioteca",
    "brushes": "Pincéis",
    "viewer3d": "3D",
    "perspectiva": "Perspectiva",
    "moodboard": "Moodboard",
    "producao": "Produção",
}


def _lista_de_modulos():
    """(chave, rótulo) dos módulos registráveis, na ordem do plugin."""
    try:
        from ...plugin import MODULOS
    except ImportError:  # pragma: no cover - fora do Krita
        return []
    return [
        (chave, i18n.t(ROTULOS.get(chave, chave)))
        for chave, _, _, _ in MODULOS
        if chave != "hub"
    ]


class HubDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: hub'))
        self.config = Config()
        self._botoes = {}
        self._build_ui()
        for docker in registro.instancias().values():
            self._conectar(docker)
        registro.ao_registrar(self._ao_registrar)
        self._atualizar_botoes()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)
        layout.addWidget(ui.rotulo(
            i18n.t('Abra e feche os módulos do HQ Tools por aqui. O botão fica marcado enquanto a doca está aberta; clicar de novo fecha.')
        ))
        grade = ui.espacamento(widgets.QGridLayout(), margem=0)
        for indice, (chave, rotulo) in enumerate(_lista_de_modulos()):
            botao = ui.botao(
                rotulo,
                i18n.t('Abre ou fecha o docker {0}.').format(rotulo),
            )
            botao.setCheckable(True)
            botao.clicked.connect(
                lambda marcado=False, chave=chave: self._alternar(chave)
            )
            self._botoes[chave] = botao
            grade.addWidget(botao, indice // 2, indice % 2)
        layout.addLayout(grade)
        self.chk_fechar = widgets.QCheckBox(i18n.t('Fechar o atual ao abrir outro'))
        self.chk_fechar.setToolTip(
            i18n.t('Marcado, abrir um módulo fecha os outros; desmarcado, eles vão abrindo juntos.')
        )
        self.chk_fechar.setChecked(bool(self.config.get("hub.fechar_ao_abrir", False)))
        self.chk_fechar.toggled.connect(
            lambda marcado: self.config.set("hub.fechar_ao_abrir", bool(marcado))
        )
        layout.addWidget(self.chk_fechar)
        layout.addWidget(ui.rotulo(
            i18n.t('Módulo desligado nas configurações não carrega, e o botão fica desabilitado.')
        ))
        layout.addStretch(1)
        self.setWidget(main)

    def _ao_registrar(self, chave, docker):
        if chave in self._botoes:
            self._conectar(docker)
            self._atualizar_botoes()

    def _conectar(self, docker):
        sinal = getattr(docker, "visibilityChanged", None)
        if sinal is None:
            return
        try:
            sinal.connect(self._atualizar_botoes)
        except (AttributeError, RuntimeError, TypeError):
            pass

    @staticmethod
    def _visivel(docker):
        try:
            return bool(docker.isVisible())
        except (AttributeError, RuntimeError):
            return False

    def _atualizar_botoes(self, *args):
        for chave, botao in self._botoes.items():
            docker = registro.obter(chave)
            botao.setEnabled(docker is not None)
            if docker is None:
                botao.setChecked(False)
                botao.setToolTip(
                    i18n.t('O módulo não está carregado (desligado nas configurações ou com erro no import).')
                )
                continue
            botao.setChecked(self._visivel(docker))

    def _alternar(self, chave):
        docker = registro.obter(chave)
        if docker is None:
            helpers.show_message(
                i18n.t('Módulo indisponível; confira as configurações do HQ Tools.')
            )
            self._atualizar_botoes()
            return
        if self._visivel(docker):
            try:
                docker.close()
            except (AttributeError, RuntimeError):
                pass
        else:
            if self.chk_fechar.isChecked():
                for outra_chave, outro in registro.instancias().items():
                    if outra_chave != chave and self._visivel(outro):
                        try:
                            outro.close()
                        except (AttributeError, RuntimeError):
                            pass
            try:
                docker.show()
                docker.raise_()
            except (AttributeError, RuntimeError):
                helpers.show_message(i18n.t('Não foi possível abrir o módulo.'))
        self._atualizar_botoes()
