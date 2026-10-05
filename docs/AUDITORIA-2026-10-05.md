# Auditoria de 2026-10-05

Segunda auditoria do HQ Tools, agora com três frentes que a de 30/09 não
cobriu: **linguagem** (Python), **ecossistema** (Krita/libkis) e **design**
(UX e design system), mais uma seção dedicada ao sistema de packs e à
biblioteca, que é o que o autor está usando para montar os kits agora.

**Estado de partida:** v0.7.2 publicada, 259 testes verdes, `py_compile` OK em
84 arquivos, git limpo.

## Como a auditoria foi feita

Três passes com roteiro próprio, cada achado confirmado no código antes de
entrar aqui (a regra de ouro da auditoria anterior: reproduzir antes de
reportar). O que não deu para reproduzir sem o Krita ficou marcado como
"a validar". O design teve duas fontes: leitura do `DESIGN.md`, do `ui.py` e
dos dockers, e QA visual das 7 capturas com o modelo de visão (em dois lotes),
com os indícios do modelo separados dos achados verificáveis, porque o QA de
visão erra em detalhe de tema e de corte de tela.

## Frente Python

| Achado | Onde | Gravidade |
|---|---|---|
| `DEFAULT_CONFIG["modules"]` não tem `viewer3d` | `core/config.py:19-28` | média |
| Caminhos do Linux ignoram `XDG_DATA_HOME`/`XDG_CACHE_HOME` (Flatpak) | `core/paths.py:14-29` | média |
| `create_next_page` registra a página no CPMT sem proteção | `pages/manager_docker.py:498` | média |
| `packs._preset_chunk_xml` só lê chunk `tEXt` | `brushes/packs.py:91-111` | baixa |
| `install_templates` recopia tudo a cada clique | `palettes/docker.py:210-224` | baixa |
| Temporário vaza se o JSON não for serializável | `core/config.py:110-124`, `core/gpl.py:62-77` | baixa |
| Miniatura de SVG duplicada e sem cache | `balloons/docker.py:81-93`, `onomatopeias/docker.py:58-69` | baixa |
| `int()` trunca coordenada negativa na máscara do contorno | `core/modelo3d.py:326-327` | baixa |
| Contagem de módulos defasada na documentação | `docs/ARQUITETURA.md:3`, `docs/ROTEIRO-CAPTURAS.md:8`, `core/ui.py:4`, `plugin.py:3` | baixa |

Notas:

- **`viewer3d` fora do padrão do config.** O módulo existe, é registrado
  (`plugin.py:43-48`) e ligado por omissão, mas quem editar o `config.json`
  para desligar módulos não encontra a chave do 3D; o arquivo gravado também
  não a lista. Correção de uma linha.
- **XDG e Flatpak.** O `INSTALL.md` promete suporte a Flatpak (`:52` e `:77`,
  pasta `~/.var/app/org.kde.krita/data/krita`), mas o código sempre resolve
  `~/.local/share/krita`. Dentro do sandbox, o `XDG_DATA_HOME` aponta para a
  pasta certa e é o que o Krita usa; ler o XDG quando definido faz a promessa
  valer, sem mudar nada em máquina sem a variável (a do autor está vazia).
- **Registro no CPMT sem try.** O `generator.generate` protege o mesmo caso
  (`generator.py:251-257`) e o docker não: uma falha de escrita no
  `comicConfig.json` sobe crua para o Qt, a página fica criada e fora da lista,
  e o autor não recebe aviso.
- **`tEXt` e `zTXt`.** Verificado com os dois packs: 3 presets do Deevad
  guardam o XML em `zTXt` e o `packs.py` devolve `None` para eles. Hoje o
  fallback pelo nome do arquivo cobre (nome interno igual ao do arquivo), mas
  um preset com nome interno diferente sumiria da aba da comunidade. O
  `scripts/auditar-packs.py` já trata `tEXt`, `zTXt` e `iTXt`.
- **Temporário vaza.** `config.save` e `gpl.save_gpl` capturam só `OSError`;
  um `TypeError` do `json.dump` deixa o arquivo temporário para trás
  (`delete=False`). O `cpmt._escrever_atomico` já usa `BaseException` com
  remoção e re-raise; é o padrão a copiar.
- **Miniaturas de SVG.** Cada `refresh` dos balões e das onomatopeias
  rasteriza **todos** os SVGs na thread da interface, sem cache. Com os kits
  do autor crescendo (é o que ele está montando agora), o `core/thumbs.py`
  tem o cache certo para reusar (chave por caminho, mtime e tamanho).
- **`int()` vs `floor`.** Na máscara de contorno, `int(min(ys)/tamanho)`
  arredonda para zero, não para baixo; com coordenada negativa a célula erra
  por um. Efeito visual pequeno (linha na borda), correção de uma linha com
  `math.floor`.

## Frente Krita (libkis)

| Achado | Onde | Gravidade |
|---|---|---|
| Flutuante ancora no viewport por índice de lista | `viewer3d/docker.py:147-167` | média (a validar) |
| Inserção do 3D e da biblioteca fora de macro de desfazer | `viewer3d/docker.py:1052`, `biblioteca/docker.py:473` | média (a validar) |
| "Guias de margem" substitui as guias existentes | `pages/manager_docker.py:590-591` | baixa |

Notas:

- **Viewport por índice.** `_viewport_da_view` casa `mdiArea.subWindowList()`
  com `janela.views()` pela posição na lista; as duas listas não têm contrato
  de ordem entre si. Com um documento só (o caso validado) funciona; com dois
  documentos abertos o flutuante pode ancorar no viewport errado e o
  fallback é a primeira sub-janela. Validar no Krita com dois documentos e,
  se confirmar, casar pelo canvas da view (`view.canvas()`) em vez do índice.
- **Desfazer.** Balões, onomatopeias e retículas usam `helpers.run_in_macro`
  (um Ctrl+Z desfaz tudo). A inserção do 3D e a da biblioteca não usam: são
  `createNode` + `setPixelData` + `addChildNode` + trava/opacidade. Validar
  no Krita se um Ctrl+Z desfaz a inserção inteira; se não, envolver em macro
  como os outros.
- **Guias.** `setVerticalGuides`/`setHorizontalGuides` trocam a lista inteira:
  as guias de perspectiva ou sangria do autor somem sem aviso ao clicar em
  "Guias de margem". O libkis tem `verticalGuides()`/`horizontalGuides()`;
  mesclar com as existentes preserva as duas coisas.
- **Compatibilidade:** nada novo a apontar. A camada `compat.py` cobre os
  enums dos dois bindings, o `qt_probe` decide pela versão do Krita e o CI
  roda os módulos puros no Windows. Continua pendente o que já estava no
  `VALIDACAO.md` (`Palette(None)` + `save()`).

## Frente Design

| Achado | Onde | Gravidade |
|---|---|---|
| Abas internas sem a escala de espaçamento da casa | `brushes/docker.py:131,152,199`, `palettes/docker.py:63,116`, `screentone/docker.py:67,256` | baixa |
| Lista de swatches estica e deixa área morta | `palettes/docker.py:72-83` | baixa |
| `DESIGN.md` segue marcado como rascunho | `docs/DESIGN.md:3-4` | baixa |
| Rótulos de miniatura e de ajuda com contraste fraco | (indício de visão, a conferir) | baixa |
| Abas de pincéis podem elidir em painel estreito | (indício de visão, a conferir) | baixa |

Notas:

- **Espaçamento.** O `ui.painel` aplica 12/8 nos painéis principais, mas as
  abas internas criam `QVBoxLayout(tab)` direto e ficam com a margem padrão do
  Qt (cerca de 9 px). É a mesma correção em sete pontos, com
  `ui.espacamento(layout)`.
- **QA visual.** Os indícios do modelo de visão que sobreviveram à conferência
  no código: swatches com área morta (real, a lista estica), abas de pincéis
  que podem elidir em painel estreito (a conferir em janela estreita) e
  contraste dos rótulos cinza (segue o tema do Krita; a conferir no Acer). O
  resto do que o modelo apontou é do tema, não do plugin: os "quadrados azuis"
  e as cores de ícone vêm do `QStyle` do Krita, decisão registrada no
  `DESIGN.md` (nada aqui pinta fundo, borda ou fonte).
- **DESIGN.md.** O ícone e a prévia social já foram executados a partir dele,
  mas o documento continua "rascunho aguardando aprovação". Ou vira aprovado,
  ou o status muda para o que falta (banner, página de exemplo).

## Packs e biblioteca (profundidade)

O sistema está sólido: formato documentado (`FONTE.md` + `LICENSE.txt` por
pack), instalação por tipo nas pastas do Krita, comparação byte a byte para
não recopiar, backup do preset do autor antes de substituir, créditos no
`CREDITS.md` e auditoria própria (`scripts/auditar-packs.py`) que confere
referência órfã lendo o XML dentro do PNG. Medido agora: Deevad v8.2 com 62
presets e Vasco com 12, zero referências quebradas.

O que ficou:

- O `tEXt`/`zTXt` do `packs.py` (ver frente Python); é o único ponto em que o
  runtime enxerga menos que o auditor.
- `pack_instalado` responde "qualquer arquivo existe": um pack pela metade
  aparece como "[instalado]" e o autor não é convidado a reinstalar. Sugestão:
  contar arquivos presentes e mostrar "parcial" quando faltar algum.
- A biblioteca do projeto (`biblioteca/core.py`) está bem guardada: escrita
  atômica, renomear/duplicar recusam colisão e o apagar só aceita SVG/PNG.
  Nada a corrigir.

## Reconciliação com a auditoria de 30/09

- **Fechado e reconferido:** escrita atômica (config, presets, CPMT), cache de
  miniaturas de `.kra`, fontes com `fc-cache` incremental, cursor de espera,
  `build-zip` com licença e créditos, conferência de tag x versão no release,
  notas do release pelo CHANGELOG, isolamento dos módulos no `plugin.py` e a
  correção do `selection_vazia` (presente em `krita_helpers.py:180-194`).
- **Continua aberto de lá:** a lista de validação dentro do Krita (parcialmente
  validada na 0.7.x), a largura do `ui.rotulo_info` em documento aberto e o
  `Palette(None)`.
- **Novo:** os achados das três frentes acima, nenhum deles da gravidade dos
  três primeiros lotes de 30/09 (dado do autor, isolamento, desempenho do
  gerenciador): o que apareceu agora é de borda.

## Quick wins aplicados nesta auditoria

1. `viewer3d` entra no padrão do `config.json`.
2. `paths.py` respeita `XDG_DATA_HOME` e `XDG_CACHE_HOME` no Linux (Flatpak).
3. `create_next_page` avisa quando o registro no CPMT falha, em vez de deixar
   a exceção subir.
4. `packs.py` lê `zTXt` e `iTXt` como o auditor, com teste sintético.
5. "Guias de margem" mescla com as guias existentes (função pura testável).
6. `install_templates` pula paleta idêntica, como as fontes e os packs.
7. Sete abas internas passam a usar `ui.espacamento`.
8. Contagem de módulos corrigida na documentação e nos docstrings.

Cada um com teste quando dá para testar fora do Krita; a suíte segue verde.

## Validação pendente no Krita (acrescentada)

- [ ] Abrir **dois documentos** e usar "Flutuar na página": o preview precisa
      ancorar no viewport do documento ativo.
- [ ] "Inserir como camada" do 3D e "Inserir" da biblioteca: um Ctrl+Z desfaz
      a inserção inteira.
- [ ] "Guias de margem" com guias já existentes: as antigas continuam.
- [ ] Abas de pincéis em painel estreito: os rótulos não podem cortar.
- [ ] Conferir as margens novas das abas de pincéis, paletas e retículas.

## Recomendações (não aplicadas)

- Cache de miniatura para os SVGs de balões e onomatopeias (reusar
  `core/thumbs.py`), quando os kits crescerem.
- `pack_instalado` com estado "parcial" em vez de "instalado".
- Um passo de lint no CI (ruff) para pegar nome morto e import não usado; hoje
  a rede é a suíte e o `py_compile`.
- `install-dev.sh` e a tabela do `INSTALL.md` para Flatpak: o script de
  desenvolvimento ainda fixa `~/.local/share/krita`.
