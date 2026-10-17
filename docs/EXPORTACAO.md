# Exportação de páginas: desenho (v1)

Avaliação madura da exportação pela doca, a pedido do autor em 17/10/2026
(a spec inicial está no `IDEIAS-FUTURAS.md` § "Exportação de páginas",
adiada em 05/10). Baseada no PoC de 17/10 no harness headless
(`scripts/poc-exportacao.py`) e no validador interativo
(`scripts/validar-exportacao.py`).

## Objetivo

O artista finaliza no Scribus/InDesign: a doca entrega os **assets por
página** (imagens ou um PDF por página); imposição, sangria e marcas de
corte continuam lá.

## Evidência (PoC 17/10, Krita 5.3.4)

| Caminho | Harness | Medição |
|---|---|---|
| `mergedimage.png` do `.kra` | ✅ | **57–62 ms**, 2480×3508 **dpi=(300,300)**, sem abrir o documento |
| `scaleImage` numa cópia reaberta | ✅ | ~1 s (A4 300 → 72 dpi) |
| criar + salvar A4 300 dpi | ✅ | ~2,5–2,8 s / 639 KB |
| `setColorSpace` CMYK | ⚠️ | o ambiente do harness não lista perfis CMYK |
| `Document.exportImage` | ❌ no harness | **derruba o Krita** headless (PNG/JPG/TIFF, com/sem view, com atraso e preparações) — validar no Krita real |

Achado de passagem corrigido: `present_document` usava `Krita.addView`, que
não existe no Krita 5.3.4 (falhava em silêncio); agora usa `Window.addView`.

## Decisões propostas (v1)

- **Entrada**: botão **"Exportar páginas..."** na fileira do gerenciador de
  páginas (junto de "Pasta..." / "Abrir pasta do Krita").
- **Presets**: **Web** (RGB, 96 dpi, JPG q85), **Impressão** (CMYK, 300 dpi,
  TIFF) e **Personalizado**; o preset só preenche os campos, tudo editável.
- **Atalho do `mergedimage`**: quando a cor é RGB, o formato é PNG/JPG e a
  resolução pedida **é a da página** (o caso comum das páginas a 300 dpi),
  extrai o `mergedimage.png` do `.kra` — 57 ms por página, sem abrir o
  documento. Fora disso: abre a cópia, `scaleImage` e `exportImage`.
- **Progresso**: `QProgressDialog` com a página atual; erros **pulam e são
  listados** no fim (página sem `mergedimage`, export que falhou).
- **Saída**: pasta `<projeto>/exportacao/`; o nome do arquivo é o da página
  com a extensão trocada; opção "abrir a pasta ao terminar".
- **Fora da v1**: PDF multi-página (não há caminho nativo; o escritor puro em
  Python segue adiado), PSD em camadas (v1.1) e imposição/sangria (Scribus).

## Campos do diálogo

| Campo | Opções | Padrão | Notas |
|---|---|---|---|
| Preset | Web / Impressão / Personalizado | Web | só preenche os campos |
| Cor | RGB / CMYK | RGB | CMYK pede perfil (combo dos perfis do Krita) e só vale para TIFF/PDF; PNG/JPG são RGB |
| Resolução | 72 / 96 / 150 / 300 dpi | dpi da página (`pages.dpi`, 300) | igual à da página ⇒ atalho do `mergedimage` |
| Formato | PNG / JPG / TIFF / PDF (1 por página) | PNG | PDF único fica fora (sem multi-página nativo) |
| Qualidade | 1–100 (JPG) | 90 | só para JPG |
| Destino | pasta | `<projeto>/exportacao/` | criar se não existir |
| Abrir a pasta ao terminar | sim/não | sim | |

## Peças de código

- **`modules/pages/exportacao.py`** (novo, puro): plano de exportação (páginas
  do projeto → trabalho por página, a regra do atalho, nome do arquivo,
  validação do destino) — testável fora do Krita.
- **`core/thumbs.py`**: `merged_bytes(kra)` reusando a chave/cache existentes
  (hoje o `preview_bytes` pega o preview pequeno, não o `mergedimage`).
- **`modules/pages/manager_docker.py`**: botão, diálogo, `QProgressDialog` e a
  chamada da exportação.
- **i18n PT/EN**: ~15 strings novas.

## Validação

1. **Harness**: diálogo monta, atalho do `mergedimage` e a escala
   (`scripts/poc-exportacao.py`); o `exportImage` **não** roda headless.
2. **Autor (interativo)**: `scripts/validar-exportacao.py` no Scripter prova
   `exportImage` (PNG/JPG/PDF) e CMYK no Krita real — é o que destrava a
   decisão do CMYK.
3. **QA de visão**: uma página exportada conferida por visão (cortes/cor).

## Decisões que faltam (autor)

1. **CMYK na v1?** — depende do validador interativo passar (perfis + TIFF).
2. Qualidade padrão do JPG (90 ok?).
3. Nome da pasta de destino (`exportacao/` ok?).
4. Presets Web (RGB 96 dpi JPG) e Impressão (CMYK 300 dpi TIFF) — confere?
