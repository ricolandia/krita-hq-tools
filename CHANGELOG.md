# Changelog

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