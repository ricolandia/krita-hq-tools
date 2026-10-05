"""Docker de balões (com kit de HQ).

Catálogo de balões vetoriais em SVG: amostras do plugin na primeira execução
e uma pasta própria para os seus modelos. O botão "Símbolos do Krita" abre o
docker nativo "Bibliotecas de símbolos" para as bibliotecas instaladas.
Inclui também a instalação das fontes de HQ que acompanham o plugin.
"""

import os
import shutil
import subprocess
import sys

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    ICON_MODE,
    IMAGE_FORMAT_ARGB32,
    LIST_ADJUST,
    LIST_STATIC,
    QImage,
    QPixmap,
    QSvgRenderer,
    TRANSPARENT,
    USER_ROLE,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from ...core import registro, ui
from ...core import i18n
from ...core.paths import BALLOONS_DIR, FONTS_TARGET, mesma_copia

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
KIT_CC0_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "resources",
    "balloons-cc0",
)
KIT_FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "fonts"
)


def ensure_default_folder(config):
    """Define a pasta padrão de balões e copia as amostras na primeira execução.

    Tolera pasta inacessível: uma pasta configurada que não existe mais (HD
    externo desmontado, pasta renomeada) levantava ``OSError`` dentro do
    ``__init__`` e o docker não abria. Agora há aviso e a pasta padrão assume.
    """
    folder = config.get("balloons.folder") or BALLOONS_DIR
    try:
        os.makedirs(folder, exist_ok=True)
        if os.path.abspath(folder) == os.path.abspath(BALLOONS_DIR):
            if not any(name.lower().endswith(".svg") for name in os.listdir(folder)):
                for name in sorted(os.listdir(SAMPLES_DIR)):
                    if name.lower().endswith(".svg"):
                        shutil.copy2(
                            os.path.join(SAMPLES_DIR, name), os.path.join(folder, name)
                        )
                if os.path.isdir(KIT_CC0_DIR):
                    for name in sorted(os.listdir(KIT_CC0_DIR)):
                        if name.lower().endswith(".svg"):
                            shutil.copy2(
                                os.path.join(KIT_CC0_DIR, name),
                                os.path.join(folder, name),
                            )
    except OSError as erro:
        helpers.log("pasta de balões inacessível ({0}): {1}".format(folder, erro))
        if os.path.abspath(folder) != os.path.abspath(BALLOONS_DIR):
            try:
                os.makedirs(BALLOONS_DIR, exist_ok=True)
                folder = BALLOONS_DIR
            except OSError:
                pass
    return folder


def render_svg_thumbnail(path, size=120):
    """Renderiza um SVG em QPixmap para a lista; devolve None se indisponível."""
    if QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return None
    image = QImage(size, int(size * 0.75), IMAGE_FORMAT_ARGB32)
    image.fill(TRANSPARENT)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


class BalloonsDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: balões'))
        registro.registrar("balloons", self)
        self.config = Config()
        self.folder = ensure_default_folder(self.config)
        self._build_ui()
        self.refresh()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = ui.rotulo_info("")
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = ui.botao(
            i18n.t('Pasta...'),
            i18n.t('Escolhe a pasta de modelos de balão; use Atualizar depois de adicionar SVGs.'),
            icone_chave="pasta",
        )
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = ui.botao(i18n.t('Abrir'), i18n.t('Abre a pasta de modelos no explorador de arquivos.'))
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        layout.addLayout(folder_row)

        self.list_balloons = widgets.QListWidget()
        self.list_balloons.setViewMode(ICON_MODE)
        self.list_balloons.setIconSize(QtCore.QSize(120, 90))
        self.list_balloons.setResizeMode(LIST_ADJUST)
        self.list_balloons.setMovement(LIST_STATIC)
        self.list_balloons.setWordWrap(True)
        self.list_balloons.itemDoubleClicked.connect(self.insert_balloon)
        layout.addWidget(self.list_balloons, 1)

        self.chk_text_layer = widgets.QCheckBox(
            i18n.t("Nomear a camada como 'text' (para o CPMT)")
        )
        self.chk_text_layer.setChecked(
            bool(self.config.get("balloons.insert_as_text_layer", False))
        )
        layout.addWidget(self.chk_text_layer)

        buttons = widgets.QHBoxLayout()
        button_insert = ui.botao(
            i18n.t('Inserir balão'), i18n.t('Insere o modelo selecionado no grupo ou camada ativa.')
        )
        button_insert.clicked.connect(self.insert_balloon)
        buttons.addWidget(button_insert)
        button_refresh = ui.botao(
            i18n.t('Atualizar'), i18n.t('Relê os modelos da pasta atual.'), icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self.refresh)
        buttons.addWidget(button_refresh)
        layout.addLayout(buttons)

        kit_row = widgets.QHBoxLayout()
        button_symbols = ui.botao(
            i18n.t('Símbolos do Krita'),
            i18n.t("Abre o docker nativo 'Bibliotecas de símbolos' do Krita"),
        )
        button_symbols.clicked.connect(self.open_native_symbols_docker)
        kit_row.addWidget(button_symbols)
        button_fonts = ui.botao(
            i18n.t('Instalar fontes de HQ'),
            i18n.t('Copia as fontes inclusas (OFL) para o sistema e atualiza o cache'),
            icone_chave="salvar",
        )
        button_fonts.clicked.connect(self.install_kit_fonts)
        kit_row.addWidget(button_fonts)
        layout.addLayout(kit_row)

        hint = ui.rotulo(
            i18n.t('Os modelos são SVGs comuns: você pode desenhar os seus (Inkscape) e salvá-los na pasta acima. Clique duas vezes para inserir no grupo ativo.'))
        layout.addWidget(hint)

        self.setWidget(main)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), i18n.t('Pasta de balões'), self.folder
        )
        if folder:
            self.folder = folder
            self.config.set("balloons.folder", folder)
            self.refresh()

    def open_folder(self):
        QtGui.QDesktopServices.openUrl(
            QtCore.QUrl.fromLocalFile(self.folder)
        )

    def refresh(self):
        self.lbl_folder.setText(i18n.t('Pasta: {0}').format(self.folder))
        self.list_balloons.clear()
        try:
            names = sorted(os.listdir(self.folder))
        except OSError as erro:
            # Lista vazia sem explicação é o pior desfecho: o autor conclui que
            # o kit sumiu.
            names = []
            self.lbl_folder.setText(
                i18n.t('Pasta: {0} (não pôde ser lida: {1})').format(self.folder, erro)
            )
        for name in names:
            if not name.lower().endswith(".svg"):
                continue
            path = os.path.join(self.folder, name)
            item = QtWidgets.QListWidgetItem(os.path.splitext(name)[0])
            item.setData(USER_ROLE, path)
            item.setToolTip(path)
            pixmap = render_svg_thumbnail(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_balloons.addItem(item)

    def insert_balloon(self):
        """Insere o balão numa macro: um Ctrl+Z desfaz tudo."""
        document = helpers.active_document()
        helpers.run_in_macro(document, self._insert_balloon)

    def _insert_balloon(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message(i18n.t('Abra um documento para inserir o balão.'))
            return
        item = self.list_balloons.currentItem()
        if item is None:
            helpers.show_message(i18n.t('Escolha um balão na lista.'))
            return
        path = item.data(USER_ROLE)
        try:
            svg = helpers.read_text_file(path)
        except OSError:
            helpers.show_message(i18n.t('Não foi possível ler o arquivo do balão.'))
            return
        base = "text" if self.chk_text_layer.isChecked() else item.text()
        name = helpers.unique_layer_name(document, base)
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message(i18n.t('Não foi possível criar a camada vetorial.'))
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            # createVectorLayer já deixou a camada no documento: sem esta
            # limpeza, um SVG ruim deixava uma camada vazia para o autor
            # encontrar e apagar à mão.
            self._descartar_camada(document, layer)
            helpers.show_message(
                i18n.t('O SVG não gerou formas. Verifique o arquivo (use formas e texto).')
            )
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        self.config.set(
            "balloons.insert_as_text_layer", self.chk_text_layer.isChecked()
        )
        helpers.show_message(i18n.t('Balão inserido: {0}').format(item.text()))

    @staticmethod
    def _descartar_camada(document, layer):
        try:
            document.removeNode(layer)
        except (AttributeError, RuntimeError):
            pass

    def open_native_symbols_docker(self, *args):
        """Mostra o docker nativo 'Bibliotecas de símbolos' do Krita."""
        window = Krita.instance().activeWindow()
        if window is None:
            helpers.show_message(i18n.t('Abra uma janela do Krita primeiro.'))
            return
        for dock in window.dockers():
            title = str(dock.windowTitle()).lower()
            if any(token in title for token in ("symbol", "símbolo", "simbolo")):
                dock.show()
                dock.raise_()
                helpers.show_message(i18n.t('Docker de símbolos do Krita aberto.'))
                return
        helpers.show_message(
            i18n.t("Docker 'Bibliotecas de símbolos' não encontrado; habilite em Configurações > Dockers.")
        )

    def install_kit_fonts(self):
        """Instala as fontes de HQ (OFL) inclusas no plugin.

        Copia só o que mudou e só roda o ``fc-cache`` quando houve mudança: a
        versão anterior recopiaria o kit inteiro e forçaria a reconstrução
        completa do cache de fontes toda vez que o botão fosse clicado, com a
        interface travada nos segundos do ``fc-cache -f``.
        """
        if not os.path.isdir(KIT_FONTS_DIR):
            helpers.show_message(i18n.t('Pasta de fontes não encontrada no plugin.'))
            return
        try:
            os.makedirs(FONTS_TARGET, exist_ok=True)
        except OSError as error:
            helpers.show_message(i18n.t('Falha ao criar a pasta de fontes: {0}').format(error))
            return
        instaladas = []
        ignoradas = 0
        for name in sorted(os.listdir(KIT_FONTS_DIR)):
            if not name.lower().endswith((".ttf", ".otf")):
                continue
            origem = os.path.join(KIT_FONTS_DIR, name)
            destino = os.path.join(FONTS_TARGET, name)
            try:
                if mesma_copia(origem, destino):
                    ignoradas += 1
                    continue
                shutil.copy2(origem, destino)
                instaladas.append(name)
            except OSError:
                continue
        if instaladas:
            self._registrar_fontes_windows(instaladas)
            self._atualizar_cache_de_fontes()
        if not instaladas:
            helpers.show_message(
                i18n.t('As {0} fonte(s) do kit já estão instaladas.').format(ignoradas)
            )
            return
        helpers.show_message(
            i18n.t('{0} fonte(s) instalada(s) ({1} já estavam). Reinicie o Krita para listá-las na ferramenta de texto.').format(len(instaladas), ignoradas)
        )

    @staticmethod
    def _registrar_fontes_windows(nomes):
        """Registra as fontes no Windows (instalação por usuário).

        Copiar o arquivo para a pasta de fontes do usuário não basta: o
        Windows precisa da entrada em ``HKCU`` para listar a fonte.
        """
        if not sys.platform.startswith("win"):
            return
        try:
            import winreg
        except ImportError:  # pragma: no cover
            return
        chave = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, chave) as registro:
                for nome in nomes:
                    caminho = os.path.join(FONTS_TARGET, nome)
                    winreg.SetValueEx(registro, nome, 0, winreg.REG_SZ, caminho)
        except OSError:
            pass

    @staticmethod
    def _atualizar_cache_de_fontes():
        """Roda o ``fc-cache`` (só no Linux) na pasta do kit, sem ``-f``.

        ``-f`` reconstrói o cache inteiro do sistema, o que numa máquina com
        muitas fontes leva dezenas de segundos. Como as fontes acabou de
        mudar, o cache incremental da pasta já basta. No Windows a fonte é
        registrada no registro; no macOS o sistema varre a pasta sozinho.
        """
        if not sys.platform.startswith("linux"):
            return
        with helpers.cursor_espera():
            try:
                subprocess.run(
                    ["fc-cache", FONTS_TARGET],
                    timeout=60,
                    capture_output=True,
                )
            except (OSError, subprocess.SubprocessError):
                pass