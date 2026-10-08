"""Smoke da produção dentro do Krita (ambiente isolado de teste).

Instancia o docker de verdade com uma pasta de projeto em /tmp, monta o
checklist de um roteiro, cicla estados, define a meta, exporta o .md e abre a
``pagina_001.kra`` de teste.

Roda no Krita 5.x/6.x: no Scripter, cole e execute; por autostart, defina
``HQ_POC_SCRIPT`` com o caminho deste arquivo.

Saídas: ``/tmp/producao-smoke.log`` e os arquivos na pasta ``/tmp/producao-smoke``.
"""

import os
import shutil
import sys
import time

REPO = "/home/ricardo/Documentos/31_APPS_GITHUB/Krita-Comics-Plugin"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from krita import Krita

BASE = "/tmp/producao-smoke"
LOG_PATH = "/tmp/producao-smoke.log"

ROTEIRO = (
    "pagina 1\n"
    "layout grade2x2\n"
    "plano p1: geral\n"
    "plano p2: close\n"
    "narracao p1: Era uma vez...\n"
    "fala p1 joao: Voce viu aquilo?\n"
    "fala p4 maria: Ultima fala.\n"
    "\n"
    "pagina 2\n"
    "layout tira3\n"
    "fala p1: Um\n"
    "fala p2: Dois\n"
    "fala p3: Tres\n"
)


def log(mensagem):
    linha = str(mensagem)
    try:
        print(linha)
    except UnicodeEncodeError:
        # O stdout embutido do Krita é latin-1; o arquivo de log é utf-8.
        print(linha.encode("ascii", "replace").decode("ascii"))
    with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
        arquivo.write(linha + "\n")


def executar_smoke():
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
    os.makedirs(BASE, exist_ok=True)
    # Execução determinística: limpa o estado da rodada anterior.
    shutil.rmtree(os.path.join(BASE, "producao"), ignore_errors=True)
    aplicacao = Krita.instance()
    log("Krita {0}".format(aplicacao.version()))

    from hq_tools.core import krita_helpers as helpers
    from hq_tools.modules.producao import core as prod
    from hq_tools.modules.producao import docker as producao_docker
    from hq_tools.modules.producao.docker import ProducaoDocker

    documento = aplicacao.createDocument(
        800, 1000, "pagina_001", "RGBA", "U8", "sRGB built-in", 72.0
    )
    if documento is not None:
        helpers.present_document(documento)
        documento.saveAs(os.path.join(BASE, "pagina_001.kra"))
        documento.setModified(False)
        documento.close()
    log("pagina de teste: {0}".format(os.path.exists(os.path.join(BASE, "pagina_001.kra"))))

    docker = ProducaoDocker()
    docker.config.set("producao.folder", BASE)
    docker.recarregar()
    log("pasta: {0!r}".format(docker.folder()))

    docker.caixa.setPlainText(ROTEIRO)
    docker.montar()
    log("pasta_dados: {0!r}".format(docker.pasta_dados()))
    log("roteiro.txt salvo: {0}".format(os.path.exists(os.path.join(BASE, "producao", "roteiro.txt"))))
    log("arvore: {0} paginas".format(docker.arvore.topLevelItemCount()))
    for indice in range(docker.arvore.topLevelItemCount()):
        item = docker.arvore.topLevelItem(indice)
        log("pagina: {0!r} | {1!r} | {2!r}".format(item.text(0), item.text(1), item.text(2)))
        for posicao in range(item.childCount()):
            filho = item.child(posicao)
            log("  painel: {0!r} | {1!r} | {2!r} | {3!r}".format(
                filho.text(0), filho.text(1), filho.text(2), filho.text(3)
            ))
    log("progresso: {0!r}".format(docker.lbl_progresso.text()))
    log("meta (sem valor): {0!r}".format(docker.lbl_meta.text()))

    item = docker.arvore.topLevelItem(0).child(0)
    docker._item_clicado(item, 1)
    log("apos 1 clique: painel 1 = {0!r}".format(item.text(1)))
    docker._item_clicado(item, 1)
    docker._item_clicado(item, 1)
    log("apos 3 cliques: painel 1 = {0!r} (volta ao esboco)".format(item.text(1)))
    docker._item_clicado(item, 1)
    log("deixado em: {0!r}".format(item.text(1)))
    estados, meta = prod.carregar(os.path.join(BASE, "producao"))
    log("estados salvos: {0} meta={1}".format(estados, meta))
    log("progresso: {0!r}".format(docker.lbl_progresso.text()))

    docker.meta.setValue(2)
    log("meta 2: {0!r}".format(docker.lbl_meta.text()))
    estados, meta = prod.carregar(os.path.join(BASE, "producao"))
    log("meta salva: {0}".format(meta))

    docker.exportar_markdown()
    caminho_md = os.path.join(BASE, "producao", "checklist.md")
    log("checklist.md existe: {0}".format(os.path.exists(caminho_md)))
    if os.path.exists(caminho_md):
        with open(caminho_md, encoding="utf-8") as arquivo:
            linhas = arquivo.read().splitlines()
        log("md: {0!r}".format(linhas[2]))
        log("md: {0!r}".format(linhas[4]))
        log("md: {0!r}".format(linhas[6]))

    # 4) auto-save do roteiro (sem passar pelo "Montar")
    docker.caixa.setPlainText(ROTEIRO + "fala p2: extra do auto-save\n")
    docker._salvar_roteiro_automatico()
    with open(os.path.join(BASE, "producao", "roteiro.txt"), encoding="utf-8") as arquivo:
        texto_salvo = arquivo.read()
    log("auto-save: contem extra={0} | indicador={1!r}".format(
        "extra do auto-save" in texto_salvo, docker.lbl_roteiro_salvo.text()))

    # 5) timetracking manual (simula 90 s de trabalho na pagina 1)
    docker._selecionar_pagina(1)
    docker._iniciar_tempo()
    docker._ultimo_save = time.monotonic() - 90
    docker._persistir_tempo()
    docker._parar_tempo()
    log("tempo: total={0}s pagina1={1}s | indicador={2!r} | botao={3!r}".format(
        docker.tempos["total"],
        docker.tempos["por_pagina"].get("1", 0),
        docker.lbl_tempo.text(),
        docker.btn_tempo.text(),
    ))
    log("tempos.json existe: {0}".format(
        os.path.exists(prod.caminho_tempos(docker.pasta_dados()))
    ))
    docker.exportar_markdown()
    with open(caminho_md, encoding="utf-8") as arquivo:
        texto_md = arquivo.read()
    log("md com tempo: {0}".format(
        [linha for linha in texto_md.splitlines() if "Tempo" in linha or "⏱" in linha]
    ))

    # 6) visual: barra de estados, pendente e captura da doca
    log("barra: {0}".format(docker.barra._contagem))
    log("pendente: pagina={0} rotulo={1!r}".format(
        docker._pagina_pendente, docker.lbl_pendente.text()
    ))
    docker.widget().resize(380, 760)
    captura = docker.widget().grab()
    caminho_captura = "/tmp/producao-smoke-docker.png"
    log("captura: {0} -> {1}".format(bool(captura.save(caminho_captura)), caminho_captura))

    # 7) storyboard: o rótulo de plano entra no SVG de texto do gerador
    from hq_tools.modules.pages import generator, roteiro as roteiro_mod

    pagina = roteiro_mod.parse_script(ROTEIRO)[0]
    svg = generator._text_svg(pagina, 1000, 1400, 300)
    log("storyboard: contem 'geral'={0} e 'close'={1}".format(
        "geral" in svg, "close" in svg
    ))

    # abrir_pagina() usa openDocument + addView + setActiveDocument (o mesmo
    # fluxo do gerenciador de páginas); no headless sem foco de janela o
    # addView derruba o processo, então aqui fica só a detecção e o open.
    caminho_pagina = prod.pagina_do_arquivo(BASE, 1)
    log("pagina_do_arquivo(1): {0}".format(os.path.basename(caminho_pagina or "")))
    aberto = aplicacao.openDocument(caminho_pagina) if caminho_pagina else None
    log("openDocument: {0}".format(aberto.name() if aberto is not None else None))
    if aberto is not None:
        aberto.setModified(False)
        aberto.close()

    log("linhas de sintaxe: {0}".format(len(producao_docker.LINHAS_SINTAXE)))
    log("exemplo de sintaxe: {0!r}".format(producao_docker.EXEMPLO.splitlines()[0]))

    # 4) reabertura: uma instância nova deve reler o roteiro e os estados
    docker2 = ProducaoDocker()
    log("reabertura: arvore={0} paginas".format(docker2.arvore.topLevelItemCount()))
    log("reabertura: progresso={0!r}".format(docker2.lbl_progresso.text()))
    log("reabertura: meta={0}".format(docker2.meta.value()))
    estados2, _ = prod.carregar(docker2.pasta_dados())
    log("reabertura: estado 1-1={0!r}".format(estados2.get("1-1")))

    # 5) sem projeto: pasta padrao do plugin e aviso de escolher a pasta
    docker2.config.set("producao.folder", "")
    docker3 = ProducaoDocker()
    log("padrao: pasta_dados={0!r}".format(docker3.pasta_dados()))
    log("padrao: aviso={0!r}".format(docker3.lbl_pasta.text()))
    docker3.caixa.setPlainText(ROTEIRO)
    docker3.montar()
    log("padrao: roteiro salvo={0}".format(os.path.exists(os.path.join(docker3.pasta_dados(), "roteiro.txt"))))
    docker4 = ProducaoDocker()
    log("padrao: reabertura arvore={0}".format(docker4.arvore.topLevelItemCount()))


if __name__ == "__main__" or os.environ.get("HQ_POC_AUTORUN"):
    executar_smoke()
