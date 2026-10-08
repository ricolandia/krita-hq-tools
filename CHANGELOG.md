# Changelog

## [Não publicado]

Roteiro: o comando `plano pN: valor` (texto livre) define o tipo de plano do
painel; ele aparece na nova coluna "Plano" da Produção, como rótulo no canto do
painel no storyboard gerado e no checklist.md.

**English:** script: the `plano pN: value` command (free text) sets the panel
shot type; it shows up in the new "Shot" column in Production, as a label in the
panel corner of the generated storyboard and in checklist.md.

## [0.15.0] — 2026-10-08

Produção (v0.15): o roteiro ganha auto-save (grava sozinho depois da última
tecla e no fechamento, com indicador "salvo HH:MM"); o checklist ganha barra de
progresso em três cores, bolinha de estado na árvore, marcador "▶" na página
pendente e botão "Abrir próxima pendente"; entra o timetracking manual
(play/pause, total e por página, salvo a cada minuto em `producao/tempos.json`)
e o `checklist.md` sai com checkboxes, emojis de estado e tempo por página.

**English:** production (v0.15): the script gets auto-save (writes on its own
after the last keystroke and on close, with a "saved HH:MM" hint); the
checklist gains a three-color progress bar, state dots in the tree, a "▶"
marker on the pending page and an "Open next pending" button; manual time
tracking lands (play/pause, total and per page, saved every minute to
`producao/tempos.json`) and `checklist.md` now has checkboxes, state emojis and
per-page time.

## [0.14.1] — 2026-10-07

Auditoria de 2026-10-07 (3ª): correções de borda, sem mudança de interface. A
inserção da biblioteca e do 3D entra em macro de desfazer (um Ctrl+Z desfaz a
inserção inteira, como nos outros módulos); código morto e imports não usados
saem; `install-dev.sh` respeita `XDG_DATA_HOME`; o smoke de inserção ganha o
caso da perspectiva a 300 dpi.

**English:** audit of 2026-10-07 (3rd): edge fixes with no UI change. Library
and 3D insertion now run inside an undo macro (one Ctrl+Z undoes the whole
insertion, like the other modules); dead code and unused imports removed;
`install-dev.sh` respects `XDG_DATA_HOME`; the insertion smoke gains the 300
dpi perspective case.

### Visualizador 3D — desempenho

O desenho do manequim ficou cerca de **3× mais rápido** no núcleo e o tick do
preview caiu de ~53–68 ms para ~31–41 ms (medido no harness, preview
240×240):

- Culling de costas no preview e na inserção (1.818 dos 3.140 triângulos;
  aprovado em QA de visão e conferência por pixel: silhueta idêntica, com
  diferença só de antialiasing nas bordas, média 0,25/255).
- Triangulação das faces pré-computada no modelo; `vertices_em_pose`
  recalculado só quando a pose muda (câmera livre para arrastar); cache das
  cores em hexadecimal; montagem do SVG com f-strings.

**English:** the mannequin drawing is about 3× faster in the core and the
preview tick dropped from ~53–68 ms to ~31–41 ms (measured in the harness,
240×240 preview): backface culling in the preview and insertion (1,818 of the
3,140 triangles; approved by vision QA and per-pixel comparison: identical
silhouette); precomputed face triangulation; `vertices_em_pose` recomputed
only when the pose changes; cached hex colors; SVG built with f-strings.

## [0.14.0] — 2026-10-07

Pose de mãos por lado no visualizador 3D: cada mão ganhou a própria caixa de
pose. Antes havia uma pose só com o seletor direita/esquerda/ambas, que
devolvia a outra mão ao repouso quando a pose do corpo mudava e não deixava
manter poses diferentes por mão.

**English:** per-hand poses in the 3D viewer: each hand now has its own pose
box. Before there was a single pose with a right/left/both selector, which
sent the other hand back to rest whenever the body pose changed and made it
impossible to keep different poses per hand.

### Visualizador 3D

- "Mão direita" e "Mão esquerda" com caixas independentes, aplicadas por cima
  da pose do corpo; o padrão segue fechada nas duas (como antes).
- `modelo3d.combinar_poses` centraliza a combinação (corpo + as duas mãos, a
  esquerda espelhada) e ganhou testes.

## [0.13.1] — 2026-10-07

Correção da inserção posicionada: em páginas de 300 dpi a arte caía muito
fora da seleção (a conta misturava pixels com os pontos dos shapes do Krita);
agora balões, onomatopeias e recursos da biblioteca entram dentro da seleção,
como os outros módulos. Também entrou a pose Joinha no visualizador 3D.

**English:** fix for the positioned insertion: on 300 dpi pages the artwork
landed far outside the selection (the math mixed pixels with Krita's shape
points); balloons, sound effects and library resources now land inside the
selection, like the other modules. The Joinha (thumbs up) pose also joined
the 3D viewer.

### Correções

- Inserção posicionada (v0.13.0): em páginas de 300 dpi a arte caía muito
  fora da seleção. A conta usava pixels da imagem sobre o espaço dos shapes
  do Krita, que é em **pontos** (``72/dpi`` de diferença). O
  ``posicionar_vetor`` agora converte a seleção e o centro da vista para
  pontos e usa a caixa dos próprios shapes; validado no smoke
  (``validar-insercao.py``, agora com documento a 300 dpi) com balão e
  onomatopeia dentro da seleção e o PNG da biblioteca exato.

### Visualizador 3D

- Pose **Joinha** (`poses/maos/joinha.json`, EN "Thumbs up"), exportada do
  `Mao_joinha_v2_.fbx` (o v1 sai vazio, sem keyframes).

## [0.13.0] — 2026-10-07

A inserção de balões, onomatopeias e recursos da biblioteca passou a levar em
conta onde você está: com uma seleção ativa, a arte entra reduzida (nunca
ampliada) e centralizada nela, desfazendo a seleção; sem seleção, nasce no
centro da vista atual, em vez do canto do documento. Também entrou a pose
**Salto** no visualizador 3D.

**English:** the insertion of balloons, sound effects and library resources
now takes where you are into account: with an active selection the artwork
lands shrunk (never enlarged) and centered in it, clearing the selection;
without one, it lands at the center of the current view instead of the
document corner. The **Salto** (jump) pose also joined the 3D viewer.

### Inserção posicionada

- Balões, onomatopeias e a biblioteca (SVG e PNG) usam `posicionar_vetor` e
  `destino_de_insercao` (`core/krita_helpers.py`): seleção ou centro da vista
  (a conta do centro reusa `parametros_do_canvas` e o mapeamento do
  visualizador 3D), com o encaixe central em `core/mapeamento.py`
  (`encaixe_central`, sem ampliar por padrão) e o moodboard passando a
  delegar para ele.
- O PNG da biblioteca é reduzido no próprio pixel data antes de entrar, então
  o encaixe vale para pintura também.
- Correção de "fantasma": a transformação dos shapes vetoriais agora repinta
  a **união** da área antiga com a nova (`updateAbsolute`); sem isso a arte
  ficava duplicada na posição original (achado no smoke `validar-insercao.py`,
  que valida os cinco casos com conferência de pixels).

### Visualizador 3D

- Pose **Salto** (`poses/corpo/salto.json`, EN "Jump"), exportada do
  `Pose_Pula_.fbx`; o `.blend` deu uma pose incompleta (20 ossos contra 27),
  então a convenção ficou registrada: poses sempre do **FBX exportado pelo
  autor**.

## [0.12.3] — 2026-10-06

O ZIP de instalação voltou a funcionar no importador do Krita: o pacote agora
inclui a entrada de diretório do módulo (`hq_tools/`), que o importador exige
para encontrar o plugin. Até a 0.12.2, todo ZIP falhava com "Nenhum arquivo
encontrado no arquivo morto" ("No plugins found in archive").

**English:** the install ZIP works again in Krita's plugin importer: the
package now includes the module directory entry (`hq_tools/`), which the
importer requires to find the plugin. Up to 0.12.2, every ZIP failed with
"No plugins found in archive".

### Correções

- `build-zip.sh`: grava as entradas de diretório no ZIP (a `hq_tools/` é a
  que o importador procura) e passa a validar o contrato do importador
  (`.desktop` > `X-KDE-Library` > `<nome>/` com `<nome>/__init__.py`),
  quebrando o build se não bater. Validado com o próprio
  `plugin_importer.py` do Krita (importa e extrai o plugin).
- INSTALL (PT/EN): contagem de dockers corrigida (12, com moodboard e
  produção), o `.action` agora é colocado pelo importador e há nota de
  solução de problemas para o erro em ZIPs antigos.

## [0.12.2] — 2026-10-06

O hub ganhou divisores: os botões ficam agrupados por fluxo
(Páginas/Produção, Moodboard/Biblioteca, Perspectiva/3D, Paletas/Pincéis,
Retículas/Balões e Onomatopeias), sem mudar nada mais.

**English:** the hub got dividers: the buttons are grouped by workflow
(Pages/Production, Moodboard/Library, Perspective/3D, Palettes/Brushes,
Screentones/Balloons and Sound effects), nothing else changed.

### Hub com divisores

- Os botões do hub ficam agrupados por divisores, na ordem pedida pelo autor:
  Páginas/Produção, Moodboard/Biblioteca, Perspectiva/3D, Paletas/Pincéis,
  Retículas/Balões e Onomatopeias; módulo fora do agrupamento cai no fim e
  nada some.
- O agrupamento vive em `core/registro.py` (`GRUPOS` + `agrupar`), com teste
  próprio; sem strings novas (só divisores).

## [0.12.1] — 2026-10-06

Correções de idioma e documentação: 81 strings que só existiam em português
foram traduzidas (rótulos de dados das docas, diálogos e as mensagens do
roteiro e do gerador) e os créditos ganharam a versão em inglês
(`CREDITS.en.md`), que também entra no ZIP.

**English:** language and documentation fixes: 81 strings that existed only
in Portuguese were translated (docker data labels, dialogs and the script
and generator messages) and the credits got an English version
(`CREDITS.en.md`), which also ships in the ZIP.

### Documentação

- `CREDITS.en.md`: créditos e licenças em inglês (o ZIP passa a levar os dois
  arquivos, e as referências dos documentos em inglês apontam para ele).
- Auditoria de i18n das docas: 81 strings que só existiam em PT foram
  traduzidas (rótulos de dados do hub, catálogo de perspectiva, opções das
  retículas, conjuntos de pincéis, formatos de página, biblioteca, o grupo
  "Juntas" do 3D, diálogos e as mensagens do parser do roteiro e do gerador).

## [0.12.0] — 2026-10-06

Módulo novo: **produção**, o checklist do roteiro. Cole o texto (a mesma
sintaxe das páginas, com o personagem opcional na fala) e use Ctrl+Enter:
cada página vira um nó com os painéis do layout, cada painel tem três estados
(esboço, arte e final), a meta de painéis por semana projeta a entrega e o
checklist sai em Markdown. Tudo fica na subpasta `producao/` do projeto (ou
na pasta padrão do plugin, com aviso, quando não há projeto aberto).

**English:** new module: **production**, the script checklist. Paste the text
(the same syntax as the pages, with the optional character on the line) and
use Ctrl+Enter: each page becomes a node with the layout panels, each panel
has three states (sketch, art and final), the weekly panel goal projects the
delivery and the checklist exports to Markdown. Everything lives in the
project's `producao/` subfolder (or in the plugin default folder, with a
notice, when no project is open).

### Produção (módulo novo)

- Checklist do roteiro: cole o texto (a mesma sintaxe das páginas) e use
  Ctrl+Enter; cada página vira um nó com os painéis do layout e cada painel
  tem três estados (esboço, arte e final), com as falas e os personagens à
  vista. Clique na coluna Estado para ciclar; o botão direito define direto.
- A sintaxe do roteiro ganhou o personagem opcional na fala
  (`fala p1 joao: texto`); o gerador de páginas continua igual.
- O `layout` aceita qualquer `gradeRxC` (ex.: `grade3x3`), além dos nomes e
  do `LxC`; a mensagem de erro orienta os formatos aceitos.
- Meta de painéis por semana com projeção de entrega, progresso, duplo
  clique abre a `pagina_NNN.kra` e "Exportar .md" salva o checklist em
  Markdown; o `roteiro.txt` e o `producao.json` ficam na subpasta
  `producao/` do projeto (criada junto com o projeto em Páginas).
- Aviso da sintaxe na própria doca (dica, placeholder e o botão "Sintaxe..."
  com o formato completo), em PT e EN.
- Sem projeto aberto, o checklist salva na pasta padrão do plugin e avisa
  para escolher a pasta do projeto; nada se perde ao fechar o Krita (a
  reabertura relê o roteiro, os estados e a meta).
- Validação: smoke `scripts/validar-producao.py` no Krita 5.3.4 isolado
  (montar, ciclar estados, meta, export e abrir a página).

## [0.11.0] — 2026-10-06

Módulo novo: **moodboard**, o quadro de referências do projeto. As imagens
escolhidas viram JPG comprimidos na pasta `moodboard/` e entram no
`moodboard.kra` como camadas de arquivo linkadas (o quadro fica leve), numa
grade que cresce; a referência selecionada pode ser inserida na seleção do
painel, travada, para desenhar por cima.

**English:** new module: **moodboard**, the project reference board. Chosen
images become compressed JPGs in the `moodboard/` folder and enter
`moodboard.kra` as linked file layers (the board stays light), on a grid that
grows; the selected reference can be inserted into the panel selection,
locked, for tracing over.

### Moodboard (módulo novo)

- Quadro de referências leve: as imagens escolhidas em "Adicionar
  referências..." são redimensionadas (lado máximo 1600 px) e salvas em JPG
  na pasta `moodboard/` do projeto (os originais não mudam); o
  `moodboard.kra` guarda só camadas de arquivo linkadas, posicionadas e
  escaladas por máscaras de transformação numa grade que cresce.
- "Inserir na seleção" (ou duplo clique) traz a referência para o painel
  como camada travada, na medida da seleção, para desenhar por cima;
  Renomear e Apagar cuidam da pasta e, se a referência está no quadro, a
  camada é atualizada junto (o quadro abre sozinho, se estiver fechado;
  caminhos são comparados resolvidos, tolerando symlink).
- Ferramentas de validação: `scripts/poc-filelayer-transform.py` (PoC da
  máscara de transformação, validado no Krita 5.3.4) e
  `scripts/validar-moodboard.py` (smoke de ponta a ponta, com o quadro
  salvo/reaberto e a inserção conferida pixel a pixel).

## [0.10.1] — 2026-10-05

Duas correções: as cores inseridas pelo visualizador 3D (e os recursos de
pintura da biblioteca) não trocam mais vermelho e azul, e os slots de pincéis
caíram para 8 com opção de limpar.

**English:** two fixes: colors inserted by the 3D viewer (and the library
paint resources) no longer swap red and blue, and the brush slots are down to
8 with a clear option.

### Pincéis: slots em 8 e como limpar

- Os slots caíram de 16 para 8 (duas fileiras), para a doca não ficar
  comprida; os atalhos vão de "HQ Tools: pincel 1" a "pincel 8" e
  configurações antigas com mais slots são truncadas na leitura.
- Agora dá para limpar: botão direito num slot (limpar este ou todos) e o
  botão "Limpar slots" esvazia tudo; os atalhos continuam existindo.

### Correções

- Cores trocadas (vermelho e azul) na inserção do visualizador 3D e nos
  recursos de pintura da biblioteca: o device RGBA 8 bits do Krita guarda os
  canais em BGRA (documentação do libkis: "Integer RGBA: Blue, Green, Red,
  Alpha"), e o código passava bytes RGBA8888 para o `setPixelData` e
  interpretava a leitura da biblioteca em RGBA. A conversão agora usa o
  `Format_ARGB32` do Qt (BGRA em memória) na inserção do 3D e nos dois
  sentidos da biblioteca (salvar e inserir recurso de pintura). Camadas
  inseridas antes da correção precisam ser reinseridas.

## [0.10.0] — 2026-10-05

O docker do visualizador 3D ficou mais curto (abas Pose, Câmera e Inserir), a
câmera ganhou perspectiva com lentes (14/28/35 mm) e a cor do manequim passou
a ser escolhível (Bege, Azul, Gelo e Grafite).

**English:** the 3D viewer docker is shorter now (Pose, Camera and Insert
tabs), the camera has perspective with lenses (14/28/35 mm) and the mannequin
color is selectable (Beige, Blue, Ice and Graphite).

### Visualizador 3D: abas e câmera com lentes

- Os controles do docker "HQ Tools: 3D" foram organizados em abas (**Pose**,
  **Câmera** e **Inserir**), com o preview sempre à vista; a altura do docker
  caiu bastante e cada etapa ficou no seu lugar.
- A câmera ganhou **Ortográfica** (padrão, como era) e **Perspectiva** com
  lentes **14 / 28 / 35 mm**: a lente mantém o enquadramento e muda só a
  convergência (14 mm dramática, 35 mm suave), e um ajuste garante que o
  conjunto continue cabendo no quadro como na ortográfica.
- A aba Câmera ganhou o seletor **Cor:** (Bege, Azul, Gelo e Grafite); a cor
  escolhida vale no preview, no flutuante e na inserção, e também nos estilos
  Silhueta e Contorno (antes fixos em preto).
- `scripts/preview-modelo3d.py` ganhou `--lente` para as prévias de QA.

## [0.9.1] — 2026-10-05

Biblioteca de poses do 3D dividida em corpo e mãos (com espelho para a mão
esquerda), linhas de efeito usando a seleção ativa e os rótulos de formulário
dos dockers traduzidos.

### Linhas de efeito com seleção

- "Inserir linhas de efeito" passa a usar a seleção ativa: as paralelas
  preenchem o retângulo da seleção e as de foco saem do centro dela, cortadas
  na borda (`effects.recortar_segmentos`), em vez dos campos em porcentagem do
  documento; sem seleção, os campos continuam valendo. A camada vetorial nova
  sai como antes.
- A retícula de preenchimento e o meio-tom já usavam a seleção como máscara
  (checkbox "Usar a seleção ativa como máscara"), então ali nada mudou.
- Os rótulos dos formulários dos dockers (retículas e páginas) passaram a ser
  traduzidos: o codemod `scripts/embrulhar-i18n.py` ganhou o `addRow` e os 31
  rótulos entraram no dicionário EN.

### Poses: biblioteca de corpo e mãos

- A biblioteca de poses do visualizador 3D foi dividida em `poses/corpo/`
  (Idle, Voa, Anda, Corre e Pose A) e `poses/maos/` (Fechada, Abertas e
  Segura, autorais para a mão direita), com dois combos no docker: "Corpo:" e
  "Mãos:".
- Novo seletor "Mão:" (Direita / Esquerda / Ambas): a pose de mão pode ser
  espelhada para a esquerda (o espelho troca o lado e nega o giro). O seletor
  normaliza a pose para a mão direita antes de aplicar o lado; as poses
  migradas guardavam os dois lados e, sem isso, "Direita", "Esquerda" e
  "Ambas" saíam iguais.
- "Limpar pose" volta ao padrão (Idle + Fechadas, nas duas mãos). Sem
  miniaturas por enquanto: os combos são listas com os nomes das poses.
- Exportador de poses (`scripts/exportar-poses3d.py`): opção `--parte
  corpo|maos|tudo`, entrada `.blend` e escolha automática da armadura
  principal quando o arquivo traz mais de um rig.

## [0.9.0] — 2026-10-05

### Idioma (PT/EN)

- A interface dos dockers agora fala português ou inglês, seguindo o idioma
  do sistema (locale `pt*` usa português; o resto usa inglês); a variável de
  ambiente `HQ_TOOLS_IDIOMA` (`pt`/`en`) força um idioma. Todas as strings
  visíveis (títulos, botões, dicas e mensagens) passam pela camada
  `core/i18n.py` (`i18n.t`), com o dicionário em `core/i18n_en.py` e o teste
  `tests/test_i18n.py` exigindo tradução para cada string (e nenhuma chave
  órfã).
- Documentação em inglês: `hq_tools/hq_tools_manual.en.html` e
  `INSTALL.en.md`, com os links nos READMEs; o ZIP passa a levar também o
  `README.en.md` e o `INSTALL.en.md`.

### Correções

- O arrasto do flutuante da perspectiva não atualizava o delta e a janela
  pulava; agora o movimento acompanha o mouse.

## [0.8.0] — 2026-10-05

Duas frentes novas: o **hub** para abrir e fechar os módulos e a **biblioteca
de linhas de perspectiva**, no mesmo fluxo de seleção do visualizador 3D
(inserção vetorial no painel). Validado dentro do Krita pelo autor em
05/10/2026.

| Hub | Perspectiva |
|---|---|
| ![Docker Hub com os botões que abrem e fecham os módulos](https://raw.githubusercontent.com/ricolandia/krita-hq-tools/main/Screenshots/10-hub.png) | ![Docker de perspectiva com a galeria de malhas, a prévia ampliada e os botões de inserir na seleção](https://raw.githubusercontent.com/ricolandia/krita-hq-tools/main/Screenshots/11-perspectiva.png) |

### Hub

- Docker "HQ Tools: hub": um botão por módulo abre e fecha a doca, com o
  botão marcado enquanto ela está aberta (fechar pelo X do Krita também
  desmarca). A opção "Fechar o atual ao abrir outro" alterna entre um módulo
  por vez e as dockas convivendo. Cada docker se registra numa lista única
  (`core/registro.py`), sem casar por título de janela.

### Biblioteca de perspectiva

- Docker "HQ Tools: perspectiva" com 9 conjuntos de linhas (frontal, dois e
  três pontos, pássaro e verme em dois níveis, curvilíneas de 4 e 5 pontos):
  escolha o conjunto, desenhe a seleção sobre o painel, use "Flutuar na
  página" (arrasto e roda) e insira no tamanho da seleção, abaixo do esboço,
  como **camada vetorial** (editável, dois nós por linha) ou referência; a
  inserção roda em macro (um Ctrl+Z desfaz), desfaz a seleção e fecha o
  flutuante (o botão "Flutuar na página" desmarca).
- Assets em `hq_tools/resources/perspectivas/` (cada linha é um `<path>` com
  exatamente 2 nós: reta `M`+`L`, arco `M`+`A`), pesquisa em
  `docs/PERSPECTIVAS.md`, gerador `scripts/gerar-perspectivas.py` e testes em
  `tests/test_perspectivas.py`.

### Correções

- Caminhos do Linux respeitam `XDG_DATA_HOME`/`XDG_CACHE_HOME` (Flatpak, como
  a tabela do `INSTALL.md` promete); `viewer3d` entrou no config padrão.
- "Guias de margem" agora mescla com as guias existentes em vez de apagá-las;
  "Instalar no Krita" das paletas pula as que já são a mesma cópia.
- Presets com o XML em `zTXt`/`iTXt` (3 do pack do Deevad) passam a ser lidos
  como no auditor de packs; "Criar próxima página" avisa quando o registro no
  CPMT falha.
- Sete abas internas passaram a usar a escala de espaçamento da casa, e a
  contagem de módulos foi corrigida nos documentos.

## [0.7.2] — 2026-10-04

O visualizador 3D ganha o fluxo por seleção e o preview flutuante sobre a
página, e as páginas novas nascem com a máscara dos painéis (os dois pedidos
vieram de um usuário no Krita Artists). Validado dentro do Krita pelo autor
em 04/10/2026.

[![Visualizador 3D sobre a página](https://raw.githubusercontent.com/ricolandia/krita-hq-tools/main/Screenshots/09-3d-na-pagina.png)](https://youtu.be/0rfDIr2QTDE)

▶ **Vídeo curto:** [Krita tools - update 3Dfloat](https://youtu.be/0rfDIr2QTDE) (o fluxo do 3D float em uso).

**Como usar o 3D sobre a página:**

1. Abra o docker "HQ Tools: 3D" e escolha o corpo e a pose.
2. Desenhe uma seleção retangular com a ferramenta de seleção sobre o painel
   de destino.
3. Ajuste a pose e o zoom (até 12x, para detalhes como uma mão): o preview
   adota a proporção da seleção e mostra exatamente o recorte que será
   inserido.
4. "Flutuar na página" mostra o preview sobre a seleção (arraste; alça ou roda
   redimensionam mantendo a proporção; opacidade; "Fixar" para desenhar por
   baixo).
5. "Inserir como camada" ou "Inserir como referência": a camada sai no tamanho
   exato da seleção, abaixo da camada ativa (o esboço fica por cima), e a
   seleção é desfeita.

### Visualizador 3D

- A inserção usa a **seleção ativa** (retângulo em pixels da imagem, sem
  conversão de tela): o preview adota a proporção dela (WYSIWYG, com zoom e
  deslocamento da câmera) e a camada entra abaixo do nó ativo.
- "Flutuar na página" só abre com seleção e aparece sobre ela.

### Páginas

- O grupo "Arte" (Sketch/Color/Ink) nasce com a "Máscara dos painéis": pintar
  fica limitado aos painéis e esconder a máscara libera a página inteira
  (sarjetas e margens).

### Correções

- Seleção: o libkis não tem `byteCount()`; a checagem antiga caía no `except`
  e considerava **toda** seleção vazia. `selection_vazia` agora usa
  `width()`/`height()`, o que conserta a inserção do 3D por seleção e a
  máscara de retículas com "Usar a seleção ativa".
- Windows: os caminhos do Krita são resolvidos por sistema (`%APPDATA%\krita`
  no Windows, `~/Library/Application Support/krita` no macOS), as fontes são
  registradas no HKCU, packs/bundles/templates usam a pasta certa e o
  `fc-cache` roda só no Linux. O CI agora também testa os módulos puros no
  Windows.

## [0.7.1] — 2026-10-03

Correção para Windows. No Krita do Windows (aplicativo gráfico sem console)
`sys.stderr` é `None`, e o plugin escrevia nele durante a importação: o HQ
Tools inteiro falhava com "Could not import hq_tools". Todas as escritas de
diagnóstico agora passam por um helper que confere se o stream existe.

- Novo `hq_tools/core/erros.py` (`escrever_erro`), usado por `compat.py`,
  `config.py` e `krita_helpers.log`.
- Testes: escrita com `sys.stderr = None` e regra estática que proíbe
  `sys.stderr` cru no código de runtime.

Também entram os ajustes feitos depois da 0.7.0:

- Ícone: o `ui.painel` aplica o ícone também no docker (abas e janelas
  flutuantes); READMEs PT/EN com o ícone no topo e social preview em
  `assets/social-preview.png`.
- Paletas: avisos claros nas duas abas (Aplicar na frente/fundo x Instalar) e
  duplo clique no swatch para aplicar na frente.
- INSTALL: o visualizador 3D não tem dependências extras (modelos e poses vão
  no ZIP; o Blender só é usado pelo autor).
- Documentação: o README deixa de anunciar o gerador de páginas a partir de
  roteiro (a aba saiu da interface na v0.3.0; o fluxo continua no código como
  referência, registrado em `docs/ROTEIRO-SINTAXE.md`).

## [0.7.0] — 2026-10-03

Segunda versão pública. Entra o **visualizador 3D** (a Rota A do
`docs/IDEIAS-FUTURAS.md`): um manequim low-poly posável para usar como
referência dentro do Krita, com escolha de corpo (Homem/Mulher) e biblioteca
de poses. A biblioteca do projeto ganha gestão de arquivos, o ícone do plugin
passa a aparecer no Gerenciador de plugins Python e o "Instalar bundle..."
muda para a aba "Packs". Validado dentro do Krita pelo autor em 03/10/2026.

### Visualizador 3D (novo módulo, em teste)

- Docker "HQ Tools: 3D" com o manequim do autor: malha MakeHuman (CC0) com
  rig Auto-Rig Pro, 68 ossos, cerca de 1.600 vértices. Sem Blender em tempo
  de execução: o FBX (binário) vira JSON pelo `scripts/exportar-modelo3d.py`
  e o núcleo lê em Python puro (sem Krita e sem numpy).
- Corpo: Homem e Mulher, com os mesmos nomes de ossos, então as poses valem
  para os dois.
- Biblioteca de poses: **Idle (mãos fechadas)**, padrão, e **Idle (mãos
  abertas)**; extração de FBX animado pelo `scripts/exportar-poses3d.py`,
  validada contra o Blender com desvio máximo de 7 mm.
- Interação: clique numa região do corpo (cabeça, tronco, braços, pernas)
  abre os sliders **Dobrar/Abrir/Girar** daquela junta, mapeados para os eixos
  reais do rig; um slider único dobra todos os dedos.
- Estilos: Sombreado, Silhueta (chapada) e Contorno (linha de silhueta com
  remoção de linhas escondidas, sem efeito de corpo transparente). Silhueta e
  Contorno são mais baratos que o sombreado.
- Câmera: arraste orbita; roda do mouse e botões −/+ dão zoom; Shift+arraste,
  botão do meio ou botão Mover deslocam o enquadramento; "Enquadrar"
  centraliza e "Frente" volta à vista frontal.
- Inserção: raster na resolução do documento, como camada comum ou como
  camada de referência travada (rótulo de cor, trava e opacidade 150).
- Núcleo com 30 testes, mais o preview `scripts/preview-modelo3d.py` para QA
  fora do Krita; `--decimar FRAÇÃO` no exportador gera modelos mais leves.

### Biblioteca do projeto

- "Renomear...", "Duplicar" e "Apagar" operam o recurso selecionado direto no
  docker, com confirmação ao apagar. Núcleo sem Krita e 8 testes.

### Docker de pincéis

- "Instalar bundle..." saiu da fileira inferior e entrou na aba "Packs", junto
  dos demais instaladores.

### Ícone do plugin

- `Icon=hq_tools` no `.desktop` e `scripts/install-icons.sh` instala os PNGs
  no tema hicolor: o Gerenciador de plugins Python passa a mostrar o ícone
  (antes ele não aparecia em lugar nenhum).

### Repositório e CI

- `Referencias/` e `Novas_ideias/` saíram do git (ficam no `.gitignore`); as
  amostras do kit seguem publicadas dentro de `modules/`.
- O CI não depende mais da pasta local: os testes do kit pulam de propósito e
  a checagem que não pode pular passou a ser só o `TestVetorizador`.

### Documentação

- README PT/EN com o módulo 3D, os controles de câmera e a captura
  `Screenshots/07-3d.png`; manual interno e INSTALL atualizados.
- `docs/IDEIAS-FUTURAS.md` com a revisão das sugestões e as decisões de rota.

### Divulgação

- Demo em vídeo (1 minuto): https://youtu.be/B9KYYyLdHF0

Suíte: 222 testes.

## [0.6.2] — 2026-10-03

Primeira versão pública. Reúne a auditoria de 2026-09-30 (quatro lotes, ver
`docs/AUDITORIA-2026-09-30.md`), a camada de interface compartilhada, o kit de
balões e onomatopeias do autor e o polimento de empacotamento e release.
Validado dentro do Krita pelo autor em 03/10/2026.

### Interface — camada compartilhada (Lotes 1 e 2)

Novo `hq_tools/core/ui.py`, com os widgets que os sete dockers construíam por
conta própria: `botao`, `rotulo`, `rotulo_info`, `separador`, `icone`,
`espacamento` e `painel`. Não há estilo próprio: fundo, borda, fonte e ícone
continuam vindo do tema do Krita, que é o que respeita a escolha do autor, o
alto dpi e a troca de tema.

- **52 botões** nos 7 dockers passaram por `ui.botao`, que exige o tooltip como
  segundo argumento. Antes: 11 botões com ícone, 22 com tooltip, e a diferença
  entre eles era grande — o docker de páginas tinha 10 tooltips e 5 ícones, o de
  retículas, que é o maior, tinha 1 e nenhum.
- **Botão sem tooltip agora quebra a assinatura**, e `tests/test_ui.py` proíbe,
  por análise estática, que `QPushButton` volte a ser criado direto num docker.
  É o que mantém os 52 tooltips sem voltarem a sumir no próximo botão.
- **Rótulo de estado não estufa mais o painel.** O `lbl_info` da aba Retículas
  (célula em px, DPI, LPI) reservava a largura da linha inteira, então um aviso
  longo alargava o docker em vez de quebrar; agora quebra linha e não reserva
  largura mínima. Vale conferir no Krita se ainda empurra: se empurrar, falta
  relaxar a política horizontal do rótulo.
- **Sem altura fixa.** Os dois `setFixedHeight(24)` dos botões de cor saíram
  (travavam a altura contra o tema); `tests/test_ui.py` também proíbe
  `setFixedHeight`/`setFixedWidth` nos dockers.
- Espaçamento unificado pela escala do `docs/DESIGN.md` (4 entre controles, 8
  entre linhas, 12 na borda) via `ui.painel`/`ui.espacamento`, e divisórias com
  `ui.separador()` nos pontos onde os grupos separam de verdade.
- Ícones por chave semântica (`"pasta"`, `"atualizar"`, `"aplicar"`), com
  fallback para `SP_FileIcon`: chave desconhecida perde o ícone, não o botão.
- Nota de verificação (2026-10-01): o import de `KRITA_PALETTES_DIR` em
  `palettes/docker.py` existe desde o commit original `d718877`, junto com
  `QtCore`/`QtGui`; não houve correção de nome não definido nesse arquivo.

### Balões e onomatopeias: kit do autor substitui as amostras

22 SVGs desenhados à mão no Inkscape pelo autor (8 caudas, 9 falas, 2
pensamentos e 3 onomatopeias), a partir do material de origem que fica fora do
repositório, sob a licença MIT do plugin.

- As 19 peças de balão (caudas, falas e pensamentos) substituem as 6 amostras
  genéricas de `modules/balloons/samples/`; as 3 onomatopeias (WHOOSH!, POW!
  e CRASH!) substituem as 8 genéricas de `modules/onomatopeias/samples/`.
  Quem já tem a pasta de amostras não recebe cópia nova: o plugin só copia na
  primeira execução.
- Caudas 01 a 04 têm a base aberta, para emendar no corpo dentro do Krita.
- O lote gerado de 29/09 e os materiais de `Referencias/vetores-teste/` foram
  removidos; os scripts de vetorização ficam como ferramenta para pranchas
  futuras.
- `tests/test_vetorizacao.py` passou a travar o kit (XML, viewBox, traço, sem
  texto, manifesto e índice em sincronia) e a igualdade byte a byte entre o
  kit e as amostras embarcadas.
- CREDITS.md registra a autoria (Ricardo Graça) e a licença MIT do kit.

### Corrigido — dados do autor (Lote A)

- **Crítico**: `create_project()` aceitava um projeto existente e escrevia por
  cima do `comicConfig.json` do autor. Agora recusa com `CPMTError`.
- **Crítico**: `CPMTManager` escrevia o `.cpmt` por cima e, se json.dump
  falhasse no meio, deixava o arquivo pela metade. Passa a escrever em arquivo
  temporário e trocar, com backup do anterior.
- Presets, packs, páginas e recursos do autor: releitura antes de alterar,
  escrita atômica e backup antes de sobrescrever. JSON ilegível não derruba mais
  o plugin, e vira `.bak` em vez de ser apagado.
- Falha ao escrever página não deixa mais um `.kra` órfão no disco.

### Corrigido — isolamento, desfazer e frequência (Lote B)

- Um docker com erro no import derrubava todos os outros: os sete módulos
  passam a ser registrados um a um, e o que falhar é avisado no log. Os caminhos
  do registro estavam errados (`screentone.docker` em vez de
  `hq_tools.modules.screentone.docker`), o que impedia o registro de funcionar.
- `screentone.docker` era importado no topo do plugin; agora é importado
  quando as ações são criadas, protegido por try/except.
- Retícula, linhas de efeito, balões e onomatopeias entram em macro de
  desfazer (Ctrl+Z). Antes, cada aplicação era um passo irreversível.
- `showFloatingMessage` recebe `0` no quarto argumento, que é o `priority`;
  omitting deixava o aviso com a prioridade errada.
- SVG que não gera formas deixava a camada vetorial vazia no documento.
- LPI↔LPC: a conversão era feita duas vezes e o valor físico podia passar do
  limite da resolução; a alternância entre retículas agora limpa os IDs de
  edição do alvo.
- Seleção vazia não era detectada (`byteCount()`), e pasta de preset
  inacessível ou arquivo em Latin-1 derrubavam a ação.

### Corrigido — PyQt5/PyQt6 e choice de binding

- `compat.py` tentava PyQt5 e caía para o outro binding. Agora `qt_probe`
  decide: versão do Krita primeiro, depois o binding já carregado no processo,
  depois o que estiver instalado, e o erro final diz o que fazer.

### Desempenho einterface (Lote C)

- Cache de miniaturas de `.kra`: o gerenciador de páginas pedia uma miniatura
  por item a cada refresh, e cada uma abria o arquivo e decodificava o
  `preview.png` — 40 páginas viravam 40 zips por refresh, na thread da
  interface. Agora os bytes e o `QPixmap` ficam em cache, com a chave
  (caminho, mtime, tamanho) e limite de 256 entradas.
- Instalar as fontes do kit não recopia mais o diretório inteiro nem roda
  `fc-cache -f` (que reconstrói o cache do sistema e trava a interface por
  segundos): copia só o que mudou e usa o `fc-cache` incremental.
- Cursor de espera durante a geração dos modelos de página, com restauração no
  `finally` — cursor de espera esquecido trava o Krita até reiniciar.

### Testes

- 76 → 161 testes. A suíte passou a rodar igual na máquina do autor e no CI:
  sem PyQt instalado ela quebrava com `ImportError`, e com PyQt6 instalado o
  teste do cache de miniaturas passava por acaso (o `qt_probe` prefere o
  binding já carregado). O falso de Qt ficou em `tests/qt_falso.py`.
- Novo `tests/test_vetorizacao.py`: cada SVG do kit é parseado como XML (é o
  que o `addShapesFromSvg` do Krita faz), com manifesto e índice em sincronia,
  e as amostras embarcadas têm que ser idênticas ao kit desenhado pelo autor
  (a pasta fonte é local, fora do repositório; no CI esses testes pulam).
- Novo `tests/test_tiles.py` (classe `TestTilesDoKit`): os 11 PNGs de
  `hq_tools/resources/patterns` têm que bater byte a byte com o que
  `tiles.gerar_todos` produz; mexer numa função de tile sem regerar o arquivo
  passa a falhar.
- Novo `tests/test_packs_recursos.py` e `scripts/auditar-packs.py`: acham preset
  que cita arquivo de pincel que não vem no pack (o preset instala e o pincel
  não carrega). A medição achou 3 casos, resolvidos no mesmo dia (seção
  abaixo): o teste agora exige **zero** referências quebradas.

### Packs de pincéis da comunidade

- **3 presets removidos do kit** por citarem uma textura que os autores dos
  packs nunca distribuiram. Medido em 2026-09-30 em todo o histórico dos dois
  repositórios de origem (`Deevad/deevad-krita-brushpresets`, 103 arquivos, do
  `master` e da tag `8.2`; `vascoalexander/krita-watercolor-set`, 42 arquivos,
  com as duas versões de preset, Krita 2.7 e 2.8): nenhum dos três arquivos
  existe em versão alguma, então não há o que buscar:

  | Preset removido | Textura citada | Pack |
  |---|---|---|
  | `deevad 2d expressive thin` | `deevad_bristle.png` | Deevad v8.2 |
  | `deevad 6n stamp floor particles` | `flat-tip-dirty.gbr` | Deevad v8.2 |
  | `X9AI_WC_Scattered_Sharp` | `T_Texture_7.gih` | Watercolor Set |

  Sem o arquivo, o preset instala e aparece na lista, e o pincel não carrega
  (o Krita cai no padrão) — o que faz o usuário perder tempo achando que o
  preset veio quebrado. Reapontar para a textura de outro preset mudaria o
  pincel que o autor escolheu, e os três `.kpp` são arquivos originais sem
  modificação declarada no `FONTE.md`. Cada pack documenta agora a remoção no
  próprio `FONTE.md`, com a contagem corrigida (Deevad 64 → **62** presets,
  Watercolor 13 → **12**).

### Empacotamento

- `scripts/build-zip.sh` agora **quebra** se `LICENSE`, `CREDITS.md` ou
  `INSTALL.md` estiverem ausentes, e confere o conteúdo do ZIP depois de gerá-lo
  (o `.desktop` e o `.action` na raiz, `__init__.py` no pacote, nada de
  `__pycache__`). Antes, saía um aviso e o ZIP seguia sem a licença.
- Workflow de release confere se a tag é a versão de `core/version.py` e publica
  a entrada da versão no CHANGELOG, em vez das notas automáticas de commit.

### Scripts

- `vetorizar-baloes.py`: `dilatar`/`erodir` não vazam mais pela borda da imagem
  (o `np.roll` trazia pixels do lado oposto); prancha inexistente ou recorte
  fora da imagem dão mensagem em vez de traceback; e a cauda fica sem
  suavização quando dá para usar os mesmos índices do corpo, com o comentário
  do código agora correspondente ao que o script faz.
- `servir-para-penpot.py`: reiniciar logo depois de parar não falha mais com
  "Address already in use", e pasta inexistente dá erro claro.
- `descoberta_scripter.py`: o bloco 7 descobre o binding do Qt em vez de
  importar PyQt5 fixo, que não existe no Krita 6.

### Base anterior (27/09)

Auditoria completa do estado v0.6.1 (delta pós-v0.5.4 + varredura geral).
76 testes passando (5 de símbolos removidos junto do código morto, 1 de
checagem estática e 3 asserções novas no fingerprint).

#### Corrigido

- **Crítico**: `screentone/docker.py` usava `DIALOG_YES`/`DIALOG_NO` sem
  importar; excluir um preset do usuário levantava NameError e, em PyQt5,
  exceção não tratada em slot derruba o Krita (qFatal). Import corrigido e
  cobertura nova: `tests/test_static.py` varre o pacote com `symtable` e falha
  em qualquer nome global usado sem definição (pegaria o bug original).
- **Editar retícula**: "Editar selecionada" agora atualiza a mesma camada.
  "Aplicar retícula" com a camada em edição troca o gerador no lugar
  (`setGenerator`) e só substitui a máscara quando há seleção ativa (ou modo
  "máscara vazia"); "Aplicar meio-tom" com a máscara em edição atualiza a
  configuração do filtro no lugar (`setFilter`). Antes cada aplicação criava
  uma camada/máscara nova e o texto do botão prometia atualizar.
- `biblioteca/docker.py`: fallback de inserção de PNG usava
  `"KeepAspectRatio"` (valor inválido no libkis, caía em "sem escala"); agora
  usa `"ToImageSize"` como no gerenciador de páginas.
- PyQt6 (preparo para o Krita 6): enum cru `QAbstractItemView.SingleSelection`
  e `menu.exec_` (removido no PyQt6) em `brushes/docker.py`; constantes
  centralizadas (`compat.SINGLE_SELECTION`, `menu.exec`).
- Posição do padrão agora participa do fingerprint de tom idêntico: aplicar o
  mesmo preset em posição diferente cria camada nova em vez de reutilizar e
  ignorar a posição. `screentone_properties` passou a ler `position_x/y` do
  preset (antes fixava 0 e o docker sobrescrevia por fora).
- Modo "Máscara vazia (revelar pintando)" não reutiliza tom idêntico: a
  reutilização esvaziaria a máscara de um tom visível existente; agora o modo
  sempre cria camada nova com máscara vazia.
- `new_project` não sobrescreve mais um `comicConfig.json` existente na pasta:
  abre o projeto e registra a página atual se ainda não estiver na lista.
- "Criar próxima página" em modo projeto evita sobrescrever arquivo existente
  quando o `pageNumber` está defasado (avança o número até achar nome livre).

#### Limpeza

- `modules/balloons/symbols.py` removido (sem uso desde a v0.2, quando a aba
  de símbolos passou a abrir o docker nativo do Krita) junto de
  `tests/test_symbols.py`; histórico preservado no git. `paths.module_dir`
  removido (sem uso).

#### Documentado

- Entrada 0.6.1 (fix do `paths.py`) que faltava no changelog; README com a
  versão atual do ZIP; ARQUITETURA com os 7 módulos e a árvore de recursos
  atualizada; SESSION com o estado v0.6.2; comentário do `.desktop` com os
  7 módulos; DESCOBERTA com o fim da extração própria de símbolos.
- `docs/VALIDACAO.md`: itens novos para validar a exclusão de preset, a
  atualização da retícula/máscara em edição e a proteção do comicConfig.

## [0.6.1] — 2026-09-26

### Corrigido

- `core/paths.py` usava `HOME` antes da definição e quebrava o import do
  plugin (dockers sumiam da listagem); corrigido com teste de regressão. 79 testes
  passando.

## [0.6.0] — 2026-09-26

### Adicionado

- Kit de padrões e texturas próprios (11 tiles gerados por código, MIT):
  papéis (liso, gramatura, trama), aguado, retículas extras (estrelas,
  corações, ruído), trama de manga, hachuras 45°/135° e granulado de nanquim;
  botão "Instalar padrões e texturas (kit)" no docker de retículas; os tiles
  entram no modo "tom com padrão" do Halftone.
- Modelos de página gerados pelo plugin (botão "Gerar modelos padrão do HQ
  Tools" no "Definir modelo de página"): A4, A3, tirinhas 1-3 tiras e grades
  2x2/3x3, com guias de margem e camadas.
- Família Londrina completa (Shadow, Outline e Sketch) nas fontes OFL do kit
  (12 famílias no total).
- Paletas novas: art-valores (escala de cinzas) e art-carta-reticula (tons com
  LPI sugerido).

### Corrigido

- Nada quebrado; 77 testes passando (10 novos: tiles e specs de modelos).

## [0.5.4] — 2026-09-26

Auditoria focada nas mudanças pós-v0.3.2 (manager, brushes, compat,
empacotamento). 66 testes passando antes e 67 depois.

### Corrigido

- Página criada a partir de modelo nunca era salva adaptada (faltava
  `saveAs` antes de fechar): formato/DPI, guias e tirinha não iam para o
  disco; agora a página adaptada é gravada.
- Regex do nome interno do `.kpp` não casava o formato real (`<Preset
  name=...>` na raiz, não `<param name="name" value=...>`): o pack do Vasco
  Basqué continuava oculto na aba Comunidade; corrigida com teste de
  integração contra um `.kpp` real do kit.
- Tirinha a partir de template: o contorno antigo (ex.: "Mask clone-outline")
  vazava sobre a tira; agora clones/outlines do template são escondidos e a
  tira entra acima de Ink.
- Numeração sem projeto (pasta avulsa): buracos na sequência sobrescreviam
  páginas existentes; agora busca o próximo índice livre.
- Referência PNG importada com "KeepAspectRatio" (valor inválido = sem
  escala); agora usa "ToImageSize".
- `generator` ganhou API pública estável (`panels_svg`, `build_page_document`,
  `save_page`); o docker de páginas não usa mais nomes privados.
- Chewy (arquivos 404 baixados por engano) removido do kit de fontes.
- Parser de `.kpp` valida a assinatura PNG e cacheia os aliases por mtime.

## [0.5.3] — 2026-09-26

### Corrigido

- Aba "Comunidade": presets de packs cujo nome interno difere do nome do
  arquivo não apareciam (ex.: Krita Watercolor Set, arquivos `X9AA_WC_*.kpp`
  com preset "X9AA - WC Basic"). Agora o casamento usa o nome interno (lido
  do chunk tEXt 'preset' do .kpp) com fallback para o nome do arquivo.

## [0.5.2] — 2026-09-26

### Adicionado

- Pack de fontes de HQ ampliado (9 famílias, todas SIL OFL 1.1 com créditos):
  Bangers, Comic Relief (Regular/Bold), Patrick Hand, Comic Neue
  (Regular/Bold), Londrina Solid, Nanum Pen Script, Gaegu e Boogaloo;
  instaláveis com um clique no docker de balões. (Luckiest Guy e Chewy saíram
  do Google Fonts; Boogaloo entrou no lugar.)

### Corrigido

- Miniaturas da aba "Comunidade" no docker de pincéis: agora em grade (72 px),
  mesmo tamanho das abas de conjuntos.

## [0.5.1] — 2026-09-26

### Adicionado

- Aba "Comunidade" no docker de pincéis: presets dos packs da comunidade já
  instalados no Krita, agrupados por pack com autor e licença; clique ativa o
  pincel.

### Corrigido

- Import ausente de `standard_icon` na aba Packs (erro ao abrir o Krita).

## [0.5.0] — 2026-09-26

### Adicionado

- Kit de pincéis da comunidade (bundling curado): Deevad v8.2 (David Revoy,
  CC-BY 4.0; 64 presets, brushes, patterns e palettes) e Krita Watercolor Set
  (Vasco Basqué, CC-0; 13 presets e 11 brushes), em
  `hq_tools/resources/brushes/<pack>/` com `LICENSE.txt` e `FONTE.md`
  (autor, origem, licença, alterações: nenhuma).
- Aba "Packs" no docker de pincéis: lista com autor/licença, "Instalar pack
  selecionado" (copia para os recursos do Krita e marca "[instalado]") e
  "Ver licença".
- `modules/brushes/packs.py` (núcleo puro) com 6 testes; CREDITS.md com as
  atribuições e a lista de candidatos excluídos por falta de licença.

## [0.4.0] — 2026-09-26

### Adicionado

- "Criar próxima página" com diálogo: formato (A4, A5, A3, tirinha, americano,
  tankobon, quadrado ou livre em mm), DPI e painéis da tirinha (3 padrão,
  ajustável); a página nasce com as guias de margem (0,5 / 1 / 1,5 cm por
  lado) já aplicadas.
- "Definir modelo de página...": usa a página atual salva ou um template de HQ
  do Krita (BD Europeu, EUA, Mangá, Tsukirino, Waffle), localizado via
  `QLibraryInfo.PrefixPath` e copiado para `~/.local/share/krita/hq_tools/modelos/`.
- Adaptação do modelo ao criar a página: formato igual = cópia direta; A3 =
  redimensiona (`scaleImage`); tirinha = substitui os painéis por uma tira
  horizontal de N painéis.
- "Camada de referência": marca a camada selecionada (rótulo, trava e
  opacidade reduzida).
- "Importar referência (PNG)...": insere o PNG como camada de arquivo travada
  no grupo ativo (renders do Blender ou poses de ferramentas web).
- `roteiro.FORMATS` ganhou A3 (297 x 420) e tirinha (297 x 210) e
  `build_strip_panels` para o layout da tira.

### Corrigido

- Nada quebrado; 58 testes passando (3 novos: formatos A3/tirinha e tira).

## [0.3.2] — 2026-09-26

Auditoria completa (especialistas em Python, API do Krita e arquitetura).
55 testes passando antes e depois.

### Corrigido

- Compatibilidade PyQt6 (Krita 6): enums crus em `brushes/docker.py`
  (CustomContextMenu, UserRole, QSizePolicy) e `screentone/docker.py`
  (QMessageBox.Yes/No) trocados pelas constantes do `core/compat.py`.
- Numeração de página em "Criar próxima página": passava `offset=contagem+1`
  ao `next_page_name` e pulava números de forma crescente; agora usa
  `offset=1` com `pageNumber+1` (sequência correta, igual ao CPMT) e caminhos
  relativos normalizados (sem `./`).
- Modo "Máscara vazia (revelar pintando)" da retícula: nascia invisível sem
  máscara editável; agora cria a camada com seleção total e anexa uma
  `SelectionMask` vazia, pintável para revelar.
- Espessura das linhas de efeito: não era convertida de px para pt (ficava
  ~4x mais grossa a 300 dpi); agora escala com o DPI.
- `cpmt.save()` reescrevia config legado em UTF-8 como UTF-16; agora preserva
  o encoding detectado (BOM).
- Empacotamento: manual movido para dentro de `hq_tools/` (o Krita só carrega
  `X-Krita-Manual` de dentro da pasta do módulo); `hq_tools.action` incluído
  no ZIP; `build-zip.sh` não depende mais do binário externo `zip`.
- Limpezas: fallback morto em `_qimage_bytes`, dupla chamada em
  `unique_layer_name`, variável morta em `halftone_cmyk_properties`, duplicata
  no regex do roteiro.
- Atalhos de pincel agora funcionam com o docker fechado (fallback direto
  pelo slot configurado).

### Documentado

- `docs/ARQUITETURA.md`, `README.md`, `SESSION.md`, `docs/DESCOBERTA.md` e o
  manual atualizados (7 módulos, 16 slots, `comicConfig.json`, kit).
- SESSION ganhou a seção "Pendências do autor": modelos de balões,
  onomatopeias, painéis e páginas (tirinha/strip e A3).

## [0.3.1] — 2026-09-25

### Adicionado

- "Novo projeto..." agora usa a pasta da página atual salva: sem documento ou
  página não salva, aviso modal "Salve a página atual em uma pasta. Essa pasta
  será a pasta do projeto."; cria `comicConfig.json` (CPMT, UTF-16) com a
  página registrada, subpastas `biblioteca/{baloes,paineis,onomatopeias}`,
  `export`, `templates` e `translations`, e aponta a biblioteca para a pasta
  do projeto.
- Biblioteca do projeto com dois tipos de camada: Vetorial (SVG via `toSvg`)
  e Pintura (PNG transparente recortado pela camada ativa, via `pixelData` +
  `QImage`); inserção de PNG como camada de pintura (`setPixelData`, com
  fallback para camada de arquivo); lista com `.svg` e `.png`.
- Avisos mistos: modais (`QMessageBox`) para fluxos e decisões; toast
  flutuante para sucessos rápidos.
- Polimento de interface: grupos (`QGroupBox`), ícones de tema
  (`compat.standard_icon`) e tooltips nos dockers de páginas e biblioteca.

### Corrigido

- Nada quebrado; ajustes de compatibilidade (enums PyQt5/PyQt6) nos dockers
  novos.

## [0.3.0] — 2026-09-25

### Adicionado

- Gerenciador de páginas: "Novo projeto..." cria a pasta do projeto (diálogo
  com nome, pasta base e subpasta); "Criar próxima página" gera a página na
  pasta do projeto (com painel, camadas e contorno) e atualiza as miniaturas;
  "Guias de margem" cria 12 guias (0,5 / 1 / 1,5 cm por lado) no documento
  ativo.
- Docker "HQ Tools: biblioteca": cria balões, painéis e onomatopeias do autor
  em documento 15 x 15 cm a 300 dpi, exporta a camada vetorial como SVG na
  pasta da biblioteca (subpastas por tipo) e insere com duplo clique.
- Docker "HQ Tools: onomatopeias": 8 amostras e pasta própria para modelos
  criados no Inkscape.
- Kit de HQ: fontes OFL (Bangers, Comic Relief Regular/Bold, Patrick Hand)
  instaláveis com um clique; balões de domínio público (CC0/PD) copiados na
  primeira execução; `CREDITS.md` com todas as licenças.
- Balões: botão "Símbolos do Krita" que abre o docker nativo do Krita.

### Corrigido

- Projetos do CPMT: o arquivo real é `comicConfig.json` (sem "s") em UTF-16;
  agora é lido corretamente, com fallback para o nome antigo.
- Aba Roteiro removida da interface (módulos puros preservados no repo).
- Slug de nomes de arquivos sem acentos quebrados (normalização Unicode).

## [0.2.0] — 2026-09-25

### Adicionado

- Pincéis v2: conjuntos sugeridos (Rascunho, Contornos, Aquarela/Guache,
  Acrílico/Óleo, Retículas) com cartões de miniatura + nome montados com os
  presets instalados do Krita; 16 slots (4 por conjunto) com atalhos;
  instalador de bundles de pincel.
- Retículas v2: editar a retícula selecionada (camada de preenchimento e
  máscara de meio-tom), máscara vazia (revelar pintando), mostrar área como
  seleção, reutilizar tons idênticos, posição X/Y do padrão, tom com padrões
  instalados do Krita (gerador Pattern como preenchimento e como tela do
  Halftone) e meio-tom colorido por canal CMYK com ângulos de impressão.
- Linhas de efeito/velocidade: gerador vetorial com foco ou paralelas.
- Paletas artísticas: 15 novas `.gpl` (Zorn, retrato, paisagem, amanhecer,
  noite, terra, pastel seco, aquarela suave, guache vibrante, acrílico, retrô
  HQ, BD linha clara, super-herói, mangá, sépia).
- Balões: aba "Símbolos do Krita" com as bibliotecas de símbolos instaladas,
  miniaturas e inserção em um clique, com licença creditada.
- Testes do núcleo ampliados (44 no total).

### Corrigido

- Símbolos: a inserção passou a abrir o docker nativo "Bibliotecas de
  símbolos" do Krita (a renderização própria não cobria todos os formatos de
  biblioteca); a aba vira navegação com licença.
- Retículas em abas (Retículas / Linhas de efeito) para não estourar a tela.
- Grade de paletas compacta, com nome e código no tooltip.

## [0.1.0] — 2026-09-25

Primeira versão.

### Adicionado

- Plugin `hq_tools` com 5 módulos: retículas e hachuras, balões, paletas,
  páginas (gerenciador + roteiro) e pincéis.
- Núcleo compartilhado: configuração JSON, helpers do Krita, leitura/escrita
  do comicsConfig.json (CPMT), miniaturas de `.kra`, paletas `.gpl`,
  compatibilidade PyQt5/PyQt6.
- Retículas: presets com LPI, cálculo de célula pelo DPI, aplicação como
  camada de preenchimento (dentro do grupo ativo, máscara da seleção) e como
  máscara do filtro Halftone (meio-tom não destrutivo).
- Balões: catálogo SVG com amostras, inserção vetorial, opção de camada `text`
  para o CPMT.
- Paletas: templates de HQ e visualização das paletas do Krita.
- Páginas: gerenciador com miniaturas (abrir, reordenar), gerador de roteiro
  com sintaxe própria e registro no CPMT.
- Pincéis: 12 slots com presets instalados e atalhos via `.action`.
- Testes do núcleo (23), scripts de instalação/ZIP e validação via Scripter.
- Documentação: README, SESSION, arquitetura, descoberta técnica, sintaxe do
  roteiro e roteiro de validação.