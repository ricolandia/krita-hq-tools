# Sintaxe do roteiro (HQ Tools)

Formato de texto simples, um arquivo por capítulo, uma página por bloco.
Palavras-chave sem acento e sem distinção de maiúsculas; linhas em branco e
comentários (`#`) são ignorados.

## Exemplo

```
# Capítulo 1
pagina 1
formato A4
dpi 300
layout grade2x2
margem 5%
sarjeta 2%
narracao p1: Era uma vez, numa cidade pequena...
fala p1: Voce viu aquilo?
fala p2: Nao vi nada.
fala p3: Entao olhe de novo.
fala p4: O que?

pagina 2
layout tira3
direcao rtl
fala p1: Primeiro quadro.
fala p2: Segundo.
fala p3: Terceiro.
```

## Comandos

| Comando | Valor | Padrão |
|---|---|---|
| `pagina N` | início de página | nova página é criada automaticamente |
| `formato` | `A4`, `A5`, `americano`, `tankobon`, `quadrado` | `A4` |
| `dpi` | 72 a 1200 | `300` |
| `layout` | nome ou `LxC` | `grade2x2` |
| `direcao` | `ltr` (ocidental) ou `rtl` (manga) | `ltr` |
| `margem` | fração ou porcentagem (`0.05` ou `5%`) | `5%` |
| `sarjeta` | fração ou porcentagem | `2%` |
| `fala pN: texto` | fala de balão do painel N | |
| `narracao pN: texto` | narração (caixa) do painel N | |

Layouts nomeados: `quadro` e `splash` (1 painel), `duplo-h` (2 na horizontal),
`duplo-v` (2 na vertical), `grade2x2`, `grade3x2`, `grade2x3`, `tira3` (3 na
vertical), `tira4`. Também aceita `LxC`, ex.: `layout 3x2` (3 linhas, 2
colunas), com máximo de 6 em cada eixo.

## Painéis

A geometria é calculada em unidades relativas (0 a 1): margem nas bordas,
sarjeta entre os painéis, células iguais. A ordem de leitura começa no topo;
com `direcao rtl` as colunas são lidas da direita para a esquerda (manga).

O painel 1 fica no topo (à esquerda em `ltr`), e os painéis crescem por linha
e coluna na ordem de leitura.

## Texto gerado

- `fala`: texto centralizado no terço médio do painel, com quebra de linha
  aproximada pela largura do painel.
- `narracao`: texto à esquerda, no topo do painel.
- Fonte: `sans-serif` (a fonte real depende do sistema); o tamanho escala com o
  formato da página.

A camada `text` do `.kra` gerado guarda esses textos; a forma do balão entra
pelo módulo de balões ou manualmente.

## Erros

Erros de sintaxe apontam a linha (ex.: painel fora do intervalo, layout
desconhecido, comando não reconhecido) e interrompem a geração sem criar
arquivos parciais.