"""Docker "moodboard": quadro de referências do projeto.

As referências viram JPG comprimidos na pasta ``moodboard/`` e entram no
quadro (``moodboard.kra``) como camadas de arquivo linkadas, posicionadas por
máscaras de transformação. O ``.kra`` fica leve (só os links) e a referência
selecionada pode ser inserida na seleção do documento ativo como camada de
arquivo travada, para desenhar por cima.
"""

import os

from krita import DockWidget, Krita

from ...core import i18n
from ...core import krita_helpers as helpers
from ...core import registro, ui
from ...core.compat import (
    DIALOG_CANCEL,
    DIALOG_NO,
    DIALOG_OK,
    DIALOG_YES,
    ICON_MODE,
    IMAGE_FORMAT_ARGB32,
    KEEP_ASPECT,
    LIST_ADJUST,
    LIST_STATIC,
    SMOOTH_TRANSFORMATION,
    USER_ROLE,
    QIcon,
    QImage,
    QPixmap,
    QtCore,
    QtGui,
    QtWidgets,
)
from ...core.config import Config
from ...core.paths import MOODBOARD_DIR
from ..biblioteca.core import renomear_recurso
from . import core as mb


class MoodboardDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t('HQ Tools: moodboard'))
        registro.registrar("moodboard", self)
        self.config = Config()
        self._build_ui()
        self.refresh()

    def canvasChanged(self, canvas):
        pass

    # ------------------------------------------------------------------ pastas

    def folder(self):
        """Pasta das referências: escolha explícita, pasta do projeto ou padrão."""
        escolhida = self.config.get("moodboard.folder")
        if escolhida:
            return escolhida
        projeto = self.config.get("pages.last_folder")
        if projeto and os.path.isdir(projeto):
            return os.path.join(projeto, mb.PASTA)
        return MOODBOARD_DIR

    def board_path(self):
        """O quadro fica ao lado da pasta de referências (mesma raiz)."""
        return os.path.join(os.path.dirname(self.folder()), mb.ARQUIVO_QUADRO)

    def pick_folder(self):
        pasta = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), i18n.t('Pasta das referências (moodboard)'), self.folder()
        )
        if pasta:
            self.config.set("moodboard.folder", pasta)
            self.refresh()

    def open_folder(self):
        pasta = self.folder()
        os.makedirs(pasta, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(pasta))

    # -------------------------------------------------------------------- UI

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        group_folder = widgets.QGroupBox(i18n.t('Pasta'))
        folder_layout = ui.espacamento(widgets.QVBoxLayout(group_folder), margem=0, espaco=ui.GAP)
        folder_row = widgets.QHBoxLayout()
        self.lbl_folder = ui.rotulo_info("")
        folder_row.addWidget(self.lbl_folder, 1)
        button_pick = ui.botao(
            i18n.t('Pasta...'),
            i18n.t('Escolhe a pasta das referências (por padrão, moodboard/ na pasta do projeto).'),
            icone_chave="pasta",
        )
        button_pick.clicked.connect(self.pick_folder)
        folder_row.addWidget(button_pick)
        button_open = ui.botao(
            i18n.t('Abrir'), i18n.t('Abre a pasta de referências no explorador de arquivos.')
        )
        button_open.clicked.connect(self.open_folder)
        folder_row.addWidget(button_open)
        folder_layout.addLayout(folder_row)

        board_row = widgets.QHBoxLayout()
        button_board = ui.botao(
            i18n.t('Abrir moodboard'),
            i18n.t('Abre o quadro moodboard.kra (cria na pasta do projeto, se ainda não existir).'),
            icone_chave="abrir",
        )
        button_board.clicked.connect(self.open_board)
        board_row.addWidget(button_board)
        folder_layout.addLayout(board_row)
        layout.addWidget(group_folder)
        layout.addWidget(ui.separador())

        group_refs = widgets.QGroupBox(i18n.t('Referências'))
        refs_layout = ui.espacamento(widgets.QVBoxLayout(group_refs), margem=0, espaco=ui.GAP)

        buttons = widgets.QHBoxLayout()
        button_add = ui.botao(
            i18n.t('Adicionar referências...'),
            i18n.t('Escolhe imagens, comprime em JPG e linka no quadro (os originais não mudam).'),
            icone_chave="novo",
        )
        button_add.clicked.connect(self.add_references)
        buttons.addWidget(button_add)
        button_refresh = ui.botao(
            i18n.t('Atualizar'), i18n.t('Relê as referências da pasta atual.'), icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self.refresh)
        buttons.addWidget(button_refresh)
        refs_layout.addLayout(buttons)

        self.list_items = widgets.QListWidget()
        self.list_items.setViewMode(ICON_MODE)
        self.list_items.setIconSize(QtCore.QSize(110, 110))
        self.list_items.setResizeMode(LIST_ADJUST)
        self.list_items.setMovement(LIST_STATIC)
        self.list_items.setWordWrap(True)
        self.list_items.itemDoubleClicked.connect(self.insert_into_selection)
        refs_layout.addWidget(self.list_items, 1)

        acoes = widgets.QHBoxLayout()
        button_insert = ui.botao(
            i18n.t('Inserir na seleção'),
            i18n.t('Insere a referência selecionada na seleção do documento ativo, travada para desenhar por cima.'),
        )
        button_insert.clicked.connect(self.insert_into_selection)
        acoes.addWidget(button_insert)
        button_rename = ui.botao(
            i18n.t('Renomear...'),
            i18n.t('Renomeia o arquivo do recurso selecionado, preservando a extensão.'),
        )
        button_rename.clicked.connect(self.rename_reference)
        acoes.addWidget(button_rename)
        button_delete = ui.botao(
            i18n.t('Apagar'),
            i18n.t('Apaga o arquivo da referência selecionada; pede confirmação antes.'),
        )
        button_delete.clicked.connect(self.delete_reference)
        acoes.addWidget(button_delete)
        refs_layout.addLayout(acoes)
        layout.addWidget(group_refs, 1)

        hint = ui.rotulo(
            i18n.t("1) 'Adicionar referências...' comprime e linka as imagens no quadro. 2) Duplo clique (ou 'Inserir na seleção') traz a referência para o painel selecionado. 3) O quadro é leve: guarda só os links para a pasta moodboard/.")
        )
        layout.addWidget(hint)

        self.setWidget(main)

    # -------------------------------------------------------------- listagem

    def refresh(self):
        pasta = self.folder()
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pass
        self.lbl_folder.setText(i18n.t('Pasta: {0}').format(pasta))
        self.list_items.clear()
        for nome, caminho in mb.listar_referencias(pasta):
            item = QtWidgets.QListWidgetItem(nome)
            item.setData(USER_ROLE, caminho)
            item.setToolTip(caminho)
            pixmap = QPixmap(caminho)
            if not pixmap.isNull():
                item.setIcon(
                    QIcon(pixmap.scaled(110, 110, KEEP_ASPECT, SMOOTH_TRANSFORMATION))
                )
            self.list_items.addItem(item)

    def _referencia_selecionada(self):
        item = self.list_items.currentItem()
        if item is None:
            helpers.show_message(i18n.t('Escolha uma referência na lista.'))
            return None
        return item.text(), item.data(USER_ROLE)

    # ---------------------------------------------------------------- quadro

    def _quadro_aberto(self):
        caminho = os.path.abspath(self.board_path())
        try:
            documentos = Krita.instance().documents()
        except (AttributeError, RuntimeError):
            return None
        for documento in documentos:
            try:
                if os.path.abspath(documento.fileName()) == caminho:
                    return documento
            except (AttributeError, RuntimeError):
                continue
        return None

    def _garantir_quadro(self):
        documento = self._quadro_aberto()
        if documento is not None:
            return documento
        caminho = self.board_path()
        if os.path.exists(caminho):
            documento = Krita.instance().openDocument(caminho)
            if documento is None:
                helpers.show_info(
                    i18n.t('Moodboard'), i18n.t('Não foi possível abrir o quadro.')
                )
                return None
            helpers.present_document(documento)
            return documento
        documento = Krita.instance().createDocument(
            mb.LARGURA, mb.ALTURA, "Moodboard", "RGBA", "U8", "sRGB built-in", 72.0
        )
        if documento is None:
            helpers.show_info(
                i18n.t('Moodboard'), i18n.t('Não foi possível criar o quadro.')
            )
            return None
        documento.saveAs(caminho)
        helpers.present_document(documento)
        return documento

    def open_board(self):
        caminho = self.board_path()
        novo = not os.path.exists(caminho)
        if self._garantir_quadro() is None:
            return
        if novo:
            helpers.show_message(i18n.t('Quadro criado: {0}').format(caminho))
        self.refresh()

    def _montar_camada(self, documento, caminho, nome, escala, dx, dy):
        """Camada de arquivo (link) + máscara de transformação (escala e posição)."""
        nome = helpers.unique_layer_name(documento, nome)
        camada = documento.createFileLayer(nome, caminho, "None", "Bilinear")
        if camada is None:
            return None
        documento.rootNode().addChildNode(camada, None)
        mascara = documento.createTransformMask("{0} (transformação)".format(nome))
        if mascara is None:
            self._remover_no(camada)
            return None
        camada.addChildNode(mascara, None)
        if not mascara.fromXML(mb.xml_transform(escala, dx, dy)):
            self._remover_no(camada)
            return None
        return camada

    def _salvar_quadro(self, documento):
        """Salva o quadro depois de mexer nas camadas (o autor não precisa lembrar)."""
        try:
            documento.save()
        except (AttributeError, RuntimeError):
            pass

    def _remover_no(self, no):
        try:
            no.remove()
        except (AttributeError, RuntimeError):
            pass

    def _crescer_quadro(self, documento, total):
        altura = mb.altura_necessaria(total)
        try:
            if altura > documento.height():
                documento.resizeImage(0, 0, documento.width(), altura)
        except (AttributeError, RuntimeError):
            pass

    # ----------------------------------------------------------- referências

    def _comprimir(self, origem, destino):
        """Redimensiona (lado máximo MAX_LADO) e salva JPG; alfa vira branco."""
        imagem = QImage(origem)
        if imagem.isNull():
            return False
        largura, altura = imagem.width(), imagem.height()
        maior = max(largura, altura)
        if maior > mb.MAX_LADO:
            fator = float(mb.MAX_LADO) / maior
            imagem = imagem.scaled(
                max(1, int(largura * fator)),
                max(1, int(altura * fator)),
                KEEP_ASPECT,
                SMOOTH_TRANSFORMATION,
            )
        if imagem.hasAlphaChannel():
            fundo = QImage(imagem.size(), IMAGE_FORMAT_ARGB32)
            fundo.fill(QtGui.QColor(255, 255, 255))
            pintor = QtGui.QPainter(fundo)
            pintor.drawImage(0, 0, imagem)
            pintor.end()
            imagem = fundo
        return bool(imagem.save(destino, "JPG", mb.QUALIDADE))

    def _avisar_compressao(self):
        if self.config.get("moodboard.aviso_compressao"):
            return True
        caixa = QtWidgets.QMessageBox(self.widget())
        caixa.setWindowTitle(i18n.t('Moodboard'))
        caixa.setText(
            i18n.t('As referências são redimensionadas (lado máximo {0} px) e salvas em JPG na pasta do projeto, para o quadro ficar leve.').format(mb.MAX_LADO)
        )
        caixa.setInformativeText(i18n.t('Os arquivos originais não são alterados.'))
        caixa.setStandardButtons(DIALOG_OK | DIALOG_CANCEL)
        marcar = QtWidgets.QCheckBox(i18n.t('Não mostrar de novo'))
        caixa.setCheckBox(marcar)
        caixa.exec()
        if caixa.clickedButton() != caixa.button(DIALOG_OK):
            return False
        if marcar.isChecked():
            self.config.set("moodboard.aviso_compressao", True)
        return True

    def add_references(self):
        pasta = self.folder()
        os.makedirs(pasta, exist_ok=True)
        if not self._avisar_compressao():
            return
        ultima = self.config.get("moodboard.ultima_pasta") or os.path.expanduser("~")
        caminhos, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self.widget(),
            i18n.t('Adicionar referências'),
            ultima,
            i18n.t('Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff)'),
        )
        if not caminhos:
            return
        self.config.set("moodboard.ultima_pasta", os.path.dirname(caminhos[0]))
        documento = self._garantir_quadro()
        if documento is None:
            return
        itens = mb.carregar_layout(pasta)
        adicionadas = 0
        falhas = []
        for origem in caminhos:
            destino = mb.caminho_referencia(pasta, os.path.basename(origem))
            if not self._comprimir(origem, destino):
                falhas.append(os.path.basename(origem))
                continue
            imagem = QImage(destino)
            x, y, escala = mb.destino(len(itens), imagem.width(), imagem.height())
            camada = self._montar_camada(
                documento, destino, os.path.splitext(os.path.basename(destino))[0], escala, x, y
            )
            if camada is None:
                falhas.append(os.path.basename(origem))
                continue
            itens.append(
                mb.item_de_layout(
                    os.path.basename(destino),
                    x,
                    y,
                    escala,
                    imagem.width(),
                    imagem.height(),
                    camada.uniqueId().toString(),
                )
            )
            adicionadas += 1
        if adicionadas:
            mb.salvar_layout(pasta, itens)
            self._crescer_quadro(documento, len(itens))
            documento.refreshProjection()
            self._salvar_quadro(documento)
        self.refresh()
        if falhas:
            helpers.show_info(
                i18n.t('Moodboard'),
                i18n.t('Não foi possível adicionar: {0}').format(", ".join(falhas)),
            )
        if adicionadas:
            helpers.show_message(i18n.t('Referências adicionadas: {0}').format(adicionadas))

    def _colocar_referencia(self, documento, camada):
        """Insere a referência visível: abaixo do ativo; acima, se ele for o fundo.

        O padrão do plugin é a referência entrar abaixo do esboço (para traçar
        por cima), mas com o fundo ativo "abaixo do ativo" esconderia a
        referência atrás dele; nesse caso ela entra logo acima.
        """
        ativo = documento.activeNode()
        if ativo is None or ativo.type() == "grouplayer":
            helpers.attach(documento, camada)
            return
        pai = ativo.parentNode() or documento.rootNode()
        try:
            chaves = [str(no.uniqueId()) for no in pai.childNodes()]
            indice = chaves.index(str(ativo.uniqueId()))
        except (AttributeError, RuntimeError, ValueError):
            indice = -1
        if indice <= 0:
            helpers.attach(documento, camada)
        else:
            helpers.attach_below_active(documento, camada)

    def insert_into_selection(self):
        selecionado = self._referencia_selecionada()
        if selecionado is None:
            return
        nome, caminho = selecionado
        documento = helpers.active_document()
        if documento is None:
            helpers.show_message(i18n.t('Abra um documento para inserir a referência.'))
            return
        selecao = helpers.selection_bounds(documento)
        if selecao is None or selecao[2] <= 0 or selecao[3] <= 0:
            helpers.show_message(
                i18n.t('Desenhe uma seleção retangular no painel para inserir a referência.')
            )
            return
        imagem = QImage(caminho)
        if imagem.isNull():
            helpers.show_message(i18n.t('Não foi possível ler a imagem.'))
            return
        x, y, largura, altura = selecao
        pos_x, pos_y, escala = mb.encaixe_em(
            x, y, largura, altura, imagem.width(), imagem.height()
        )

        def _inserir():
            camada = self._montar_camada(documento, caminho, nome, escala, pos_x, pos_y)
            if camada is None:
                return False
            self._colocar_referencia(documento, camada)
            camada.setLocked(True)
            camada.setColorLabel(1)
            camada.setOpacity(150)
            documento.setActiveNode(camada)
            helpers.deselect(documento)
            documento.refreshProjection()
            return True

        if not helpers.run_in_macro(documento, _inserir):
            return
        helpers.show_message(i18n.t('Referência inserida: {0}').format(nome))

    # ------------------------------------------------------------- gerência

    def _item_do_arquivo(self, itens, caminho):
        nome = os.path.basename(caminho)
        for indice, item in enumerate(itens):
            if item.get("arquivo") == nome:
                return indice, item
        return None, None

    def _remover_camada(self, documento, item):
        identificador = item.get("camada")
        if not identificador:
            return True
        try:
            camada = documento.nodeByUniqueID(QtCore.QUuid(identificador))
        except (AttributeError, RuntimeError, TypeError):
            return False
        if camada is None:
            return True
        self._remover_no(camada)
        try:
            documento.refreshProjection()
        except (AttributeError, RuntimeError):
            pass
        return True

    def rename_reference(self):
        selecionado = self._referencia_selecionada()
        if selecionado is None:
            return
        nome, caminho = selecionado
        novo, ok = QtWidgets.QInputDialog.getText(
            self.widget(), i18n.t('Renomear referência'), i18n.t('Novo nome:'), text=nome
        )
        if not ok or not novo.strip():
            return
        pasta = self.folder()
        itens = mb.carregar_layout(pasta)
        indice, item = self._item_do_arquivo(itens, caminho)
        documento = None
        if item is not None:
            documento = self._quadro_aberto()
            if documento is None:
                helpers.show_info(
                    i18n.t('Moodboard'),
                    i18n.t('Abra o quadro antes de renomear uma referência que está nele (o link da camada precisa ser refeito).'),
                )
                return
        try:
            novo_caminho = renomear_recurso(caminho, novo.strip())
        except OSError as erro:
            helpers.show_info(i18n.t('Moodboard'), i18n.t('Falha ao renomear: {0}').format(erro))
            return
        if item is not None and documento is not None:
            self._remover_camada(documento, item)
            camada = self._montar_camada(
                documento,
                novo_caminho,
                os.path.splitext(os.path.basename(novo_caminho))[0],
                item.get("escala", 1.0),
                item.get("x", 0.0),
                item.get("y", 0.0),
            )
            if camada is not None:
                item["arquivo"] = os.path.basename(novo_caminho)
                item["camada"] = camada.uniqueId().toString()
                mb.salvar_layout(pasta, itens)
            documento.refreshProjection()
            self._salvar_quadro(documento)
        self.refresh()

    def delete_reference(self):
        selecionado = self._referencia_selecionada()
        if selecionado is None:
            return
        nome, caminho = selecionado
        resposta = QtWidgets.QMessageBox.question(
            self.widget(),
            i18n.t('Apagar referência?'),
            i18n.t("Apagar '{0}'? O arquivo sai da pasta do moodboard.").format(nome),
            DIALOG_YES | DIALOG_NO,
            DIALOG_NO,
        )
        if resposta != DIALOG_YES:
            return
        pasta = self.folder()
        itens = mb.carregar_layout(pasta)
        indice, item = self._item_do_arquivo(itens, caminho)
        documento = None
        if item is not None:
            documento = self._quadro_aberto()
            if documento is None:
                helpers.show_info(
                    i18n.t('Moodboard'),
                    i18n.t('Abra o quadro antes de apagar uma referência que está nele (a camada de arquivo ficaria sem link).'),
                )
                return
        try:
            mb.apagar_referencia(caminho)
        except (OSError, ValueError) as erro:
            helpers.show_info(i18n.t('Moodboard'), i18n.t('Falha ao apagar: {0}').format(erro))
            return
        if item is not None and documento is not None:
            self._remover_camada(documento, item)
            itens.pop(indice)
            mb.salvar_layout(pasta, itens)
            documento.refreshProjection()
            self._salvar_quadro(documento)
        self.refresh()
