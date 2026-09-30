#!/usr/bin/env python3
"""Serve uma pasta por HTTP com CORS, para o Penpot buscar arquivos.

O plugin do Penpot roda no navegador; para ``uploadMediaUrl`` e ``fetch``
funcionarem, o servidor precisa mandar ``Access-Control-Allow-Origin``.

Uso:
    python3 servir-para-penpot.py PASTA [--porta 8791]
"""

import argparse
import functools
import http.server
import os
import socketserver
import sys


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *args):
        pass


class Servidor(socketserver.TCPServer):
    # Sem isto, reiniciar o servidor logo depois de parar dá "Address already in
    # use" (a porta fica em TIME_WAIT) e o autor reinicia o script achando que
    # é outra coisa.
    allow_reuse_address = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--porta", type=int, default=8791)
    args = ap.parse_args()
    if not os.path.isdir(args.pasta):
        ap.error("a pasta {0} não existe".format(args.pasta))
    handler = functools.partial(Handler, directory=args.pasta)
    try:
        with Servidor(("127.0.0.1", args.porta), handler) as servidor:
            print("servindo {0} em http://localhost:{1} (Ctrl+C para parar)".format(
                args.pasta, args.porta))
            servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nparado")
    except OSError as erro:
        sys.exit("não consegui abrir a porta {0}: {1}".format(args.porta, erro))


if __name__ == "__main__":
    main()
