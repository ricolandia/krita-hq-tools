"""Posições das guias de margem (núcleo puro, sem Krita).

O gerenciador de páginas cria guias de 0,5 / 1 / 1,5 cm por lado. O libkis
troca a lista inteira de guias a cada chamada, então as guias que o autor já
tinha (perspectiva, sangria, corte) eram apagadas sem aviso; aqui ficam as
contas para gerar as de margem e mesclar com as existentes.
"""

MARGENS_CM = (0.5, 1.0, 1.5)


def posicoes_de_margem(largura, altura, dpi, margens_cm=MARGENS_CM):
    """Guias de margem em pixels: ``(verticais, horizontais)``."""
    verticais = []
    horizontais = []
    for margem in margens_cm:
        px = float(margem) * float(dpi) / 2.54
        verticais.extend([px, float(largura) - px])
        horizontais.extend([px, float(altura) - px])
    return verticais, horizontais


def mesclar(existentes, novas):
    """União ordenada das guias, sem repetir (arredonda a 0,001 px)."""
    valores = {round(float(valor), 3) for valor in (existentes or [])}
    valores.update(round(float(valor), 3) for valor in (novas or []))
    return sorted(valores)
