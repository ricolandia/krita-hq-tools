# Ideias futuras e propostas avaliadas

Registro das propostas avaliadas (ex.: pasta `Novas_ideias/`) que ainda não
foram integradas. Cada item traz o veredito e as condições para entrar no
plugin.

**Prioridade atual (03/10/2026):** a biblioteca de poses do visualizador 3D:
catalogar as novas poses, dividir em corpo e mãos, "Salvar pose atual" e
miniatura no seletor. O Gantt atualizado está no Trilium (nota do roadmap).

## Proposta avaliada: balde com fechamento de falhas (`fillbucket`)

Fonte: `Novas_ideias/hq_tools_fillbucket_proposta/` (núcleo `core/gapclose.py`
com 7 testes, docker não validado e relato do problema da morfologia).
Avaliação em 2026-09-25. **Decisão: avaliar sem integrar** (a pedido do autor).

### Veredito

- **Abordagem correta**: dilatar a tinta só para conter o flood fill, sem
  erodir depois (a erosão desfaz a ponte em linhas de 1 px), excluindo sempre
  a tinta original da área de pintura. A lição documentada no relato é boa
  engenharia.
- **Núcleo**: os 7 testes passam (validado com numpy do sistema).
- **Docker**: não validado dentro do Krita.

### Bloqueio e correções obrigatórias antes de qualquer integração

1. **numpy não existe no Python do AppImage** do Krita 5.3.4 (confirmado por
   inspeção: zero arquivos em `site-packages/numpy`). O núcleo precisaria ser
   reescrito em Python puro (mesma API e mesmos testes).
2. **Ordem de canais**: a proposta assume BGRA (`[2,1,0,3]`), mas na biblioteca
   do plugin (v0.3.1, validada) o `pixelData` de camada RGBA 8 bits veio em
   RGBA (QImage RGBA8888 direto). Com a troca, vermelho e azul sairiam
   trocados.
3. **Camada nova copia a lineart**: `pintado = rgba.copy()` colocaria a
   lineart do recorte na camada "Cor (balde)". O correto é camada nova
   transparente com apenas a área pintada, dentro do grupo ativo.
4. **Imports**: `from core.gapclose import ...` não casa com o padrão do repo;
   usaria import relativo (`hq_tools/modules/fillbucket/gapclose.py`).

### Ideias futuras anotadas (do mesmo documento de avaliação)

- **UX v1 do balde**: seleção ativa + ponto X/Y manual (sem risco de
  captura de clique); recorte pelo retângulo da seleção com aviso para áreas
  grandes (ex.: >800x800 px), já que o label em Python puro fica lento.
- **Clique direto no canvas (v1.1)**: PoC de event filter no
  `view.canvas().canvasWidget()` + transformações do `Canvas` (20 linhas),
  antes de acoplar ao módulo.
- **Presets de assistentes por painel** (2 pontos, 3 pontos, régua de
  simetria): salvar e reaplicar config de assistente por painel; barato e
  economiza tempo repetitivo.
- **Balão paramétrico** (cauda reposicionável + texto que redimensiona o
  balão): depende de validar texto-em-forma (fluxo em forma) no Krita 6.
- **Exportação webtoon/social**: dispensável por enquanto (Batch Exporter
  cobre o genérico).
- **Preflight de impressão** (sangria, marcas de corte, numeração): continua
  no Scribus.

## Fora de escopo (confirmado)

- Modelos 3D posáveis no canvas: não razoável via plugin; Blender por fora.
- Apagador vetorial por interseção: API de vetores do Krita não expõe trim
  por interseção de forma acessível.

## Referência 3D: rotas avaliadas (2026-09-25)

Decisão do autor: seguir o plano inicial (Blender renderiza a referência por
painel e o plugin importa no quadro); as rotas abaixo ficam anotadas.

### Rota A: visualizador próprio (modelo com rig do Blender → JSON → Python)

Viável e a mais integrada, com condições:

- Script de exportação (add-on do Blender) grava JSON: hierarquia de juntas
  (FK), malha com pesos por vértice (até 4 ossos), faces e materiais.
- No Krita, módulo em Python puro (sem numpy): skinning (matrizes 4x4 +
  pesos), projeção ortográfica com câmera rotativa, painter's algorithm e
  saída em SVG vetorial (polígonos chapados, cor por normal).
- Manipulação por sliders de junta (FK), câmera, presets de pose + espelhar;
  inserção como camada vetorial travada no painel.
- Condições: malha low-poly (500-1500 faces) para fluidez; sem numpy;
  sliders na v1 (arrastar no canvas fica para depois); Blender só na criação
  do modelo (Krita manipula offline).
- **Em teste (03/10/2026):** F1 e F2 concluídos: exportador FBX->JSON
  (`scripts/exportar-modelo3d.py`), núcleo `hq_tools/core/modelo3d.py` (FK,
  skinning, projeção ortográfica, SVG) com 16 testes, preview em SVG e QA de
  visão em 6 poses. O modelo do autor (MakeHuman CC0 + rig Auto-Rig Pro, 68
  ossos, 1591 vértices) já roda e bate com o Blender na validação numérica.
  Eixos medidos no rig: Y = eixo do osso (torção), Z = frente/trás (a junta),
  X = abrir para o lado. F3 feito (03/10): docker "HQ Tools: 3D" com clique
  na região, sliders semânticos (Dobrar/Abrir/Girar), dedos em um slider e
  inserção raster/referência. Biblioteca de poses e corpo (03/10):
  `scripts/exportar-poses3d.py` extrai as rotações de FBX animado (desvio
  máximo de 7 mm contra o Blender), `idle_maos_fechadas` é o padrão dos dois
  corpos e `mulher.json` entrou com seletor Corpo. Preview flutuante (03/10):
  a inserção usa a seleção ativa (pixels da imagem), o preview adota a
  proporção dela (WYSIWYG) e "Flutuar na página" aparece sobre a seleção
  (arrasto, alça/roda, opacidade, "Fixar"); inserir entra abaixo do esboço e
  desfaz a seleção.
- **Dividir a biblioteca em corpo e mãos (anotado em 03/10):** hoje cada pose
  mistura corpo e dedos (Idle com mãos fechadas/abertas). O plano é separar em
  `poses/corpo/` (sem ossos de dedo) e `poses/maos/` (só dedos), com o
  extrator ganhando `--parte corpo|maos` e o docker com dois combos que se
  combinam (pose do corpo + pose das mãos). Padrão: corpo idle + mãos fechadas.
  Migrar as duas poses atuais para o novo formato.

### Rota B: Blender Layer (plugin existente)

- Yuntokon/BlenderLayer: 388 estrelas, GPL-3.0, feito para artistas 2D
  usarem modelo 3D como referência; suporta a Pose Library do Blender (poses
  aplicadas direto do docker).
- Ressalvas: último commit em out/2024 (sem atualizações ~2 anos), 12 issues
  abertas; validar no Krita 5.3.4 antes de confiar.

### Rota C: pose makers na web (Poserr, SetPose)

- Poserr (krita-artists.org, jun/2026): ferramenta de pose 3D gratuita no
  navegador (35 likes); SetPose similar. Fluxo: posar no navegador, exportar
  PNG, importar como camada de referência.
- Licenças a confirmar antes de depender; fluxo manual (navegador).

### Decisão atual (autor)

Trabalhar no Blender, renderizar a referência por painel e importar no quadro
(plano original, convenção `pXX_qYY_*.png` como camada de referência travada).
O botão "Camada de referência" do HQ Tools (marca com rótulo de cor, trava e
baixa opacidade) foi aprovado para entrar nesse fluxo.

## Revisão da lista de sugestões (03/10/2026)

Revisão dos recursos possíveis a partir do que já existe no plugin, do mais
fácil ao mais difícil. As estimativas são de engenharia; arte e conteúdo
entram à parte. O item nº 1 das pendências continua sendo o Krita 6
(validação e ferramentas novas de texto/painéis), pré-requisito do balão
paramétrico.

### Entraram no plugin (03/10)

- **Gestão da biblioteca**: "Renomear...", "Duplicar" e "Apagar" operam o
  recurso selecionado direto no docker (antes só havia criar, salvar e
  inserir).
- **"Instalar bundle..." na aba "Packs"** do docker de pincéis, junto dos
  demais instaladores (ver pendência resolvida abaixo).

### Anotadas, ainda fora

- **Lettering nas páginas geradas**: o gerador desenha as falas como `<text>`
  sans-serif simples; usar os balões e as fontes do kit deixaria o storyboard
  mais perto da arte final. Parente do item "Atualizar textos das páginas
  geradas" (SESSION.md).
- **Preset de "estilo de painel"**: um clique aplica sombra + contorno +
  retícula coerentes na página, reaproveitando os presets do módulo de
  retículas. Diferente da "hachura por presets de pincel", que é desenho à
  mão.
- **Exportar o conjunto próprio como bundle**: viabilidade incerta; avaliar o
  formato `.bundle` do Krita antes de estimar.
- **Clique direto no canvas**: a PoC de ~20 linhas (event filter no
  `canvasWidget` + transformações do `Canvas`) desbloquearia o balde por
  clique e o reposicionamento da cauda por arrasto. Continua como v1.1 do
  fillbucket.

### Correções de rota (o que não é lacuna)

- Exportação e lote de páginas ficam no CPMT (decisão vigente no SESSION);
  exportar pelo manager do plugin é mudança de escopo, não lacuna.
- Exportação rápida de página dentro do plugin exigiria código novo
  (`exportImage`), não reuso do `saveAs`, que grava `.kra`.
- PDF multi-página não tem caminho nativo no Krita; exigiria PDF em Python
  puro (zlib) ou ferramenta externa.
- Apagador vetorial por interseção: fora de escopo confirmado (a API de
  vetores não expõe trim por interseção).

## Novas ideias (05/10/2026)

Três ideias do autor, anotadas para avaliação. Nenhuma entra antes da
biblioteca de poses (prioridade atual); o hub é o candidato natural a entrar
primeiro pela facilidade.

### 1. Painel de hub

Um docker "HQ Tools: hub" com um botão por módulo (os 8 de hoje, mais os que
vierem, como a biblioteca de perspectiva), no espírito de central de controle:

- Cada botão **abre o docker do módulo**; clicar de novo **fecha**, e o botão
  fica marcado (estado "aberto") enquanto a doca estiver visível.
- Opção (checkbox) "fechar o atual ao abrir outro": marcada, abrir um módulo
  fecha os demais (um por vez); desmarcada, vai abrindo e convivendo com os
  outros.

Notas de engenharia: no PyKrita o `DockWidget` é um `QDockWidget` (mostrar com
`show()`, fechar com `close()`, e o sinal `visibilityChanged` sincroniza o
estado marcado do botão). Os módulos já têm precedente de registro de
instância (`brushes.register_docker`); o hub pode manter um registro parecido
em vez de casar por título de janela, que é frágil (como no botão "Bibliotecas
de símbolos"). Docker que o Krita ainda não instanciou precisa de aviso em vez
de botão morto. Sem risco para o desenho: só mostra e esconde dockas.

**Feito (05/10/2026):** docker `modules/hub/` com o registro em
`core/registro.py` (cada docker se registra no `__init__` e o hub escuta as
chegadas), estado marcado pelo `visibilityChanged` e a opção de fechar o atual
(`hub.fechar_ao_abrir`). Sem release ainda.

### 2. Biblioteca de linhas de perspectiva

Docker novo no molde do visualizador 3D: catálogo de conjuntos de linhas de
perspectiva, seleção retangular sobre o painel, preview WYSIWYG e inserção no
tamanho da seleção (abaixo do esboço, como referência), com flutuante sobre a
seleção para **arrastar e dar zoom** antes de assentar.

Conjuntos pedidos pelo autor:

- frontal (1 ponto);
- 3 pontos;
- dois níveis de "eyebird" (vista de pássaro);
- 2 níveis de worm view (vista de baixo);
- 2 níveis de curvilíneas.

Cores por família de linhas (azul, cinza e laranja) para separar direções e
horizonte. A ideia é cobrir as perspectivas mais comuns de graphic novel.

Notas de engenharia: o núcleo é geometria pura, no espírito de
`screentone/effects.py` (as linhas radiais de um foco já existem em
`effect_lines_focus`); cada conjunto vira uma lista de segmentos com cor e o
SVG vai para uma camada. Reusa o fluxo do 3D já validado: `mapeamento`
(widget↔imagem), `selection_bounds`, `attach_below_active`, `deselect` e o
padrão do flutuante (`_Flutuante`); e, aprendendo com a auditoria de 05/10, a
inserção entra em macro de desfazer (`run_in_macro`).

**Feito (05/10/2026):** os 9 conjuntos de linhas foram gerados em
`hq_tools/resources/perspectivas/` (cada linha com exatamente 2 nós), com
pesquisa e catálogo em `docs/PERSPECTIVAS.md`, gerador em
`scripts/gerar-perspectivas.py` e testes em `tests/test_perspectivas.py`.
O docker `modules/perspectiva/` entrou com o fluxo de seleção completo
(inserção raster abaixo do esboço, em macro de desfazer) e o flutuante com
arrasto e roda. Sem release ainda.

**Perguntas abertas:** arrastar/zoom ajusta o quê no grid (mover os pontos de
fuga, girar o horizonte, mudar a densidade de linhas)? As cores por família
são fixas ou escolhíveis? Inserir como vetor (editável) ou raster (mais
simples, como o 3D)?

### Relação com o que já está anotado

- "Presets de assistentes por painel" (acima) é o parente próximo: lá são os
  assistentes nativos do Krita configurados por painel; aqui são linhas
  desenhadas como arte de referência. As duas podem conviver; decidir qual
  resolve melhor o fluxo do autor.
- O hub conversa com a decisão de 26/09 (dockers separados, agrupamento em
  abas pelo próprio Krita): ele não funde os módulos, só dá um atalho de
  abertura e fechamento.

## Pendência resolvida (03/10/2026)

- Botão "Instalar bundle..." pouco visível na fileira inferior do docker de
  pincéis (junto de "Atualizar presets"/"Preencher slots"). **Feito**: o botão
  mudou para a aba "Packs", junto de "Instalar pack selecionado"; a fileira
  inferior ficou com as ações de presets e slots.