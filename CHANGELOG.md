# Changelog

## [Não publicado]

Correções e melhorias da auditoria de 2026-09-30, ainda sem validar dentro do
Krita (ver `docs/AUDITORIA-2026-09-30.md`). A versão só sobe quando o roteiro de
validação rodar dentro do Krita 5 e 6.

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
- Novo `tests/test_vetorizacao.py`: o lote de balões em
  `Referencias/baloes-vetorizados` tem que continuar sendo reproduzível pelo
  script, byte a byte, e cada SVG é parseado como XML (é o que o
  `addShapesFromSvg` do Krita faz).
- Novo `tests/test_tiles.py` (classe `TestTilesDoKit`): os 11 PNGs de
  `hq_tools/resources/patterns` têm que bater byte a byte com o que
  `tiles.gerar_todos` produz; mexer numa função de tile sem regerar o arquivo
  passa a falhar.
- Novo `tests/test_packs_recursos.py` e `scripts/auditar-packs.py`: acham preset
  que cita arquivo de pincel que não vem no pack (o preset instala e o pincel
  não carrega). A lista atual tem 3 arquivos, que dependem de decisão do autor.

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

## [0.6.2] — 2026-09-27

Auditoria completa do estado v0.6.1 (delta pós-v0.5.4 + varredura geral).
76 testes passando (5 de símbolos removidos junto do código morto, 1 de
checagem estática e 3 asserções novas no fingerprint).

### Corrigido

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

### Limpeza

- `modules/balloons/symbols.py` removido (sem uso desde a v0.2, quando a aba
  de símbolos passou a abrir o docker nativo do Krita) junto de
  `tests/test_symbols.py`; histórico preservado no git. `paths.module_dir`
  removido (sem uso).

### Documentado

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