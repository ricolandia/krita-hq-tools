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