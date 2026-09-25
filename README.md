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
| Retículas e hachuras | Presets de retícula com LPI real (célula calculada pelo DPI do documento), aplicação como camada de preenchimento não destrutiva dentro do grupo do painel, meio-tom como máscara do filtro Halftone sobre tom pintado, tom com padrões do Krita, meio-tom colorido por canal (CMYK), edição da retícula já aplicada, máscara vazia para revelar pintando, mostrar área, reutilização de tons idênticos, posição do padrão e linhas de efeito/velocidade. |
| Balões | Catálogo de balões vetoriais em SVG (amostras inclusas e pasta própria), inserção com um clique no grupo ativo, opção de camada `text` para o CPMT e aba com as bibliotecas de símbolos do Krita (BalloonSymbols, Pepper&Carrot e as que você instalar). |
| Paletas | Templates de HQ e artísticas (tons, nanquim, pele, céu, vegetação, chapadas, Zorn, retrato, paisagem, amanhecer, noite, terra, pastel, aquarela, guache, acrílico, retrô, BD, super-herói, mangá, sépia), aplicação na cor de frente/fundo, instalação no Krita e visualização das paletas instaladas. |
| Páginas | Gerenciador com miniaturas internas dos `.kra`, duplo clique para abrir e reordenação arrastando (gravada no projeto CPMT); gerador de páginas a partir de roteiro em sintaxe própria. |
| Pincéis | Conjuntos sugeridos (Rascunho, Contornos, Aquarela/Guache, Acrílico/Óleo, Retículas) com cartões de miniatura + nome, montados com os presets instalados no Krita; 16 slots com atalhos configuráveis; instalador de bundles de pincel. |

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
   Depois de aplicar, selecione a camada e use "Editar selecionada" para
   ajustar LPI, ângulo e posição sem recriar nada.
2. **Meio-tom**: pinte o tom numa camada e aplique "Meio-tom (máscara de
   filtro)"; o preset vira pontos ou linhas reativos ao tom. Em documento
   CMYKA, o modo "Cores por canal" usa os ângulos de impressão (15/75/0/45).
3. **Balão**: duplo clique no modelo; o balão entra no grupo ativo como vetor.
   A aba "Símbolos do Krita" insere os balões das bibliotecas do Krita.
4. **Páginas**: crie um projeto no CPMT, abra o `comicsConfig.json` no
   gerenciador e use a aba Roteiro para gerar páginas com painéis e falas.
5. **Pincéis**: navegue pelos conjuntos (Rascunho, Contornos, Aquarela/Guache,
   Acrílico/Óleo, Retículas), clique no cartão para ativar; botão direito
   atribui ao slot. Atalhos em Configurar Krita > Atalhos > Scripts > HQ Tools.
6. **Linhas de efeito**: no docker de retículas, seção "Linhas de
   efeito/velocidade": escolha foco ou paralelas e insira como vetor.

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