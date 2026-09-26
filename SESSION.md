# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-26 (v0.6.0).

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

## Estado (v0.5.0)

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

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (itens 3c e 7b): instalar os packs e
  as fontes, reiniciar e conferir a aba "Comunidade" e o seletor de fontes.

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
bash scripts/install-dev.sh                # instalar em dev
bash scripts/build-zip.sh                  # gerar ZIP instalável
```

## Pendências do autor (Ricardo)

- Criar os modelos vetoriais melhorados: **balões**, **onomatopeias** e
  **painéis** (estilos próprios), para substituir as amostras atuais.
- Criar modelos de **página**: **tirinha (strip**, 1-3 tiras) e **página A3**,
  para o "Criar próxima página" e os formatos do plugin.
- Verificar a visibilidade do botão "Instalar bundle..." no docker de pincéis
  (sugestão: mover para a aba "Packs").

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