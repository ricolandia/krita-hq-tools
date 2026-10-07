"""Smoke da inserção posicionada (balões, onomatopeias e biblioteca).

Valida, dentro do Krita, que a inserção usa a seleção (reduzindo para caber)
ou o centro da vista, em vez do canto do documento:

  A) balão com seleção -> a arte cabe na seleção;
  B) balão sem seleção -> a arte vai para o centro da vista;
  C) onomatopeia com seleção -> mesma conta do balão;
  D) PNG da biblioteca com seleção -> pixel data reduzido e posicionado;
  E) PNG da biblioteca sem seleção -> centro da vista.

Roda no Krita 5.x/6.x: no Scripter, cole e execute; por autostart, defina
``HQ_POC_SCRIPT`` com o caminho deste arquivo. Saídas em ``/tmp/insercao-*``.
"""

import os
import sys

REPO = "/home/ricardo/Documentos/31_APPS_GITHUB/Krita-Comics-Plugin"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

try:
    from PyQt5 import QtGui
except ImportError:  # Krita 6
    from PyQt6 import QtGui

from krita import Krita, Selection

BASE = "/tmp/insercao-smoke"
LOG_PATH = "/tmp/insercao-smoke.log"
BALAO = os.path.join(REPO, "hq_tools/modules/balloons/samples/Fala_Speak_01_.svg")
ONO = os.path.join(REPO, "hq_tools/modules/onomatopeias/samples/Ono_VSFX_01_.svg")
PNG = os.path.join(BASE, "referencia.png")


def log(mensagem):
    linha = str(mensagem)
    try:
        print(linha)
    except UnicodeEncodeError:
        print(linha.encode("ascii", "replace").decode("ascii"))
    with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def _selecionar(documento, x, y, largura, altura):
    selecao = Selection()
    selecao.select(x, y, largura, altura, 255)
    documento.setSelection(selecao)


def _exportar(documento, caminho):
    imagem = documento.projection(0, 0, 0, 0)
    if imagem is not None and not imagem.isNull():
        return bool(imagem.save(caminho))
    largura, altura = documento.width(), documento.height()
    dados = documento.pixelData(0, 0, largura, altura)
    if dados is None:
        return False
    reserva = QtGui.QImage(bytes(dados), largura, altura, QtGui.QImage.Format_ARGB32)
    return bool(reserva.save(caminho))


def _detalhar_camada(rotulo, camada):
    """Loga bounds da camada e a transformação de cada shape."""
    if camada is None:
        log("{0}: camada nula".format(rotulo))
        return
    log("{0}: bounds={1}".format(rotulo, camada.bounds()))
    try:
        shapes = camada.shapes()
    except (AttributeError, RuntimeError) as erro:
        log("{0}: sem shapes ({1})".format(rotulo, erro))
        return
    for shape in shapes:
        try:
            log("   shape {0!r} box={1} transform={2}".format(
                shape.name(), shape.boundingBox(), shape.transformation()
            ))
        except (AttributeError, RuntimeError) as erro:
            log("   shape com erro: {0}".format(erro))


def _png_de_teste(caminho, largura, altura, cor):
    imagem = QtGui.QImage(largura, altura, QtGui.QImage.Format_RGB32)
    imagem.fill(QtGui.QColor(*cor))
    return imagem.save(caminho, "PNG")


def _inserir_vetor(documento, helpers, svg_path, nome):
    """O mesmo caminho dos dockers de balões/onomatopeias."""
    svg = helpers.read_text_file(svg_path)
    camada = documento.createVectorLayer(nome)
    if camada is None:
        return None, False
    shapes = camada.addShapesFromSvg(svg)
    if not shapes:
        camada.remove()
        return None, False
    tinha_selecao = helpers.has_selection(documento)
    helpers.attach(documento, camada)
    documento.setActiveNode(camada)
    posicionou = helpers.posicionar_vetor(documento, camada)
    documento.refreshProjection()
    if tinha_selecao:
        helpers.deselect(documento)
    return camada, posicionou


def executar():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    os.makedirs(BASE, exist_ok=True)
    aplicacao = Krita.instance()
    log("Krita {0}".format(aplicacao.version()))

    from hq_tools.core import krita_helpers as helpers

    documento = aplicacao.createDocument(
        1600, 1000, "pagina-teste", "RGBA", "U8", "sRGB built-in", 300.0
    )
    janela = aplicacao.activeWindow()
    if janela is not None:
        janela.addView(documento)
        views = list(janela.views())
        if views:
            # Headless: sem foco de janela o activeView pode ser None; no uso
            # real a vista ativa é a do documento que o autor está olhando.
            view = views[-1]
            helpers.active_view = lambda: view
    log("dpi: {0} | centro da vista: {1}".format(
        documento.resolution(), helpers.centro_da_vista(documento)
    ))

    _selecionar(documento, 200, 300, 600, 400)
    camada, ok = _inserir_vetor(documento, helpers, BALAO, "balao-selecao")
    log("A) balao com selecao (200,300 600x400): posicionou={0}".format(ok))
    _detalhar_camada("A", camada)
    log("A) export: {0}".format(_exportar(documento, "/tmp/insercao-a-balao-selecao.png")))

    camada, ok = _inserir_vetor(documento, helpers, BALAO, "balao-centro")
    log("B) balao sem selecao: posicionou={0}".format(ok))
    _detalhar_camada("B", camada)
    log("B) export: {0}".format(_exportar(documento, "/tmp/insercao-b-balao-centro.png")))

    _selecionar(documento, 1000, 500, 400, 300)
    camada, ok = _inserir_vetor(documento, helpers, ONO, "ono-selecao")
    log("C) onomatopeia com selecao (1000,500 400x300): posicionou={0}".format(ok))
    _detalhar_camada("C", camada)
    log("C) export: {0}".format(_exportar(documento, "/tmp/insercao-c-ono-selecao.png")))

    from hq_tools.modules.biblioteca.docker import BibliotecaDocker

    biblioteca = BibliotecaDocker()
    _png_de_teste(PNG, 800, 600, (30, 120, 220))
    _selecionar(documento, 900, 100, 400, 300)
    biblioteca._insert_paint(documento, PNG, "png-selecao")
    log("D) PNG 800x600 na selecao (900,100 400x300): export={0}".format(
        _exportar(documento, "/tmp/insercao-d-png-selecao.png")
    ))

    helpers.deselect(documento)
    biblioteca._insert_paint(documento, PNG, "png-centro")
    log("E) PNG sem selecao: export={0}".format(
        _exportar(documento, "/tmp/insercao-e-png-centro.png")
    ))

    camadas = [no.name() for no in documento.rootNode().findChildNodes(recursive=False)]
    log("camadas: {0}".format(camadas))


if __name__ == "__main__" or os.environ.get("HQ_POC_AUTORUN"):
    executar()
