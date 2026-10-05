"""Docker de páginas: gerenciador com miniaturas (aba única).

O projeto é uma pasta com arquivos ``.kra``: "Novo projeto..." usa a pasta da
página salva, "Abrir projeto..." lê um ``comicConfig.json`` do CPMT e "Pasta..."
abre qualquer pasta. "Criar próxima página" gera (ou usa o modelo de página)
com guias de margem automáticas. Referências: marca a camada como referência
travada ou importa um PNG como camada de arquivo.
"""

import os
import shutil

from krita import DockWidget, Krita

from ...core import krita_helpers as helpers
from ...core.compat import (
    DIALOG_NO,
    DIALOG_YES,
    DRAG_INTERNAL_MOVE,
    ICON_MODE,
    LIST_ADJUST,
    MOVE_ACTION,
    USER_ROLE,
    QtCore,
    QtGui,
    QtWidgets,
    pyqtSignal,
    qlibrary_prefix,
)
from ...core.config import Config
from ...core.cpmt import CPMTError, CPMTProject, create_project_with_page
from ...core.paths import KRITA_HOME, MODELOS_DIR
from ...core import registro, ui
from ...core.thumbs import thumbnail_pixmap
from ..biblioteca import core as biblioteca_core
from . import generator, guias, modelos as modelos_lib, roteiro

FORMATO_ITENS = (
    ("A4", "A4"),
    ("A5", "A5"),
    ("A3", "A3 (297 x 420 mm)"),
    ("tirinha", "Tirinha (297 x 210 mm)"),
    ("americano", "Americano"),
    ("tankobon", "Tankobon"),
    ("quadrado", "Quadrado"),
    ("livre", "Livre (largura x altura)"),
)


def _descartar_pagina_orphã(document, path):
    """Fecha o documento e apaga o ``.kra`` que ficou sem registro.

    Só mexe no arquivo que o próprio fluxo acabou de criar: se a remoção
    falhar (permissão, arquivo aberto em outro app), o erro vai para o log em
    vez de mascarar o aviso que o usuário já recebeu.
    """
    helpers.close_document(document)
    try:
        if os.path.isfile(path):
            os.unlink(path)
    except OSError as error:
        helpers.log("não foi possível remover a página órfã {0}: {1}".format(path, error))


class PageListWidget(QtWidgets.QListWidget):
    orderChanged = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


class PagesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: páginas")
        registro.registrar("pages", self)
        self.config = Config()
        self.project = None
        self.folder = ""
        self._loading = False
        self._build_ui()
        self._restore_last()

    def canvasChanged(self, canvas):
        pass

    def _restore_last(self):
        last_project = self.config.get("pages.last_project")
        if last_project and os.path.isfile(last_project):
            self._load_project(last_project)
            return
        last_folder = self.config.get("pages.last_folder")
        if last_folder and os.path.isdir(last_folder):
            self.project = None
            self.folder = last_folder
            self.lbl_project.setText("Projeto: {0}".format(last_folder))
            self.refresh()

    def _build_ui(self):
        widgets = QtWidgets
        main, layout = ui.painel(self)

        group_project = widgets.QGroupBox("Projeto")
        project_layout = ui.espacamento(widgets.QVBoxLayout(group_project), margem=0, espaco=ui.GAP)
        self.lbl_project = ui.rotulo_info(
            "Nenhum projeto aberto. Crie um projeto a partir da página salva, "
            "abra um comicConfig.json do CPMT ou abra uma pasta com .kra.")
        project_layout.addWidget(self.lbl_project)
        row = widgets.QHBoxLayout()
        button_new = ui.botao("Novo projeto...", "Usa a pasta da página atual salva como pasta do projeto.", icone_chave="novo")
        button_new.clicked.connect(self.new_project)
        row.addWidget(button_new)
        button_open = ui.botao("Abrir projeto...", "Abre o comicConfig.json de um projeto CPMT", icone_chave="abrir")
        button_open.clicked.connect(self.pick_project)
        row.addWidget(button_open)
        button_folder = ui.botao("Pasta...", "Abre uma pasta com arquivos .kra", icone_chave="pasta")
        button_folder.clicked.connect(self.pick_folder)
        row.addWidget(button_folder)
        project_layout.addLayout(row)
        layout.addWidget(group_project)

        group_page = widgets.QGroupBox("Página")
        page_layout = ui.espacamento(widgets.QVBoxLayout(group_page), margem=0, espaco=ui.GAP)
        row_page = widgets.QHBoxLayout()
        button_new_page = ui.botao(
            "Criar próxima página",
            "Cria uma página nova (formato, DPI, modelo) na pasta do projeto",
            icone_chave="novo",
        )
        button_new_page.clicked.connect(self.create_next_page)
        row_page.addWidget(button_new_page)
        button_guides = ui.botao(
            "Guias de margem",
            "Cria 12 guias no documento ativo (0,5 / 1 / 1,5 cm por lado); "
            "substitui as guias existentes",
        )
        button_guides.clicked.connect(self.create_margin_guides)
        row_page.addWidget(button_guides)
        page_layout.addLayout(row_page)
        row_model = widgets.QHBoxLayout()
        button_model = ui.botao(
            "Definir modelo de página...",
            "Usa a página atual ou um template de HQ do Krita como modelo "
            "para as próximas páginas",
        )
        button_model.clicked.connect(self.define_model)
        row_model.addWidget(button_model)
        self.lbl_model = ui.rotulo_info("")
        row_model.addWidget(self.lbl_model, 1)
        page_layout.addLayout(row_model)
        layout.addWidget(group_page)
        layout.addWidget(ui.separador())

        group_ref = widgets.QGroupBox("Referência")
        ref_layout = ui.espacamento(widgets.QHBoxLayout(group_ref), margem=0, espaco=ui.GAP)
        button_ref = ui.botao(
            "Camada de referência",
            "Marca a camada selecionada como referência (rótulo, trava e "
            "opacidade reduzida)",
        )
        button_ref.clicked.connect(self.mark_reference_layer)
        ref_layout.addWidget(button_ref)
        button_import = ui.botao(
            "Importar referência (PNG)...",
            "Insere um PNG como camada de referência travada no grupo ativo",
            icone_chave="abrir",
        )
        button_import.clicked.connect(self.import_reference)
        ref_layout.addWidget(button_import)
        layout.addWidget(group_ref)
        layout.addWidget(ui.separador())

        group_list = widgets.QGroupBox("Páginas")
        list_layout = ui.espacamento(widgets.QVBoxLayout(group_list), margem=0, espaco=ui.GAP)
        row2 = widgets.QHBoxLayout()
        button_refresh = ui.botao(
            "Atualizar miniaturas", "Regera as miniaturas das páginas.", icone_chave="atualizar"
        )
        button_refresh.clicked.connect(self.refresh)
        row2.addWidget(button_refresh)
        button_open_folder = ui.botao(
            "Abrir pasta", "Abre a pasta do projeto atual no explorador.", icone_chave="pasta"
        )
        button_open_folder.clicked.connect(self.open_current_folder)
        row2.addWidget(button_open_folder)
        list_layout.addLayout(row2)

        self.list_pages = PageListWidget()
        self.list_pages.setViewMode(ICON_MODE)
        self.list_pages.setIconSize(QtCore.QSize(150, 210))
        self.list_pages.setGridSize(QtCore.QSize(180, 250))
        self.list_pages.setResizeMode(LIST_ADJUST)
        self.list_pages.setDragDropMode(DRAG_INTERNAL_MOVE)
        self.list_pages.setDefaultDropAction(MOVE_ACTION)
        self.list_pages.setWordWrap(True)
        self.list_pages.itemDoubleClicked.connect(self.open_page)
        self.list_pages.orderChanged.connect(self._on_order_changed)
        list_layout.addWidget(self.list_pages, 1)
        layout.addWidget(group_list, 1)

        hint = ui.rotulo(
            "Clique duas vezes para abrir a página. Arraste para reordenar "
            "(a ordem é salva no projeto CPMT quando aberto por ele).")
        layout.addWidget(hint)

        self.setWidget(main)
        self._refresh_model_label()

    # ------------------------------------------------------------------ projeto

    def new_project(self):
        """Cria o projeto a partir da pasta da página atual salva."""
        document = helpers.active_document()
        if document is None:
            helpers.show_info(
                "Novo projeto",
                "Abra e salve a página antes de criar o projeto.",
            )
            return
        if not document.fileName():
            answer = QtWidgets.QMessageBox.question(
                self.widget(),
                "Novo projeto",
                "Salve a página atual em uma pasta. Essa pasta será a pasta "
                "do projeto.\n\nSalvar a página agora?",
                DIALOG_YES | DIALOG_NO,
            )
            if answer != DIALOG_YES:
                return
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self.widget(),
                "Salvar a página (pasta do projeto)",
                self.folder or os.path.expanduser("~"),
                "Krita (*.kra)",
            )
            if not path:
                return
            if not path.lower().endswith(".kra"):
                path += ".kra"
            if not document.saveAs(path):
                helpers.show_info(
                    "Novo projeto",
                    "Não foi possível salvar a página.",
                )
                return
        folder = os.path.dirname(document.fileName())
        page_name = os.path.basename(document.fileName())
        biblio = os.path.join(folder, "biblioteca")
        for _, _, sub in biblioteca_core.TIPOS:
            try:
                os.makedirs(os.path.join(biblio, sub), exist_ok=True)
            except OSError as error:
                helpers.show_info(
                    "Novo projeto",
                    "Não foi possível criar a biblioteca: {0}".format(error),
                )
                return
        if CPMTProject.is_project(folder):
            try:
                project = CPMTProject(folder)
                relatives = [os.path.normpath(item) for item in project.page_relatives()]
                if os.path.normpath(page_name) not in relatives:
                    project.register_pages([page_name])
            except (OSError, ValueError) as error:
                helpers.show_info(
                    "Novo projeto",
                    "Não foi possível abrir o projeto existente: {0}".format(error),
                )
                return
            aviso = "Projeto existente atualizado em {0}."
        else:
            try:
                create_project_with_page(folder, page_name, os.path.basename(folder))
            except (OSError, CPMTError) as error:
                helpers.show_info(
                    "Novo projeto",
                    "Não foi possível gravar o projeto: {0}".format(error),
                )
                return
            aviso = "Projeto criado em {0}."
        self.config.set("biblioteca.folder", biblio)
        self._load_project(os.path.join(folder, "comicConfig.json"))
        helpers.show_info(
            "Novo projeto",
            aviso.format(folder) + "\n\nA biblioteca (balões, painéis e "
            "onomatopeias) fica na subpasta 'biblioteca'.",
        )

    def pick_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.widget(),
            "Abrir comicConfig.json do CPMT",
            self.folder or os.path.expanduser("~"),
            "comicConfig.json",
        )
        if path:
            self._load_project(path)

    def pick_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self.widget(), "Pasta com páginas .kra", self.folder or os.path.expanduser("~")
        )
        if folder:
            self.project = None
            self.folder = folder
            self.config.set("pages.last_folder", folder)
            self.lbl_project.setText("Projeto: {0}".format(folder))
            self.refresh()

    def _load_project(self, config_path):
        try:
            self.project = CPMTProject(os.path.dirname(config_path))
        except (OSError, ValueError):
            helpers.show_message("Não foi possível abrir o projeto CPMT.")
            return
        self.folder = self.project.pages_dir()
        self.lbl_project.setText(
            "Projeto: {0} ({1} páginas)".format(
                self.project.project_name, len(self.project.page_relatives())
            )
        )
        self.config.set("pages.last_project", config_path)
        self.refresh()

    # ------------------------------------------------------------------ páginas

    def _new_page_dialog(self):
        """Diálogo de nova página; devolve opções ou None se cancelado."""
        widgets = QtWidgets
        dialog = widgets.QDialog(self.widget())
        dialog.setWindowTitle("Criar página")
        form = widgets.QFormLayout(dialog)

        cmb_formato = widgets.QComboBox()
        for chave, rotulo in FORMATO_ITENS:
            cmb_formato.addItem(rotulo, chave)
        atual = self.config.get("pages.format", "A4") or "A4"
        index = cmb_formato.findData(atual)
        if index >= 0:
            cmb_formato.setCurrentIndex(index)
        form.addRow("Formato:", cmb_formato)

        spin_dpi = widgets.QSpinBox()
        spin_dpi.setRange(72, 1200)
        spin_dpi.setValue(self.config.get_int("pages.dpi", 300))
        form.addRow("DPI:", spin_dpi)

        spin_w = widgets.QDoubleSpinBox()
        spin_w.setRange(50, 600)
        spin_w.setValue(210)
        spin_w.setSuffix(" mm")
        spin_h = widgets.QDoubleSpinBox()
        spin_h.setRange(50, 600)
        spin_h.setValue(210)
        spin_h.setSuffix(" mm")
        row_livre = widgets.QHBoxLayout()
        row_livre.addWidget(ui.rotulo("L:"))
        row_livre.addWidget(spin_w)
        row_livre.addWidget(ui.rotulo("A:"))
        row_livre.addWidget(spin_h)
        form.addRow("Livre:", row_livre)

        spin_strip = widgets.QSpinBox()
        spin_strip.setRange(1, 8)
        spin_strip.setValue(self.config.get_int("pages.strip_panels", 3))
        form.addRow("Painéis da tirinha:", spin_strip)

        def _update_enabled():
            chave = cmb_formato.currentData()
            row_livre.setEnabled(chave == "livre")
            spin_strip.setEnabled(chave == "tirinha")

        cmb_formato.currentIndexChanged.connect(_update_enabled)
        _update_enabled()

        modelo_path = self.config.get("pages.model") or ""
        chk_modelo = widgets.QCheckBox("Usar modelo de página")
        chk_modelo.setChecked(bool(self.config.get("pages.use_model", False)))
        chk_modelo.setEnabled(bool(modelo_path) and os.path.isfile(modelo_path))
        form.addRow("", chk_modelo)

        buttons_row = widgets.QHBoxLayout()
        button_ok = ui.botao("Criar", "Cria a pasta do projeto e a primeira página.")
        button_ok.setDefault(True)
        button_cancel = ui.botao("Cancelar", "Fecha a janela sem criar nada.")
        button_ok.clicked.connect(dialog.accept)
        button_cancel.clicked.connect(dialog.reject)
        buttons_row.addStretch(1)
        buttons_row.addWidget(button_cancel)
        buttons_row.addWidget(button_ok)
        form.addRow(buttons_row)

        if dialog.exec() != 1:
            return None
        chave = cmb_formato.currentData()
        dpi = spin_dpi.value()
        self.config.set("pages.format", chave)
        self.config.set("pages.dpi", dpi)
        self.config.set("pages.strip_panels", spin_strip.value())
        self.config.set("pages.use_model", chk_modelo.isChecked())
        return {
            "formato": chave,
            "dpi": dpi,
            "w_mm": spin_w.value(),
            "h_mm": spin_h.value(),
            "strip_panels": spin_strip.value(),
            "modelo_path": modelo_path if chk_modelo.isChecked() else "",
        }

    def create_next_page(self):
        """Cria uma página nova na pasta do projeto e atualiza a grade."""
        if not self.folder:
            helpers.show_info("Nova página", "Crie ou abra um projeto primeiro.")
            return
        opcoes = self._new_page_dialog()
        if opcoes is None:
            return
        fmt = opcoes["formato"]
        dpi = opcoes["dpi"]
        if fmt == "livre":
            width_px = int(round(opcoes["w_mm"] * dpi / 25.4))
            height_px = int(round(opcoes["h_mm"] * dpi / 25.4))
        else:
            width_px, height_px = roteiro.page_pixels({"format": fmt}, fmt, dpi)

        if self.project is not None:
            numero = self.project.page_number + 1
            filename = self.project.next_page_name(offset=1)
            path = os.path.join(self.project.pages_dir(), filename)
            while os.path.exists(path):
                numero += 1
                filename = self.project.next_page_name(
                    offset=numero - self.project.page_number
                )
                path = os.path.join(self.project.pages_dir(), filename)
            if self.project.pages_location:
                relative = os.path.normpath(
                    os.path.join(self.project.pages_location, filename)
                )
            else:
                relative = filename
            titulo = "{0} - pagina {1}".format(self.project.project_name, numero)
        else:
            numero = self._proximo_indice_livre()
            filename = "pagina_{0:03d}.kra".format(numero)
            path = os.path.join(self.folder, filename)
            relative = filename
            titulo = "pagina {0}".format(numero)

        modelo = opcoes.get("modelo_path") or ""
        if modelo and os.path.isfile(modelo):
            document = None
            try:
                shutil.copy2(modelo, path)
                document = Krita.instance().openDocument(path)
                if document is None:
                    raise RuntimeError("não foi possível abrir o modelo")
                self._adaptar_modelo(
                    document, fmt, width_px, height_px, dpi, opcoes["strip_panels"]
                )
                self.apply_margin_guides(document)
                if not document.saveAs(path):
                    raise RuntimeError("não foi possível salvar a página adaptada")
                document.setModified(False)
            except (OSError, RuntimeError) as error:
                helpers.show_info(
                    "Nova página", "Falha ao usar o modelo: {0}".format(error)
                )
                # A cópia do modelo foi colada em `path` antes da falha: sem
                # remover, sobra um .kra na pasta de páginas que não está na
                # lista do CPMT e o usuário só descobre ao recontar os arquivos.
                _descartar_pagina_orphã(document, path)
                return
            helpers.close_document(document)
        else:
            page = {
                "index": numero,
                "format": fmt if fmt != "livre" else "A4",
                "dpi": dpi,
                "margin": 0.05,
                "gutter": 0.0,
                "panels": [(0.05, 0.05, 0.9, 0.9)],
                "balloons": [],
            }
            if fmt == "tirinha":
                page["panels"] = roteiro.build_strip_panels(opcoes["strip_panels"])
            panel_svg = generator.panels_svg(page, width_px, height_px, dpi)
            try:
                document = generator.build_page_document(
                    page, titulo, panel_svg, "", width_px, height_px, dpi
                )
                self.apply_margin_guides(document)
                generator.save_page(document, path)
            except (RuntimeError, OSError) as error:
                helpers.show_info("Nova página", "Falha ao criar a página: {0}".format(error))
                return

        registrada = True
        if self.project is not None:
            try:
                self.project.register_pages([relative])
            except (OSError, CPMTError) as error:
                registrada = False
                helpers.log(
                    "página criada, mas registro no CPMT falhou: {0}".format(error)
                )
        self.refresh()
        if registrada:
            helpers.show_info("Nova página", "Página criada: {0}".format(filename))
        else:
            helpers.show_info(
                "Nova página",
                "Página criada ({0}), mas não foi possível registrá-la no "
                "projeto; confira a lista do CPMT.".format(filename),
            )

    def _proximo_indice_livre(self):
        """Próximo número de página livre (sem sobrescrever buracos)."""
        import re as _re

        numeros = []
        try:
            nomes = os.listdir(self.folder)
        except OSError:
            nomes = []
        for nome in nomes:
            match = _re.search(r"pagina_(\d+)\.kra$", nome)
            if match:
                numeros.append(int(match.group(1)))
        numero = 1
        while numero in numeros:
            numero += 1
        return numero

    def _adaptar_modelo(self, document, fmt, width_px, height_px, dpi, strip_panels):
        """Redimensiona e/ou adapta o modelo ao formato pedido."""
        if document.width() != width_px or document.height() != height_px:
            document.scaleImage(width_px, height_px, dpi, dpi, "Bilinear")
        if fmt == "tirinha":
            self._aplicar_tira(document, strip_panels, width_px, height_px, dpi)
        document.refreshProjection()

    def _aplicar_tira(self, document, count, width_px, height_px, dpi):
        """Substitui os painéis do documento por uma tira horizontal."""
        ocultar = []
        for node in document.rootNode().findChildNodes(recursive=True):
            nome = node.name().lower()
            if node.type() == "vectorlayer" and nome in ("panels", "mask"):
                ocultar.append(node)
            elif node.type() == "clonelayer" and any(
                parte in nome for parte in ("outline", "contorno", "clone")
            ):
                ocultar.append(node)
            elif node.type() == "vectorlayer" and any(
                parte in nome for parte in ("outline", "contorno")
            ):
                ocultar.append(node)

        target = None
        for node in ocultar:
            pai = node.parentNode()
            if pai is not None and pai.type() == "grouplayer":
                target = pai
                break
        if target is None:
            for node in document.rootNode().findChildNodes(recursive=True):
                if node.type() == "grouplayer" and node.name().lower().startswith("page"):
                    target = node
                    break
        if target is None:
            target = document.rootNode()

        for node in ocultar:
            if node.parentNode() == target:
                node.setVisible(False)

        acima = None
        for child in target.childNodes():
            if child.name() == "Ink":
                acima = child
                break

        page = {"panels": roteiro.build_strip_panels(count), "format": "tirinha", "dpi": dpi}
        svg = generator.panels_svg(page, width_px, height_px, dpi)
        nova = document.createVectorLayer("panels")
        target.addChildNode(nova, acima)
        nova.addShapesFromSvg(svg)
        clone = document.createCloneLayer("panels contorno", nova)
        if clone is not None:
            clone.setBlendingMode("multiply")
            target.addChildNode(clone, nova)

    def apply_margin_guides(self, document):
        """Cria as guias de margem sem apagar as guias que o autor já tinha.

        O libkis troca a lista inteira a cada chamada; mesclar com as guias
        atuais preserva perspectiva, sangria e corte.
        """
        dpi = helpers.document_dpi(document)
        width = document.width()
        height = document.height()
        verticais, horizontais = guias.posicoes_de_margem(width, height, dpi)
        try:
            existentes_v = list(document.verticalGuides())
            existentes_h = list(document.horizontalGuides())
        except (AttributeError, RuntimeError, TypeError):
            existentes_v, existentes_h = [], []
        document.setVerticalGuides(guias.mesclar(existentes_v, verticais))
        document.setHorizontalGuides(guias.mesclar(existentes_h, horizontais))

    def create_margin_guides(self):
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra a página para criar as guias.")
            return
        self.apply_margin_guides(document)
        helpers.show_message(
            "Guias de margem criadas (0,5 / 1 / 1,5 cm por lado), mantendo as "
            "guias existentes."
        )

    # ------------------------------------------------------------------ modelo

    def _refresh_model_label(self):
        modelo = self.config.get("pages.model") or ""
        if modelo and os.path.isfile(modelo):
            self.lbl_model.setText("Modelo: {0}".format(os.path.basename(modelo)))
        else:
            self.lbl_model.setText("Sem modelo definido (gera o padrão).")

    def _listar_templates_krita(self):
        """Templates de HQ do Krita: prefixo do Qt e pasta de templates do usuário."""
        candidatos = []
        prefixo = qlibrary_prefix()
        if prefixo:
            candidatos.append(os.path.join(prefixo, "share", "krita", "templates", "comics"))
        candidatos.append(os.path.join(KRITA_HOME, "templates", "comics"))
        resultado = {}
        for pasta in candidatos:
            if not os.path.isdir(pasta):
                continue
            for raiz in (pasta, os.path.join(pasta, ".source")):
                if not os.path.isdir(raiz):
                    continue
                for nome in sorted(os.listdir(raiz)):
                    if nome.lower().endswith(".kra") and nome not in resultado:
                        resultado[nome] = os.path.join(raiz, nome)
        return resultado

    def _gerar_modelos_padrao(self):
        """Gera os modelos de página do HQ Tools na pasta de modelos."""
        os.makedirs(MODELOS_DIR, exist_ok=True)
        gerados = []
        for nome, formato, chave in modelos_lib.MODELOS:
            dpi = 300
            width_px, height_px = roteiro.page_pixels({"format": formato}, formato, dpi)
            page = {
                "index": 1,
                "format": formato,
                "dpi": dpi,
                "margin": 0.05,
                "gutter": 0.0,
                "panels": modelos_lib.layout_paineis(chave),
                "balloons": [],
            }
            panel_svg = generator.panels_svg(page, width_px, height_px, dpi)
            try:
                with helpers.cursor_espera():
                    document = generator.build_page_document(
                        page, nome, panel_svg, "", width_px, height_px, dpi
                    )
                    self.apply_margin_guides(document)
                    destino = os.path.join(
                        MODELOS_DIR, "modelo-{0}.kra".format(modelos_lib.slug(nome))
                    )
                    generator.save_page(document, destino)
                gerados.append((nome, destino))
            except (RuntimeError, OSError):
                continue
        return gerados

    def define_model(self):
        """Escolhe o modelo de página: página atual salva ou template do Krita."""
        widgets = QtWidgets
        dialog = widgets.QDialog(self.widget())
        dialog.setWindowTitle("Definir modelo de página")
        layout = ui.espacamento(widgets.QVBoxLayout(dialog), margem=0, espaco=ui.GAP)
        layout.addWidget(
            ui.rotulo(
                "O modelo é copiado para {0} e usado pelas próximas páginas.".format(
                    MODELOS_DIR
                )
            )
        )
        cmb = widgets.QComboBox()
        cmb.addItem("Página atual (precisa estar salva)", "atual")
        for nome, caminho in self._listar_templates_krita().items():
            cmb.addItem("Template do Krita: {0}".format(nome), caminho)
        nomes_por_slug = modelos_lib.nome_por_slug()
        if os.path.isdir(MODELOS_DIR):
            for nome in sorted(os.listdir(MODELOS_DIR)):
                if not (nome.lower().endswith(".kra") and nome.startswith("modelo-")):
                    continue
                slug_arquivo = nome[len("modelo-"):-4]
                rotulo = nomes_por_slug.get(slug_arquivo, nome)
                caminho = os.path.join(MODELOS_DIR, nome)
                if cmb.findData(caminho) < 0:
                    cmb.addItem("HQ Tools: {0}".format(rotulo), caminho)
        gerar_row = widgets.QHBoxLayout()
        button_gerar = ui.botao(
            "Gerar modelos padrão do HQ Tools",
            "Cria A4, A3, tirinhas (1-3) e grades (2x2, 3x3) na pasta de modelos",
            icone_chave="novo",
        )
        gerar_row.addWidget(button_gerar)

        def _gerar_agora():
            gerados = self._gerar_modelos_padrao()
            for nome, caminho in gerados:
                if cmb.findData(caminho) < 0:
                    cmb.addItem("HQ Tools: {0}".format(nome), caminho)
            helpers.show_info(
                "Modelo de página",
                "{0} modelos gerados em {1}.".format(len(gerados), MODELOS_DIR),
            )

        button_gerar.clicked.connect(_gerar_agora)
        layout.addLayout(gerar_row)
        layout.addWidget(cmb)
        buttons_row = widgets.QHBoxLayout()
        button_ok = ui.botao("Usar como modelo", "Usa o modelo escolhido nas próximas páginas.")
        button_ok.setDefault(True)
        button_cancel = ui.botao("Cancelar", "Fecha a janela sem escolher modelo.")
        button_ok.clicked.connect(dialog.accept)
        button_cancel.clicked.connect(dialog.reject)
        buttons_row.addStretch(1)
        buttons_row.addWidget(button_cancel)
        buttons_row.addWidget(button_ok)
        layout.addLayout(buttons_row)

        if dialog.exec() != 1:
            return
        escolha = cmb.currentData()
        if escolha == "atual":
            document = helpers.active_document()
            if document is None or not document.fileName():
                helpers.show_info(
                    "Modelo de página",
                    "Salve a página atual antes de usá-la como modelo.",
                )
                return
            origem = document.fileName()
        else:
            origem = escolha if os.path.isfile(escolha) else None
            if not origem:
                helpers.show_info("Modelo de página", "Modelo não encontrado.")
                return
        os.makedirs(MODELOS_DIR, exist_ok=True)
        base = os.path.basename(origem)
        if base.startswith("modelo-"):
            destino = os.path.join(MODELOS_DIR, base)
        else:
            destino = os.path.join(MODELOS_DIR, "modelo-{0}".format(base))
        try:
            shutil.copy2(origem, destino)
        except OSError as error:
            helpers.show_info("Modelo de página", "Falha ao copiar: {0}".format(error))
            return
        self.config.set("pages.model", destino)
        self.config.set("pages.use_model", True)
        self._refresh_model_label()
        helpers.show_info(
            "Modelo de página",
            "Modelo definido: {0}.\n\nAs próximas páginas usarão este modelo "
            "(formato/DPI escolhidos no diálogo adaptam tamanho e tirinha).".format(
                os.path.basename(destino)
            ),
        )

    # ------------------------------------------------------------------ referência

    def mark_reference_layer(self):
        """Marca a camada selecionada como referência (rótulo, trava, opacidade)."""
        document = helpers.active_document()
        if document is None:
            helpers.show_info("Referência", "Abra um documento.")
            return
        node = document.activeNode()
        if node is None:
            helpers.show_info("Referência", "Selecione a camada a marcar.")
            return
        node.setColorLabel(1)
        node.setLocked(True)
        node.setOpacity(150)
        document.refreshProjection()
        helpers.show_info(
            "Referência",
            "Camada '{0}' marcada como referência (travada).".format(node.name()),
        )

    def import_reference(self):
        """Importa um PNG como camada de referência travada no grupo ativo."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.widget(), "Referência (PNG)", os.path.expanduser("~"), "PNG (*.png)"
        )
        if not path:
            return
        document = helpers.active_document()
        if document is None:
            helpers.show_info("Referência", "Abra a página para importar.")
            return
        parent, above = helpers.target_container(document)
        nome = helpers.unique_layer_name(document, "Referência")
        layer = document.createFileLayer(nome, path, "ToImageSize", "Bilinear")
        if layer is None:
            helpers.show_info("Referência", "Não foi possível criar a camada.")
            return
        parent.addChildNode(layer, above)
        layer.setLocked(True)
        layer.setOpacity(150)
        layer.setColorLabel(1)
        document.refreshProjection()
        helpers.show_info(
            "Referência",
            "Referência importada e travada no grupo ativo: {0}".format(
                os.path.basename(path)
            ),
        )

    # ------------------------------------------------------------------ lista

    def open_current_folder(self):
        folder = self.folder
        if not folder:
            helpers.show_message("Crie ou abra um projeto primeiro.")
            return
        os.makedirs(folder, exist_ok=True)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def _page_paths(self):
        if self.project is not None:
            return list(zip(self.project.page_relatives(), self.project.page_paths()))
        if not self.folder:
            return []
        try:
            names = sorted(
                name for name in os.listdir(self.folder) if name.lower().endswith(".kra")
            )
        except OSError:
            return []
        return [(name, os.path.join(self.folder, name)) for name in names]

    def refresh(self):
        # O try/finally importa: `_loading` desligado é o que impede o Qt de
        # disparar `_on_order_changed` ao remontar a lista, o que gravaria uma
        # ordem pela metade. Se a montagem falhasse no meio, a flag ficava
        # ligada e nenhuma reordenação manual voltaria a funcionar na sessão,
        # sem aviso nenhum.
        self._loading = True
        try:
            self.list_pages.clear()
            for relative, path in self._page_paths():
                item = QtWidgets.QListWidgetItem(os.path.basename(path))
                item.setData(USER_ROLE, relative)
                item.setToolTip(path)
                pixmap = thumbnail_pixmap(path)
                if pixmap is not None:
                    item.setIcon(QtGui.QIcon(pixmap))
                self.list_pages.addItem(item)
        finally:
            self._loading = False
        if self.project is not None:
            self.lbl_project.setText(
                "Projeto: {0} ({1} páginas)".format(
                    self.project.project_name, self.list_pages.count()
                )
            )

    def _on_order_changed(self):
        if self._loading or self.project is None:
            return
        ordered = [
            self.list_pages.item(index).data(USER_ROLE)
            for index in range(self.list_pages.count())
        ]
        # Um item sem caminho (item solto arrastado para a lista) viraria
        # "None" no comicConfig.json e o CPMT exportaria a página duas vezes.
        if any(not relative for relative in ordered):
            ordered = [
                relative
                for relative in ordered
                if relative
            ]
        # A gravação pode falhar (arquivo corrompido, sem permissão): sem o
        # try, a exceção subia para o Qt e a tela continuava mostrando a nova
        # ordem, que na verdade nunca foi salva.
        try:
            self.project.set_page_order(ordered)
        except (OSError, CPMTError) as error:
            helpers.show_info(
                "Ordem das páginas",
                "Não foi possível gravar a nova ordem: {0}".format(error),
            )
            self._loading = True
            try:
                self.refresh()
            finally:
                self._loading = False
            return
        self.lbl_project.setText(
            "Projeto: {0} ({1} páginas)".format(
                self.project.project_name, self.list_pages.count()
            )
        )
        helpers.show_message("Ordem das páginas atualizada no projeto.")

    def open_page(self, item):
        relative = item.data(USER_ROLE)
        path = relative
        if self.project is not None:
            path = os.path.join(self.project.root, relative)
        elif self.folder:
            path = os.path.join(self.folder, relative)
        if not os.path.isfile(path):
            helpers.show_message("Arquivo não encontrado: {0}".format(path))
            return
        document = Krita.instance().openDocument(path)
        if document is None:
            helpers.show_message("Não foi possível abrir a página.")
            return
        window = Krita.instance().activeWindow()
        if window is not None:
            window.addView(document)
        Krita.instance().setActiveDocument(document)