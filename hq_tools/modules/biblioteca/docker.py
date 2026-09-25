"""Docker "biblioteca do projeto": cria e guarda os recursos do autor.

Balões, painéis e onomatopeias criados pelo próprio autor: o botão "Criar novo
recurso" abre um documento quadrado (15 x 15 cm a 300 dpi); depois de desenhar
na camada vetorial, "Salvar recurso do documento" exporta o desenho como SVG
na pasta da biblioteca e já aparece na lista, pronto para inserir com um
clique dentro do grupo ativo.
"""

import os

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
from ...core.paths import BIBLIOTECA_DIR
from . import core as lib

TAMANHO = lib.tamanho_novo_documento()


def render_svg_thumbnail(path, size=120):
    if QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(path)
    if not renderer.isValid():
        return None
    image = QImage(size, size, IMAGE_FORMAT_ARGB32)
    image.fill(TRANSPARENT)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


class BibliotecaDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: biblioteca")
        self.config = Config()
        self.folder = self.config.get("biblioteca.folder") or BIBLIOTECA_DIR
        os.makedirs(self.folder, exist_ok=True)
        for _, _, sub in lib.TIPOS:
            os.makedirs(os.path.join(self.folder, sub), exist_ok=True)
        self._build_ui()
        self.refresh()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        widgets = QtWidgets
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = widgets.QLabel("")
        self.lbl_folder.setWordWrap(True)
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = widgets.QPushButton("Pasta...")
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = widgets.QPushButton("Abrir")
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        layout.addLayout(folder_row)

        tipo_row = widgets.QHBoxLayout()
        tipo_row.addWidget(widgets.QLabel("Tipo:"))
        self.cmb_tipo = widgets.QComboBox()
        for chave, rotulo, _ in lib.TIPOS:
            self.cmb_tipo.addItem(rotulo, chave)
        self.cmb_tipo.currentIndexChanged.connect(self.refresh)
        tipo_row.addWidget(self.cmb_tipo, 1)
        button_refresh = widgets.QPushButton("Atualizar")
        button_refresh.clicked.connect(self.refresh)
        tipo_row.addWidget(button_refresh)
        layout.addLayout(tipo_row)

        self.list_items = widgets.QListWidget()
        self.list_items.setViewMode(ICON_MODE)
        self.list_items.setIconSize(QtCore.QSize(120, 120))
        self.list_items.setResizeMode(LIST_ADJUST)
        self.list_items.setMovement(LIST_STATIC)
        self.list_items.setWordWrap(True)
        self.list_items.itemDoubleClicked.connect(self.insert_resource)
        layout.addWidget(self.list_items, 1)

        buttons = widgets.QHBoxLayout()
        button_new = widgets.QPushButton("Criar novo recurso")
        button_new.setToolTip(
            "Abre um documento 15 x 15 cm a 300 dpi para desenhar o recurso"
        )
        button_new.clicked.connect(self.create_resource)
        buttons.addWidget(button_new)
        button_save = widgets.QPushButton("Salvar recurso do documento")
        button_save.setToolTip(
            "Exporta a camada vetorial do documento ativo como SVG na biblioteca"
        )
        button_save.clicked.connect(self.save_resource)
        buttons.addWidget(button_save)
        button_insert = widgets.QPushButton("Inserir selecionado")
        button_insert.clicked.connect(self.insert_resource)
        buttons.addWidget(button_insert)
        layout.addLayout(buttons)

        hint = widgets.QLabel(
            "1) 'Criar novo recurso' abre o documento quadrado. 2) Desenhe na "
            "camada vetorial (formas e texto). 3) 'Salvar recurso do documento' "
            "guarda o SVG na pasta da biblioteca. Depois é só inserir no grupo "
            "ativo com duplo clique."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setWidget(main)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), "Pasta da biblioteca", self.folder
        )
        if folder:
            self.folder = folder
            self.config.set("biblioteca.folder", folder)
            self.refresh()

    def open_folder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.folder))

    def refresh(self):
        self.lbl_folder.setText("Pasta: {0}".format(self.folder))
        tipo = self.cmb_tipo.currentData()
        self.list_items.clear()
        for nome, path in lib.listar_recursos(self.folder, tipo):
            item = QtWidgets.QListWidgetItem(nome)
            item.setData(USER_ROLE, path)
            item.setToolTip(path)
            pixmap = render_svg_thumbnail(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_items.addItem(item)

    def create_resource(self):
        tipo = self.cmb_tipo.currentData()
        rotulo = lib.TIPO_CHAVE[tipo]
        document = Krita.instance().createDocument(
            TAMANHO, TAMANHO, "Novo {0}".format(rotulo),
            "RGBA", "U8", "sRGB built-in", lib.DPI_PADRAO,
        )
        if document is None:
            helpers.show_message("Não foi possível criar o documento.")
            return
        layer = document.createVectorLayer("recurso")
        if layer is not None:
            document.rootNode().addChildNode(layer, None)
            document.setActiveNode(layer)
        document.refreshProjection()
        helpers.show_message(
            "Desenhe o {0} na camada vetorial e use 'Salvar recurso do "
            "documento'.".format(rotulo.lower())
        )

    def _vector_layer_with_shapes(self, document):
        node = document.activeNode()
        if node is not None and node.type() == "vectorlayer":
            try:
                if node.shapes():
                    return node
            except (AttributeError, RuntimeError):
                pass
        for child in document.rootNode().findChildNodes(recursive=True):
            if child.type() == "vectorlayer":
                try:
                    if child.shapes():
                        return child
                except (AttributeError, RuntimeError):
                    continue
        return None

    def save_resource(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra o documento do recurso desenhado.")
            return
        layer = self._vector_layer_with_shapes(document)
        if layer is None:
            helpers.show_message(
                "O documento não tem uma camada vetorial com formas."
            )
            return
        try:
            svg = layer.toSvg()
        except (AttributeError, RuntimeError) as error:
            helpers.show_message("Não foi possível exportar a camada: {0}".format(error))
            return
        if not svg or "<svg" not in svg.lower():
            helpers.show_message("A camada vetorial está vazia.")
            return
        tipo = self.cmb_tipo.currentData()
        rotulo = lib.TIPO_CHAVE[tipo]
        nome, ok = QtWidgets.QInputDialog.getText(
            self.widget(),
            "Salvar {0}".format(rotulo.lower()),
            "Nome do recurso:",
            text=lib.nome_padrao(tipo),
        )
        if not ok or not nome.strip():
            return
        try:
            path = lib.salvar_recurso(svg, self.folder, tipo, nome.strip())
        except OSError as error:
            helpers.show_message("Falha ao salvar: {0}".format(error))
            return
        self.refresh()
        answer = QtWidgets.QMessageBox.question(
            self.widget(),
            "Fechar documento?",
            "Recurso salvo. Fechar o documento de desenho?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if answer == QtWidgets.QMessageBox.Yes:
            document.setModified(False)
            document.close()
        helpers.show_message("Recurso salvo: {0}".format(os.path.basename(path)))

    def insert_resource(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra um documento para inserir o recurso.")
            return
        item = self.list_items.currentItem()
        if item is None:
            helpers.show_message("Escolha um recurso na lista.")
            return
        path = item.data(USER_ROLE)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                svg = handle.read()
        except OSError:
            helpers.show_message("Não foi possível ler o arquivo.")
            return
        name = helpers.unique_layer_name(document, item.text())
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message("Não foi possível criar a camada vetorial.")
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            helpers.show_message("O SVG não gerou formas.")
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message("Recurso inserido: {0}".format(item.text()))