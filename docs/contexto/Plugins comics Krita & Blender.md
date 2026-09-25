## Krita

**Comics Project Management Tools** (já vem com o Krita)

*   Manual dos plugins padrão: [https://docs.krita.org/reference\_manual/default\_python\_plugins.html](https://docs.krita.org/reference_manual/default_python_plugins.html)
*   README do plugin: [https://lxr.kde.org/source/graphics/krita/plugins/python/comics\_project\_management\_tools/README.md](https://lxr.kde.org/source/graphics/krita/plugins/python/comics_project_management_tools/README.md) (inclui o passo a passo: criar projeto, abrir o `comicsConfig.json`, "Add Page")
*   O manual também aparece dentro do Krita, em _Configurações > Configurar Krita > Gerenciador de plugins Python_.
*   Tutoriais de fluxo de HQ no Krita:
    *   David Revoy, "Comic page from A to Z" (1h46, com template de página e biblioteca de balões): [https://www.davidrevoy.com/article321/comic-page-from-a-to-z-with-krita/show](https://www.davidrevoy.com/article321/comic-page-from-a-to-z-with-krita/show)
    *   Série "Krita for Comics" (10 vídeos, do setup de página ao letreiramento): [https://pinnguaq.com/?p=8321](https://pinnguaq.com/?p=8321)

**Comic Panel Editing Tool**

*   Manual: [https://docs.krita.org/en/reference\_manual/tools/comic\_panel\_editing\_tool.html](https://docs.krita.org/en/reference_manual/tools/comic_panel_editing_tool.html)
*   Novidades do Krita 6.0 (texto e painéis vetoriais): [https://alternativeto.net/news/2026/3/krita-6-0-debuts-with-linux-wayland-and-hdr-support-new-text-tools-and-comic-panel-editor](https://alternativeto.net/news/2026/3/krita-6-0-debuts-with-linux-wayland-and-hdr-support-new-text-tools-and-comic-panel-editor)

**Batch Exporter.** Corrijo o que eu disse antes: ele não é da comunidade. É um plugin pré-instalado do Krita, listado no mesmo manual dos plugins padrão (link acima).

**Manga Panel Creator Pro**

*   [https://github.com/Alaxus-Megas/Manga\_panel\_\_maker\_for\_krita\_plugin](https://github.com/Alaxus-Megas/Manga_panel__maker_for_krita_plugin)
*   Tutorial: só o README. A instalação é por _Ferramentas > Scripts > Importar plugin Python_, com o ZIP do repositório.

<span style="color:hsl(0, 75%, 60%);">**InkBalloon + Comic Page Manager ( pago - $36 )**</span>

*   [<span style="color:hsl(0, 75%, 60%);">https://krita-artists.org/t/inkballoon-comic-page-manager-comic-workflow-for-krita/184807</span>](https://krita-artists.org/t/inkballoon-comic-page-manager-comic-workflow-for-krita/184807)
*   <span style="color:hsl(0, 75%, 60%);">Tutorial: o próprio tópico traz descrição e demonstrações. Não achei vídeo separado.</span>

**Rogudator's Comic Panel Generator / Speech Bubble Generator**

*   Código: [https://github.com/rogudator/rogudators\_comic\_panel\_generator](https://github.com/rogudator/rogudators_comic_panel_generator)
*   Tópico do autor, com vídeo de demonstração: [https://krita-artists.org/t/rogudators-comic-panel-generator/37060](https://krita-artists.org/t/rogudators-comic-panel-generator/37060)
*   Versões na Gumroad: painéis [https://rogudator.gumroad.com/l/UbPzz](https://rogudator.gumroad.com/l/UbPzz) · balões [https://rogudator.gumroad.com/l/bvvnn](https://rogudator.gumroad.com/l/bvvnn)

**Blender Layer** (vista 3D do Blender como camada no Krita)

*   [https://krita-artists.org/t/plugin-blender-layer-live-3d-view-in-krita/63394](https://krita-artists.org/t/plugin-blender-layer-live-3d-view-in-krita/63394)
*   Ele transmite a vista 3D do Blender para o Krita como uma camada comum. A última versão que vi é para o Krita 5.2.6, então teste no seu.

**Krita-Blender Workflow Bridge**

*   [https://krita-artists.org/t/krita-blender-workflow-bridge-plugin-make-the-transition-between-krita-and-blender-easier/108018](https://krita-artists.org/t/krita-blender-workflow-bridge-plugin-make-the-transition-between-krita-and-blender-easier/108018)
*   É voltado a ilustradores e criadores de quadrinhos, mas é experimental. Tutorial: só o tópico.

**PaintBridge Krita** (só para o caso de você querer avaliar; foco em textura, não em HQ)

*   [https://superhivemarket.com/products/paintbridge-krita](https://superhivemarket.com/products/paintbridge-krita)
*   Não funciona com o Blender 5.1.0, mas as outras versões 5.x funcionam.

**Shortcut Composer**

*   Página oficial: [https://krita-artists.org/t/shortcut-composer/55314](https://krita-artists.org/t/shortcut-composer/55314)
*   Código: [https://github.com/wojtryb/Shortcut-Composer](https://github.com/wojtryb/Shortcut-Composer)
*   Artigo introdutório, com vídeo: [https://gamefromscratch.com/improving-krita-with-shortcut-composer/](https://gamefromscratch.com/improving-krita-with-shortcut-composer/)
*   **Atenção para o Debian:** no Linux, a versão oficialmente suportada do Krita é o AppImage; rodar com Snap ou pacote da distribuição não é recomendado, e o plugin exige o Krita 5.3.0. Se usar este plugin, use o AppImage.

**Criar plugins próprios**

*   Guia oficial: [https://docs.krita.org/en/user\_manual/python\_scripting/krita\_python\_plugin\_howto.html](https://docs.krita.org/en/user_manual/python_scripting/krita_python_plugin_howto.html)
*   Lista de plugins e recursos da comunidade: [https://github.com/armstrongl/awesome-krita](https://github.com/armstrongl/awesome-krita)
*   Página geral de recursos do manual: [https://docs.krita.org/en/resources\_page.html](https://docs.krita.org/en/resources_page.html)

---

**Usabilidade**

*   Mixer Slider Docker: escolhe cores em gradientes entre a cor atual e outras selecionadas.
*   Palette Docker: gerencia paletas, com grupos e exportação para GIMP ou Inkscape.
*   Quick Settings Docker: define rapidamente opacidade, fluxo e tamanho a partir de uma lista.
*   Ten Brushes: atribui predefinições de pincel a dez atalhos.
*   Workflow Buttons: botões que combinam ferramenta, pincel, cor e script Python.

**Fluxo de trabalho**

*   **Comics Project Management Tools**: organiza as páginas, cuida dos metadados e exporta para vários formatos.
*   **Batch Exporter**: exporta camadas e grupos em vários tamanhos, formatos e pastas, e renomeia camadas rapidamente.

**Imagem e documento**

*   Assign Profile Dialog, Color Space (converte para RGBA, CMYKA ou L_a_b), Channels to Layers, Document Tools (escala, corta e gira numa ação), Filter Manager e High Pass.

**Arquivos**

*   Export Layers e Last Documents Docker.

**Scripting em Python**

*   **Krita Script Starter**: gera a estrutura de um plugin (`.desktop`, pasta, `__init__.py`, arquivo principal e manual).
*   Python Plugin Importer: instala plugins a partir de ZIP.
*   **Scripter**: console para escrever e rodar código com depuração.
*   Ten Scripts: como o Ten Brushes, mas para scripts.

Para HQ, os úteis são o <span style="color:hsl(150, 75%, 60%);">**Comics Project Management Tools**,</span> o <span style="color:hsl(150, 75%, 60%);">**Batch Exporter**</span> e o <span style="color:hsl(150, 75%, 60%);">**Color Space** (para o CMYK).</span> Para o plugin que você quer criar, o <span style="color:hsl(150, 75%, 60%);">**Script Starter** e o **Scripter**</span> economizam bastante trabalho. A <span style="color:hsl(150, 75%, 60%);">**Comic Panel Editing Tool**</span> não é plugin: é uma ferramenta nativa do Krita.

## Blender

**Grease Pencil + Line Art**

*   Referência da API do modificador (5.0): [https://docs.blender.org/api/5.0/bpy.types.GreasePencilLineartModifier.html](https://docs.blender.org/api/5.0/bpy.types.GreasePencilLineartModifier.html)
*   Manual do Blender (raiz; não achei o link direto da página do Line Art nem do Freestyle nas buscas): [https://docs.blender.org/manual/](https://docs.blender.org/manual/)
*   Curso "PANELS", HQ com Grease Pencil, com templates americano, mangá e europeu: [https://www.cgcookie.com/courses/panels-create-a-comic-book-with-grease-pencil-in-blender](https://www.cgcookie.com/courses/panels-create-a-comic-book-with-grease-pencil-in-blender) (também à venda em [https://superhivemarket.com/products/panels-create-a-comic-using-grease-pencil-in-blender](https://superhivemarket.com/products/panels-create-a-comic-using-grease-pencil-in-blender)). É pago ou por assinatura.
*   Painel de HQ inteiro no Blender (2019; usa o Grease Pencil antigo): [https://www.blendernation.com/2019/07/17/create-a-comic-panel-entirely-in-blender/](https://www.blendernation.com/2019/07/17/create-a-comic-panel-entirely-in-blender/)
*   Stream sobre diagramação de página com Grease Pencil (2023): [https://www.youtube.com/watch?v=ThqiDj37kRk](https://www.youtube.com/watch?v=ThqiDj37kRk)

Como esses materiais são anteriores ao Blender 5.x, a interface do Grease Pencil aparece diferente.

**3D Comic Toolkit (Spiraloid)**

*   [https://github.com/spiraloid/Spiraloid-Toolkit-for-Blender-3DComicToolkit](https://github.com/spiraloid/Spiraloid-Toolkit-for-Blender-3DComicToolkit)
*   Foi feito para quadrinhos 3D em navegador, não para impressão. Tutorial: só o README.

**Câmeras e marcadores (para o meu tutorial de câmeras)**

*   Vincular câmera a marcador, passo a passo (2010): [https://www.blendernation.com/2010/11/17/changing-cameras-during-an-animation-in-blender-2-5/](https://www.blendernation.com/2010/11/17/changing-cameras-during-an-animation-in-blender-2-5/)
*   Marcadores no Blender, artigo de 2025: [https://rew.it.com/how-do-you-add-markers-in-blender](https://rew.it.com/how-do-you-add-markers-in-blender)
*   Add-on _Camera Markers to Scene Strips_, com vídeo: [https://github.com/tin2tin/Camera-Markers-to-Scene-Strips/wiki](https://github.com/tin2tin/Camera-Markers-to-Scene-Strips/wiki)

**MB-Lab** (bonecos para blocagem). Corrijo minha indicação anterior.

*   [https://github.com/animate1978/MB-Lab](https://github.com/animate1978/MB-Lab)
*   É a versão final do MB-Lab, porque o desenvolvimento seguiu para o Charmorph. Ele exige o Blender 4.0 ou superior, então não sei se funciona no seu 5.2. Não achei o link do Charmorph nas buscas; procure por "CharMorph Blender".

**BlenderKit** (biblioteca de modelos e materiais)

*   Código: [https://www.github.com/BlenderKit/BlenderKit](https://www.github.com/BlenderKit/BlenderKit)
*   Documentação: [https://github.com/BlenderKit/Blendkit/wiki/BlenderKit-add-on-documentation/0cc6685f1549440e0285b88cccdd2beb50bf6462](https://github.com/BlenderKit/Blendkit/wiki/BlenderKit-add-on-documentation/0cc6685f1549440e0285b88cccdd2beb50bf6462)
*   Tem plano gratuito e plano pago com mais conteúdo.

## Outras ferramentas

**Storyboarder**

*   Site: [https://wonderunit.com/storyboarder/](https://wonderunit.com/storyboarder/) (o download é por envio de e-mail)
*   Código: github.com/wonderunit/storyboarder
*   Curso "How to Use Storyboarder", com aulas de desenho, linha do tempo, importação e exportação: [https://2danimation101.teachable.com/courses/666455/lectures/11883374](https://2danimation101.teachable.com/courses/666455/lectures/11883374) (pode exigir cadastro)
*   A versão mais recente que vi é a 3.0, de fevereiro de 2021, o que reforça que o desenvolvimento é lento. Não confunda com o storyboarder.ai, que é outro produto.

**Scribus**

*   Site: [https://www.scribus.net/](https://www.scribus.net/)
*   Artigo introdutório sobre diagramação com Scribus: [https://opensource.com/article/21/12/desktop-publishing-scribus](https://opensource.com/article/21/12/desktop-publishing-scribus)
*   Guia de instalação por AppImage e template: [https://wiki.ufal.ms.mff.cuni.cz/scribus](https://wiki.ufal.ms.mff.cuni.cz/scribus)

Se quiser, posso montar uma ordem de teste (o que instalar primeiro e o que descartar) com base nesses links.