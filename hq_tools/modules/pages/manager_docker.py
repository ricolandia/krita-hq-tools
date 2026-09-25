"""Docker de páginas: gerenciador com miniaturas (aba única).

O projeto é uma pasta com arquivos ``.kra``: "Novo projeto..." cria a pasta,
"Abrir projeto..." lê o ``comicConfig.json`` de um projeto CPMT e "Pasta..."
abre qualquer pasta com páginas. Clique duplo abre a página; arrastar reordena
(gravado no projeto CPMT quando houver).
"""

import os

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
    standard_icon,
)
from ...core.config import Config
from ...core.cpmt import CPMTProject, create_project_with_page
from ...core.thumbs import thumbnail_pixmap
from ..biblioteca import core as biblioteca_core
from . import generator, roteiro


class PageListWidget(QtWidgets.QListWidget):
    orderChanged = pyqtSignal()

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


class PagesDocker(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: páginas")
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
        main = widgets.QWidget(self)
        layout = widgets.QVBoxLayout(main)

        group_project = widgets.QGroupBox("Projeto")
        project_layout = widgets.QVBoxLayout(group_project)
        self.lbl_project = widgets.QLabel(
            "Nenhum projeto aberto. Crie um projeto a partir da página salva, "
            "abra um comicConfig.json do CPMT ou abra uma pasta com .kra."
        )
        self.lbl_project.setWordWrap(True)
        project_layout.addWidget(self.lbl_project)
        row = widgets.QHBoxLayout()
        button_new = widgets.QPushButton("Novo projeto...")
        button_new.setIcon(standard_icon("SP_FileDialogNewFolder"))
        button_new.setToolTip(
            "Usa a pasta da página atual salva como pasta do projeto"
        )
        button_new.clicked.connect(self.new_project)
        row.addWidget(button_new)
        button_open = widgets.QPushButton("Abrir projeto...")
        button_open.setIcon(standard_icon("SP_DialogOpenButton"))
        button_open.setToolTip("Abre o comicConfig.json de um projeto CPMT")
        button_open.clicked.connect(self.pick_project)
        row.addWidget(button_open)
        button_folder = widgets.QPushButton("Pasta...")
        button_folder.setIcon(standard_icon("SP_DirOpenIcon"))
        button_folder.setToolTip("Abre uma pasta com arquivos .kra")
        button_folder.clicked.connect(self.pick_folder)
        row.addWidget(button_folder)
        project_layout.addLayout(row)
        layout.addWidget(group_project)

        group_page = widgets.QGroupBox("Página")
        page_layout = widgets.QHBoxLayout(group_page)
        button_new_page = widgets.QPushButton("Criar próxima página")
        button_new_page.setIcon(standard_icon("SP_FileDialogNewFolder"))
        button_new_page.setToolTip(
            "Cria uma página nova na pasta do projeto e atualiza as miniaturas"
        )
        button_new_page.clicked.connect(self.create_next_page)
        page_layout.addWidget(button_new_page)
        button_guides = widgets.QPushButton("Guias de margem")
        button_guides.setToolTip(
            "Cria 12 guias no documento ativo (0,5 / 1 / 1,5 cm por lado); "
            "substitui as guias existentes"
        )
        button_guides.clicked.connect(self.create_margin_guides)
        page_layout.addWidget(button_guides)
        layout.addWidget(group_page)

        group_list = widgets.QGroupBox("Páginas")
        list_layout = widgets.QVBoxLayout(group_list)
        row2 = widgets.QHBoxLayout()
        button_refresh = widgets.QPushButton("Atualizar miniaturas")
        button_refresh.setIcon(standard_icon("SP_BrowserReload"))
        button_refresh.clicked.connect(self.refresh)
        row2.addWidget(button_refresh)
        button_open_folder = widgets.QPushButton("Abrir pasta")
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

        hint = widgets.QLabel(
            "Clique duas vezes para abrir a página. Arraste para reordenar "
            "(a ordem é salva no projeto CPMT quando aberto por ele)."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.setWidget(main)

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
        try:
            create_project_with_page(folder, page_name, os.path.basename(folder))
        except OSError as error:
            helpers.show_info(
                "Novo projeto",
                "Não foi possível gravar o projeto: {0}".format(error),
            )
            return
        self.config.set("biblioteca.folder", biblio)
        self._load_project(os.path.join(folder, "comicConfig.json"))
        helpers.show_info(
            "Novo projeto",
            "Projeto criado em {0}.\n\nA biblioteca (balões, painéis e "
            "onomatopeias) fica na subpasta 'biblioteca'.".format(folder),
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

    def create_next_page(self):
        """Cria uma página nova na pasta do projeto e atualiza a grade."""
        if not self.folder:
            helpers.show_message("Crie ou abra um projeto primeiro.")
            return
        fmt = self.config.get("pages.format", "A4") or "A4"
        dpi = int(self.config.get("pages.dpi", 300) or 300)

        if self.project is not None:
            numero = len(self.project.page_relatives()) + 1
            filename = self.project.next_page_name(offset=numero)
            path = os.path.join(self.project.pages_dir(), filename)
            if self.project.pages_location:
                relative = os.path.join(self.project.pages_location, filename)
            else:
                relative = filename
            titulo = "{0} - pagina {1}".format(self.project.project_name, numero)
        else:
            try:
                existentes = [
                    name
                    for name in os.listdir(self.folder)
                    if name.lower().endswith(".kra")
                ]
            except OSError:
                existentes = []
            numero = len(existentes) + 1
            filename = "pagina_{0:03d}.kra".format(numero)
            path = os.path.join(self.folder, filename)
            relative = filename
            titulo = "pagina {0}".format(numero)

        page = {
            "index": numero,
            "format": fmt,
            "dpi": dpi,
            "margin": 0.05,
            "gutter": 0.0,
            "panels": [(0.05, 0.05, 0.9, 0.9)],
            "balloons": [],
        }
        width, height = roteiro.page_pixels(page, fmt, dpi)
        panel_svg = generator._panels_svg(page, width, height, dpi)
        try:
            document = generator._build_document(
                page, titulo, panel_svg, "", width, height, dpi
            )
            generator._save_document(document, path)
        except (RuntimeError, OSError) as error:
            helpers.show_message("Falha ao criar a página: {0}".format(error))
            return

        if self.project is not None:
            self.project.register_pages([relative])
        self.refresh()
        helpers.show_message("Página criada: {0}".format(filename))

    def create_margin_guides(self):
        """Cria 12 guias no documento ativo: 0,5 / 1 / 1,5 cm por lado."""
        document = helpers.active_document()
        if document is None:
            helpers.show_message("Abra a página para criar as guias.")
            return
        dpi = helpers.document_dpi(document)
        width = document.width()
        height = document.height()
        verticais = []
        horizontais = []
        for margem in (0.5, 1.0, 1.5):
            px = float(margem) * dpi / 2.54
            verticais.extend([px, width - px])
            horizontais.extend([px, height - px])
        document.setVerticalGuides(sorted(set(round(v, 3) for v in verticais)))
        document.setHorizontalGuides(sorted(set(round(v, 3) for v in horizontais)))
        helpers.show_message("Guias de margem criadas (0,5 / 1 / 1,5 cm por lado).")

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
        self._loading = True
        self.list_pages.clear()
        for relative, path in self._page_paths():
            item = QtWidgets.QListWidgetItem(os.path.basename(path))
            item.setData(USER_ROLE, relative)
            item.setToolTip(path)
            pixmap = thumbnail_pixmap(path)
            if pixmap is not None:
                item.setIcon(QtGui.QIcon(pixmap))
            self.list_pages.addItem(item)
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
        self.project.set_page_order(ordered)
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