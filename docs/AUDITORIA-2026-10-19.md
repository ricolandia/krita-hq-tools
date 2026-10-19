# Auditoria de 19/10/2026: bugs, interface, i18n e performance

Auditoria do plugin depois da v0.25.0, com foco no que o autor pediu: bugs,
polimento de interface, experiência de uso e desempenho. Sem recurso novo e
sem release: o que entrou são correções e ajustes de layout.

## Método

- Suíte, lint e packs (baseline e depois do lote).
- Varredura AST de funções sem referência no repositório.
- Varredura de strings em português fora do `i18n.t` (o modo EN ficaria em PT
  em silêncio).
- Captura dos 12 dockers dentro do Krita real (xvfb), em 380x720, medindo
  tamanho mínimo, rótulos maiores que a largura, botões sem dica e estados.
- Sonda de tamanho mínimo por aba para achar docker que não cabe em tela de
  768 px.
- Benchmarks: render 3D 700x700 com pose cacheada, gerenciador com 200
  páginas e montagem dos 12 dockers.
- Krita 5.3.4 e 6.0.4 (paridade dos helpers novos).
- Os arquivos editados passaram pelo formatador do ambiente (ruff format):
  ajuste de aspas e quebras de linha, sem mudança de comportamento.

## Baseline

- 448 testes verdes, lint limpo, 74 presets sem órfã.
- Nenhum `except:` nu, nenhum `print` de depuração, nenhum `setFixed*` nos
  dockers, botões só via `ui.botao`.
- Dois candidatos a código morto: `Config.get_float` e `generator.generate`
  (sem chamada no repo; mantidos por enquanto).

## Bugs

### 1. Duplicar página podia escolher um número ocupado

`PagesDocker._proximo_indice_livre` usava `re.search(r"pagina_(\d+)\.kra$")`,
sensível a maiúsculas. Numa pasta com `Pagina_005.KRA` (o Windows não
diferencia maiúsculas) o número 5 era considerado livre e a cópia podia
sobrescrever a página existente. Reproduzido na seleção do número; corrigido
com o módulo puro `hq_tools/modules/pages/nomes.py`
(`proximo_indice_livre`, regex `IGNORECASE`), mais uma rede de segurança
`while os.path.exists(destino)` na duplicação. Sete testes novos em
`tests/test_nomes_pagina.py`.

## Interface e experiência

### 2. Dockers não cabiam em tela de 768 px

- **Retículas:** altura mínima 939 px (aba com formulário de 861 px). Agora as
  abas ficam em `ui.rolavel(...)` e a altura mínima caiu para 147 px; a largura
  mínima do conteúdo é preservada (472 px), então não aparece barra horizontal
  nem campo cortado.
- **3D:** altura mínima 895 px. As abas também ficaram roláveis e o preview
  ganhou política `Ignored` (ele se adapta ao espaço, o render acompanha). A
  altura mínima caiu para 445 px.
- **Produção:** o aviso da pasta ficava numa coluna de 107 px ao lado de três
  botões, virando nove linhas; a projeção da meta era cortada e a árvore do
  checklist ficava com ~40 px. O rótulo virou uma linha inteira (com os botões
  embaixo), a meta ganhou linha própria, a árvore tem mínimo de 100 px e a
  dica foi encurtada. Mínimo: 356x711.

### 3. Caminhos longos ocupavam três ou quatro linhas

Os rótulos "Pasta: ..." de balões, onomatopeias, biblioteca e moodboard
quebravam em várias linhas e empurravam o conteúdo. Entrou
`ui.rotulo_caminho`: uma linha, elipse no meio, caminho inteiro no tooltip e
texto selecionável para copiar. O mesmo helper foi usado na produção.

### 4. "Tipo de camada:" quebrava em duas linhas

Na biblioteca o rótulo era cortado em "Tipo de" / "camada:". Virou "Camada:",
com dica explicando o tipo do recurso novo.

### 5. Checkboxes sem dica

Cinco da retícula (alinhar, inverter, padrão do Krita, seleção como máscara,
reutilizar) e o de balões ("Nomear a camada como 'text'") ganharam tooltip.

## i18n

- Nomes dos modelos de página ("A4 padrão", "Tirinha 1 tira", "Grade 2x2"...)
  apareciam em PT no modo EN; agora passam por `i18n.t` e têm tradução. O
  rótulo do modelo escolhido também mostra o nome amigável, não o
  `modelo-a4-padrao.kra`.
- O nome padrão da retícula (`QLineEdit("Retícula")` e os fallbacks) era
  hardcoded; agora usa `i18n.t("Retícula")` ("Screentone" no EN).
- Erros de destino da exportação ("pasta de destino vazia", "não é uma
  pasta") estavam em PT dentro da mensagem traduzida; agora passam pelo i18n.
- A dica nova da produção entrou no dicionário EN; a dica antiga e a chave
  "Tipo de camada:" saíram (órfãs).
- `tests/test_i18n.py` passou a cobrir os nomes de `modelos.MODELOS`, que vão
  por `i18n.t` em tempo de execução.

## Performance (medida, sem achado crítico)

- **3D:** com a pose cacheada (o caminho do arrasto), 700x700 com culling:
  chapado 5,2 ms, sombreado 6,6 ms, toon 6,1 ms. Dentro do alvo de 10 ms.
  Sem o cache, o skinning sobe para ~10 ms; o viewer já cacheia por revisão de
  pose.
- **Gerenciador:** 200 páginas, refresh frio 0,18 s e quente 0,01 s (cache de
  miniaturas).
- **Montagem:** os 12 dockers juntos somam 134 ms (3D 50 ms, perspectiva 24 ms,
  pincéis 20 ms; o resto abaixo de 15 ms).

## O que ficou anotado (não aplicado)

- Aviso de sobrescrita na exportação quando o arquivo de destino já existe.
- `Config.get_float` e `generator.generate` sem uso: remover ou documentar como
  API.
- Nomes de camada do documento em PT ("Referência", "Perspectiva", "Linhas de
  efeito") mesmo no modo EN; decidir se traduz ou se fica como convenção.
- Abas de pincéis ainda usam setas de rolagem em 478 px; encurtar
  "Aquarela/Guache" e "Acrílico/Óleo" só na aba resolveria.
- Combo de padrão do Krita na retícula trunca o nome fechado; falta tooltip
  com o texto atual.
- Árvore da produção continua curta no mínimo do docker (100 px); cresce com
  a doca.
- Ações do gerenciador (duplicar/renomear/remover) continuam sem teste de UI;
  os casos de nome case-insensitive agora têm teste no núcleo.

## Validação

- Suíte: **455 testes** verdes (448 + 7 novos), lint limpo, 74 presets.
- 12 dockers montam no **Krita 5.3.4** e no **6.0.4**; captura sem corte real
  (o único "cortado" restante é o texto longo com quebra de linha, que ocupa
  várias linhas) e sem botão sem dica além dos botões internos do Qt.
- Capturas em `/tmp/opencode/ui-audit/` (locais, não versionadas).
