# Assets do HQ Tools

Marca do plugin (ícone) gerada no fluxo do `docs/DESIGN.md`: design system
primeiro, desenho no Penpot, QA com o modelo de visão e export local.

## Arquivos

| Arquivo | Uso |
|---|---|
| `icon-light.svg` / `icon-dark.svg` | Mestre 512 px (retícula fina 6x4), versões clara e escura |
| `icon-light-small.svg` / `icon-dark-small.svg` | Grade pequena dedicada (6 pontos grossos) para 128 px ou menos |
| `icon-light-512.png`, `icon-light-256.png` | PNGs do mestre claro |
| `icon-light-128/64/32/16.png` | PNGs da grade pequena clara |
| `icon-dark-512.png`, `icon-dark-128.png`, `icon-dark-64.png` | PNGs escuros (preview do GitHub e fundos escuros) |

Cores: papel `#F4EFE6`, tinta `#141414`. Sem accent: a gota de tinta saiu do
desenho por decisão do autor; o accent `#D7263D` segue reservado para textos e
selos no site e no banner.

## Origem editável (Penpot)

Boards no projeto conectado ao MCP:

- `HQ Tools · icone claro 512` e `HQ Tools · icone escuro 512` (mestre, 24 pontos)
- `HQ Tools · icone pequeno claro 128` e `HQ Tools · icone pequeno escuro 128`
  (grade dedicada, 6 pontos)

O QA de visão apontou que reduzir a grade fina para 64 px vira textura suja;
por isso existe a grade pequena desenhada à parte, em vez de só reescalar.

## Regenerar os PNGs

Os SVGs são a fonte dos PNGs. Rasterizar com o Chrome headless e ajustar os
tamanhos com o ImageMagick:

```bash
google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --screenshot=icon-light-512.png --window-size=512,512 file://$(pwd)/icon-light.svg
google-chrome --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --screenshot=icon-light-128.png --window-size=128,128 file://$(pwd)/icon-light-small.svg
convert icon-light-128.png -resize 64x64 icon-light-64.png
```
