# Changelog

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