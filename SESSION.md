# SESSION — HQ Tools (Krita-Comics-Plugin)

Fonte da verdade do projeto. Atualizado em 2026-09-25.

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

## Estado (v0.1.0)

Feito:

- Pesquisa técnica documentada (`docs/DESCOBERTA.md`): chaves exatas do
  gerador Screentone, do filtro Halftone, da API libkis e do comicsConfig.json,
  com fontes (código-fonte KDE/krita master, AppImage local).
- Plugin completo: scaffold, núcleo compartilhado, 5 módulos, `.desktop`,
  `.action` (12 atalhos de pincel), manual HTML.
- Testes do núcleo: 23 passando (`python3 -m unittest discover -s tests`).
- Scripts: `install-dev.sh`, `build-zip.sh`, `descoberta_scripter.py`.
- Git iniciado com commits por fase.

Pendente (validação dentro do Krita):

- Rodar o roteiro de `docs/VALIDACAO.md` (inclui os blocos do Scripter).
- Confirmar: texto de SVG vira texto editável na 5.3.4 (bloco 5); comportamento
  de `Palette(None)` + `save()`; dump das configs reais vs. geradas pelo plugin.

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