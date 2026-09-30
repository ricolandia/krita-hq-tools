# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-30 (v0.6.2 + auditoria
em 4 lotes, ainda sem release).

Espelho no Trilium (VPS): nota **"HQ Tools - Plugin Krita"** (`JVRkycXWq0KN`,
em Apps e Jogos), com as subnotas Estado e decisões, Instalação e uso,
Publicação (GitHub), Validação no Krita (pendente) e Resumo visual (Mermaid).

## Contexto

Ricardo quer produzir páginas de quadrinhos no Krita (Debian, AppImage) e
avaliou junto a IAs o que existe de plugins e o que valeria construir. A
conclusão da pesquisa está em `docs/contexto/` (os 4 arquivos originais).

## Decisões (25/09/2026)

- **Alvo:** Krita 5.3.4 (AppImage atual, Qt5/PyQt5/Python 3.13). Krita 6.0.4
  (Qt6/PyQt6) fica para depois; `core/compat.py` centraliza a compatibilidade.
- **Escopo:** plugin único `hq_tools` com 7 módulos habilitáveis: retículas e
  hachuras, balões, onomatopeias, paletas, páginas, pincéis e biblioteca do
  projeto.
- **Ordem das fases:** retículas → balões + paletas → páginas → pincéis.
- **Roteiro:** sintaxe própria (ver `docs/ROTEIRO-SINTAXE.md`).
- **Integração:** só CPMT (comicConfig.json, sem "s", UTF-16); sem renders do
  Blender por ora.
- **Manager de páginas:** ver, abrir e reordenar (exportação/lote ficam no CPMT).
- **Pincéis:** módulo próprio com slots e atalhos (não Ten Brushes/Shortcut
  Composer).
- **Paletas:** docker próprio com templates `.gpl`.
- Licença MIT; docs em `.md` na pasta do projeto (regra de documentação).

## Estado (v0.6.2)

Feito:

- v0.1.0 a v0.4.0 completas (ver CHANGELOG).
- **Kit de pincéis da comunidade (v0.5.0)**: curadoria com licença verificada
  na fonte; inclusos Deevad v8.2 (David Revoy, CC-BY 4.0, 64 presets + brushes/
  patterns/palettes) e Krita Watercolor Set (Vasco Basqué, CC-0, 13 presets +
  11 brushes) em `hq_tools/resources/brushes/`, cada um com `LICENSE.txt` e
  `FONTE.md`; aba "Packs" no docker de pincéis (instalar com um clique,
  ver licença, marca "[instalado]"); `modules/brushes/packs.py` puro com 6
  testes; CREDITS.md com atribuições e a lista de candidatos excluídos por
  falta de licença (Cityscape, Pesi's, portnov, Lilly_Mist, InkP).
- Testes do núcleo: 64 passando.
- **Ajuste (v0.5.1)**: aba "Comunidade" no docker de pincéis com os presets
  dos packs já instalados, agrupados por pack (autor e licença); fix do import
  de `standard_icon`. 65 testes passando.
- **Ajuste (v0.5.2)**: pack de fontes ampliado para 9 famílias OFL (Bangers,
  Comic Relief, Patrick Hand, Comic Neue, Londrina Solid, Nanum Pen Script,
  Gaegu, Boogaloo) com créditos no CREDITS.md; miniaturas da aba "Comunidade"
  em grade 72 px (mesmo tamanho dos conjuntos).
- **Ajuste (v0.5.3)**: aba Comunidade casa presets pelo nome interno do .kpp.
- **Auditoria focada + correções (v0.5.4)**: página com modelo agora é salva
  adaptada (faltava `saveAs` antes de fechar); regex do nome interno corrigida
  para o formato real (`<Preset name=...>`); tirinha esconde clones/outlines
  do template e insere painéis acima de Ink; numeração sem projeto não
  sobrescreve buracos; referência PNG usa "ToImageSize"; API pública no
  generator (panels_svg/build_page_document/save_page); Chewy (404) removido
  do kit; cache de aliases e validação de PNG no parser. 67 testes passando.
- **Kit ampliado (v0.6.0)**: 11 padrões/texturas próprios (papéis, retículas
  extras, trama de manga, hachuras, granulado) com botão de instalação no
  docker de retículas; modelos de página gerados no Krita (A4, A3, tirinhas
  1-3, grades 2x2/3x3) no "Definir modelo"; família Londrina completa nas
  fontes (12 famílias); paletas art-valores e art-carta-reticula. 77 testes
  passando.
- **Fix crítico (v0.6.1)**: `paths.py` usava `HOME` antes da definição e
  quebrava o import do plugin (dockers sumiam da listagem); corrigido com
  teste de regressão (`test_paths.py`); import validado com stub do krita;
  80 testes passando.
- **Auditoria completa + correções (v0.6.2)**: import ausente de
  `DIALOG_YES/NO` no docker de retículas (excluir preset derrubava o Krita em
  PyQt5) com novo teste estático (`test_static.py`, symtable); "Editar
  selecionada" agora atualiza a mesma camada (`setGenerator`) e a mesma
  máscara (`setFilter`) em vez de criar outra; `biblioteca` com
  `"ToImageSize"` no fallback de PNG; PyQt6: `SINGLE_SELECTION` no compat e
  `menu.exec`; posição no fingerprint de tom idêntico; modo "máscara vazia"
  não reutiliza tom; `new_project` preserva `comicConfig.json` existente;
  "Criar próxima página" não sobrescreve arquivo com `pageNumber` defasado;
  `symbols.py`/`test_symbols.py` e `paths.module_dir` removidos (código morto);
  docs atualizadas (CHANGELOG 0.6.1/0.6.2, README, ARQUITETURA, desktop).
  76 testes passando.
- **Decisão (26/09)**: dockers mantidos separados (7 módulos). Integrar tudo
  num único docker pioraria o workspace; o agrupamento em abas fica a cargo
  do próprio Krita (arrastar um docker sobre o outro em Configurações >
  Dockers). Avaliado e descartado: fundir catálogos num "HQ Tools: catálogos"
  e "hub único com abas". Dica documentada no README e no manual.

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (itens 2b, 3c, 5, 7b): padrões
  instalados, modelos gerados, fontes novas e abas Packs/Comunidade.
- Confirmar após o fix v0.6.1: os 7 dockers de volta na listagem do Krita.
- Itens novos da v0.6.2: excluir um preset do usuário (sem derrubar o Krita),
  "Editar selecionada" + Aplicar atualizando a mesma retícula/máscara, e
  "Novo projeto..." em pasta com `comicConfig.json` existente (não sobrescreve).

## Auditoria de 2026-09-30 (4 lotes, sem release ainda)

Auditoria por quatro frentes (correção, desempenho, robustez, testes/docs),
aplicada em quatro commits. Relatório completo em
**`docs/AUDITORIA-2026-09-30.md`**; changelog na seção `[Não publicado]`.
**161 testes verdes, com e sem PyQt instalado.** A versão continua 0.6.2: nada
foi validado dentro do Krita ainda, e a checklist de validação está no fim do
relatório.

| Lote | Commit | O que era |
|---|---|---|
| A | `e7da031` | dado do autor sobrescrito (projeto, `.cpmt`, presets, packs, páginas) |
| B | `e3142c3` | um docker quebrado derrubava os sete; ações fora do Ctrl+Z; `compat` sem escolha de binding |
| C | `33fb020` | miniatura decodificada por item a cada refresh; fontes recopravam tudo com `fc-cache -f` |
| D | `0e01706` | ZIP saía sem licença/créditos (só aviso); release sem conferir a tag; scripts de apoio |

Follow-ups: `97106bb` (não sobrescrever `comicConfig.json`) e `e738ba8`
(isolar o Qt da suíte, que não rodava no CI e rodava diferente na máquina).

Duas descobertas que valem lembrar:

- **A suíte nunca rodou no CI**: sem PyQt, 18 testes quebravam com `ImportError`.
  E na máquina do autor, com PyQt6 instalado, o teste do cache de miniaturas
  pegava o Qt de verdade e comparava `None` com `None` — passava por acaso. O
  falso está em `tests/qt_falso.py`, registrado como PyQt5 e PyQt6.
- **O lote de balões é reproduzível byte a byte** por
  `scripts/vetorizar-lote.py`, e `tests/test_vetorizacao.py` trava isso. Uma
  refactor "óbvia" no `vetorizar-baloes.py` (cortar o pescoço antes de suavizar)
  mudava a cauda de 9 para 37 segmentos em `balao-04b` sem erro nenhum.

- **Packs de pincéis: 3 arquivos citados e ausentes** (`deevad_bristle.png`,
  `flat-tip-dirty.gbr`, `T_Texture_7.gih`), medidos com
  `scripts/auditar-packs.py`. Os 3 presets instalam, mas o pincel não carrega.
  Pendente de decisão: buscar o original ou remover os presets.
  `tests/test_packs_recursos.py` trava a lista. Cuidado ao ler os .kpp: 4 usam
  chunk `zTXt` (comprimido) e 32 têm o pincel embutido, sem arquivo externo;
  sem tratar isso, a auditoria acusa problema onde não há.

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
PYTHONPATH=/tmp/semqt python3 -m unittest discover -s tests   # simular o CI (sem PyQt)
bash scripts/install-dev.sh                # instalar em dev
bash scripts/build-zip.sh                  # gerar ZIP instalável
```

## Pendências do autor (Ricardo)

Espelho no Trilium: subnota "Lista do autor (a criar)" (`FoIRvo2ztN0D`).

**Balões (SVG na biblioteca)**
- Jogo próprio de balões para substituir as amostras: fala redondo, fala
  oval, grito, pensamento, sussurro, narração e legenda.
- Variantes de cauda (esquerda, direita, embaixo) para os tipos de fala.
- Estilo consistente entre si (traço, cantos, sombra opcional).
- **Piloto (29/09):** 2 balões vetorizados a partir de `Referencias/baloes/`
  (`02a` e `05a`), aprovados no QA de visão; SVGs e prévias em
  `Referencias/vetores-teste/` (`balao-02a.svg`, `balao-05a.svg`, versões
  `-sem-suavizar` para comparar, renders `v-com/v-sem-*.png` e comparações
  `comparacao-*-3.png` com referência | sem suavizar | com suavizar).
  Ajustes do dia: o corpo ficou **sem a cauda integrada** (só o arco do
  balão, fechado no pescoço) e a cauda é uma forma única com a base por
  baixo do corpo; a suavização (`--suavizar 5`) tira o tremido do contorno
  mantendo as ondas maiores, e a cauda usa o contorno bruto (a média móvel
  achatava protuberâncias pequenas); a moldura é a união das duas formas
  mais a margem do traço (antes a cauda era cortada). Scripts novos e
  reutilizáveis: `scripts/vetorizar-baloes.py` (opções `--corte`,
  `--traco-px`, `--base-interna`, `--alargar-base`, `--suavizar`,
  `--epsilon`, `--linhas`) e `scripts/servir-para-penpot.py` (HTTP com CORS
  para o Penpot buscar arquivos). O autor desenhou a própria versão do `05a`
  no Inkscape (`Versao_rico.svg`) e ela virou a escolhida do piloto
  (`balao-05a-rico.svg`): canvas normalizado para a união das formas, cauda
  com traço aberto na base (para unir no Krita depois) e traço de 3 mm,
  escolhido no QA por casar com o peso da referência. Lição do dia: o SVG do
  Inkscape tem `transform` no grupo; analisar sem aplicar o transform engana
  (o arquivo original estava certo). O pipeline aceita arquivos do autor:
  basta normalizar o canvas (considerando transforms), deixar a cauda aberta
  e unificar o traço.
- **Lote (29/09):** 15 SVGs em `Referencias/baloes-vetorizados/` (14 gerados
  pelo `scripts/vetorizar-lote.py` + o `05a` do autor), com `previa.png`,
  `INDEX.md` e `lote.json` (prancha, recorte, traço e pescoço de cada um).
  QA de visão: corpos consistentes; caudas curtas de 02c, 03a, 03b, 04b,
  05b, 05d e 06b, mais a 06a, ficaram marcadas para o autor revisar; `03c`
  descartado (interior partido, precisa de corte manual fino). Ajuste fino
  de uma cauda: `--corte X1,Y1,X2,Y2`, `--alargar-base`, `--base-interna`.
  Pendente: revisão do autor, subir no Penpot e integrar no plugin.

**Onomatopeias (SVG)**
- Conjunto próprio para substituir as 8 amostras: impacto, velocidade, som
  pequeno e sons de ação.
- Versões com contorno e com preenchimento, para combinar com o nanquim.

**Painéis e páginas (modelos)**
- Já atendido pelo plugin: "Gerar modelos padrão do HQ Tools" cria A4, A3,
  tirinha de 1 a 3 tiras e grades 2x2/3x3 com guias de margem; os templates
  de HQ do próprio Krita (BD, EUA, mangá, Tsukirino, Waffle) entram direto no
  "Definir modelo de página"; americano e tankobon já existem no diálogo de
  nova página.
- Opcional (identidade própria): página modelo com o seu traço, desenhada no
  Krita e usada em "Página atual"; SVG de painel para a biblioteca.
- Validar: os modelos gerados ainda não existem na máquina (pasta
  `~/.local/share/krita/hq_tools/modelos/` vazia); clicar no botão do diálogo.

**Pincéis e traço**
- Presets próprios de hachura à mão (pincel para hachurar por cima da retícula).
- Avaliar conjuntos de pincéis próprios para os slots, além dos nativos e dos
  packs.
- Verificar a visibilidade do botão "Instalar bundle..." no docker de pincéis
  (sugestão: mover para a aba "Packs").
- Como criar (ou pedir a adaptação de) pincéis: subnota do Trilium "Como
  criar pincéis e traços (tutorial)" (`Z5UzRfufJAVV`).

**Divulgação**
- Ícone: **pronto** em `assets/` (mestre 512 claro/escuro mais a grade pequena
  dedicada para 128/64/32/16, sem a gota por decisão do autor), aprovado no QA
  de visão; editável nos 4 boards do Penpot e regras em `docs/DESIGN.md`.
- Banner ou capa para o repositório e redes (próximo passo, mesmo fluxo).
- Capturas e GIFs: roteiro pronto em `docs/ROTEIRO-CAPTURAS.md` (10 cenas com
  formato e nomes de arquivo).
- Página de exemplo (uma HQ curta) mostrando o fluxo completo, para o README
  e a release.
- Fluxo (Open Design → Penpot → vision → publicação): subnota do Trilium
  "Divulgação — fluxo (ícone, banner, página)" (`a6yFTPximC1C`).
- Design system aprovado: `docs/DESIGN.md` (paleta nanquim e papel, display
  Bangers/Londrina, regras de ícone e banner).

**Publicação**
- Criar o repositório no GitHub e subir o main (aguardando as bibliotecas).
- Criar a tag v0.6.2 (a release sai com o ZIP automaticamente).
- Trocar o endereço do repositório no CREDITS.md e no SESSION.md.
- Revisar README e INSTALL antes de abrir o repositório.

Pronto para a publicação: `INSTALL.md` (guia do usuário), CI em
`.github/workflows/` (tests em push/PR com Python 3.11/3.13 + checagem do ZIP;
release automática em tag `v*`), manual interno alinhado à v0.6.2 e CREDITS
com placeholder do repositório. O ZIP atual está em `dist/hq_tools-0.6.2.zip`
(não versionado; inclui `hq_tools.action` e `hq_tools.desktop`).

## Pendências futuras (fora de escopo por ora)

- Krita 6 (migração PyQt6 e ferramentas novas de texto/painéis).
- Renders do Blender como camada de referência (convenção `pXX_qYY`).
- Exportação e renomeação em lote no manager (segue no CPMT).
- Hachura desenhada à mão via presets de pincel específicos.
- Atualizar textos das páginas geradas e camada de referência.
- Balde com fechamento de falhas (proposta avaliada em `Novas_ideias/`, ver
  `docs/IDEIAS-FUTURAS.md`): núcleo sem numpy, canais RGBA, camada nova
  transparente; UX com seleção + X/Y manual; PoC de clique no canvas como
  v1.1.
- Presets de assistentes por painel; balão paramétrico (depende do Krita 6).
- Referência 3D: decisão atual é seguir o plano original (Blender renderiza
  por painel, `pXX_qYY_*.png` importado como camada de referência travada);
  o botão "Camada de referência" no HQ Tools foi aprovado. Rotas alternativas
  anotadas em `docs/IDEIAS-FUTURAS.md` (visualizador próprio com rig do
  Blender via JSON, Blender Layer, pose makers web).