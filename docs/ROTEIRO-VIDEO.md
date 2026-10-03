# Roteiro do vídeo (demo do HQ Tools)

Vídeo de apresentação do plugin para a release, o README, o site e as redes.
Cenas gravadas no Krita 5.3.4 com o HQ Tools instalado, sem voz, com texto
curto na tela. Duração alvo: 90 segundos (mínimo 60, máximo 120).

- Formato: 16:9, 1920 x 1080, 30 fps.
- Áudio: sem voz; música leve com licença livre (ou sem áudio).
- Texto na tela: PT; a versão EN é o mesmo vídeo com as cartelas trocadas.
- Destino: Bunny Stream (player) com capa clicável no README PT/EN.

## Preparação

- Krita 5.3.4 com os 8 dockers agrupados como abas num painel à direita
  (retículas, balões, onomatopeias, paletas, páginas, pincéis, biblioteca, 3D).
- Projeto de demonstração aberto: uma página de HQ com arte simples (sem dados
  de clientes), salva numa pasta, para o gerenciador e a biblioteca já terem o
  que mostrar.
- Deixar prontos: um balão e uma onomatopeia do kit na biblioteca, uma camada
  de tom para a retícula e o docker 3D já carregado (pose padrão).
- Janela em 1920 x 1080, mesmo tema do início ao fim, notificações silenciadas,
  barra de tarefas escondida, cursor visível.
- Gravação: OBS (ou Kooha) em 30 fps, 1080p; pausar 1 s antes e depois de cada
  ação; agir devagar; cortar as esperas na edição.

## Cenas

| Tempo | Cena | O que fazer | Texto na tela |
|---|---|---|---|
| 0:00-0:06 | Abertura | Ícone do plugin em fundo limpo, sem cliques | HQ Tools / ferramentas de quadrinhos para Krita |
| 0:06-0:20 | Retículas | Docker "HQ Tools: retículas": escolher "Sombra média 60 LPI" e "Aplicar retícula"; dar zoom na célula; "Editar selecionada", mudar o LPI e aplicar | Retículas com LPI real, sem sair do Krita |
| 0:20-0:33 | Balões e biblioteca | Docker de balões: duplo clique num balão e numa onomatopeia; docker "Biblioteca do projeto": salvar um recurso e mostrar Renomear/Duplicar/Apagar | Balões, onomatopeias e a sua biblioteca |
| 0:33-0:45 | Páginas | Docker de páginas: "Criar próxima página" (A4, 300 dpi, grade 2x2); mostrar a miniatura na grade e as guias de margem | Página nova com formato, guias e grade |
| 0:45-0:55 | Pincéis | Docker de pincéis: alternar os conjuntos e ativar um pincel; aba "Packs" com um pack instalado | Pincéis em conjuntos e slots, com packs da comunidade |
| 0:55-1:25 | Visualizador 3D | Docker "HQ Tools: 3D": Corpo = Mulher; Pose = Idle (mãos fechadas); arrastar para orbitar; clique na coxa e dobrar o joelho; Estilo = Contorno e depois Silhueta; Shift+arraste para enquadrar; "Inserir como referência"; traçar um traço por cima da referência | Manequim 3D posável como referência / clique na região e ajuste a junta / insira travado e trace por cima |
| 1:25-1:30 | Fechamento | Ícone e URL na tela | Grátis e MIT / github.com/ricolandia/krita-hq-tools |

## Cartelas em inglês (mesmo vídeo)

| Cena | Texto |
|---|---|
| Abertura | HQ Tools / comic tools for Krita |
| Retículas | Screentones with real LPI, right inside Krita |
| Balões e biblioteca | Balloons, sound effects and your own library |
| Páginas | New pages with format, guides and grid |
| Pincéis | Brushes in sets and slots, plus community packs |
| Visualizador 3D | Posable 3D mannequin as reference / click a region and adjust the joint / insert it locked and trace over it |
| Fechamento | Free and MIT / github.com/ricolandia/krita-hq-tools |

## Pós-produção

- Cortes secos entre cenas; nada de filtros que mudem o visual do plugin.
- Cartelas com fonte limpa (sans-serif), 1 a 2 s cada, fundo escuro ou claro
  conforme o trecho.
- Música: trilha CC0/CC-BY curta e baixa (ou sem áudio).
- Exportar H.264 MP4, 1080p, ~8 Mbps; assistir inteiro antes de subir.
- Capa: usar a captura `Screenshots/07-3d.png` (ou um quadro do vídeo) com o
  título.
- Subir no Bunny Stream; guardar o link do player e do MP4.
- No README PT/EN, capa clicável apontando para o player:
  `[![Assista ao demo](Screenshots/07-3d.png)](URL_DO_PLAYER)`.

## Checklist antes de gravar

- [ ] Plugin na versão que está sendo divulgada e Krita reiniciado.
- [ ] Dockers agrupados e no mesmo lugar durante todo o vídeo.
- [ ] Documento demo sem nomes de clientes.
- [ ] Notificações e atualizações silenciadas; nada de pop-up.
- [ ] Testar um trecho de 10 s antes de gravar o vídeo inteiro.
- [ ] Guardar o bruto e o projeto de edição.
