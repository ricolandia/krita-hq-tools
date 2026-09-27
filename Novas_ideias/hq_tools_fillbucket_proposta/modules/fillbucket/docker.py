"""
modules/fillbucket/docker.py

Integração com o Krita do núcleo core/gapclose.py: "balde com fechamento
de falhas". Segue a convenção do projeto (lógica pura em core/, sem
import de krita; este arquivo só faz a ponte).

STATUS: esqueleto não validado dentro do Krita. Ao contrário do resto do
HQ Tools, eu não tenho acesso a uma instalação real do Krita para rodar
isto no Scripter, então há três pontos de incerteza explícitos abaixo
(marcados VALIDAR) que você precisa checar antes de confiar no módulo:

1. Ordem de canais de `Node.pixelData` — pode vir BGRA, não RGBA.
2. Existência e assinatura de `Selection.setPixelData`.
3. Como capturar o clique do usuário no canvas a partir de um docker
   (a API pública de docker não expõe isso da mesma forma que uma
   KisTool nativa — ver a seção "Captura de clique" abaixo).

Fluxo pretendido:
  1. Usuário seleciona a camada de lineart e clica um ponto "vazio".
  2. O módulo lê os pixels da camada em bytes, monta um array numpy.
  3. Roda luminance_mask -> close_gaps -> label_regions -> region_mask.
  4. Cria uma seleção (Selection) a partir da máscara resultante.
  5. Preenche essa seleção com a cor de frente numa camada de pintura
     nova (ou existente, à escolha do usuário), dentro do grupo ativo.
"""
import struct

import numpy as np

from core.gapclose import close_gaps, label_regions, luminance_mask, region_mask

try:
    from PyQt5.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # Krita 6 (Qt6) — mesma ideia do core/compat.py do projeto
    from PyQt6.QtWidgets import (
        QComboBox,
        QDoubleSpinBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase, Krita


RAIO_PADRAO_PX = 2
LIMIAR_LUMINANCIA_PADRAO = 200


def bytes_para_rgba(dados: bytes, largura: int, altura: int) -> np.ndarray:
    """Converte o retorno de `Node.pixelData` num array (H, W, 4) uint8 RGBA.

    VALIDAR NO KRITA: a documentação da libkis descreve o layout de bytes
    do QByteArray como dependente do tipo de cor/profundidade do
    documento; para 8 bits RGBA a ordem mais comum internamente no Krita
    é BGRA, não RGBA. Teste com uma camada conhecida (ex.: um pixel
    vermelho puro) e ajuste a ordem dos canais abaixo se a cor ler
    trocada — troque `[2, 1, 0, 3]` por `[0, 1, 2, 3]` conforme o
    resultado.
    """
    arr = np.frombuffer(dados, dtype=np.uint8)
    arr = arr.reshape((altura, largura, 4))
    ordem_bgra_para_rgba = [2, 1, 0, 3]
    return arr[:, :, ordem_bgra_para_rgba].copy()


def rgba_para_bytes(rgba: np.ndarray) -> bytes:
    """Inverso de `bytes_para_rgba` (RGBA numpy -> bytes BGRA do Krita)."""
    ordem_rgba_para_bgra = [2, 1, 0, 3]
    return rgba[:, :, ordem_rgba_para_bgra].copy().tobytes()


class FillBucketDocker(DockWidget):
    """Docker "HQ Tools: balde com fechamento de falhas".

    Fluxo simplificado (sem captura de clique no canvas — ver nota no
    topo do arquivo): o usuário faz uma seleção retangular grosseira ao
    redor da área a colorir com as ferramentas nativas do Krita, define
    um ponto semente dentro dela nos campos X/Y do docker (relativo ao
    canto superior esquerdo da seleção), e aperta "Preencher". Isso evita
    depender de captura de clique no canvas, que eu não consegui validar
    sem uma instalação real do Krita para testar — ver STATUS no topo.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HQ Tools: balde com fechamento de falhas")

        raiz = QWidget()
        layout = QVBoxLayout()

        self.raio_spin = QDoubleSpinBox()
        self.raio_spin.setRange(0, 10)
        self.raio_spin.setValue(RAIO_PADRAO_PX)
        self.raio_spin.setSuffix(" px de falha a fechar")

        linha_raio = QHBoxLayout()
        linha_raio.addWidget(QLabel("Fechar falhas até:"))
        linha_raio.addWidget(self.raio_spin)

        self.seed_x_spin = QDoubleSpinBox()
        self.seed_x_spin.setRange(0, 100000)
        self.seed_y_spin = QDoubleSpinBox()
        self.seed_y_spin.setRange(0, 100000)
        linha_seed = QHBoxLayout()
        linha_seed.addWidget(QLabel("Ponto dentro da seleção — X:"))
        linha_seed.addWidget(self.seed_x_spin)
        linha_seed.addWidget(QLabel("Y:"))
        linha_seed.addWidget(self.seed_y_spin)

        botao_preencher = QPushButton("Preencher com a cor de frente")
        botao_preencher.clicked.connect(self.preencher)

        layout.addLayout(linha_raio)
        layout.addLayout(linha_seed)
        layout.addWidget(botao_preencher)
        layout.addStretch()
        raiz.setLayout(layout)
        self.setWidget(raiz)

    def canvasChanged(self, canvas):
        pass  # exigido pela API de DockWidget; nada a fazer aqui

    def preencher(self):
        app = Krita.instance()
        doc = app.activeDocument()
        if doc is None:
            QMessageBox.warning(None, "HQ Tools", "Abra um documento primeiro.")
            return

        no = doc.activeNode()
        selecao = doc.selection()
        if selecao is None:
            QMessageBox.warning(
                None,
                "HQ Tools",
                "Faça uma seleção retangular ao redor da área a colorir "
                "antes de clicar em Preencher.",
            )
            return

        x0, y0 = selecao.x(), selecao.y()
        largura, altura = selecao.width(), selecao.height()

        dados = no.pixelData(x0, y0, largura, altura)
        rgba = bytes_para_rgba(dados, largura, altura)

        ink = luminance_mask(rgba, threshold=LIMIAR_LUMINANCIA_PADRAO)
        parede = close_gaps(ink, radius=int(self.raio_spin.value()))
        labels, n_regioes = label_regions(parede)

        seed_x = int(self.seed_x_spin.value())
        seed_y = int(self.seed_y_spin.value())
        if not (0 <= seed_x < largura and 0 <= seed_y < altura):
            QMessageBox.warning(
                None, "HQ Tools", "O ponto X/Y precisa estar dentro da seleção."
            )
            return

        try:
            area = region_mask(labels, seed_x, seed_y) & ~ink
        except ValueError:
            QMessageBox.warning(
                None,
                "HQ Tools",
                "Esse ponto caiu em cima da tinta. Escolha um ponto "
                "dentro de uma área vazia.",
            )
            return

        if not area.any():
            QMessageBox.information(
                None, "HQ Tools", "Nenhuma área a preencher nesse ponto."
            )
            return

        # VALIDAR NO KRITA: cor de frente do Krita é BGRA de 8 bits nesta
        # API? `View.foregroundColor()` devolve um ManagedColor; a
        # conversão abaixo assume 8 bits e é o ponto mais provável de
        # quebrar em documentos de maior profundidade de cor (16/32 bits).
        view = app.activeWindow().activeView()
        cor = view.foregroundColor().componentsOrdered()
        cor_rgba = tuple(int(round(c * 255)) for c in cor[:3]) + (255,)

        pintado = rgba.copy()
        pintado[area] = np.array(cor_rgba, dtype=np.uint8)

        camada_nova = doc.createNode("Cor (balde)", "paintlayer")
        no.parentNode().addChildNode(camada_nova, no)
        camada_nova.setPixelData(rgba_para_bytes(pintado), x0, y0, largura, altura)

        doc.refreshProjection()


DOCKER_ID = "hq_tools_fillbucket"
Krita.instance().addDockWidgetFactory(
    DockWidgetFactory(DOCKER_ID, DockWidgetFactoryBase.DockRight, FillBucketDocker)
)
