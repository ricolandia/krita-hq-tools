# Comparativo com outros softwares de quadrinhos (19/10/2026)

O autor vai criar mais balões, caudas, onomatopeias e poses. Este documento
olha para os softwares de quadrinhos mais usados para separar o que o Krita e
o HQ Tools já cobrem, o que vale trazer e o que deve ficar fora.

**Critério de entrada:** o recurso amplia o controle do artista, não decide
arte por ele; é viável no libkis/PyQt sem dependência nova; funciona igual no
Krita 5.3.4 e no 6.0.4. Recurso que só existe para "automatizar a página" fica
de fora por princípio, como o lettering automático descartado em 19/10.

## Resumo dos softwares

- **Clip Studio Paint (CSP, PRO/EX):** ferramenta de balão com camada própria e
  cauda, molduras de painel (frame border folders) que recortam o desenho,
  divisão de painéis, templates, gerenciamento de páginas no EX, figuras 3D
  ajustáveis com pose scanner por foto e hand scanner, catálogo enorme de
  materiais, texto com justificar/kerning/texto em círculo, exportação PDF/ePub
  e prévia de webtoon no celular.
- **MediBang Paint:** divisão de painéis (Panel Divide), materiais e retículas,
  várias páginas num arquivo só, nuvem, projeto em grupo e ferramenta de texto.
- **Comic Life 4:** foco em layout e montagem, com templates, balões de várias
  caudas, legendas, lettering em caminho, editor de roteiro (SmartScript),
  painéis que recortam o conteúdo, páginas espelhadas e exportação PDF/ePub.
- **Krita nativo:** ferramenta de edição de painéis (5.3: corte com gutter e
  junção), templates de quadrinhos, camadas vetoriais e assistentes de
  perspectiva/simetria.
- **HQ Tools:** balões, onomatopeias e perspectivas; visualizador 3D com poses
  de corpo e mãos; retículas e linhas de efeito; paletas; pincéis; moodboard;
  páginas (CPMT); produção; exportação PNG/JPG.

## Comparação por eixo

| Eixo | CSP | MediBang | Comic Life | Krita nativo | HQ Tools | Leitura |
|---|---|---|---|---|---|---|
| Painéis | molduras com recorte, divisão, templates | divisão e materiais | templates, recorte automático | ferramenta de corte/junção (5.3) | grade do roteiro + máscara no grupo "Arte" | coberto no básico; falta layout fora da grade e regenerar a máscara |
| Balões e caudas | camada de balão, cauda, texto junto | balões e materiais | balões com várias caudas, formas | vetor livre | SVG do kit, inserção por seleção | coberto; o acervo é conteúdo do autor |
| Lettering | justificar, kerning, círculo, fontes | texto simples | lettering em caminho, 3D | texto básico | fontes do kit instaladas | **fora**: lettering é decisão manual |
| SFX e linhas de efeito | pincéis e efeitos | materiais | lettering de SFX | pincéis | onomatopeias e linhas de efeito | coberto; ampliar é conteúdo |
| Retículas | materiais e tons | materiais e tons | preenchimentos | filtros e padrões | retículas e efeitos | coberto |
| Poses e 3D | figuras ajustáveis, pose scanner, hand scanner | não tem | não tem | não tem nativo | visualizador próprio, poses, mãos, salvar pose | forte; falta organização do acervo e bundle |
| Materiais e acervo | catálogo com busca | catálogo | biblioteca de elementos | símbolos | pastas locais e packs | **lacuna**: navegação e importação em lote |
| Páginas e produção | EX gerencia páginas | várias páginas num arquivo | organizador de páginas | CPMT | gerenciador + produção + exportação | coberto e mais forte no checklist |
| Exportação | PNG, PDF, ePub, webtoon | PNG, PSD | PNG, PDF, ePub | PNG, JPG, PDF por filtro | PNG/JPG (mergedimage) | coberto para imagem; PDF/ePub ficam no Scribus/CPMT |
| Webtoon | ferramentas próprias | básico | não tem | manual | fora de escopo | fora |
| Nuvem e colaboração | assets e sync | nuvem e grupo | não tem | não tem | local | fora |

## O que vale trazer (ordenado pelo acervo)

1. **Acervo navegável.** Hoje os dockers de balões, onomatopeias e biblioteca
   leem uma pasta plana (`os.listdir`) e mostram uma grade. Com dezenas de
   itens funciona, com centenas vira rolagem. Busca por nome, filtro por tipo e
   favoritos resolvem sem gerar conteúdo nem decidir arte. É a melhoria mais
   alinhada ao "vou criar mais balões, caudas, onomatopeias e poses".
2. **Importação em lote com validação.** Apontar uma pasta e trazer vários
   SVGs/PNGs de uma vez, gerando miniatura, conferindo formato e nome, e
   listando o que entrou e o que foi recusado. A biblioteca já relê uma pasta;
   falta o pacote de importação e o relatório.
3. **Organização das poses.** Categorias (corpo/mãos já existem), busca,
   favoritos e exportar/importar a biblioteca própria (o "bundle" que já está
   no roadmap). Mais poses continuam sendo conteúdo do autor.
4. **Painéis fora da grade e regeneração da máscara.** O gerador monta a página
   em grade; a ferramenta nativa do Krita cobre corte e junção, mas editar os
   painéis depois deixa a máscara do grupo "Arte" desatualizada. Um
   "regenerar máscara dos painéis" é pequeno e seguro. Layout irregular é
   médio e pede decisão de desenho.
5. **Cauda junto do balão (avaliar).** O kit tem caudas separadas e a inserção
   já funciona. Juntar as duas peças num clique é conveniência, mas encosta no
   balão paramétrico que o autor adiou; decidir antes de implementar.

## O que não vale trazer

- **Lettering automático** nas páginas geradas: descartado em 19/10 por
  engessar o artista.
- **Pose scanner por foto / IA**: dependência pesada e fora do escopo do
  plugin.
- **Nuvem, colaboração e webtoon**: o fluxo é local e o Batch Exporter cobre o
  webtoon.
- **PDF/ePub**: Scribus/CPMT resolvem a publicação.
- **Molduras de painel paramétricas**: a ferramenta nativa do Krita 5.3 mais a
  máscara do grupo "Arte" já cobrem o recorte.

## Recomendação

Começar pelo **acervo navegável + importação em lote**, que atende direto o
momento do autor (produzir mais peças) sem tocar no desenho. Na sequência, o
**bundle da biblioteca** e o **regenerar máscara**. O **clique direto no
canvas** continua como está no roadmap e destrava o balde e a cauda arrastável
quando entrar.

## Fontes

- CSP, balões: https://help.clip-studio.com/en-us/manual_en/540_comic/Balloons.htm
- CSP, painéis: https://help.clip-studio.com/en-us/manual_en/540_comic/Frames_and_Panels.htm
- CSP, quadrinhos: https://www.clipstudio.net/en/comics-manga/
- CSP, 3D: https://www.clipstudio.net/en/design/tool/3d/
- MediBang, criação de quadrinhos: https://medibangpaint.com/en/tutorial/pc/create-comics
- Comic Life 4: https://plasq.com/apps/comiclife4/mac
- Krita, ferramenta de painéis: https://docs.krita.org/en/reference_manual/tools/comic_panel_editing_tool.html
