# HQ Tools: ferramentas de quadrinhos para o Krita

Plugin do Krita com retículas e hachuras, balões vetoriais, paletas,
gerenciador de páginas com miniaturas, gerador de páginas a partir de roteiro e
atalhos de pincel. Feito para o Krita 5.3.4 (AppImage, PyQt5) com preparação
para o Krita 6 (PyQt6).

Os quatro documentos originais de contexto do projeto estão em
`docs/contexto/`.

## Módulos

| Módulo | O que faz |
|---|---|
| Retículas e hachuras | Presets de retícula com LPI real (célula calculada pelo DPI do documento), aplicação como camada de preenchimento não destrutiva dentro do grupo do painel, e meio-tom como máscara do filtro Halftone sobre tom pintado. Cross-hatch em dois ângulos. |
| Balões | Catálogo de balões vetoriais em SVG (amostras inclusas e pasta própria), inserção com um clique no grupo ativo, opção de camada `text` para o CPMT. |
| Paletas | Templates de HQ (tons, nanquim, pele, céu, vegetação, cores chapadas), aplicação na cor de frente/fundo, instalação no Krita e visualização das paletas instaladas. |
| Páginas | Gerenciador com miniaturas internas dos `.kra`, duplo clique para abrir e reordenação arrastando (gravada no projeto CPMT); gerador de páginas a partir de roteiro em sintaxe própria. |
| Pincéis | 12 slots que ativam presets instalados no Krita, com atalhos configuráveis em Configurar Krita > Atalhos. |

## Instalação

Modo desenvolvimento (editar e testar direto do repositório):

```bash
bash scripts/install-dev.sh
```

Distribuição (ZIP para Ferramentas > Scripts > Importar plugin Python):

```bash
bash scripts/build-zip.sh
# resultado em dist/hq_tools-0.1.0.zip
```

Depois: ative **HQ Tools** no Gerenciador de plugins Python e reinicie o
Krita. Os dockers ficam em Configurações > Dockers com o prefixo "HQ Tools".

## Uso rápido

1. **Retícula**: docker "HQ Tools: retículas", escolha um preset (ex.: Sombra
   média 60 LPI) e "Aplicar retícula". O plugin usa o DPI do documento para a
   conta de célula; marque "Usar a seleção ativa" para limitar ao painel.
2. **Meio-tom**: pinte o tom numa camada e aplique "Meio-tom (máscara de
   filtro)"; o preset vira pontos ou linhas reativos ao tom.
3. **Balão**: duplo clique no modelo; o balão entra no grupo ativo como vetor.
4. **Páginas**: crie um projeto no CPMT, abra o `comicsConfig.json` no
   gerenciador e use a aba Roteiro para gerar páginas com painéis e falas.
5. **Pincéis**: escolha os presets nos slots e defina os atalhos em
   Configurar Krita > Atalhos > Scripts > HQ Tools.

## Sintaxe do roteiro

```
pagina 1
formato A4
layout grade2x2
fala p1: texto da fala
narracao p1: texto de narração
```

Referência completa em `docs/ROTEIRO-SINTAXE.md`.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests -v   # testes do núcleo (fora do Krita)
```

- Arquitetura: `docs/ARQUITETURA.md`
- Descoberta técnica (API do Krita, chaves de configuração): `docs/DESCOBERTA.md`
- Validação dentro do Krita: `docs/VALIDACAO.md`

O núcleo puro (parser de roteiro, presets de retícula, comicsConfig, paletas
GPL) não importa `krita` e roda em qualquer Python. Os módulos de interface
importam `krita` e só executam dentro do Krita.

## Configuração

Tudo em `~/.local/share/krita/hq_tools/`:

- `config.json` (módulos habilitados, presets, pastas, slots de pincel);
- `screentone_presets.json` (presets de retícula do usuário);
- `balloons/` (modelos de balão, com amostras na primeira execução).

## Licença

MIT. Usa recursos nativos do Krita: gerador Screentone e filtro Halftone
(Deif Lou) e o Comics Project Management Tools (time do Krita). Ver `LICENSE`.