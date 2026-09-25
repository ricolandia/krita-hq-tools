## Checklists e pipelines para HQ com software livre

### Comparando com as outras duas respostas

As duas concordam com o essencial: Krita como base, Blender como apoio, Python para plugins. Mas há pontos que corrigi ou que não consegui confirmar:

*   **"Krita Blender Workflow Bridge só funciona no Windows" (2ª resposta):** o plugin existe e é voltado a ilustradores e criadores de quadrinhos, mas o autor o descreve como experimental. Ele facilita a passagem do esboço no Krita para cenas 3D no Blender e a volta. A restrição ao Windows não apareceu no que li, então teste no Debian antes de contar com ele.
*   **"Krita Tile Grid" e "Mojo Moo for comics" (2ª resposta):** não achei confirmação nas buscas. Trate como não verificados.
*   **Storyboarder importando PSD do Krita (2ª resposta):** não confirmei. O caminho seguro é PNG.
*   **"CPMT importa os renders" (1ª resposta):** o Comics Project Management Tools organiza páginas, metadados e exportação, não importa renders do Blender. Você coloca as imagens como camadas nas páginas.
*   **"Fluxo centrado no Blender" (1ª resposta):** é uma opinião defensável, mas não a única. Discordo em parte, como explico no final.
*   **Screentones no Krita (1ª resposta):** o Krita tem filtro de meio-tom (halftone), mas sem a biblioteca de retículas do Clip Studio Paint. Vale testar com o seu estilo.

Acrescentei o que as duas deixaram de fora: **Blender Layer** e **PaintBridge**, que verifiquei.

### Checklist de plugins do Krita

**Já vem com o Krita (ative em** _**Configurações > Gerenciador de plugins Python**_**):**

*   Comics Project Management Tools (docker de projeto, templates, exportação CBZ/EPUB/PDF)
*   Comic Panel Editing Tool (painéis e sarjetas em camada vetorial)
*   Ferramenta de texto do Krita 6 (edição no canvas, OpenType)
*   Assistentes de perspectiva e estabilizadores de traço

**Comunidade, para testar:**

*   **Manga Panel Creator Pro** (MIT): automatiza painéis, pastas e camadas de máscara.
*   **InkBalloon + Comic Page Manager**: balões de fala mais um gerenciador de páginas. Lançamento recente, teste a estabilidade.
*   **Rogudator's Comic Panel / Speech Bubble Generator**: dockers de painéis e balões, distribuídos via Gumroad.
*   **Blender Layer**: transmite a vista 3D do Blender para o Krita como uma camada normal, sobre a qual você pode desenhar, mudar o modo de mesclagem e aplicar estilos. A última atualização que vi é de 2023 (Krita 5.2.6), então confirme compatibilidade com o seu Krita.
*   **Krita-Blender Workflow Bridge**: experimental, veja acima.
*   **Krita Batch Exporter**: exporta camadas e grupos em lote, com escala e corte. Útil para entregar páginas.
*   **Shortcut Composer**: atalhos complexos.

**Ressalva:** o **PaintBridge Krita** é um link ao vivo Blender-Krita, mas focado em pintura de texturas em UV, não em quadrinhos. Não é o que você precisa.

### Checklist de add-ons do Blender

**Nativo (sem instalar nada):**

*   **Grease Pencil** com modificador **Line Art** (contornos automáticos a partir de geometria 3D)
*   **Freestyle** (linhas no render, para saída raster)
*   Câmeras ortográficas e de perspectiva, com uma câmera por painel
*   Compositor (mesclar passes de linha, profundidade e sombra)
*   Extensões e Python (`bpy`) para automação

**Para procurar (não verifiquei versões atuais):**

*   Add-ons de balões e letreiramento, como o **3D Comic Toolkit** (Spiraloid), pensado para quadrinhos 3D em web, não impressão
*   Bibliotecas de manequins e poses (ex.: MB-Lab, ou rigs livres)
*   Add-ons de cenário e perspectiva (ex.: BlenderKit para assets)

Um curso de HQ com Grease Pencil monta uma página padrão americana com áreas de corte e segurança e uma câmera por página ligada a marcadores da linha do tempo. Vale ver como referência para o seu setup por script.

### Pipeline A: Blender → Krita (desenhar por cima)

1.  **Roteiro e thumbnails** (papel ou Krita, rápido).
2.  **Blocagem no Blender:** um arquivo por página ou por capítulo, uma câmera por painel, com a proporção do painel.
3.  **Renders de apoio** por painel: linha (Freestyle ou Line Art), profundidade e um passe de sombra simples.
4.  **Krita, um arquivo** `**.kra**` **por página** (via CPMT), com o painel montado pelo Comic Panel Editing Tool ou Manga Panel Creator.
5.  **Importar o render** como camada de referência (opacidade baixa, travada) dentro de cada painel.
6.  **Lápis, arte-final e cor** em camadas próprias, sobre a referência.
7.  **Balões e texto** (InkBalloon ou ferramenta de texto).
8.  **Exportar:** PNG/PDF para web via CPMT, PDF ou TIFF para impressão. Se precisar de CMYK, confira o resultado no Scribus ou no seu fluxo de gráfica, porque o suporte no Krita pode exigir cuidado.

Um script Python no Blender que renderiza todas as câmeras com nomes previsíveis (`p01_q03_linha.png`) economiza muito aqui.

### Pipeline B: centrado no Blender

1.  Blocagem 3D e câmeras por painel.
2.  Arte-final com **Grease Pencil** (linhas vetoriais desenhadas no espaço 3D ou Line Art).
3.  Cor e sombra com materiais ou fills do Grease Pencil.
4.  Balões e texto com curvas/objetos de texto (mais trabalhoso).
5.  Render por painel ou por página, e montagem da página.
6.  **Krita ou GIMP** apenas para retoques, meio-tom e finalização.

É o caminho de maior automação, mas o mais custoso se o seu estilo depende de traço à mão e textura de pincel.

### Pipeline C: Blender → papel (nanquim e aquarela)

1.  **Blocagem no Blender**, como no pipeline A, mas pensando em **impressão de referência**.
2.  **Imprimir o render em papel de calco ou papel comum** na escala real do painel. Duas opções:
    *   Mesa de luz: desenhar o lápis por cima.
    *   Imprimir em tom claro num papel de gramatura adequada e entintar em cima (se o papel aguentar a água, para aquarela).
3.  **Lápis** sobre a base, corrigindo proporção e expressão que o 3D não dá.
4.  **Nanquim** (pena ou pincel). Deixar secar bem.
5.  **Aquarela** sobre a arte-final. Use tinta à prova d'água, ou teste antes: alguns nanquins borram.
6.  **Escanear** em alta resolução (600 dpi, ou 300 dpi mínimo se for só impressão).
7.  **Krita:** limpar, corrigir níveis e cor, separar a linha da cor, se quiser.
8.  **Balões e letreiramento** digitalmente (InkBalloon ou ferramenta de texto), **Scribus** para a página final e o PDF de impressão.

Duas decisões práticas: se a aquarela for feita em papel especial, a base do Blender deve ser passada à mesa de luz, não impressa direto. E vale escanear cada painel separado ou a página inteira, conforme o tamanho do papel e do scanner.

### O que eu recomendaria

Comece pelo **pipeline A** numa página de teste e avalie: quanto tempo o Blender economiza de fato, e se o Krita basta para balões e painéis. Quem quer o traço orgânico do nanquim provavelmente ficará com **A + C**, usando o mesmo Blender como base. O pipeline B só compensa se o estilo for mais gráfico e você quiser automatizar bastante.