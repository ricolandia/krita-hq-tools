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

### 3b. Símbolos do Krita (aba dos balões)

- Aba "Símbolos do Krita": aparecem as bibliotecas `BalloonSymbols.svg` e
  `pepper_carrot_speech_bubbles.svg` com nomes e licença (miniaturas quando o
  Qt conseguir renderizar; senão, quadrados com iniciais).
- O botão e o duplo clique abrem o docker nativo "Bibliotecas de símbolos" do
  Krita (a renderização e a inserção ficam por conta dele: arraste e solte no
  canvas).

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