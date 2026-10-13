"""Sincronização das amostras do plugin com a pasta do usuário.

Balões e onomatopeias vivem numa pasta do usuário que recebe as amostras do
plugin e os modelos criados por ele. Regras da sincronização:

- amostra ausente é copiada (também em pastas já usadas, para as amostras
  novas chegarem nas atualizações);
- arquivo existente igual à amostra do plugin é deixado como está;
- amostra alterada pelo usuário (hash diferente do último sincronizado) é
  preservada: o modelo dele manda;
- amostra apagada de propósito não volta (o nome fica no marcador);
- amostra que mudou no plugin substitui a versão sincronizada antiga.

O marcador ``.amostras_sincronizadas.json`` (nome → hash) guarda o que foi
sincronizado; pasta sem permissão de escrita segue sem marcador.
"""

import hashlib
import json
import os
import shutil

MARCADOR = ".amostras_sincronizadas.json"


def _hash(caminho):
    digestor = hashlib.md5()
    with open(caminho, "rb") as handle:
        for bloco in iter(lambda: handle.read(65536), b""):
            digestor.update(bloco)
    return digestor.hexdigest()


def _carregar_marcador(caminho):
    try:
        with open(caminho, encoding="utf-8") as handle:
            dados = json.load(handle)
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def sincronizar(pasta, origens):
    """Copia para ``pasta`` as amostras ausentes ou desatualizadas.

    ``origens`` são as pastas de amostras do plugin (uma delas pode não
    existir, como o kit CC0 opcional). Devolve ``{"copiadas", "atualizadas",
    "preservadas"}`` com os nomes em cada caso.
    """
    marcador_caminho = os.path.join(pasta, MARCADOR)
    anterior = _carregar_marcador(marcador_caminho)
    atual = dict(anterior)
    resultado = {"copiadas": [], "atualizadas": [], "preservadas": []}
    for origem in origens:
        if not os.path.isdir(origem):
            continue
        for nome in sorted(os.listdir(origem)):
            if not nome.lower().endswith(".svg"):
                continue
            fonte = os.path.join(origem, nome)
            if not os.path.isfile(fonte):
                continue
            impressao = _hash(fonte)
            destino = os.path.join(pasta, nome)
            if not os.path.exists(destino):
                if nome in anterior:
                    continue  # apagada de propósito: não ressuscita
                shutil.copy2(fonte, destino)
                resultado["copiadas"].append(nome)
            else:
                impressao_destino = _hash(destino)
                if impressao_destino == impressao:
                    pass  # já é a amostra do plugin
                elif nome in anterior and impressao_destino != anterior[nome]:
                    resultado["preservadas"].append(nome)  # alterada pelo usuário
                    continue
                else:
                    shutil.copy2(fonte, destino)
                    resultado["atualizadas"].append(nome)
            atual[nome] = impressao
    if atual != anterior:
        try:
            with open(marcador_caminho, "w", encoding="utf-8") as handle:
                json.dump(atual, handle, ensure_ascii=False, indent=1, sort_keys=True)
        except OSError:
            pass  # sem permissão de escrita: segue sem marcador
    return resultado
