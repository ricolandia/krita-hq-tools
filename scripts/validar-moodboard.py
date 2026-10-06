"""Smoke do moodboard dentro do Krita (ambiente isolado de teste).

Instancia o docker de verdade, monta um quadro em /tmp com três referências de
tamanhos diferentes (comprimidas pelo próprio docker), salva, fecha e reabre o
``.kra`` para conferir que os links das camadas de arquivo sobrevivem.

Roda no Krita 5.x/6.x: no Scripter, cole e execute; por autostart, defina
``HQ_POC_SCRIPT`` com o caminho deste arquivo.

Saídas: ``/tmp/moodboard-smoke.log``, ``/tmp/moodboard-smoke.png`` e
``/tmp/moodboard-smoke-reaberto.png``.
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

from krita import Krita

BASE = "/tmp/moodboard-smoke"
LINK = "/tmp/moodboard-link"
PASTA = os.path.join(LINK, "moodboard")
LOG_PATH = "/tmp/moodboard-smoke.log"


def log(mensagem):
    linha = str(mensagem)
    print(linha)
    with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def _jpg_de_teste(caminho, largura, altura, cor):
    imagem = QtGui.QImage(largura, altura, QtGui.QImage.Format_RGB32)
    imagem.fill(QtGui.QColor(*cor))
    return imagem.save(caminho, "JPG", 95)


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


def executar_smoke():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    if os.path.islink(LINK):
        os.remove(LINK)
    os.makedirs(BASE, exist_ok=True)
    os.symlink(BASE, LINK)
    os.makedirs(PASTA, exist_ok=True)
    aplicacao = Krita.instance()
    log("Krita {0}".format(aplicacao.version()))

    from hq_tools.modules.moodboard import core as mb
    from hq_tools.modules.moodboard.docker import MoodboardDocker

    docker = MoodboardDocker()
    docker.config.set("moodboard.folder", PASTA)
    docker.config.set("moodboard.aviso_compressao", True)
    log("pasta de referencias: {0}".format(docker.folder()))
    log("quadro: {0}".format(docker.board_path()))

    origens = [
        (os.path.join(BASE, "larga.jpg"), 1200, 800, (220, 40, 40)),
        (os.path.join(BASE, "alta.jpg"), 400, 600, (40, 180, 60)),
        (os.path.join(BASE, "gigante.jpg"), 2000, 1000, (40, 80, 220)),
    ]
    for caminho, largura, altura, cor in origens:
        log("jpg de teste {0}: {1}".format(os.path.basename(caminho), _jpg_de_teste(caminho, largura, altura, cor)))

    documento = docker._garantir_quadro()
    if documento is None:
        log("FALHA: quadro nao abriu")
        return
    itens = []
    for caminho, _, _, _ in origens:
        destino = mb.caminho_referencia(PASTA, os.path.basename(caminho))
        if not docker._comprimir(caminho, destino):
            log("FALHA: compressao de {0}".format(caminho))
            continue
        imagem = QtGui.QImage(destino)
        x, y, escala = mb.destino(len(itens), imagem.width(), imagem.height())
        camada = docker._montar_camada(
            documento, destino, os.path.splitext(os.path.basename(destino))[0], escala, x, y
        )
        if camada is None:
            log("FALHA: camada de {0}".format(destino))
            continue
        item = mb.item_de_layout(
            os.path.basename(destino), x, y, escala, imagem.width(), imagem.height(),
            camada.uniqueId().toString(),
        )
        itens.append(item)
        log(
            "item {0}: x={1:.1f} y={2:.1f} escala={3:.4f} {4}x{5} camada={6}".format(
                len(itens), item["x"], item["y"], item["escala"],
                item["largura"], item["altura"], item["camada"],
            )
        )
    mb.salvar_layout(PASTA, itens)
    docker._crescer_quadro(documento, len(itens))
    documento.refreshProjection()
    docker._salvar_quadro(documento)

    # 3) guarda de apagar/renomear: o quadro é achado com o caminho por symlink?
    caminho_ref = os.path.join(PASTA, itens[0]["arquivo"])
    _, item = docker._item_do_arquivo(itens, caminho_ref)
    log("guarda: item encontrado={0}".format(item is not None))
    log("guarda: board_path={0!r}".format(docker.board_path()))
    for aberto in aplicacao.documents():
        try:
            nome_arquivo = aberto.fileName()
            log(
                "guarda: doc aberto name={0!r} fileName={1!r} abspath-igual={2} realpath-igual={3}".format(
                    aberto.name(),
                    nome_arquivo,
                    os.path.abspath(nome_arquivo) == os.path.abspath(docker.board_path()),
                    os.path.realpath(nome_arquivo) == os.path.realpath(docker.board_path()),
                )
            )
        except (AttributeError, RuntimeError) as erro:
            log("guarda: doc aberto erro {0}".format(erro))
    achado = docker._quadro_aberto()
    log("guarda: quadro aberto={0}".format(achado.name() if achado is not None else None))
    log("exportacao inicial: {0}".format(_exportar(documento, "/tmp/moodboard-smoke.png")))
    log("tamanho do quadro: {0}x{1}".format(documento.width(), documento.height()))
    caminho_kra = docker.board_path()
    log("tamanho do kra: {0} bytes".format(os.path.getsize(caminho_kra)))

    quadro = docker._quadro_para_atualizar()
    log("guarda: quadro para atualizar={0}".format(quadro.name() if quadro is not None else None))
    if quadro is not None and item is not None:
        removida = docker._remover_camada(quadro, item)
        itens.remove(item)
        mb.salvar_layout(PASTA, itens)
        quadro.refreshProjection()
        docker._salvar_quadro(quadro)
        log(
            "guarda: camada removida={0}; camadas agora={1}".format(
                removida, [no.name() for no in quadro.rootNode().findChildNodes(recursive=False)]
            )
        )
        log("exportacao apagada: {0}".format(_exportar(quadro, "/tmp/moodboard-smoke-apagada.png")))

    documento.setModified(False)
    documento.close()
    reaberto = aplicacao.openDocument(caminho_kra)
    if reaberto is None:
        log("FALHA: reabertura do quadro")
        return
    reaberto.refreshProjection()
    log("exportacao reaberto: {0}".format(_exportar(reaberto, "/tmp/moodboard-smoke-reaberto.png")))
    camadas = reaberto.rootNode().findChildNodes(recursive=False)
    log("camadas no kra reaberto: {0}".format([no.name() for no in camadas]))
    reaberto.setModified(False)
    reaberto.close()

    # 2) inserir na seleção
    from hq_tools.core import krita_helpers as helpers

    pagina = aplicacao.createDocument(1600, 1000, "pagina-teste", "RGBA", "U8", "sRGB built-in", 300.0)
    if pagina is None:
        log("FALHA: pagina de teste")
        return
    helpers.present_document(pagina)
    selecao = helpers.Selection()
    selecao.select(200, 100, 800, 600, 255)
    pagina.setSelection(selecao)
    docker.refresh()
    for indice in range(docker.list_items.count()):
        if docker.list_items.item(indice).text() == "gigante":
            docker.list_items.setCurrentRow(indice)
    ativo = aplicacao.activeDocument()
    log("documento ativo antes do insert: {0}".format(ativo.name() if ativo is not None else None))
    log("referencia selecionada na lista: {0}".format(docker.list_items.currentItem().text()))
    # No ambiente headless o Krita não marca a página como ativa (não há foco
    # de janela); no uso real o ativo é o documento que o autor está olhando.
    helpers.active_document = lambda: pagina
    docker.insert_into_selection()
    pagina.refreshProjection()
    log("selecao ativa (depois): {0}".format(helpers.selection_bounds(pagina)))
    for no in pagina.rootNode().findChildNodes(recursive=True):
        try:
            log(
                "no: {0} tipo={1} visivel={2} pos={3} opacidade={4} bounds={5}".format(
                    no.name(), no.type(), no.visible(), no.position(), no.opacity(), no.bounds()
                )
            )
        except (AttributeError, RuntimeError) as erro:
            log("no: erro {0}".format(erro))
    log("exportacao selecao: {0}".format(_exportar(pagina, "/tmp/moodboard-smoke-selecao.png")))
    pagina.setModified(False)
    pagina.close()


if __name__ == "__main__" or os.environ.get("HQ_POC_AUTORUN"):
    executar_smoke()
