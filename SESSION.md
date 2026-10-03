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
  na fonte; inclusos Deevad v8.2 (David Revoy, CC-BY 4.0, 62 presets + brushes/
  patterns/palettes) e Krita Watercolor Set (Vasco Basqué, CC-0, 12 presets +
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
- Kit do autor: lista de modelos na pasta de balões e a inserção no grupo
  ativo (conferir também uma cauda com base aberta, para emendar no corpo).

## Auditoria de 2026-09-30 (4 lotes, sem release ainda)

Auditoria por quatro frentes (correção, desempenho, robustez, testes/docs),
aplicada em quatro commits. Relatório completo em
**`docs/AUDITORIA-2026-09-30.md`**; changelog na seção `[Não publicado]`.
**161 testes verdes, com e sem PyQt instalado** (177 depois da camada de
interface, ver adiante). A versão continua 0.6.2: nada foi validado dentro do
Krita ainda, e a checklist de validação está no fim do relatório.

| Lote | Commit | O que era |
|---|---|---|
| A | `e7da031` | dado do autor sobrescrito (projeto, `.cpmt`, presets, packs, páginas) |
| B | `e3142c3` | um docker quebrado derrubava os sete; ações fora do Ctrl+Z; `compat` sem escolha de binding |
| C | `33fb020` | miniatura decodificada por item a cada refresh; fontes recopravam tudo com `fc-cache -f` |
| D | `0e01706` | ZIP saía sem licença/créditos (só aviso); release sem conferir a tag; scripts de apoio |

Follow-ups: `97106bb` (não sobrescrever `comicConfig.json`) e `e738ba8`
(isolar o Qt da suíte, que não rodava no CI e rodava diferente na máquina).

Duas descobertas que valem lembrar:

- **O CI não rodava o teste dos balões**: `test_vetorizacao.py` exige numpy e
  Pillow e pulava em silêncio (5 de 7 testes, inclusive a reprodução byte a byte
  dos 15 SVGs). O workflow agora instala as dependências e falha se aparecer
  `skipped`.
- **A suíte nunca rodou no CI**: sem PyQt, 18 testes quebravam com `ImportError`.
  E na máquina do autor, com PyQt6 instalado, o teste do cache de miniaturas
  pegava o Qt de verdade e comparava `None` com `None` — passava por acaso. O
  falso está em `tests/qt_falso.py`, registrado como PyQt5 e PyQt6.
- **O lote de balões gerado era reproduzível byte a byte** por
  `scripts/vetorizar-lote.py`, e `tests/test_vetorizacao.py` travava isso. Uma
  refactor "óbvia" no `vetorizar-baloes.py` (cortar o pescoço antes de suavizar)
  mudava a cauda de 9 para 37 segmentos em `balao-04b` sem erro nenhum. O lote
  gerado saiu de cena em 03/10 (substituído pelo desenho do autor); o teste
  agora valida o kit entregue, e os scripts seguem cobertos por testes próprios.

- **Packs de pincéis: os 3 presets com textura ausente foram removidos**
  (`deevad 2d expressive thin`, `deevad 6n stamp floor particles`,
  `X9AI_WC_Scattered_Sharp`). A hipótese era que faltassem no pacote de origem;
  medido o histórico inteiro dos dois repositórios, **nunca existiram**:
  `Deevad/deevad-krita-brushpresets` (103 arquivos, `master` e tag `8.2`) e
  `vascoalexander/krita-watercolor-set` (42 arquivos, Krita 2.7 e 2.8) não têm
  nenhum dos 3. Sem a textura o preset instala, aparece na lista e o pincel não
  carrega; reapontar trocaria o pincel do autor. Cada `FONTE.md` registra a
  remoção e corrige a contagem (64 → 62, 13 → 12), e
  `tests/test_packs_recursos.py` agora exige zero referências quebradas.
  Cuidado ao ler os .kpp: 4 usam chunk `zTXt` (comprimido) e 32 têm o pincel
  embutido, sem arquivo externo; sem tratar isso, a auditoria acusa problema
  onde não há.

## Interface: camada compartilhada (2026-10-01, lotes 1 e 2, sem release)

Novo `hq_tools/core/ui.py` (`botao`, `rotulo`, `rotulo_info`, `separador`,
`icone`, `espacamento`, `painel`), aplicado aos 7 dockers: **52 botões** agora
passam por `ui.botao`, **177 testes verdes**. Sem estilo próprio, o visual
continua sendo o do tema do Krita (decisão do Ricardo: seguir o tema, nada de
QSS). Detalhes na seção `[Não publicado]` do CHANGELOG.

O que a auditoria de interface mostrou, e que vale como regra para o resto do
código de interface:

- **Não havia regra, só 7 decisões independentes.** 52 botões escritos em
  momentos diferentes: 11 com ícone, 22 com tooltip. O docker de páginas (o
  mais cuidado) tinha 10 tooltips e 5 ícones; o de retículas, que é o maior, tinha
  1 e nenhum. A correção não é o tooltip em si, é a trava que impede o próximo
  botão de nascer sem ele: `dica` é o segundo argumento de `botao`, sem padrão, e
  `tests/test_ui.py` proíbe `QPushButton` direto e `setFixedHeight/Width` nos
  dockers por `ast`. Regressão de interface agora quebra a suíte.
- **Rótulo de estado é o que alarga o docker.** O Qt reserva para um `QLabel` a
  largura da linha inteira como largura mínima, então o `lbl_info` da aba
  Retículas ("célula 4.32 px a 300 dpi = máx. 85.7 lpi, reduzida ao aplicar")
  estufava o painel em vez de quebrar a linha. `rotulo_info` liga o wrap e zera a
  largura mínima. **A conferir no Acer**: se ainda empurrar, falta relaxar a
  política horizontal do rótulo (não dá para provar layout sem PyQt).
- **`setFixedHeight(24)` nos botões de cor brigava com o tema.** Tirado; quem
  manda no tamanho é o tema.
- Ícone por chave semântica (`"pasta"`, `"atualizar"`, `"aplicar"`) e fallback
  `SP_FileIcon`: chave errada perde o ícone, não o botão. A API de ícones do
  tema do Krita (em vez do `QStyle`) continua **não verificada** e fora do lote.
- Nota de verificação (2026-10-01): o import de `KRITA_PALETTES_DIR` em
  `palettes/docker.py` existe desde o commit original `d718877`, junto com
  `QtCore`/`QtGui`; não houve correção de nome não definido nesse arquivo.

Escopo que **não** foi mexido, de propósito: `QToolButton` dos slots e dos
cartões (tem reordenação por arrastar e clique direito, que é comportamento, não
aparência), tipografia das listas de miniaturas, tamanho dos ícones da lista.

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
python3 -m unittest tests.test_tiles -v    # um arquivo só (a partir da raiz)
PYTHONPATH=. python3 tests/test_tiles.py    # um arquivo direto
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
- **Lote gerado (29/09, substituído):** 15 SVGs saídos das pranchas com o
  `scripts/vetorizar-lote.py`; o autor decidiu redesenhar tudo em 01/10 e
  removeu esse lote em 03/10. Os scripts ficam como ferramenta para pranchas
  futuras.
- **Lote do autor (02 e 03/10): 22 SVGs** em
  `Referencias/baloes-vetorizados/` (8 caudas, 9 falas, 2 pensamentos e 3
  onomatopeias), com `INDEX.md` e `lote.json` novos. QA de visão em 03/10:
  nenhum traço cortado ou forma quebrada; para revisar com o autor apenas
  `Cauda_Tail_01_` (a cauda aberta mais ambígua), `Fala_Speak_03_` (sem
  preenchimento) e `Ono_VSFX_01_` (letras quase encostadas), mais o traço
  fino de `Fala_Speak_03/08/09` (0,68 a 0,70 mm contra 0,90 a 1,01 mm no
  resto). `tests/test_vetorizacao.py` passou a travar o lote do autor (XML,
  viewBox, paths com traço, sem texto, manifesto e índice em sincronia).
- **Integrado (03/10):** as 19 peças de balão viraram as amostras de
  `hq_tools/modules/balloons/samples/` (as 6 genéricas saíram) e as 3
  onomatopeias substituíram as 8 genéricas de `onomatopeias/samples/`.
  `Cauda_` no lugar de
  `Calda_`; licença MIT registrada no CREDITS.md; `tests/test_vetorizacao.py`
  passou a exigir kit e amostras idênticos byte a byte. A pasta do usuário
  do Acer foi atualizada à mão (o plugin só copia amostras com a pasta
  vazia). A publicação fica para depois da validação no Krita.

**Onomatopeias (SVG)**
- Conjunto próprio para substituir as 8 amostras: impacto, velocidade, som
  pequeno e sons de ação.
- Versões com contorno e com preenchimento, para combinar com o nanquim.
- **Parcial (03/10):** 3 já no lugar das 8 amostras (`Ono_VSFX_01/02/03_`:
  "WHOOSH!", "POW!" e "CRASH!", fonte Bangers convertida em contorno). Faltam
  os sons menores; referências de estudo em `Referencias/Onomat/` (não
  versionadas ainda).

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
- Repositório no GitHub: **https://github.com/ricolandia/krita-hq-tools**
  (criado em 03/10; remote `origin` por SSH). O projeto deixou de ser pasta
  local.
- **Validado dentro do Krita pelo autor em 03/10/2026.** A release v0.6.2 sai
  pela tag `v0.6.2` (o CI roda os testes, monta o ZIP e publica).
- Subir o `main`: os commits locais (auditoria, kit de balões, capturas)
  entram no primeiro push.
- A tag `v0.6.2` fecha a publicação: a release sai com o ZIP pelo CI.
- Pasta local fora do repositório (03/10): `Referencias/` e `Novas_ideias/`
  entraram no `.gitignore` e saíram do índice (`git rm --cached`); os arquivos
  continuam no disco. As amostras do kit seguem publicadas dentro de
  `modules/`, e os testes do kit pulam no CI quando a pasta falta.

Pronto: `INSTALL.md` (guia do usuário), CI em `.github/workflows/` (tests em
push/PR com Python 3.11/3.13 + checagem do ZIP; release automática em tag
`v*`), manual interno alinhado à v0.6.2, CREDITS e SESSION com o endereço do
repositório. O ZIP atual está em `dist/hq_tools-0.6.2.zip` (não versionado;
inclui `hq_tools.action` e `hq_tools.desktop`).

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