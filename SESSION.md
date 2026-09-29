# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-27 (v0.6.2).

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

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
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

**Onomatopeias (SVG)**
- Conjunto próprio para substituir as 8 amostras: impacto, velocidade, som
  pequeno e sons de ação.
- Versões com contorno e com preenchimento, para combinar com o nanquim.

**Painéis e páginas (modelos)**
- Tirinha de 1 a 3 tiras, para o "Criar próxima página" e o "Definir modelo".
- Página A3 com guias.
- Modelo vetorial de painéis com o seu traço (contorno e sarjetas próprios).
- Avaliar modelos para americano e tankobon (os formatos já existem no diálogo).

**Pincéis e traço**
- Presets próprios de hachura à mão (pincel para hachurar por cima da retícula).
- Avaliar conjuntos de pincéis próprios para os slots, além dos nativos e dos
  packs.
- Verificar a visibilidade do botão "Instalar bundle..." no docker de pincéis
  (sugestão: mover para a aba "Packs").

**Divulgação**
- Ícone do plugin para o gerenciador do Krita e para o repositório.
- Banner ou capa para o repositório e redes.
- Capturas e GIFs curtos: aplicar retícula, criar página, editar retícula,
  pincéis.
- Página de exemplo (uma HQ curta) mostrando o fluxo completo, para o README
  e a release.

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