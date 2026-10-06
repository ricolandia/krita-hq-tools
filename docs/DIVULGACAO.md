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

## Pendências

- **Topics do repositório** (na UI do GitHub: About > engrenagem > Topics):
  `krita`, `krita-plugin`, `comics`, `comic-tools`, `webtoon`, `manga`,
  `python`, `pyqt5`, `qt`, `art-tools`, `open-source`.
- **PR no awesome-krita** (adicionar o HQ Tools na seção Plugins).
- **Tip para o LibreArts**.

## Log de postagens

| Data | Canal | O que foi | Retorno |
|---|---|---|---|
| | | | |
