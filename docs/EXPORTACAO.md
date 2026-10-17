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

### Validação interativa (17/10, Krita real do autor)

`scripts/validar-exportacao.py` rodou no Scripter; resultados:

| Variante | Resultado |
|---|---|
| PNG nativo (300 dpi) | ✅ 5,5 s/página, 2480×3508 dpi=(300,300) |
| PNG 96 dpi (cópia + `scaleImage`) | ✅ 2,0 s, 794×1123 dpi=(96,96) |
| JPG q90 | ✅ 2,2 s, 2480×3508 dpi=(300,300) |
| **CMYK (TIFF)** | ❌ **sem perfis CMYK instalados** (`profiles("CMYK","U8")` vazio) |
| **PDF (1 página)** | ❌ o filtro não criou o arquivo (caminho não confiável) |
| `mergedimage` (atalho) | ✅ **69 ms**, 2480×3508 dpi=(300,300) |

- **`exportImage` funciona no Krita real** (o crash era só do harness headless).
- O atalho do `mergedimage` é **pixel a pixel idêntico** ao PNG exportado na
  mesma resolução (diff = 0 no `ImageChops.getbbox()`) e **80× mais rápido**
  (69 ms vs 5,5 s).

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
- **Fora da v1**: CMYK e PDF (evidência acima), PSD em camadas (v1.1) e
  imposição/sangria (Scribus).

## Campos do diálogo

| Campo | Opções | Padrão | Notas |
|---|---|---|---|
| Preset | Web / Impressão / Personalizado | Web | só preenche os campos |
| Cor | RGB (fixo na v1) | RGB | CMYK fica para quando houver perfil instalado |
| Resolução | 72 / 96 / 150 / 300 dpi | dpi da página (`pages.dpi`, 300) | igual à da página ⇒ atalho do `mergedimage` |
| Formato | PNG / JPG | PNG | CMYK/PDF fora da v1 (evidência) |
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

## Decisões fechadas pela evidência (17/10)

1. **CMYK fora da v1** — não há perfis CMYK no Krita do autor (o
   `profiles("CMYK","U8")` volta vazio); revisitar se um perfil for instalado.
2. **PDF fora da v1** — o filtro não cria o arquivo nem em uma página; o
   caminho não é confiável. O escritor puro em Python segue adiado.
3. **v1 = RGB**, PNG/JPG, 72/96/150/300 dpi, pasta `<projeto>/exportacao/`.
4. **Presets**: Web = RGB 96 dpi JPG q90; Impressão = **RGB 300 dpi PNG**
   (lossless; o CMYK sai quando houver perfil). TIFF RGB pode entrar depois.
5. Qualidade JPG padrão: **90**.
