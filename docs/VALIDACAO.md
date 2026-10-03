# Validação dentro do Krita

Checklist para validar o HQ Tools no Krita 5.3.4 (AppImage). O núcleo puro já é
coberto por testes (`python3 -m unittest discover -s tests`); aqui o foco é o
comportamento dentro do programa.

**Status (03/10/2026):** roteiro validado pelo autor; release v0.6.2 publicada
pela tag `v0.6.2`. Este documento fica como referência para as próximas.

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
  "Aplicar retícula" **atualiza a mesma camada** (contar camadas antes e
  depois: não cresce). Sem seleção ativa, a máscara da camada é preservada;
  com seleção ativa, a área muda para a seleção. Repetir com uma máscara de
  meio-tom (intensity e cmyk): "Aplicar meio-tom" atualiza a máscara
  selecionada (contar máscaras: não cresce).
- **Excluir preset**: salvar um preset do usuário ("Salvar como..."), clicar
  "Excluir" e confirmar: o preset some da lista e o Krita continua aberto
  (regressão da v0.6.2; antes derrubava o programa).
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
  Após "Instalar padrões e texturas (kit)", os tiles próprios (papéis,
  estrelas, corações, hachuras...) aparecem na lista de padrões.
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
- "Instalar fontes de HQ": as 12 famílias (Bangers, Comic Relief, Patrick Hand,
  Comic Neue, Londrina Solid/Shadow/Outline/Sketch, Nanum Pen Script, Gaegu,
  Boogaloo) vão para `~/.local/share/fonts/hq_tools`; após reiniciar o Krita,
  aparecem na ferramenta de texto. Conferir créditos em `CREDITS.md`.

### 3d. Onomatopeias

- Docker "HQ Tools: onomatopeias": 3 amostras na primeira execução; duplo
  clique insere no grupo ativo como camada vetorial.
- Adicionar um SVG próprio (Inkscape) na pasta e Atualizar.

### 3e. Biblioteca do projeto

- "Criar novo recurso" (tipo de camada Vetorial ou Pintura): abre um documento
  15 x 15 cm a 300 dpi com a camada "recurso".
- Vetorial: desenhar formas/texto e "Salvar recurso do documento": SVG na
  subpasta do tipo.
- Pintura: desenhar com pincel e salvar: PNG transparente recortado pela
  camada ativa (RGBA 8 bits); conferir transparência abrindo o PNG.
- Inserir: SVG vira camada vetorial; PNG vira camada de pintura
  (setPixelData; fallback camada de arquivo).
- Duplo clique no recurso insere no grupo ativo do documento da página.
- Trocar a pasta da biblioteca (pode ser a pasta do projeto, criada por
  "Novo projeto...") e conferir a listagem.

### 4. Paletas

- Aba Templates: clicar numa cor e "Aplicar na frente" muda a cor ativa.
- "Instalar no Krita": os `.gpl` aparecem na pasta de paletas; após reiniciar,
  as mesmas paletas aparecem na aba "Paletas do Krita" (PaletteView).

### 5. Páginas (gerenciador)

- "Novo projeto...": com a página atual salva, a pasta dela vira o projeto:
  subpastas `biblioteca/{baloes,paineis,onomatopeias}`, `export`, `templates`,
  `translations` e `comicConfig.json` (UTF-16) com a página em `pages`.
  Em pasta que já tem `comicConfig.json`, o projeto existente é aberto e a
  página atual entra na lista (o config não é recriado do zero).
- Sem documento ativo ou página não salva: aviso modal; "Salvar agora" abre o
  diálogo e continua o fluxo com a pasta escolhida.
- "Abrir projeto...": abrir o `comicConfig.json` de um projeto criado pelo
  CPMT ou pelo próprio fluxo acima.
- "Criar próxima página": abre o diálogo de nova página (formato, DPI,
  painéis da tirinha). A página nasce com as guias de margem (0,5/1/1,5 cm)
  já aplicadas. Formatos: A4/A5/A3/tirinha/americano/tankobon/quadrado/livre
  (largura e altura em mm). Em projeto CPMT, a página é registrada no
  `comicConfig.json`.
- "Definir modelo de página...": usar a página atual salva, um template de HQ
  do Krita (BD Europeu, EUA, Mangá, Tsukirino, Waffle) ou os modelos gerados
  pelo botão "Gerar modelos padrão do HQ Tools" (A4, A3, tirinhas 1-3, grades
  2x2 e 3x3, com guias). Ao criar a página com modelo: formato igual = cópia
  direta; A3 = redimensiona; tirinha = substitui os painéis por uma tira
  horizontal (3 por padrão).
- "Guias de margem": no documento ativo, criam-se 12 guias (0,5 / 1 / 1,5 cm
  por lado); conferir posições: 59/118/177 px a 300 dpi a partir de cada borda.
  Atenção: substitui as guias existentes.
- Referências: "Camada de referência" marca a camada selecionada (rótulo,
  trava, opacidade reduzida); "Importar referência (PNG)" insere o PNG como
  camada de arquivo travada no grupo ativo (usado para renders do Blender ou
  poses de ferramentas web).
- Duplo clique abre a página; arrastar reordena e grava no `comicConfig.json`
  (abrir o arquivo e conferir a ordem da lista `pages`).

### 5b. Avisos

- Fluxos e decisões (salvar página, projeto criado, recurso salvo, falhas)
  aparecem em janela modal; sucessos rápidos (pincel, retícula, inserção)
  continuam no toast flutuante do canvas.

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

### 7b. Packs da comunidade (aba Packs)

- A aba "Packs" lista Deevad v8.2 (David Revoy, CC-BY 4.0) e Krita Watercolor
  Set (Vasco Basqué, CC-0), com origem no tooltip.
- "Ver licença" mostra o LICENSE.txt do pack; os créditos estão no CREDITS.md.
- "Instalar pack selecionado" copia os arquivos para as pastas de recursos do
  Krita (paintoppresets/brushes/patterns/palettes) e marca "[instalado]".
- Após reiniciar o Krita, os presets aparecem no docker de presets e na aba
  "Comunidade" do HQ Tools (agrupados por pack, com autor e licença); clique
  no preset ativa o pincel. Os conjuntos padrão (Rascunho, Contornos, etc.)
  continuam montados pelos presets nativos do Krita, sem poluir com os packs.

## Problemas conhecidos e tratamento

- Texto de SVG pode chegar como shape não editável por texto na 5.3.4 (bloco
  5): usar a ferramenta de texto do Krita sobre o shape, ou digitar por cima
  na camada `text`.
- `Palette(None)` + `save()` não validado: por isso os templates são `.gpl`.
- Mudar `modules.*` na config exige reiniciar o Krita.
- Se um docker não aparecer, conferir o log do Krita (Ferramentas > Scripts >
  Scripter imprime erros de importação na inicialização).