# Pack: Krita Watercolor Set (Vasco Basqué)

- Autor: Vasco Basqué (vascoalexander)
- Origem: https://github.com/vascoalexander/krita-watercolor-set
- Licenca: CC-0 (dominio publico; icones de David Revoy/MyPaint tambem CC-0)
- Arquivos inclusos: paintoppresets (12, da versao Krita 2.8), brushes (11),
  originais do autor
- Alteracoes: 1 preset removido (ver "Presets removidos" abaixo); todos os
  outros arquivos sao originais, sem modificacao
- Instalacao: copiados para as pastas de recursos do usuario pelo plugin

## Presets removidos

| Preset | Textura citada | Motivo |
|---|---|---|
| `X9AI_WC_Scattered_Sharp` | `T_Texture_7.gih` | nao existe no repo do autor |

O preset instala e aparece na lista, mas o pincel nao carrega: o Krita cai no
pincel padrao. Medido em 2026-09-30 em todo o historico do repositorio (42
arquivos, incluindo as duas versoes de preset, Krita 2.7 e 2.8): nenhuma
versao contem essa textura, entao nao ha como recupera-la. A serie "Scattered"
veio com 4 presets e saiu com 3 (Small, Soft, Medium); faltou a textura do
Sharp, que era o unico que nao apontava para um `Aqua_*.gbr`. Como o preset e
so um ponteiro para a textura, nao ha o que adaptar sem trocar o pincel que o
autor escolheu.
