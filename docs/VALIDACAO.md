# Validação dentro do Krita

Checklist para validar o HQ Tools no Krita 5.3.4 (AppImage). O núcleo puro já é
coberto por testes (`python3 -m unittest discover -s tests`); aqui o foco é o
comportamento dentro do programa.

## Instalação em desenvolvimento

```bash
bash scripts/install-dev.sh
```

Abra o Krita, ative **HQ Tools** em Configurar Krita > Gerenciador de plugins
Python e reinicie. Os dockers aparecem em Configurações > Dockers com o prefixo
"HQ Tools".

## Roteiro de teste (um item por vez)

### 1. Descoberta via Scripter (opcional, mas recomendado)

Ferramentas > Scripts > Scripter, cole os blocos de
`scripts/descoberta_scripter.py` (um por vez, Ctrl+Enter) e confira:

| Bloco | Esperado |
|---|---|
| 1 | lista filtros com "halftone" e amostras de recursos |
| 2 | dump das propriedades de uma camada Screentone criada na mão |
| 3 | dump das propriedades de uma máscara Halftone configurada na interface |
| 4 | camada de preenchimento criada no documento |
| 5 | formas importadas do SVG (anotar `type()` de cada shape, texto vira texto?) |
| 6 | máscara de meio-tom criada sobre a camada ativa |
| 7 | paleta em memória com 3 cores |

Diferenças entre o dump do bloco 2/3 e o que o plugin gera (ver
`docs/DESCOBERTA.md`) devem ser corrigidas no código.

### 2. Retículas

- Abrir documento 300 dpi; com um painel em grupo, selecionar uma área e
  aplicar "Sombra média 60 LPI".
- Esperado: camada de preenchimento dentro do grupo ativo, limitada pela
  seleção, com 10 px por célula (zoom para conferir).
- Pintar um cinza numa camada e aplicar "Meio-tom para filtro 60 LPI": nasce
  uma máscara na camada, não destrutiva; mudar o preset e reaplicar atualiza.
- Cross-hatch: aplicar "Hachura cruzada A" e "B" em sequência.
- Salvar um preset novo e reiniciar o Krita: o preset persiste.

### 3. Balões

- Primeira execução cria a pasta padrão com as amostras.
- Duplo clique insere o balão no grupo ativo como vetor; mover o nó e o traço
  com a ferramenta de forma.
- Com a opção "text" marcada, a camada se chama `text`; num projeto CPMT, a
  exportação ACBF/EPUB coleta os textos.
- Adicionar um SVG próprio na pasta e clicar Atualizar.

### 4. Paletas

- Aba Templates: clicar numa cor e "Aplicar na frente" muda a cor ativa.
- "Instalar no Krita": os `.gpl` aparecem na pasta de paletas; após reiniciar,
  as mesmas paletas aparecem na aba "Paletas do Krita" (PaletteView).

### 5. Páginas (gerenciador)

- Criar um projeto no CPMT (docker Comic Management > New Project).
- No HQ Tools > Páginas > Projeto..., abrir o `comicsConfig.json` do projeto:
  grade com miniaturas aparece.
- Duplo clique abre a página; arrastar reordena e grava no `comicsConfig.json`
  (abrir o arquivo e conferir a ordem da lista `pages`).

### 6. Páginas (roteiro)

- Aba Roteiro: usar o exemplo, escolher formato/DPI e "Gerar páginas" dentro
  do projeto aberto.
- Esperado: N arquivos `.kra` na pasta de páginas, registrados no
  `comicsConfig.json`, cada um com grupo PageNN, `panels` (retângulos),
  Sketch/Color/Ink, contorno multiplicado e `text` com falas.
- Exportar via CPMT (ACBF ou EPUB) e conferir frames/texto por painel.
- Testar `direcao rtl` e `layout 2x3`.

### 7. Pincéis

- Docker mostra 12 slots com os presets instalados no Krita.
- "Sugerir padrões" preenche os slots com presets existentes.
- Atalhos: Configurar Krita > Atalhos > Scripts > HQ Tools, atribuir teclas
  (ex.: F5 a F8 para os 4 primeiros) e testar a troca de pincel.

## Problemas conhecidos e tratamento

- Texto de SVG pode chegar como shape não editável por texto na 5.3.4 (bloco
  5): usar a ferramenta de texto do Krita sobre o shape, ou digitar por cima
  na camada `text`.
- `Palette(None)` + `save()` não validado: por isso os templates são `.gpl`.
- Mudar `modules.*` na config exige reiniciar o Krita.
- Se um docker não aparecer, conferir o log do Krita (Ferramentas > Scripts >
  Scripter imprime erros de importação na inicialização).