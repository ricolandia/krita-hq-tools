# Ideias futuras e propostas avaliadas

Registro das propostas avaliadas (ex.: pasta `Novas_ideias/`) que ainda não
foram integradas. Cada item traz o veredito e as condições para entrar no
plugin.

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
- Próximo marco quando for retomado: PoC com manequim procedimental mínimo
  (2 ossos, poucos vértices) antes do modelo final do autor.

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

## Pendência de verificação do autor (26/09)

- Botão "Instalar bundle..." pouco visível no docker de pincéis (fileira
  inferior, junto de "Atualizar presets"/"Preencher slots"). O autor vai
  verificar; sugestão registrada: mover para a aba "Packs" com ícone próprio.