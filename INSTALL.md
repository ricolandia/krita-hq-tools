# Instalação do HQ Tools (guia do usuário)

Passo a passo para instalar o plugin em qualquer máquina com Krita. Se você
já tem o repositório e quer desenvolver, veja `scripts/install-dev.sh` e o
`README.md`; este guia é para quem vai só usar.

## Requisitos

- Krita 5.3.4 ou mais novo (AppImage, Flatpak ou pacote da distribuição).
- O plugin é testado no Krita 5.3.4; há preparação para o Krita 6 (PyQt6),
  mas a validação completa no 6 ainda não foi feita.
- Um ZIP de release (`hq_tools-<versão>.zip`) baixado da página de releases.
- **O visualizador 3D não tem dependências extras**: os modelos e as poses vão
  dentro do ZIP e o plugin lê tudo em Python puro (sem numpy). O Blender é
  usado só pelo autor para gerar os arquivos a partir dos FBX; não é preciso
  instalá-lo, nem ter internet.

## Instalação rápida (ZIP)

1. Baixe o arquivo `hq_tools-<versão>.zip` da página de releases.
2. No Krita: Ferramentas > Scripts > **Importar plugin Python desde arquivo...**
   e escolha o ZIP.
3. Em Configurar Krita > **Gerenciador de plugins Python**, marque **HQ Tools**.
4. Feche e reabra o Krita.
5. Os 12 dockers aparecem em Configurações > Dockers com o prefixo "HQ Tools":
   retículas, balões, onomatopeias, paletas, páginas, pincéis, biblioteca,
   3D, perspectiva, moodboard, produção e hub.
   Para agrupá-los como abas de um mesmo painel, arraste um docker sobre o
   outro (o Krita junta automaticamente; desagrupar é só arrastar de volta).
6. Atalhos de pincel (opcional): descompacte o ZIP, copie o arquivo
   `hq_tools.action` para a pasta `actions` do Krita (veja a tabela de pastas
   abaixo) e reinicie. Os atalhos aparecem em Configurar Krita > Atalhos >
   Scripts > HQ Tools (pincel 1 a 16).
7. Ícone do plugin (opcional, Linux): para o ícone aparecer no Gerenciador de
   plugins Python, copie o PNG de `<pykrita>/hq_tools/resources/icon-256.png`
   para `~/.local/share/icons/hicolor/256x256/apps/hq_tools.png` e reinicie o
   Krita. No Windows e no macOS o ícone do gerenciador depende do tema.

## Instalação manual (sem o diálogo de importação)

Copie para a pasta de plugins Python do Krita:

- a pasta `hq_tools` e o arquivo `hq_tools.desktop` para a pasta `pykrita`;
- o arquivo `hq_tools.action` para a pasta `actions`.

Depois ative o plugin no Gerenciador de plugins Python e reinicie o Krita.

## Pastas do Krita por tipo de instalação

| Tipo de instalação | `pykrita` | `actions` |
|---|---|---|
| AppImage / pacote comum (Linux) | `~/.local/share/krita/pykrita/` | `~/.local/share/krita/actions/` |
| Flatpak | `~/.var/app/org.kde.krita/data/krita/pykrita/` | `~/.var/app/org.kde.krita/data/krita/actions/` |
| Windows | `%APPDATA%\krita\pykrita\` | `%APPDATA%\krita\actions\` |
| macOS | `~/Library/Application Support/krita/pykrita/` | `~/Library/Application Support/krita/actions/` |

## Primeiros passos

1. **Retícula**: no docker "HQ Tools: retículas", escolha um preset e clique
   em "Aplicar retícula". O plugin usa o DPI do documento para a conta de
   célula; marque "Usar a seleção ativa" para limitar ao painel.
2. **Balão**: duplo clique num modelo insere no grupo ativo; o botão
   "Instalar fontes de HQ" copia as fontes do kit para o sistema.
3. **Páginas**: salve a página em uma pasta, use "Novo projeto..." e depois
   "Criar próxima página" para continuar a sequência com guias de margem.
4. **Pincéis**: clique no cartão para ativar; botão direito atribui ao slot
   (16 slots com atalhos).

O manual completo de uso fica em `hq_tools_manual.html` (mostrado no próprio
gerenciador de plugins) e no `README.md` do projeto. Versões em inglês:
`hq_tools_manual.en.html` e `INSTALL.en.md`.

## Idioma da interface

Os dockers seguem o idioma do sistema (o Krita segue o locale por padrão):
qualquer locale de português usa português; o resto usa inglês. Para forçar um
idioma, defina a variável de ambiente `HQ_TOOLS_IDIOMA` como `pt` ou `en`
antes de abrir o Krita.

## Onde o plugin guarda os dados

Na pasta de dados do Krita, que muda por sistema:

| Sistema | Pasta base |
|---|---|
| Linux | `~/.local/share/krita/` (Flatpak: `~/.var/app/org.kde.krita/data/krita/`) |
| Windows | `%APPDATA%\krita\` |
| macOS | `~/Library/Application Support/krita/` |

Dentro dela:

| Dado | Pasta |
|---|---|
| Configuração e presets de retícula do usuário | `hq_tools/` (`config.json`, `screentone_presets.json`) |
| Balões e onomatopeias próprios | `hq_tools/balloons/` e `hq_tools/onomatopeias/` |
| Modelos de página | `hq_tools/modelos/` |
| Fontes de HQ instaladas | Linux: `~/.local/share/fonts/hq_tools/` · Windows: `%LOCALAPPDATA%\Microsoft\Windows\Fonts` (registro em HKCU) · macOS: `~/Library/Fonts` |
| Padrões do kit (tom com padrão) | `patterns/` |
| Paletas instaladas | `palettes/` |
| Packs de pincel da comunidade | `{paintoppresets,brushes,patterns,palettes}` |

## Kit que acompanha o plugin

- 12 famílias de fontes de HQ (SIL OFL 1.1), instaláveis com um clique;
- balões de domínio público (CC0/PD) copiados na primeira execução;
- 11 padrões e texturas próprios (papéis, retículas, hachuras), instaláveis
  no docker de retículas;
- packs de pincéis da comunidade (Deevad v8.2, CC-BY 4.0 e Krita Watercolor
  Set, CC-0), instaláveis na aba "Packs" do docker de pincéis.

Créditos e licenças completos em `CREDITS.md`. Tudo que é instalado nos
recursos do Krita (fontes, padrões, paletas, packs) exige reiniciar o
programa para aparecer.

## Desinstalação

1. Em Configurar Krita > Gerenciador de plugins Python, desmarque HQ Tools.
2. Remova os arquivos copiados: `hq_tools` e `hq_tools.desktop` da pasta
   `pykrita`, e `hq_tools.action` da pasta `actions`.
3. Para apagar também os dados do usuário, remova
   `~/.local/share/krita/hq_tools/` (cuidado: apaga presets, balões próprios,
   onomatopeias e modelos). Fontes, padrões e packs instalados nas pastas de
   recursos do Krita podem ser removidos manualmente se não quiser mais.

## Solução de problemas

- **Docker não aparece na listagem**: confira se HQ Tools está marcado no
  Gerenciador de plugins Python e reinicie o Krita. Erros de importação na
  inicialização aparecem em Ferramentas > Scripts > Scripter (aba Python).
- **Atalhos de pincel não aparecem**: o importador do Krita (ZIP de 0.12.3 em
  diante) já coloca o `hq_tools.action` na pasta `actions`; em ZIPs antigos,
  copie o arquivo manualmente.
- **"Nenhum arquivo encontrado no arquivo morto" ao importar o ZIP**: é um
  defeito dos ZIPs até a 0.12.2 (faltava a entrada de diretório do módulo);
  baixe a release 0.12.3 ou mais nova.
- **Fontes/padrões/paletas novas não aparecem**: o Krita lê os recursos na
  inicialização; reinicie depois de instalar qualquer item do kit.
- **Pincel dos packs não aparece**: confira se a aba "Packs" marca
  "[instalado]" e reinicie; os presets ficam na lista de pincéis do Krita
  com o nome interno do pack.
- **Um preset que estava na lista sumiu**: três presets foram retirados do kit
  (`deevad 2d expressive thin`, `deevad 6n stamp floor particles` e
  `X9AI_WC_Scattered_Sharp`). Os três apontavam para texturas que os autores
  dos packs não distribuíram, então o preset instalava e o pincel não carregava.
  Quem instalou uma versão anterior pode apagá-los da pasta de pincéis do
  plugin; o motivo está no `FONTE.md` de cada pack.
- **Projeto do CPMT não abre**: o plugin lê o `comicConfig.json` (sem "s")
  em UTF-16, o padrão do Comics Project Management Tools embutido no Krita;
  a variante antiga `comicsConfig.json` (UTF-8) também é aceita.

## Licença

Código em MIT. Recursos de terceiros (fontes, balões, packs) com licenças
próprias documentadas em `CREDITS.md`. O plugin usa recursos nativos do
Krita (gerador Screentone e filtro Halftone de Deif Lou, e o Comics Project
Management Tools do time do Krita), sem redistribuí-los.