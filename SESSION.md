# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-26 (v0.4.0).

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

## Estado (v0.4.0)

Feito:

- v0.1.0 a v0.3.1 completas (ver CHANGELOG).
- **Auditoria (v0.3.2)**: 3 especialistas (Python, API do Krita × krita.pyi,
  arquitetura); 0 críticos no 5.3.4; corrigidos 4 bugs de PyQt6 (Krita 6),
  numeração de página, máscara vazia da retícula, espessura das linhas de
  efeito (DPI), encoding do CPMT, manual dentro do pacote, `.action` no ZIP,
  build-zip sem `zip` externo; docs atualizadas.
- **Pacote fácil (v0.4.0)**: guias de margem automáticas na página nova;
  diálogo de nova página (A4/A5/A3/tirinha/americano/tankobon/quadrado/livre
  em mm, DPI, painéis da tirinha 3 padrão); "Definir modelo de página"
  (página atual ou template de HQ do Krita localizado via `QLibraryInfo`,
  copiado para `~/.local/share/krita/hq_tools/modelos/`); adaptação do modelo
  (A3 redimensiona via `scaleImage`, tirinha vira tira horizontal); "Camada de
  referência" (rótulo, trava, opacidade) e "Importar referência (PNG)"
  (camada de arquivo travada no grupo ativo).
- Testes do núcleo: 58 passando.

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (item 5 atualizado: diálogo de nova
  página, modelo com template do Krita, tirinha, referências).
- Confirmar: `QLibraryInfo.PrefixPath` achando os templates de comics no
  AppImage; `scaleImage` e a troca de painéis da tirinha; `createFileLayer`
  com "KeepAspectRatio"/"Bilinear".

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