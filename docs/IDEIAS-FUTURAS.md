# Ideias futuras e propostas avaliadas

Registro das propostas avaliadas (ex.: pasta `Novas_ideias/`) que ainda não
foram integradas. Cada item traz o veredito e as condições para entrar no
plugin.

**Roadmap reavaliado (05/10/2026):** prioridade: o que falta da biblioteca de
poses do visualizador 3D ("Salvar pose atual", miniatura no seletor e o
joinha, que o autor vai refazer). O estado completo, com o que já foi feito e
o que vem, está na seção "Roadmap reavaliado" abaixo; a linha do tempo viva é
a da nota do roadmap no Trilium.

## Roadmap reavaliado (05/10/2026)

### Feito até agora (dentro e fora do roadmap original)

- **v0.1–v0.4 (set/2026):** módulos base (retículas, balões, paletas, páginas
  com CPMT, roteiro e tirinhas).
- **v0.5:** pincéis da comunidade (Deevad, Watercolor) com licença verificada,
  9 famílias de fontes e aba Comunidade.
- **v0.6:** onomatopeias, biblioteca do projeto e a auditoria de 30/09 em
  4 lotes (dados do autor, isolamento/desfazer, desempenho, empacotamento).
- **v0.7:** visualizador 3D completo (Rota A), máscara dos painéis no grupo
  "Arte", compatibilidade Windows e o fluxo por seleção WYSIWYG.
- **v0.8:** hub dos módulos e biblioteca de linhas de perspectiva (9
  conjuntos, inserção como camada vetorial), mais os quick wins da auditoria
  de 05/10.
- **v0.9:** interface PT/EN nos dockers (373 strings) e documentação em
  inglês (manual e INSTALL).
- **v0.9+ (05/10):** biblioteca de poses dividida em corpo e mãos, com o
  espelho da mão e as poses novas (Voa, Anda, Corre, Pose A, Fechada, Abertas
  e Segura).
- **v0.11 (em preparo, 06/10):** moodboard (quadro de referências linkado à
  pasta do projeto), validado por PoC e smoke dentro do Krita 5.3.4.
- **Fora do roadmap original:** camada de UI compartilhada (52 botões), ícone
  e social preview, vídeos demo no YouTube com roteiros de captura, CI no
  Windows, automação de release (tag → ZIP + notas do CHANGELOG), duas
  auditorias (30/09 e 05/10) e a documentação espelhada no Trilium.

### Moodboard (implementado em 06/10/2026, aguardando validação do autor)

Pedido do autor: quadro horizontal de referências, leve, com as imagens
comprimidas em JPG e "linkadas" como no HTML, e a referência podendo ser
inserida num painel dentro de uma seleção. Decisões e achados:

- Referências em `<projeto>/moodboard/*.jpg` (lado máximo 1600 px, qualidade
  85; aviso na primeira vez) e o `moodboard.kra` guarda **camadas de
  arquivo** (só o caminho relativo): o quadro fica com centenas de KB mesmo
  com dezenas de referências.
- **Camada de arquivo não aceita transformação direta** (a ferramenta de
  transformar não afeta; bug T4595 do KDE): posição/escala vão numa **máscara
  de transformação** (`scaleX`/`scaleY` no centro original + deslocamento em
  `transformedCenter`; a `flattenedPerspectiveTransform` sozinha é ignorada
  no modo livre). Validado no PoC `scripts/poc-filelayer-transform.py`.
- Grade de células de 640 px, 8 colunas (tela de 5552 px), que cresce em
  altura (`resizeImage`) conforme as referências; `moodboard.json` guarda o
  layout (para renomear/apagar atualizando a camada).
- "Inserir na seleção" reusa o fluxo WYSIWYG da perspectiva, mas entra
  **abaixo do ativo** e, com o fundo ativo, acima dele (senão some atrás do
  fundo).

### Próximo (reavaliado)

1. **Biblioteca de poses, o que falta:** "Salvar pose atual" (biblioteca do
   usuário), miniatura no seletor e o joinha (o autor vai refazer a pose).
2. **Validação no Krita da v0.9.0:** hub (abrir/fechar), malha de perspectiva
   (Ctrl+Z único), flutuante com dois documentos e a interface em inglês.
3. **Krita 6:** validar o plugin no PyQt6 (pré-requisito do balão
   paramétrico) e conferir dockers e i18n no 6.
4. **Lettering nas páginas geradas:** usar os balões e as fontes do kit no
   lugar do texto sans-serif do storyboard.
5. **Clique direto no canvas:** PoC de ~20 linhas (event filter no
   `canvasWidget` + transformações do Canvas); destrava o balde por clique e
   a cauda arrastável.
6. **Fillbucket em Python puro:** reescrever o núcleo sem numpy, com as
   correções obrigatórias (ordem de canais, camada transparente, imports).
7. **Balão paramétrico:** cauda reposicionável e texto que redimensiona o
   balão (depois do Krita 6).
8. **Avaliar e decidir:** preset de "estilo de painel", exportar o conjunto
   próprio como bundle e os presets de assistente de perspectiva por painel
   (com a biblioteca de perspectiva pronta, o valor caiu; decidir se sai da
   lista).
9. **Exportação de páginas (amadurecer, adiada em 05/10):** diálogo com cor
   (RGB/CMYK + perfil), resolução (72/96/150/300), saída (pasta de imagens ou
   PDF único) e presets web/impressão; especificação abaixo.

**Fora de escopo (mantido):** exportação webtoon (Batch Exporter cobre),
preflight de impressão (Scribus), rotas B/C do 3D (Blender Layer e pose
makers web) e apagador vetorial por interseção.

### Exportação de páginas (amadurecer, adiada em 05/10/2026)

Pedido do autor em 05/10, adiado por precisar de um desenho maior. A ideia é
que o artista finalize no Scribus/InDesign, então a doca entrega os assets por
página e imposição/sangria ficam lá.

- **Diálogo de exportação** ao clicar em "Exportar páginas...", com:
  - **Cor:** RGB × CMYK (com escolha de perfil ICC; PNG é só RGB, então CMYK
    pede TIFF/PSD/PDF com perfil embutido, e o Krita converte o documento com
    os perfis dele);
  - **Resolução:** 72 / 96 / 150 / 300 dpi (exige reamostragem: cópia do
    documento com `scaleImage` ou redimensionamento depois);
  - **Saída:** pasta com imagens por página **ou** um único PDF (e,
    possivelmente, PSD em camadas, que o Krita exporta com camadas);
  - **Presets:** "Web" (RGB, 96 dpi, PNG/JPG) e "Impressão" (CMYK, 300 dpi,
    TIFF/PDF com perfil), mais o modo avançado.
- **Tecnicamente:** esse caminho abre cada `.kra` e usa `exportImage` com um
  `InfoObject` de opções por página (mais lento, com progresso). O extrator do
  `mergedimage.png` (verificado em 05/10: resolução cheia, 2480x3508 a 300 dpi)
  fica como exportação web rápida, se sobreviver.
- **Páginas sem imagem mesclada / erros:** pular e listar no fim.
- **Fora:** imposição, sangria e marcas de corte (Scribus).

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
- **Dividir a biblioteca em corpo e mãos (anotado em 03/10, feito em 05/10):**
  a biblioteca foi separada em `poses/corpo/` (Idle, Voa, Anda, Corre e Pose A)
  e `poses/maos/` (Fechada, Abertas e Segura, autorais para a mão direita), com
  dois combos que se combinam no docker (Corpo + Mãos) e o seletor "Mão:"
  (Direita / Esquerda / Ambas) aplicando o espelho (troca de lado com o giro
  negado). O extrator ganhou `--parte corpo|maos|tudo` e aceita `.blend`. O
  joinha ficou de fora por ora (o autor vai refazer a pose).

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

- Exportação e lote de páginas ficam no CPMT (decisão vigente no SESSION).
  Em 05/10/2026 o autor pediu exportação pela doca; o desenho maduro está na
  seção "Exportação de páginas (amadurecer)", adiado para depois.
- Exportação rápida de página dentro do plugin exigiria código novo
  (`exportImage`), não reuso do `saveAs`, que grava `.kra`.
- PDF multi-página não tem caminho nativo no Krita; o escritor puro em Python
  fica na especificação adiada.
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
(inserção como camada vetorial abaixo do esboço, em macro de desfazer) e o
flutuante com arrasto e roda. Sem release ainda.

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