#!/usr/bin/env python3
"""Gera um lote de balões vetorizados a partir das pranchas de referência.

Cada trabalho chama o `vetorizar-baloes.py` com o recorte da forma e os
parâmetros calibrados (suavização, traço, base interna). As formas sem corte
manual usam a detecção automática de pescoço; os casos que falham ficam
listados no fim para revisão.

Uso:
    python3 vetorizar-lote.py [--saida Referencias/baloes-vetorizados]
"""

import argparse
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VETORIZADOR = os.path.join(AQUI, "vetorizar-baloes.py")
PRANCHAS = os.path.join(os.path.dirname(AQUI), "Referencias", "baloes")

# nome: (prancha, x, y, largura, altura, traco_px, corte)
TRABALHOS = {
    "balao-02a": ("Refer_ball_02.png", 225, 7, 185, 216, 6.0, "113,154,89,153"),
    "balao-02b": ("Refer_ball_02.png", 652, 21, 193, 193, 6.0, ""),
    "balao-02c": ("Refer_ball_02.png", 240, 291, 176, 133, 6.0, ""),
    "balao-02d": ("Refer_ball_02.png", 439, 39, 185, 157, 6.0, ""),
    "balao-03a": ("Refer_ball_03.png", 344, 181, 176, 120, 5.0, ""),
    "balao-03b": ("Refer_ball_03.png", 691, 341, 129, 113, 5.0, ""),
    "balao-04a": ("Refer_ball_04.png", 503, 99, 119, 99, 4.0, ""),
    "balao-04b": ("Refer_ball_04.png", 123, 185, 95, 87, 4.0, ""),
    "balao-05b": ("Refer_ball_05.png", 752, 345, 223, 129, 5.0, ""),
    "balao-05c": ("Refer_ball_05.png", 38, 190, 133, 189, 5.0, ""),
    "balao-05d": ("Refer_ball_05.png", 191, 210, 163, 121, 5.0, ""),
    "balao-06a": ("Refer_ball_06.png", 415, 281, 110, 178, 5.0, ""),
    "balao-06b": ("Refer_ball_06.png", 557, 246, 154, 90, 5.0, ""),
    "balao-06c": ("Refer_ball_06.png", 714, 457, 144, 94, 5.0, ""),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default=os.path.join(os.path.dirname(AQUI), "Referencias", "baloes-vetorizados"))
    ap.add_argument("--somente", default="")
    args = ap.parse_args()
    os.makedirs(args.saida, exist_ok=True)
    registro = {}
    problemas = []
    for nome, (prancha, x, y, w, h, traco, corte) in TRABALHOS.items():
        if args.somente and nome not in args.somente.split(","):
            continue
        saida = os.path.join(args.saida, nome + ".svg")
        cmd = [sys.executable, VETORIZADOR, os.path.join(PRANCHAS, prancha),
               str(x), str(y), str(w), str(h), saida,
               "--traco-px", str(traco), "--suavizar", "5", "--base-interna", "12"]
        if corte:
            cmd += ["--corte", corte]
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        if resultado.returncode != 0:
            problemas.append((nome, resultado.stderr.strip()[-200:]))
            continue
        registro[nome] = {"prancha": prancha, "recorte": [x, y, w, h], "traco_px": traco,
                          "corte": corte or "auto"}
        print("ok:", nome)
    with open(os.path.join(args.saida, "lote.json"), "w", encoding="utf-8") as handle:
        json.dump(registro, handle, indent=2, ensure_ascii=False)
    if problemas:
        print("\nrevisar:")
        for nome, erro in problemas:
            print(" ", nome, "->", erro)
    print("\ntotal:", len(registro))


if __name__ == "__main__":
    main()
