# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-25 (v0.3.1).

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

## Estado (v0.3.1)

Feito:

- v0.1.0, v0.2.0 e v0.3.0 completas (ver CHANGELOG).
- **Novo projeto (v0.3.1)**: usa a pasta da página atual salva; sem página ou
  sem save, aviso modal "Salve a página atual em uma pasta. Essa pasta será a
  pasta do projeto."; cria `comicConfig.json` (CPMT, UTF-16), subpastas de
  biblioteca (`biblioteca/{baloes,paineis,onomatopeias}`), `export`,
  `templates`, `translations`, e aponta o docker de biblioteca para a pasta.
- **Biblioteca v2**: recursos vetoriais (SVG via `toSvg`) ou de pintura (PNG
  transparente recortado pela camada ativa via `pixelData` + `QImage`);
  inserção de PNG como camada de pintura (`setPixelData`, fallback camada de
  arquivo); lista com `.svg` e `.png`.
- **Avisos mistos**: modais para fluxos/decisões (`helpers.show_info` com
  `QMessageBox`), toast para sucessos rápidos.
- **Polimento de UI**: `QGroupBox` (Projeto, Página, Recursos, Recurso novo),
  ícones de tema via `compat.standard_icon`, tooltips e alinhamento uniforme.
- Testes do núcleo: 55 passando.

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (itens 3e com pintura/PNG, 5 com o
  fluxo novo de projeto, 5b).
- Confirmar: `pixelData` + `QImage(RGBA8888)` para exportar pintura com
  transparência; `setPixelData` inserindo PNG; `QMessageBox` com o
  `Window.qwindow()` como pai.

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