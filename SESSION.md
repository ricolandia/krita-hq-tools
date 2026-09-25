# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-25 (v0.3.0).

## Contexto

Ricardo quer produzir páginas de quadrinhos no Krita (Debian, AppImage) e
avaliou junto a IAs o que existe de plugins e o que valeria construir. A
conclusão da pesquisa está em `docs/contexto/` (os 4 arquivos originais).

## Decisões (25/09/2026)

- **Alvo:** Krita 5.3.4 (AppImage atual, Qt5/PyQt5/Python 3.13). Krita 6.0.4
  (Qt6/PyQt6) fica para depois; `core/compat.py` centraliza a compatibilidade.
- **Escopo:** plugin único `hq_tools` com 5 módulos habilitáveis: retículas e
  hachuras, balões, paletas, páginas, pincéis.
- **Ordem das fases:** retículas → balões + paletas → páginas → pincéis.
- **Roteiro:** sintaxe própria (ver `docs/ROTEIRO-SINTAXE.md`).
- **Integração:** só CPMT (comicsConfig.json); sem renders do Blender por ora.
- **Manager de páginas:** ver, abrir e reordenar (exportação/lote ficam no CPMT).
- **Pincéis:** módulo próprio com slots e atalhos (não Ten Brushes/Shortcut
  Composer).
- **Paletas:** docker próprio com templates `.gpl`.
- Licença MIT; docs em `.md` na pasta do projeto (regra de documentação).

## Estado (v0.3.0)

Feito:

- v0.1.0 e v0.2.0 completas (ver CHANGELOG).
- **Gerenciador de páginas repensado (v0.3.0)**: aba única; "Novo projeto..."
  cria a pasta do projeto (diálogo nome + pasta base + subpasta); "Criar
  próxima página" gera página (A4 300 dpi padrão, fundo, grupo PageNN, painel
  com margem, Sketch/Color/Ink, contorno) e atualiza as miniaturas; "Guias de
  margem" cria 12 guias (0,5/1/1,5 cm por lado) no documento ativo; aba
  Roteiro removida da interface (módulos puros preservados).
- **CPMT corrigido**: arquivo real é `comicConfig.json` (sem "s") em UTF-16;
  leitura com BOM e fallback para `comicsConfig.json` legado.
- **Kit de HQ**: fontes OFL (Bangers, Comic Relief Regular/Bold, Patrick
  Hand) instaláveis com um clique; 2 balões CC0/PD (Amada44 e SupremeLordBagel)
  copiados na primeira execução; `CREDITS.md` com todas as licenças.
- **Docker "HQ Tools: biblioteca"**: cria balões, painéis e onomatopeias do
  autor em documento 15 x 15 cm a 300 dpi; "Salvar recurso do documento"
  exporta a camada vetorial como SVG na pasta da biblioteca (subpastas por
  tipo); inserção com duplo clique.
- **Docker "HQ Tools: onomatopeias"**: 8 amostras + pasta própria.
- **Balões**: aba de símbolos removida; botão "Símbolos do Krita" abre o
  docker nativo.
- Testes do núcleo: 51 passando.

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (itens 3c/3d/3e, 5 com nova página e
  guias).
- Confirmar: `Document.setVerticalGuides`/`setHorizontalGuides` substituindo
  guias; exportação `VectorLayer.toSvg()` gerando SVG reimportável; fontes
  instaladas aparecendo no seletor de fontes do Krita após reinício.

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
bash scripts/install-dev.sh                # instalar em dev
bash scripts/build-zip.sh                  # gerar ZIP instalável
```

## Pendências futuras (fora de escopo por ora)

- Krita 6 (migração PyQt6 e ferramentas novas de texto/painéis).
- Renders do Blender como camada de referência (convenção `pXX_qYY`).
- Exportação e renomeação em lote no manager (segue no CPMT).
- Hachura desenhada à mão via presets de pincel específicos.
- Atualizar textos das páginas geradas e camada de referência.
- Página criada por "Criar próxima página" com guias de margem já aplicadas
  (hoje as guias são um botão separado).