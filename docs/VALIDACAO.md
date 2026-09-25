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

### 2b. Retículas v0.2

- **Editar selecionada**: aplicar uma retícula, selecionar a camada e clicar
  "Editar selecionada": os campos carregam os valores; mudar LPI/ângulo e
  "Aplicar" atualiza a mesma camada. Repetir com uma máscara de meio-tom
  (intensity e cmyk).
- **Máscara vazia**: aplicar com "Máscara vazia (revelar pintando)": a camada
  nasce sem retícula visível; pintar branco na máscara (camada de seleção)
  revela o tom.
- **Mostrar área**: com a camada de retícula selecionada, o botão vira a
  máscara em seleção (formigas dançando na área do tom).
- **Reutilizar**: aplicar duas vezes o mesmo preset na mesma página: a segunda
  não cria camada nova, só máscara de seleção na existente.
- **Posição X/Y**: aplicar, selecionar, "Editar selecionada", mudar posição e
  reaplicar: o padrão desloca sem mover a camada.
- **Tom por padrão**: marcar "Usar padrão do Krita" e escolher um padrão
  (ex.: Stripes02.pat): camada de preenchimento com o padrão. E no meio-tom
  com o mesmo padrão: a tela usa o padrão (ex.: listras virando meio-tom).
- **CMYK**: em documento CMYKA, aplicar "Cores por canal": a máscara gera
  meios-tons por canal; conferir os 4 ângulos (15/75/0/45) e a ausência de
  moiré em zoom.
- **Linhas de efeito**: "Foco" com centro em 50/50: linhas convergem ao centro;
  "Paralelas" com região e ângulo: linhas preenchem a região; a camada é
  vetorial e editável.

### 3. Balões

- Primeira execução cria a pasta padrão com as amostras.
- Duplo clique insere o balão no grupo ativo como vetor; mover o nó e o traço
  com a ferramenta de forma.
- Com a opção "text" marcada, a camada se chama `text`; num projeto CPMT, a
  exportação ACBF/EPUB coleta os textos.
- Adicionar um SVG próprio na pasta e clicar Atualizar.

### 3b. Símbolos do Krita (botão nos balões)

- No docker de balões, o botão "Símbolos do Krita" abre o docker nativo
  "Bibliotecas de símbolos" (título em pt_BR ou en, casado por substring).
- Com o docker nativo aberto, arrastar um balão para o canvas funciona como o
  Krita espera.

### 3c. Kit de HQ (balões CC0 e fontes)

- Primeira execução: a pasta padrão de balões recebe as amostras do plugin e
  os 2 balões CC0/PD (`balao-fala-amada44.svg`, `balao-talk-to-me-cc0.svg`).
- "Instalar fontes de HQ": as 3 fontes (Bangers, Comic Relief, Patrick Hand)
  vão para `~/.local/share/fonts/hq_tools`; após reiniciar o Krita, aparecem
  na ferramenta de texto. Conferir créditos em `CREDITS.md`.

### 3d. Onomatopeias

- Docker "HQ Tools: onomatopeias": 8 amostras na primeira execução; duplo
  clique insere no grupo ativo como camada vetorial.
- Adicionar um SVG próprio (Inkscape) na pasta e Atualizar.

### 3e. Biblioteca do projeto

- "Criar novo recurso": abre um documento 15 x 15 cm a 300 dpi com camada
  vetorial "recurso".
- Desenhar formas/texto e "Salvar recurso do documento": o SVG entra na
  subpasta do tipo (baloes/paineis/onomatopeias) e a lista atualiza; o
  documento pergunta se fecha.
- Duplo clique no recurso insere no grupo ativo do documento da página.
- Trocar a pasta da biblioteca (pode ser a pasta do projeto) e conferir a
  listagem.

### 4. Paletas

- Aba Templates: clicar numa cor e "Aplicar na frente" muda a cor ativa.
- "Instalar no Krita": os `.gpl` aparecem na pasta de paletas; após reiniciar,
  as mesmas paletas aparecem na aba "Paletas do Krita" (PaletteView).

### 5. Páginas (gerenciador)

- "Novo projeto...": nome + pasta base + subpasta marcada: a pasta é criada e
  vira o projeto (grade vazia).
- "Abrir projeto...": abrir o `comicConfig.json` de um projeto criado pelo
  CPMT (agora o nome/encoding corretos são aceitos).
- "Criar próxima página": gera a página (A4 300 dpi por padrão, configurável
  em `pages.format`/`pages.dpi`), com fundo branco, grupo PageNN, painel com
  margem, Sketch/Color/Ink e contorno; a miniatura aparece na grade. Em
  projeto CPMT, a página é registrada no `comicConfig.json`.
- "Guias de margem": no documento ativo, criam-se 12 guias (0,5 / 1 / 1,5 cm
  por lado); conferir posições: 59/118/177 px a 300 dpi a partir de cada borda.
  Atenção: substitui as guias existentes.
- Duplo clique abre a página; arrastar reordena e grava no `comicConfig.json`
  (abrir o arquivo e conferir a ordem da lista `pages`).

### 6. Páginas (roteiro) — removido

A aba Roteiro saiu da interface na v0.3.0; os módulos puros
(`modules/pages/roteiro.py` e `generator.py`) continuam no repositório como
referência e para a criação de páginas por script, mas não são mais
registrados no plugin.

### 7. Pincéis

- Docker mostra os conjuntos (Rascunho, Contornos, Aquarela/Guache,
  Acrílico/Óleo, Retículas) com cartões de miniatura + nome, montados com os
  presets instalados.
- Clique no cartão ativa o pincel; botão direito atribui ao slot.
- "Preencher slots com sugestões": os 16 slots recebem 4 por conjunto.
- Atalhos: Configurar Krita > Atalhos > Scripts > HQ Tools (pincel 1 a 16).
- "Instalar bundle...": escolher um `.bundle` (ex.: Cityscape Brushes em
  APP/Plugins/Krita), reiniciar e conferir os presets novos no Krita.

## Problemas conhecidos e tratamento

- Texto de SVG pode chegar como shape não editável por texto na 5.3.4 (bloco
  5): usar a ferramenta de texto do Krita sobre o shape, ou digitar por cima
  na camada `text`.
- `Palette(None)` + `save()` não validado: por isso os templates são `.gpl`.
- Mudar `modules.*` na config exige reiniciar o Krita.
- Se um docker não aparecer, conferir o log do Krita (Ferramentas > Scripts >
  Scripter imprime erros de importação na inicialização).