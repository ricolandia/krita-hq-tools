"""Leitura e escrita do ``comicsConfig.json`` do Comics Project Management Tools.

O CPMT (plugin embutido do Krita) guarda a lista de páginas como caminhos
relativos à raiz do projeto, junto de ``pageNumber`` (contador de páginas).
Este módulo permite que o HQ Tools leia, reordene e registre páginas geradas.
"""

import json
import os
import re
import tempfile

CONFIG_NAMES = ("comicConfig.json", "comicsConfig.json")


class CPMTProject:
    """Acesso tolerante ao projeto CPMT em uma pasta.

    O CPMT grava ``comicConfig.json`` em UTF-16 (com BOM); o nome antigo
    ``comicsConfig.json`` (UTF-8) continua sendo aceito na leitura.
    """

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.config_name = None
        for name in CONFIG_NAMES:
            if os.path.isfile(os.path.join(self.root, name)):
                self.config_name = name
                break
        if self.config_name is None:
            raise FileNotFoundError(
                "comicConfig.json não encontrado em {0}".format(self.root)
            )
        self.config_path = os.path.join(self.root, self.config_name)
        with open(self.config_path, "rb") as handle:
            head = handle.read(2)
        encoding = "utf-16" if head in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
        with open(self.config_path, "r", encoding=encoding) as handle:
            self.config = json.load(handle)

    @classmethod
    def is_project(cls, root):
        root = os.path.abspath(root)
        return any(
            os.path.isfile(os.path.join(root, name)) for name in CONFIG_NAMES
        )

    @property
    def project_name(self):
        return str(self.config.get("projectName") or "projeto")

    @property
    def pages_location(self):
        return str(self.config.get("pagesLocation") or "pages")

    @property
    def page_number(self):
        return int(self.config.get("pageNumber") or 0)

    def page_relatives(self):
        pages = self.config.get("pages") or []
        return [str(page) for page in pages]

    def page_paths(self):
        return [os.path.join(self.root, page) for page in self.page_relatives()]

    def next_page_name(self, offset=1):
        """Nome de arquivo no padrão do CPMT: ``Projeto001.kra``.

        O CPMT só insere um sublinhado extra quando o nome do projeto termina
        em dígito, então o padrão é ``nome + 3 dígitos``.
        """
        name = self.project_name.replace(" ", "_")
        extra = "_" if name and name[-1].isdigit() else ""
        number = self.page_number + int(offset)
        return "{0}{1}{2:03d}.kra".format(name, extra, number)

    def next_page_relative(self, offset=1):
        filename = self.next_page_name(offset)
        if self.pages_location:
            return os.path.join(self.pages_location, filename)
        return filename

    def pages_dir(self):
        return os.path.join(self.root, self.pages_location)

    def register_pages(self, relatives):
        """Acrescenta páginas ao projeto e avança o contador ``pageNumber``."""
        relatives = list(relatives)
        if not relatives:
            return
        pages = self.config.setdefault("pages", [])
        pages.extend(relatives)
        numbers = []
        for relative in relatives:
            match = re.search(r"(\d+)(?=\.kra$)", relative)
            if match:
                numbers.append(int(match.group(1)))
        if numbers:
            self.config["pageNumber"] = max(self.page_number, max(numbers))
        self.save()

    def set_page_order(self, relatives):
        """Reescreve a ordem das páginas (lista de caminhos relativos)."""
        self.config["pages"] = [str(item) for item in relatives]
        self.save()

    def save(self):
        directory = os.path.dirname(self.config_path)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-16", newline="", dir=directory, delete=False
        )
        try:
            with handle:
                json.dump(self.config, handle, indent=4, sort_keys=True, ensure_ascii=False)
            os.replace(handle.name, self.config_path)
        except OSError:
            try:
                os.unlink(handle.name)
            except OSError:
                pass
