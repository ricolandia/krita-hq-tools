"""Leitura e escrita do ``comicsConfig.json`` do Comics Project Management Tools.

O CPMT (plugin embutido do Krita) guarda a lista de páginas como caminhos
relativos à raiz do projeto, junto de ``pageNumber`` (contador de páginas).
Este módulo permite que o HQ Tools leia, reordene e registre páginas geradas.
"""

import json
import os
import re
import tempfile
import uuid

CONFIG_NAMES = ("comicConfig.json", "comicsConfig.json")


class CPMTError(ValueError):
    """Erro de leitura ou escrita do arquivo de projeto do CPMT."""


def create_project_with_page(folder, page_relative, project_name=None):
    """Cria um projeto CPMT na pasta, registrando a página já salva.

    Grava ``comicConfig.json`` (UTF-16, padrão do CPMT) com a página na lista
    ``pages`` e ``pageNumber`` em 1. Devolve o caminho do arquivo criado.

    Recusa uma pasta que já tem projeto: sobrescrever o ``comicConfig.json``
    apagaria a lista de páginas, a ordem e o UUID de um projeto inteiro sem
    perguntar nada. Para acrescentar página a um projeto existente, use
    :meth:`CPMTProject.register_pages`.
    """
    folder = os.path.abspath(folder)
    os.makedirs(folder, exist_ok=True)
    existente = next(
        (
            name
            for name in CONFIG_NAMES
            if os.path.isfile(os.path.join(folder, name))
        ),
        None,
    )
    if existente is not None:
        raise CPMTError(
            "a pasta já tem um projeto ({0}); a página não foi registrada. "
            "Abra o projeto existente para acrescentar a página.".format(existente)
        )
    name = project_name or os.path.basename(folder) or "projeto"
    config = {
        "projectName": name,
        "concept": "",
        "language": "pt_BR",
        "pagesLocation": ".",
        "exportLocation": "export",
        "templateLocation": "templates",
        "translationsLocation": "translations",
        "uuid": str(uuid.uuid4()),
        "pageNumber": 1,
        "pages": [str(page_relative)],
    }
    for sub in ("export", "templates", "translations"):
        os.makedirs(os.path.join(folder, sub), exist_ok=True)
    path = os.path.join(folder, "comicConfig.json")
    _escrever_atomico(path, config, "utf-16")
    return path


def _escrever_atomico(path, config, encoding):
    """Grava JSON por arquivo temporário e troca pelo original.

    O CPMT do Krita lê esse arquivo em memória e não tolera meio arquivo: uma
    escrita interrompida deixava o projeto sem lista de páginas.
    """
    directory = os.path.dirname(path) or "."
    prefix = ".{0}.".format(os.path.basename(path))
    handle = tempfile.NamedTemporaryFile(
        "w", encoding=encoding, newline="", dir=directory, prefix=prefix, delete=False
    )
    try:
        with handle:
            json.dump(config, handle, indent=4, sort_keys=True, ensure_ascii=False)
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


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
        self._encoding = "utf-16" if head in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
        with open(self.config_path, "r", encoding=self._encoding) as handle:
            try:
                self.config = json.load(handle)
            except ValueError as error:
                # Antes disso o erro subia como JSONDecodeError, que os
                # chamadores não pegavam, então uma pasta com config quebrada
                # aparecia como falha genérica do módulo em vez de "projeto
                # inválido".
                raise CPMTError(
                    "{0} está corrompido ({1}). Restaure uma cópia ou apague o "
                    "arquivo para recriar o projeto.".format(self.config_path, error)
                )
        if not isinstance(self.config, dict):
            raise CPMTError(
                "{0} não tem o formato esperado (objeto JSON).".format(self.config_path)
            )

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
        try:
            return int(self.config.get("pageNumber") or 0)
        except (TypeError, ValueError):
            # pageNumber corrompido não pode derrubar a criação de páginas:
            # sem ele o nome seguinte repetiria uma página já existente.
            return 0

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
        """Acrescenta páginas ao projeto e avança o contador ``pageNumber``.

        Ignora caminhos já registrados. Reexecutar o mesmo roteiro era o
        caminho comum para a mesma página aparecer duas vezes na lista do CPMT,
        e o plugin de exportação do Krita exporta o mesmo arquivo duas vezes.
        """
        relatives = list(relatives)
        if not relatives:
            return []
        pages = self.config.setdefault("pages", [])
        ja_cadastradas = {str(item) for item in pages}
        novas = []
        for relative in relatives:
            relative = str(relative)
            if relative in ja_cadastradas:
                continue
            ja_cadastradas.add(relative)
            novas.append(relative)
        if not novas:
            return []
        pages.extend(novas)
        numbers = []
        for relative in novas:
            match = re.search(r"(\d+)(?=\.kra$)", relative)
            if match:
                numbers.append(int(match.group(1)))
        if numbers:
            self.config["pageNumber"] = max(self.page_number, max(numbers))
        self.save()
        return novas

    def set_page_order(self, relatives):
        """Reescreve a ordem das páginas (lista de caminhos relativos)."""
        order = []
        vistas = set()
        for item in relatives:
            item = str(item)
            if item in vistas:
                continue
            vistas.add(item)
            order.append(item)
        self.config["pages"] = order
        self.save()

    def save(self):
        _escrever_atomico(self.config_path, self.config, self._encoding)
