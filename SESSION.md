# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-25 (v0.2).

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

## Estado (v0.2.0)

Feito:

- v0.1.0 completa: plugin com 5 módulos, núcleo, testes (23), scripts,
  documentação e git com tag v0.1.0.
- **Pincéis v2**: conjuntos (Rascunho, Contornos, Aquarela/Guache,
  Acrílico/Óleo, Retículas) montados com os presets do próprio Krita, cartões
  com miniatura + nome, 16 slots (4 por conjunto), atribuição por menu de
  contexto, instalador de bundles (.bundle).
- **Retículas v2**: editar retícula selecionada (camada de preenchimento e
  máscara de meio-tom), máscara vazia (revelar pintando), mostrar área como
  seleção, reutilizar tons idênticos, posição X/Y do padrão, tom com padrões
  instalados do Krita (gerador Pattern no preenchimento e como tela do
  Halftone), meio-tom por canal CMYK (ângulos 15/75/0/45).
- **Linhas de efeito/velocidade**: gerador vetorial (foco e paralelas) no
  docker de retículas.
- **Paletas artísticas**: 15 novas `.gpl` (Zorn, retrato, paisagem, amanhecer,
  noite, terra, pastel, aquarela, guache, acrílico, retrô HQ, BD linha clara,
  super-herói, mangá, sépia).
- **Símbolos do Krita**: aba nos balões listando as bibliotecas de
  `~/.local/share/krita/symbols` (BalloonSymbols e Pepper&Carrot inclusas),
  miniaturas via QSvgRenderer e inserção vetorial em um clique com licença
  creditada.
- Testes do núcleo: 44 passando (`python3 -m unittest discover -s tests`).

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (inclui os itens 2b, 3b e o pincel v2).
- Confirmar: inserção de símbolos via `addShapesFromSvg` (estilos/defs),
  edição de máscara de meio-tom e CMYK em documento CMYKA, padrões como tela,
  `Resource.image()` devolvendo a miniatura dos `.kpp`.

## Comandos

```bash
python3 -m unittest discover -s tests -v   # testes
bash scripts/install-dev.sh                # instalar em dev
bash scripts/build-zip.sh                  # gerar ZIP instalável
```

## Pendências futuras (fora de escopo por ora)

- Krita 6 (migração PyQt6 e ferramentas novas de texto/painéis).
- Renders do Blender como camada de referência (convenção `pXX_qYY`).
- Balão com forma gerado pelo roteiro (hoje só o texto é posicionado).
- Exportação e renomeação em lote no manager (segue no CPMT).
- Hachura desenhada à mão via presets de pincel específicos.
- Atualizar textos das páginas geradas a partir do roteiro (regravar a camada
  `text`) e camada de referência (v0.3).