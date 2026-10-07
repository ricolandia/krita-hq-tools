# Auditoria de 2026-10-07

Terceira auditoria do HQ Tools, com escopo completo e foco no que entrou
depois da auditoria de 05/10 (v0.8.0 a v0.14.0): hub, perspectiva, pincéis
com slots, moodboard, produção, camada i18n, inserção posicionada e as poses
de mão do 3D.

**Estado de partida:** v0.14.0 publicada, 393 testes verdes, `py_compile` OK
em 110 arquivos, git limpo, harness headless do Krita recriado.

## Como a auditoria foi feita

Cinco frentes com roteiro próprio, cada achado **reproduzido antes de
entrar** (a regra de ouro das auditorias anteriores). O que só roda dentro do
Krita foi verificado no harness headless (`HQ_POC_SCRIPT` + `xvfb-run`), com
os smokes do repositório e medições próprias; o QA visual usou o modelo de
visão nas capturas 11–15, com os indícios do modelo separados dos achados
verificáveis. Quick wins aplicados na hora, com a suíte verde a cada passo;
o resto virou recomendação.

## Frente Python (estática)

`py_compile` nos 110 arquivos + varredura AST própria (imports e nomes
mortos, `except` amplo, `open` fora de `with`, defaults mutáveis, `assert` em
produção, marcadores).

| Achado | Onde | Gravidade | Destino |
|---|---|---|---|
| Função morta `selection_for_apply` (substituída por `destino_de_insercao`) | `core/krita_helpers.py` | baixa | removida |
| Import não usado `sys` | `scripts/embrulhar-i18n.py` | baixa | removido |
| Import não usado `os` | `tests/test_packs_recursos.py` | baixa | removido |
| Import não usado `QtCore` | `scripts/poc-filelayer-transform.py` | baixa | removido |
| Handle de arquivo sem `with` (2 ocorrências) | `tests/test_cpmt.py` | baixa | corrigido |
| Handle de arquivo sem `with` | `scripts/validar-producao.py` | baixa | corrigido |

**Verificado, não é achado:** `except BaseException` em `core/cpmt.py:82` e
`modules/screentone/core.py:380` (escrita atômica: limpa o temporário e
relança); `except` amplos do PoC e do `qt_falso` (teste); `pyqtSlot` sem uso
no shim `core/compat.py` (export de compatibilidade); dockers entram por
carregamento dinâmico (`plugin.py` → `_importar_classe`) e os geradores de
perspectiva/tiles por registry interno, então não são código morto. Sem
`TODO`/`FIXME` no código.

## Frente Krita (libkis)

| Achado | Onde | Gravidade | Destino |
|---|---|---|---|
| Inserção da **biblioteca** e do **3D** fora de macro de desfazer (os outros 5 módulos usavam `run_in_macro`) | `modules/biblioteca/docker.py`, `modules/viewer3d/docker.py` | média | quick win aplicado |

**Medição da convenção do `addShapesFromSvg`** (harness, documento a 300
dpi): SVG **sem unidade** é interpretado em **pixels do documento** (100
unidades → 24 pt + traço); com `pt` no tamanho, 1 unidade = 1 **ponto**.
Conferidos os três produtores de SVG: linhas de efeito (`lines_to_svg`, em
`pt` ✓), páginas (`generator`, em `pt` ✓) e perspectiva (`linhas.gerar`, sem
unidade → pixels ✓ correto por construção). O `posicionar_vetor` (correção de
300 dpi da v0.13.1) converte pixels→pontos para os shapes ✓.

**Falso positivo desfeito:** a hipótese de que a perspectiva precisava de
conversão para pontos foi **reproduzida e derrubada** pelo caso F novo do
`validar-insercao.py` (a malha cai dentro da seleção convertida: caixa
46,9/23,4 com 218,1×169,3 contra 48/24 com 216×168 ✓). O caso F fica como
regressão no smoke.

**Smokes no harness (07/10):** `validar-moodboard`, `validar-producao` e
`validar-insercao` (A–F) → `runner: OK`; o teste headless das poses por mão
(v0.14.0) também passou no mesmo dia.

**Verificado, correto:** `run_in_macro` (try/finally, tolerante a falha do
`beginMacro`); `selection_bounds`/`deselect`/`document_dpi` (com fallbacks);
máscara de transparência (bytes cinza 8 bits, validada pelo autor na v0.7.2);
BGRA nos três pontos de conversão (biblioteca, 3D e máscara); moodboard
(camada de arquivo + máscara de transformação com limpeza em falha, `realpath`
e macro); timers do 3D (singleShot filho do widget); `attach`,
`attach_below_active` e `target_container`.

## Frente Desempenho

Medições fora do Krita (melhor de 5 rodadas) e o tick real do docker 3D no
harness.

| Item | Tempo |
|---|---|
| `roteiro.parse_script` (600 painéis, 58 KB) | 3,1 ms |
| `producao.montar` (600 painéis) | 3,6 ms |
| `producao.para_markdown` / `progresso` | 1,2 ms / 5,6 ms |
| `moodboard.listar_referencias` (500) | 0,55 ms |
| `moodboard.salvar` / `carregar_layout` (500 itens) | 3,5 ms / 2,0 ms |
| `moodboard.destino` (500 posições) | 0,4 ms |
| `mascara.mascara_dos_paineis` (100 painéis, 2480×3508) | 18,5 ms |
| `effects` (gerar/recortar/SVG, 143 linhas) | ≤ 0,2 ms cada |
| `modelo3d.carregar` / `aplicar_semantica` / `vertices_em_pose` | 4,9 / 0,3 / 2,7 ms |
| `modelo3d.renderizar` SVG 800×600 | 20,6 ms |
| **Tick do docker 3D no Krita (240×240)** | **46–68 ms** |

O tick do 3D é o ponto mais pesado da interface: a geração+rasterização do
SVG domina e o custo não cai com o tamanho do preview (a 240×240 continua
~50 ms). Com o timer de 30 ms o arrasto roda a ~15 fps; funciona (validado
pelo autor), mas é o candidato natural a otimização. Sem laços O(n²) nem I/O
repetido nos demais cores.

## Frente Design/UX (QA visual)

QA de visão nas capturas 11–15:

- **11 (perspectiva)**, **13 (moodboard)** e **14 (produção)**: sem texto
  cortado, sobreposto ou ilegível; contraste bom. Observação cosmética: o
  rótulo da miniatura sobre a malha azul (11) perde um pouco de contraste.
- **12 (hub + 3D)**: a captura mostra a interface **antiga** de mãos
  ("Mãos: Fechada" / "Mão: Direita") — precisa de recaptura para a v0.14.0
  (já registrado no SESSION).
- **15 (thumbnail do vídeo)**: ok; o "Modelo" sem valor visível é do quadro
  do vídeo, não da interface.
- **Indícios do modelo descartados após conferir o código:** "finalis" (o
  rótulo é "finais", `producao/docker.py:454`) e "nivel" (os presets têm
  acento: "Pássaro · nível 1", `perspectiva/linhas.py:241`).

Consistência: os dockers novos usam a camada `ui.` (17–25 usos cada) e não
têm `setStyleSheet`/larguras fixas/margens cruas; a cobertura de i18n dos
rótulos de dados já era travada por teste desde a v0.12.1.

## Empacotamento e docs

- `build-zip.sh`: contrato do importador ok; ZIP 0.14.0 gerado e conferido.
- `auditar-packs.py --estrito`: 74 presets, **0 referência órfã**.
- Contagens de módulos corretas nas docs ("12 dockers" no INSTALL PT/EN) e a
  tabela de Flatpak presente no INSTALL.
- `install-dev.sh` ainda fixava `~/.local/share/krita`: agora respeita
  `XDG_DATA_HOME` (quick win).

## Reconciliação com as auditorias anteriores

- **Fechado desde a 05/10:** merge das guias de margem; `Palette(None)` (o
  docker de paletas agora guarda `resource is None` antes de instanciar);
  contagem de módulos; tabela Flatpak do INSTALL; `install-dev.sh` (nesta
  auditoria).
- **Continua aberto (recomendações):** cache de miniatura para os SVGs de
  balões/onomatopeias (o `core/thumbs.py` não é usado por esses dockers);
  `pack_instalado` com estado "parcial"; lint no CI; listas de validação
  dentro do Krita (consolidadas abaixo).
- **Resolvido de passagem:** `ui.rotulo_info` ganhou `setMinimumWidth(0)` e
  `setWordWrap` (documentado no próprio helper); falta a conferência visual
  em documento aberto (na lista).

## Quick wins aplicados nesta auditoria

1. Macro de desfazer na inserção da biblioteca e do 3D (consistência com os
   outros cinco módulos).
2. `selection_for_apply` removida (código morto) e três imports não usados.
3. Três handles de arquivo passaram a usar `with` (teste e smoke).
4. `install-dev.sh` respeita `XDG_DATA_HOME`.
5. Caso F no `validar-insercao.py`: malha da perspectiva dentro da seleção a
   300 dpi (regressão medida no harness).

## Validação pendente no Krita (consolidada)

- [ ] **Ctrl+Z único** ao inserir da biblioteca e do 3D (agora com macro) e ao
      aplicar retícula/linha de efeito/balão/onomatopeia/moodboard/perspectiva.
- [ ] Inserir a **perspectiva** numa página a 300 dpi: a malha cobre a seleção
      (o caso F do smoke mede isso fora da interface; falta o olho no app).
- [ ] Abrir **dois documentos** e usar "Flutuar na página" (ancorar no
      viewport do documento ativo).
- [ ] "Guias de margem" com guias já existentes: as antigas continuam.
- [ ] Abas de pincéis em painel estreito: rótulos sem corte; conferir as
      margens novas das abas de pincéis, paletas e retículas.
- [ ] `ui.rotulo_info` com documento aberto: o aviso quebra em vez de estufar.
- [ ] Recapturar a captura `12-hub-e-3d.png` com as caixas "Mão direita" e
      "Mão esquerda" (v0.14.0).
- [ ] Desligar um módulo em Configurar Krita e reabrir: os outros continuam.
- [ ] No Krita 6 (PyQt6): repetir o essencial (o `qt_probe` decide o binding).

## Recomendações (não aplicadas)

- **Tick do 3D:** memoizar `_rgb_para_hex` (~20% no render puro; a luz segue a
  câmera, então o ganho real é menor no arrasto), montar as partes do SVG com
  f-strings e estudar rasterizar com `QPainter` direto no lugar do
  SVG→`QSvgRenderer`; se o arrasto incomodar, prévia em resolução reduzida
  durante o gesto.
- Cache de miniatura para os SVGs de balões e onomatopeias (reusar
  `core/thumbs.py`), quando os kits crescerem.
- `pack_instalado` com estado "parcial" em vez de "instalado".
- Lint (ruff) no CI para pegar nome morto e import não usado sem depender da
  suíte.
- Fundo sutil nos rótulos das miniaturas de perspectiva (contraste sobre a
  malha azul).
