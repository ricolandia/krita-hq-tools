# Balões vetorizados (lote de 29/09/2026)

15 balões `SVG` para o kit handdrawn, gerados a partir das pranchas em
`Referencias/baloes/` com o `scripts/vetorizar-baloes.py` (lote em
`scripts/vetorizar-lote.py`). Cada arquivo tem dois grupos: `balao` (corpo
fechado) e `cauda` (forma separada, com o traço aberto na base, para unir no
Krita depois). Sem texto. Prévia geral: `previa.png`.

## Lista

| Arquivo | Origem | Recorte (x,y,l,a) | Traço | Pescoço |
|---|---|---|---|---|
| balao-02a.svg | Refer_ball_02.png | 225,7,185,216 | 6 px | manual 113,154 / 89,153 |
| balao-02b.svg | Refer_ball_02.png | 652,21,193,193 | 6 px | automático |
| balao-02c.svg | Refer_ball_02.png | 240,291,176,133 | 6 px | automático |
| balao-02d.svg | Refer_ball_02.png | 439,39,185,157 | 6 px | automático |
| balao-03a.svg | Refer_ball_03.png | 344,181,176,120 | 5 px | automático |
| balao-03b.svg | Refer_ball_03.png | 691,341,129,113 | 5 px | automático |
| balao-04a.svg | Refer_ball_04.png | 503,99,119,99 | 4 px | automático |
| balao-04b.svg | Refer_ball_04.png | 123,185,95,87 | 4 px | automático |
| balao-05a.svg | desenho do autor (Inkscape) |  | 3 mm | manual |
| balao-05b.svg | Refer_ball_05.png | 752,345,223,129 | 5 px | automático |
| balao-05c.svg | Refer_ball_05.png | 38,190,133,189 | 5 px | automático |
| balao-05d.svg | Refer_ball_05.png | 191,210,163,121 | 5 px | automático |
| balao-06a.svg | Refer_ball_06.png | 415,281,110,178 | 5 px | automático |
| balao-06b.svg | Refer_ball_06.png | 557,246,154,90 | 5 px | automático |
| balao-06c.svg | Refer_ball_06.png | 714,457,144,94 | 5 px | automático |

O `lote.json` guarda os mesmos parâmetros em JSON.

## Status (QA de visão, 29/09)

- **Corpos**: consistentes, contorno handdrawn fechado, sem texto.
- **Caudas**: variam de tamanho; as que saíram muito pequenas ou encostadas
  na borda ficam para revisão do autor. Numa primeira passada o QA aprovou 13
  de 15; numa segunda foi mais crítico com as caudas curtas (02c, 03a, 03b,
  04b, 05b, 05d, 06b) e com 06a.
- **Descartado**: `03c` (o interior da forma sai partido; precisa de corte
  manual fino ou redesenho).

## Como ajustar

- Uma cauda específica: rodar o vetorizador só nela com `--corte X1,Y1,X2,Y2`
  (coordenadas do pescoço no recorte), `--alargar-base` e `--base-interna`.
- Redesenho manual: como o `05a`, feito no Inkscape e depois normalizado
  (canvas, traço unificado, cauda sem fechar o traço).
- Regenerar tudo: `python3 scripts/vetorizar-lote.py`.
