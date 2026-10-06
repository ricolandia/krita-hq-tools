"""Docker "biblioteca do projeto": cria e guarda os recursos do autor.

O autor pode criar o recurso como vetorial (camada de formas) ou como pintura
(camada de desenho comum). O vetorial é salvo como SVG (``toSvg``); a pintura
é salva como PNG transparente recortado pela própria camada ativa. Os dois
tipos aparecem na lista e são inseridos no grupo ativo com um duplo clique
(SVG vira camada vetorial; PNG vira camada de pintura). A lista também
renomeia, duplica e apaga o recurso selecionado, sem sair do Krita.
"""

import os

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    DIALOG_NO,
    DIALOG_YES,
    ICON_MODE,
    IMAGE_FORMAT_ARGB32,
    KEEP_ASPECT,
    LIST_ADJUST,
    LIST_STATIC,
    SMOOTH_TRANSFORMATION,
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
from ...core.paths import BIBLIOTECA_DIR
from . import core as lib

TAMANHO = lib.tamanho_novo_documento()

MODOS_CAMADA = (("Vetorial (formas)", "vetorial"), ("Pintura (pincel)", "pintura"))


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


def render_png_thumbnail(path, size=120):
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return None
    return pixmap.scaled(size, size, KEEP_ASPECT, SMOOTH_TRANSFORMATION)


def _qimage_bytes(image):
    return bytes(image.constBits().asstring(image.sizeInBytes()))


class BibliotecaDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: biblioteca'))
        registro.registrar("biblioteca", self)
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
        main, layout = ui.painel(self)

        group_lib = widgets.QGroupBox(i18n.t('Biblioteca'))
        lib_layout = ui.espacamento(widgets.QVBoxLayout(group_lib), margem=0, espaco=ui.GAP)
        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = ui.rotulo_info("")
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = ui.botao(
            i18n.t('Pasta...'),
            i18n.t('Escolhe a pasta de recursos (biblioteca); use Atualizar depois de adicionar arquivos.'),
            icone_chave="pasta",
        )
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = ui.botao(i18n.t('Abrir'), i18n.t('Abre a pasta de recursos no explorador de arquivos.'))
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        lib_layout.addLayout(folder_row)
        layout.addWidget(group_lib)
        layout.addWidget(ui.separador())

        group_new = widgets.QGroupBox(i18n.t('Recurso novo'))
        new_layout = ui.espacamento(widgets.QHBoxLayout(group_new), margem=0, espaco=ui.GAP)
        new_layout.addWidget(ui.rotulo(i18n.t('Tipo de camada:')))
        self.cmb_camada = widgets.QComboBox()
        for rotulo, valor in MODOS_CAMADA:
            self.cmb_camada.addItem(i18n.t(rotulo), valor)
        new_layout.addWidget(self.cmb_camada, 1)
        button_new = ui.botao(
            i18n.t('Criar novo recurso'),
            i18n.t('Abre um documento 15 x 15 cm a 300 dpi para desenhar o recurso'),
            icone_chave="novo",
        )
        button_new.clicked.connect(self.create_resource)
        new_layout.addWidget(button_new)
        layout.addWidget(group_new)
        layout.addWidget(ui.separador())

        group_list = widgets.QGroupBox(i18n.t('Recursos'))
        list_layout = ui.espacamento(widgets.QVBoxLayout(group_list), margem=0, espaco=ui.GAP)
        tipo_row = widgets.QHBoxLayout()
        tipo_row.addWidget(ui.rotulo(i18n.t('Tipo:')))
        self.cmb_tipo = widgets.QComboBox()
        for chave, rotulo, _ in lib.TIPOS:
            self.cmb_tipo.addItem(i18n.t(rotulo), chave)
        self.cmb_tipo.currentIndexChanged.connect(self.refresh)
        tipo_row.addWidget(self.cmb_tipo, 1)
        button_refresh = ui.botao(
            i18n.t('Atualizar'), i18n.t('Relê os recursos da pasta atual.'), icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self.refresh)
        tipo_row.addWidget(button_refresh)
        list_layout.addLayout(tipo_row)

        self.list_items = widgets.QListWidget()
        self.list_items.setViewMode(ICON_MODE)
        self.list_items.setIconSize(QtCore.QSize(110, 110))
        self.list_items.setResizeMode(LIST_ADJUST)
        self.list_items.setMovement(LIST_STATIC)
        self.list_items.setWordWrap(True)
        self.list_items.itemDoubleClicked.connect(self.insert_resource)
        list_layout.addWidget(self.list_items, 1)

        buttons = widgets.QHBoxLayout()
        button_save = ui.botao(
            i18n.t('Salvar recurso do documento'),
            i18n.t('Exporta a camada ativa (vetorial ou pintura) para a biblioteca'),
            icone_chave="salvar",
        )
        button_save.clicked.connect(self.save_resource)
        buttons.addWidget(button_save)
        button_insert = ui.botao(
            i18n.t('Inserir selecionado'), i18n.t('Insere o recurso selecionado na camada ativa.')
        )
        button_insert.clicked.connect(self.insert_resource)
        buttons.addWidget(button_insert)
        list_layout.addLayout(buttons)

        gerir = widgets.QHBoxLayout()
        button_rename = ui.botao(
            i18n.t('Renomear...'),
            i18n.t('Renomeia o arquivo do recurso selecionado, preservando a extensão.'),
        )
        button_rename.clicked.connect(self.rename_resource)
        gerir.addWidget(button_rename)
        button_duplicate = ui.botao(
            i18n.t('Duplicar'),
            i18n.t('Cria uma cópia do recurso selecionado na mesma pasta.'),
            icone_chave="novo",
        )
        button_duplicate.clicked.connect(self.duplicate_resource)
        gerir.addWidget(button_duplicate)
        button_delete = ui.botao(
            i18n.t('Apagar'),
            i18n.t('Apaga o arquivo do recurso selecionado; pede confirmação antes.'),
        )
        button_delete.clicked.connect(self.delete_resource)
        gerir.addWidget(button_delete)
        list_layout.addLayout(gerir)
        layout.addWidget(group_list, 1)

        hint = ui.rotulo(
            i18n.t("1) Escolha o tipo e 'Criar novo recurso'. 2) Desenhe na camada (formas/texto ou pincel). 3) 'Salvar recurso do documento' guarda como SVG ou PNG transparente. 4) Duplo clique insere no grupo ativo; Renomear, Duplicar e Apagar organizam a pasta."))
        layout.addWidget(hint)

        self.setWidget(main)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), i18n.t('Pasta da biblioteca'), self.folder
        )
        if folder:
            self.folder = folder
            self.config.set("biblioteca.folder", folder)
            self.refresh()

    def open_folder(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.folder))

    def refresh(self):
        self.lbl_folder.setText(i18n.t('Pasta: {0}').format(self.folder))
        tipo = self.cmb_tipo.currentData()
        self.list_items.clear()
        for nome, path in lib.listar_recursos(self.folder, tipo):
            item = QtWidgets.QListWidgetItem(nome)
            item.setData(USER_ROLE, path)
            item.setToolTip(path)
            pixmap = None
            if path.lower().endswith(".png"):
                pixmap = render_png_thumbnail(path)
            else:
                pixmap = render_svg_thumbnail(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_items.addItem(item)

    def create_resource(self):
        tipo = self.cmb_tipo.currentData()
        rotulo = lib.TIPO_CHAVE[tipo]
        modo = self.cmb_camada.currentData()
        document = Krita.instance().createDocument(
            TAMANHO, TAMANHO, "Novo {0}".format(rotulo),
            "RGBA", "U8", "sRGB built-in", lib.DPI_PADRAO,
        )
        if document is None:
            helpers.show_message(i18n.t('Não foi possível criar o documento.'))
            return
        if modo == "pintura":
            layer = document.createNode(i18n.t("recurso"), "paintlayer")
            if layer is not None:
                document.rootNode().addChildNode(layer, None)
                document.setActiveNode(layer)
        else:
            layer = document.createVectorLayer(i18n.t("recurso"))
            if layer is not None:
                document.rootNode().addChildNode(layer, None)
                document.setActiveNode(layer)
        document.refreshProjection()
        if not helpers.present_document(document):
            # Sem view o usuário não enxergaria a camada criada nem conseguiria
            # desenhá-la; o documento ficaria oculto até o próximo Ctrl+Tab.
            helpers.show_info(
                i18n.t('Novo recurso'),
                i18n.t('O documento foi criado, mas o Krita não abriu uma aba para ele. Procure a aba do novo documento e volte aqui para salvar.'),
            )
            return
        helpers.show_message(
            i18n.t("Desenhe o {0} na camada 'recurso' e use 'Salvar recurso do documento'.").format(i18n.t(rotulo).lower())
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

    def _paint_layer_with_content(self, document):
        node = document.activeNode()
        if node is not None and node.type() == "paintlayer":
            try:
                if not node.bounds().isEmpty():
                    return node
            except (AttributeError, RuntimeError):
                pass
        for child in document.rootNode().findChildNodes(recursive=True):
            if child.type() == "paintlayer":
                try:
                    if not child.bounds().isEmpty():
                        return child
                except (AttributeError, RuntimeError):
                    continue
        return None

    def save_resource(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Abra o documento do recurso desenhado.'))
            return
        tipo = self.cmb_tipo.currentData()
        rotulo = lib.TIPO_CHAVE[tipo]
        modo = self.cmb_camada.currentData()

        if modo == "pintura":
            self._save_paint(document, tipo, rotulo)
        else:
            self._save_vector(document, tipo, rotulo)

    def _save_vector(self, document, tipo, rotulo):
        layer = self._vector_layer_with_shapes(document)
        if layer is None:
            helpers.show_info(
                i18n.t('Biblioteca'),
                i18n.t('O documento não tem uma camada vetorial com formas.'),
            )
            return
        try:
            svg = layer.toSvg()
        except (AttributeError, RuntimeError) as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Não foi possível exportar: {0}').format(error))
            return
        if not svg or "<svg" not in svg.lower():
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('A camada vetorial está vazia.'))
            return
        nome, ok = QtWidgets.QInputDialog.getText(
            self.widget(), i18n.t('Salvar {0}').format(i18n.t(rotulo).lower()),
            i18n.t('Nome do recurso:'), text=lib.nome_padrao(tipo),
        )
        if not ok or not nome.strip():
            return
        try:
            path = lib.salvar_recurso(svg, self.folder, tipo, nome.strip())
        except OSError as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Falha ao salvar: {0}').format(error))
            return
        self.refresh()
        self._ask_close(document)
        helpers.show_info(i18n.t('Biblioteca'), i18n.t('Recurso salvo: {0}').format(os.path.basename(path)))

    def _save_paint(self, document, tipo, rotulo):
        layer = self._paint_layer_with_content(document)
        if layer is None:
            helpers.show_info(
                i18n.t('Biblioteca'),
                i18n.t('O documento não tem uma camada de pintura com conteúdo.'),
            )
            return
        if document.colorModel() != "RGBA" or document.colorDepth() != "U8":
            helpers.show_info(
                i18n.t('Biblioteca'),
                i18n.t('O documento não é RGBA 8 bits; exporte a camada como PNG manualmente (Camada > Importar/Exportar).'),
            )
            return
        try:
            bounds = layer.bounds()
        except (AttributeError, RuntimeError):
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Não foi possível ler a camada.'))
            return
        if bounds is None or bounds.isEmpty():
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('A camada de pintura está vazia.'))
            return
        data = layer.pixelData(bounds.x(), bounds.y(), bounds.width(), bounds.height())
        # Os bytes do device RGBA 8 bits vêm em BGRA (documentação do libkis);
        # o Format_ARGB32 do Qt interpreta nessa ordem, senão vermelho e azul
        # saem trocados no PNG salvo.
        image = QImage(
            bytes(data), bounds.width(), bounds.height(), IMAGE_FORMAT_ARGB32
        )
        if image.isNull():
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Não foi possível montar a imagem.'))
            return
        nome, ok = QtWidgets.QInputDialog.getText(
            self.widget(), i18n.t('Salvar {0}').format(i18n.t(rotulo).lower()),
            i18n.t('Nome do recurso:'), text=lib.nome_padrao(tipo),
        )
        if not ok or not nome.strip():
            return
        try:
            folder = lib.pasta_do_tipo(self.folder, tipo)
            path = lib.caminho_livre(folder, nome.strip(), ".png")
            if not image.save(path, "PNG"):
                raise OSError("PNG não gravado")
        except OSError as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Falha ao salvar: {0}').format(error))
            return
        self.refresh()
        self._ask_close(document)
        helpers.show_info(i18n.t('Biblioteca'), i18n.t('Recurso salvo: {0}').format(os.path.basename(path)))

    def _ask_close(self, document):
        answer = QtWidgets.QMessageBox.question(
            self.widget(),
            i18n.t('Fechar documento?'),
            i18n.t('Recurso salvo. Fechar o documento de desenho?'),
            DIALOG_YES | DIALOG_NO,
        )
        if answer == DIALOG_YES:
            document.setModified(False)
            document.close()

    def insert_resource(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message(i18n.t('Abra um documento para inserir o recurso.'))
            return
        item = self.list_items.currentItem()
        if item is None:
            helpers.show_message(i18n.t('Escolha um recurso na lista.'))
            return
        path = item.data(USER_ROLE)
        if path.lower().endswith(".png"):
            self._insert_paint(document, path, item.text())
        else:
            self._insert_vector(document, path, item.text())

    def _recurso_selecionado(self):
        item = self.list_items.currentItem()
        if item is None:
            helpers.show_message(i18n.t('Escolha um recurso na lista.'))
            return None
        return item.text(), item.data(USER_ROLE)

    def rename_resource(self):
        selecionado = self._recurso_selecionado()
        if selecionado is None:
            return
        nome, path = selecionado
        novo, ok = QtWidgets.QInputDialog.getText(
            self.widget(), i18n.t('Renomear recurso'), i18n.t('Novo nome:'), text=nome
        )
        if not ok or not novo.strip():
            return
        try:
            lib.renomear_recurso(path, novo.strip())
        except OSError as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Falha ao renomear: {0}').format(error))
            return
        self.refresh()

    def duplicate_resource(self):
        selecionado = self._recurso_selecionado()
        if selecionado is None:
            return
        _, path = selecionado
        try:
            copia = lib.duplicar_recurso(path)
        except OSError as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Falha ao duplicar: {0}').format(error))
            return
        self.refresh()
        helpers.show_message(i18n.t('Cópia criada: {0}').format(os.path.basename(copia)))

    def delete_resource(self):
        selecionado = self._recurso_selecionado()
        if selecionado is None:
            return
        nome, path = selecionado
        answer = QtWidgets.QMessageBox.question(
            self.widget(),
            i18n.t('Apagar recurso?'),
            i18n.t("Apagar '{0}'? O arquivo sai da pasta da biblioteca.").format(nome),
            DIALOG_YES | DIALOG_NO,
            DIALOG_NO,
        )
        if answer != DIALOG_YES:
            return
        try:
            lib.apagar_recurso(path)
        except (OSError, ValueError) as error:
            helpers.show_info(i18n.t('Biblioteca'), i18n.t('Falha ao apagar: {0}').format(error))
            return
        self.refresh()

    def _insert_vector(self, document, path, nome):
        try:
            svg = helpers.read_text_file(path)
        except OSError:
            helpers.show_message(i18n.t('Não foi possível ler o arquivo.'))
            return
        name = helpers.unique_layer_name(document, nome)
        layer = document.createVectorLayer(name)
        if layer is None:
            helpers.show_message(i18n.t('Não foi possível criar a camada vetorial.'))
            return
        shapes = layer.addShapesFromSvg(svg)
        if not shapes:
            helpers.show_message(i18n.t('O SVG não gerou formas.'))
            return
        helpers.attach(document, layer)
        document.setActiveNode(layer)
        helpers.show_message(i18n.t('Recurso inserido: {0}').format(nome))

    def _insert_paint(self, document, path, nome):
        image = QImage(path)
        if image.isNull():
            helpers.show_message(i18n.t('Não foi possível ler o PNG.'))
            return
        # O setPixelData espera os canais em BGRA (documentação do libkis); o
        # Format_ARGB32 do Qt é BGRA em memória. Com RGBA8888 o vermelho e o
        # azul sairiam trocados.
        rgba = image.convertToFormat(IMAGE_FORMAT_ARGB32)
        width = rgba.width()
        height = rgba.height()
        name = helpers.unique_layer_name(document, nome)
        layer = document.createNode(name, "paintlayer")
        if layer is None:
            helpers.show_message(i18n.t('Não foi possível criar a camada de pintura.'))
            return
        data = _qimage_bytes(rgba)
        if not layer.setPixelData(data, 0, 0, width, height):
            file_layer = document.createFileLayer(
                name, path, "ToImageSize", "Bilinear"
            )
            if file_layer is None:
                helpers.show_message(i18n.t('Não foi possível inserir o PNG.'))
                return
            helpers.attach(document, file_layer)
            document.setActiveNode(file_layer)
        else:
            helpers.attach(document, layer)
            document.setActiveNode(layer)
        helpers.show_message(i18n.t('Recurso inserido: {0}').format(nome))