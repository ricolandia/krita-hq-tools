# Pack: Deevad v8.2 (brushkit)

- Autor: David Revoy (davidrevoy.com)
- Origem: https://github.com/Deevad/deevad-krita-brushpresets (v8.2, 2017)
- Licenca: Creative Commons Attribution 4.0 (CC-BY 4.0), atribuicao a David
  Revoy em caso de redistribuicao, comercializacao ou modificacao
- Arquivos inclusos: paintoppresets (62), brushes (29), patterns (6),
  palettes (2), originais do autor
- Alteracoes: 2 presets removidos (ver "Presets removidos" abaixo); todos os
  outros arquivos sao originais, sem modificacao
- Instalacao: copiados para as pastas de recursos do usuario pelo plugin

## Presets removidos

| Preset | Textura citada | Motivo |
|---|---|---|
| `deevad 2d expressive thin` | `deevad_bristle.png` | nao existe no repo do autor |
| `deevad 6n stamp floor particles` | `flat-tip-dirty.gbr` | nao existe no repo do autor |

O preset instala e aparece na lista, mas o pincel nao carrega: o Krita cai no
pincel padrao. Medido em 2026-09-30 em todo o historico do repositorio (103
arquivos no total, conferidos no master e na tag 8.2): nenhuma versao contem
essas duas texturas, entao nao ha como recupera-las. Como o preset e so um
ponteiro para a textura (nem o pincel nem a textura estao embutidos no .kpp),
nao ha o que adaptar sem trocar o pincel que o autor escolheu.
