# Divulgação do HQ Tools

Onde divulgar o plugin, o que dizer e o que evitar. Regra de ouro: a
transparência fica no repositório (`README` e `CREDITS`); em cada canal,
siga as regras locais. Onde a assistência de IA na codificação é motivo de
remoção, não poste (e não esconda).

## O que dizer (e o que não dizer)

- O plugin **não tem função de IA** e o kit **não inclui arte gerada por
  IA**; a IA foi usada como assistente de codificação. Essa distinção é
  verdadeira e é o melhor enquadramento em qualquer comunidade.
- Divulgue o que o plugin faz (retículas, balões, páginas, pincéis, 3D,
  perspectiva, moodboard, produção), com capturas e os vídeos demo.
- Evite transformar a IA no assunto do post: ela já está declarada no
  repositório para quem quiser saber.

## Canais onde a assistência de IA na codificação derruba a postagem

- **Krita Artists** (fórum): a regra de 2026 proíbe plugins "com IA" e
  código gerado por IA (o ToS cita "code and plugins that are AI
  generated"); a própria declaração do autor derruba a postagem. Não
  repostar; o pedido de revisão ficou descartado a pedido do autor.
- **r/krita**: as regras citam o ToS do Krita Artists ("...or any image or
  plugin generated with AI technology"). Não postar.

## Lista de canais

### A. Alto valor, sem restrição a IA

1. **awesome-krita** (PR em `armstrongl/awesome-krita`, seção Plugins):
   adicionar uma linha com o link do repositório. A lista já inclui plugins
   com IA, então não há restrição; PR simples e durável (backlink).
2. **LibreArts** (librearts.org): site de notícias de ferramentas livres
   criativas; mandar um "tip" com o pitch e o link da release.
3. **Hacker News** (Show HN): "Show HN: HQ Tools, comics production tools
   for Krita (open source)"; público técnico, IA como assistente é normal.
4. **Lobsters** (post "Show", requer conta).
5. **r/opensource** (ler as regras de autopromoção; showcase com capturas).
6. **Mastodon/Fediverse** (pubkit): vídeos demo com #Krita #FOSS #Comics;
   **Lemmy** (c/opensource, c/krita).
7. **Discord da comunidade Krita** (o servidor do Rakurri, citado no
   próprio fórum como o lugar alternativo para plugins "com IA"): pedir
   convite e postar no canal de plugins.
8. **GitHub**: topics do repositório (ver "Pendências") e a descrição.
9. **YouTube**: descrição dos demos com links e capítulos.

### B. Comunidades de quadrinhos

10. **Reddit**: r/comics, r/webtoons, r/ComicBookCollabs, r/comic_crits,
    r/graphicnovels (cada um com regras de autopromoção; usar a flair).
11. **Comic Fury** (fórum de webcomics), **Penciljack** e **Digital
    Webbing** (fóruns clássicos de quadrinhos).
12. **DeviantArt** (grupos de Krita e de quadrinhos), **Tumblr** e
    **Bluesky**.
13. **Instagram/TikTok**: cortes curtos dos demos.
14. **Brasil**: r/Quadrinhos, grupos de quadrinhos (Facebook/Telegram/
    Discord, ex.: "Quadrinhos Nacionais", "Autores de Quadrinhos", "Krita
    Brasil"), **blog ricolandia** (post PT/EN com SEO), newsletter e
    LinkedIn.

### C. Oficiais (mais burocráticos)

15. **docs.krita.org, "User-made Python Plugins"**: tentar um MR no
    repositório da documentação, sendo transparente; pode ser recusado (o
    processo deles cita o fórum e o IRC, que estão fechados para o autor).
16. **KDE Discuss** (discuss.kde.org, categoria Community): fórum oficial
    do KDE, com pouco tráfego de Krita (os devs não frequentam).
17. **KDE Store** (store.kde.org): conferir se existe categoria de Krita
    para plugins (o grosso é brush/recurso); se houver, listar.
18. **(Long shot) empacotar junto com o Krita** (MR no invent.kde.org):
    não recomendo agora (exige manutenção contínua e esbarra na moratória
    de código com IA do próprio Krita).
19. **AlternativeTo/Product Hunt**: encaixe fraco; opcional.

### D. Divulgação indireta

20. **David Revoy (Deevad)**: bloga sobre Krita e pincéis, e o kit usa os
    brushes dele com atribuição; um toque amigável pode render menção.
21. **Rakurri**, **Ramon Miranda** e newsletters de software livre e de
    quadrinhos.

## Kit de divulgação

**Pitch (PT):** "HQ Tools é um plugin de código aberto (MIT) para o Krita
com ferramentas de produção de quadrinhos: retículas e hachuras, balões e
onomatopeias vetoriais, gerenciador de páginas, pincéis com atalhos,
visualizador 3D, biblioteca de perspectivas, moodboard e checklist de
produção. Instala em um clique (Importar plugin Python) e o manual sai em
PT e EN."

**Pitch (EN):** "HQ Tools is an open-source (MIT) Krita plugin with comics
production tools: screentones and hatching, vector balloons and sound
effects, a page manager, brush shortcuts, a 3D viewer, a perspective
library, a moodboard and a production checklist. One-click install (Import
Python Plugin); manual in EN and PT."

**Links:** repositório https://github.com/ricolandia/krita-hq-tools ·
release mais recente (asset `hq_tools-<versão>.zip`) · vídeos:
https://youtu.be/B9KYYyLdHF0 (todos os recursos) e
https://youtu.be/0rfDIr2QTDE (3D flutuante).

**Instalação em 1 linha:** baixe o ZIP da release e use
Ferramentas > Scripts > Importar plugin Python; ative em Configurar Krita >
Gerenciador de plugins Python.

**Transparência:** código com assistência de IA (opencode + DeepSeek); sem
funções de IA; sem arte gerada por IA (ver `CREDITS.md`).

## Textos prontos

### LibreArts (email de pauta)

Contato: alexandre.prokoudine@gmail.com (Aleksandr Prokudin, fundador).
Enviar em inglês, curto e factual; sem falar de IA (o repositório já
declara).

**Assunto:**

```
News tip: HQ Tools, a comics production toolkit for Krita (MIT)
```

**Corpo:**

```
Hi Aleksandr,

I would like to suggest a news tip: HQ Tools, an open-source (MIT) plugin for Krita aimed at comics production. It is not a brush pack; it adds a set of dockers to Krita:

- Screentones and hatching with real LPI (halftone as a non-destructive filter layer, per-panel masks, action and speed lines)
- Vector speech balloons and sound effects (hand-drawn kit plus a project library)
- Page manager (templates, margin guides, per-panel mask, CPMT integration)
- Brush slots with configurable shortcuts (community packs included: Deevad, Krita Watercolor Set)
- Poseable 3D mannequin viewer (camera with lenses, insert into the selection)
- Perspective grid library (9 sets, inserted as editable vector layers)
- Moodboard with linked references and a production checklist (pages and panels, weekly goal, Markdown export)
- Manual in English and Portuguese

Repository: https://github.com/ricolandia/krita-hq-tools
Latest release: https://github.com/ricolandia/krita-hq-tools/releases/latest
License: MIT, Krita 5.3.4 (prepared for Krita 6). Screenshots and short demo videos are in the README.

I am the author, a comic artist and animator from Brazil. If it fits Libre Arts, I can provide more details, images or a short walkthrough.

Thanks for your time,
Ricardo Graça
```

## Pendências

- **Topics do repositório**: **feitos** em 06/10 (11 topics aplicados via
  `gh`): `krita`, `krita-plugin`, `comics`, `comic-tools`, `webtoon`,
  `manga`, `python`, `pyqt5`, `qt`, `art-tools`, `open-source`.
- **awesome-krita**: PR **aberto** em 06/10 (armstrongl/awesome-krita#2,
  1 arquivo, +1 linha na seção Plugins), aguardando a revisão do
  mantenedor. O passo a passo abaixo fica como referência de como foi
  feito.
- **Tip para o LibreArts**: texto pronto (seção "Textos prontos"),
  aguardando o envio pelo autor para alexandre.prokoudine@gmail.com.

### awesome-krita (PR pelo editor web, sem fork local)

O `contributing.md` do repositório pede **PR com branch** (a "suggestion"
de issue é só para propor seções novas); o item vai **no fim da seção
Plugins** e a linha segue o formato `- [nome](link https) - Descrição com
maiúscula e ponto final.` O lint (`npx awesome-lint readme.md`) não acusa
nada novo (o repositório já tinha 2 erros antigos: o ToC e um item sem
ponto). A linha validada é:

```
- [HQ Tools](https://github.com/ricolandia/krita-hq-tools) - Comics production toolkit for Krita: screentones and hatching, balloons, pages, brushes, 3D viewer, perspective, moodboard and production checklist.
```

Passo a passo (o fork é criado pelo próprio GitHub, sem terminal):

1. Abra https://github.com/armstrongl/awesome-krita/blob/main/readme.md
2. Clique no lápis ("Edit this file"); o GitHub avisa que vai criar um fork.
3. No fim da seção "## Plugins" (depois da linha do Oughtasave, antes de
   "## Textures and patterns"), cole a linha acima.
4. "Commit changes..." > "Create a new branch for this commit and start a
   pull request" > branch `add-hq-tools` > "Propose changes".
5. Título do PR: `Add HQ Tools`. Corpo (sem falar de IA; a lista já tem
   plugins com IA e o assunto só desviaria o PR):

```
Adds [HQ Tools](https://github.com/ricolandia/krita-hq-tools), an open-source (MIT) comics production toolkit for Krita.

What it does: screentones and hatching (real LPI), vector balloons and sound effects, a page manager (templates, margin guides, panel mask, CPMT), brush slots with shortcuts, a poseable 3D mannequin viewer, a perspective grid library, a moodboard with linked references and a production checklist.

- License: MIT
- Krita: 5.3.4 (tested; prepared for Krita 6)
- Latest release: https://github.com/ricolandia/krita-hq-tools/releases/latest
- README with screenshots and short demo videos, manual in English and Portuguese
```

Alternativa (menos trabalho para o autor, mais para o mantenedor, e sem
garantia): abrir uma issue pedindo a inclusão, com o link e a linha pronta.
O repositório não tem formulário de issue ativo (o template existe só na
cópia `ci/`), então seria uma issue em texto simples.

**Tom e conduta:** o repositório adota o Contributor Covenant 2.0
(comportamento respeitoso, sem assédio nem ataques; o contato de denúncia
ficou no placeholder do template). O PR deve ter tom neutro e objetivo, sem
debate de IA e sem autopromoção exagerada; se o mantenedor recusar ou pedir
ajustes, responder com tranquilidade, porque o próprio código dá a ele o
direito de recusar contribuições.

Se um dia o caminho pelo terminal voltar a interessar: o clone local está em
`~/Documentos/32_APPS_GITHUB_contribuicoes/Krita_Awesome`, na branch
`add-hq-tools`, com o commit "Add HQ Tools to Plugins" pronto (basta criar o
fork e apontar o remoto).

## Log de postagens

| Data | Canal | O que foi | Retorno |
|---|---|---|---|
| 06/10/2026 | GitHub (topics) | 11 topics aplicados no repositório (via `gh`) | descoberta/SEO na busca do GitHub |
| 06/10/2026 | awesome-krita | PR #2 (armstrongl/awesome-krita#2): uma linha na seção Plugins, formato validado com `awesome-lint` | aguardando revisão do mantenedor (só um bot de diff comentou) |
