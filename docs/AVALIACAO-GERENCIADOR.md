# Avaliação do gerenciador de projetos/páginas (17/10/2026)

> **Status (17/10):** todos os achados (A–E) e as propostas maiores
> aprovadas pelo autor ("Sim. Todos") foram **implementados**, provados no
> harness (badge da produção por estado, "(ausente)", menu de contexto com
> Abrir/Abrir selecionadas/Duplicar/Renomear/Remover — este só no modo
> projeto, com a semântica do CPMT: o arquivo fica no disco —, ordem natural
> no modo pasta e o fallback `pagesLocation: "."`) e **testados pelo autor
> na interface ("Feito!")**.

A pedido do autor ("algo que ficou de fora da minha parte: avaliar o que pode
melhorar no gerenciador de projetos"). Método de sempre: cada achado foi
**reproduzido** — parte pura com o `CPMTProject` e parte na UI no harness do
Krita real. Fontes de referência: o código do CPMT embutido no AppImage e os
**projetos reais do autor** (`~/Downloads/My_comics_1/2/3`).

## O que já está bom (não mexer)

Novo projeto (cria a pasta, a biblioteca e a produção), abrir projeto
CPMT/pasta, criar página (formatos, tirinha, modelo com adaptação e guias),
reordenar com persistência no `comicConfig.json`, miniaturas com cache por
mtime, restauração do último projeto/pasta, limpeza da página órfã no fluxo
do modelo, mensagens em PT/EN e a exportação nova (v0.23.0).

## Achados (reproduzidos)

### A. Não há ações por página (remover/duplicar)

- **Evidência**: a lista não tem menu de contexto nem ações (grep por
  `customContextMenu`/`Key_Delete` vazio; policy = `DefaultContextMenu` no
  harness); a fileira tem só criar/atualizar/abrir pasta/exportar.
- **Referência do CPMT**: `slot_remove_selected_page` — *"Remove the selected
  page from the list of pages. This does not remove it from disk (far too
  dangerous)."* — ou seja, **remover é tirar da lista, nunca apagar o
  arquivo**.
- **Proposta (v1)**: clique direito na página com:
  - **"Remover da lista..."** (com confirmação; só no modo projeto; usa o
    `set_page_order` sem o item; a mensagem avisa que o arquivo fica no
    disco) — espelha o CPMT;
  - **"Duplicar página"** — copia o `.kra` com o próximo nome livre
    (`next_page_name`/`pagina_NNN`) e registra no projeto.

### B. `pagesLocation` ausente aponta para uma subpasta que não existe

- **Evidência (pura)**: config sem a chave ⇒ `pages_dir()` = `<raiz>/pages`
  (não existe) e a próxima página seria salva em `pages/Teste002.kra`.
  **Na UI**: o rótulo mostra "Projeto: Sem (1 páginas)" mas a pasta de
  trabalho aponta para `sem-pageslocation/pages` (inexistente).
- **Referência**: os **três projetos reais** usam `pagesLocation: "."`
  (páginas na raiz); o CPMT, quando a chave está em branco, **pergunta** onde
  salvar.
- **Proposta**: fallback `"."` (a convenção real e a do nosso próprio
  `create_project_with_page`), em vez de `"pages"`.

### C. Ordem lexical no modo pasta

- **Evidência**: `sorted(["pagina_1.kra", "pagina_10.kra", "pagina_2.kra"])`
  ⇒ `pagina_1, pagina_10, pagina_2`.
- **Proposta**: ordenação natural (chave com o número extraído), como o
  próprio `_proximo_indice_livre` já entende.

### D. Página registrada cujo arquivo sumiu entra na lista sem aviso

- **Evidência (pura)**: `page_relatives()` devolve 2 entradas com
  `[True, False]` de existência; **na UI** a lista mostra `sumiu.kra` igual às
  outras (abrir dá "Arquivo não encontrado", sem quebrar — o tratamento já é
  bom).
- **Proposta**: marcar a página ausente no rótulo ("(ausente)") e deixar o
  "Remover da lista..." (achado A) resolver; o usuário entende o que houve
  sem abrir.

### E. Limpeza de órfã só no fluxo do modelo

- **Evidência**: no `create_next_page`, o fluxo do **modelo** chama
  `_descartar_pagina_orphã` quando falha; o fluxo do **gerador** faz
  `show_info(...); return` — se o `save_page` falhar no meio, o `.kra`
  parcial (e o documento) ficam.
- **Proposta**: usar o mesmo descarte nos dois caminhos.

## Propostas maiores (avaliar depois)

- **Estado da produção na grade**: uma bolinha/badge por página lendo o
  `producao.json` (o produção já tem os estados; a grade é o lugar natural
  para vê-los de relance).
- **"Renomear página..."**: exige cuidado com a lista do CPMT (renomear o
  arquivo + atualizar a entrada) — só depois de A entrar.
- **"Abrir selecionadas"**: abrir várias páginas de uma vez (Krita aguenta
  abas; utilidade a confirmar).

## Decisões para o autor

1. Quais quick wins entram (A, B, C, D, E)?
2. O "Remover da lista" segue o CPMT (nunca apaga o arquivo)? (recomendado)
3. O "Duplicar" copia o arquivo como está (nome novo, conteúdo igual)?
4. O badge da produção entra na fila ou fica anotado?
