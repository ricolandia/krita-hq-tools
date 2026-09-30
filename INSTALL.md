# Instalação do HQ Tools (guia do usuário)

Passo a passo para instalar o plugin em qualquer máquina com Krita. Se você
já tem o repositório e quer desenvolver, veja `scripts/install-dev.sh` e o
`README.md`; este guia é para quem vai só usar.

## Requisitos

- Krita 5.3.4 ou mais novo (AppImage, Flatpak ou pacote da distribuição).
- O plugin é testado no Krita 5.3.4; há preparação para o Krita 6 (PyQt6),
  mas a validação completa no 6 ainda não foi feita.
- Um ZIP de release (`hq_tools-<versão>.zip`) baixado da página de releases.

## Instalação rápida (ZIP)

1. Baixe o arquivo `hq_tools-<versão>.zip` da página de releases.
2. No Krita: Ferramentas > Scripts > **Importar plugin Python desde arquivo...**
   e escolha o ZIP.
3. Em Configurar Krita > **Gerenciador de plugins Python**, marque **HQ Tools**.
4. Feche e reabra o Krita.
5. Os 7 dockers aparecem em Configurações > Dockers com o prefixo "HQ Tools":
   retículas, balões, onomatopeias, paletas, páginas, pincéis e biblioteca.
   Para agrupá-los como abas de um mesmo painel, arraste um docker sobre o
   outro (o Krita junta automaticamente; desagrupar é só arrastar de volta).
6. Atalhos de pincel (opcional): descompacte o ZIP, copie o arquivo
   `hq_tools.action` para a pasta `actions` do Krita (veja a tabela de pastas
   abaixo) e reinicie. Os atalhos aparecem em Configurar Krita > Atalhos >
   Scripts > HQ Tools (pincel 1 a 16).

## Instalação manual (sem o diálogo de importação)

Copie para a pasta de plugins Python do Krita:

- a pasta `hq_tools` e o arquivo `hq_tools.desktop` para a pasta `pykrita`;
- o arquivo `hq_tools.action` para a pasta `actions`.

Depois ative o plugin no Gerenciador de plugins Python e reinicie o Krita.

## Pastas do Krita por tipo de instalação

| Tipo de instalação | `pykrita` | `actions` |
|---|---|---|
| AppImage / pacote comum | `~/.local/share/krita/pykrita/` | `~/.local/share/krita/actions/` |
| Flatpak | `~/.var/app/org.kde.krita/data/krita/pykrita/` | `~/.var/app/org.kde.krita/data/krita/actions/` |

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
gerenciador de plugins) e no `README.md` do projeto.

## Onde o plugin guarda os dados

Tudo em `~/.local/share/krita/hq_tools/` (ou `~/.var/app/org.kde.krita/data/
krita/hq_tools/` no Flatpak):

| Dado | Pasta |
|---|---|
| Configuração e presets de retícula do usuário | `~/.local/share/krita/hq_tools/` (`config.json`, `screentone_presets.json`) |
| Balões e onomatopeias próprios | `~/.local/share/krita/hq_tools/balloons/` e `onomatopeias/` |
| Modelos de página | `~/.local/share/krita/hq_tools/modelos/` |
| Fontes de HQ instaladas | `~/.local/share/fonts/hq_tools/` |
| Padrões do kit (tom com padrão) | `~/.local/share/krita/patterns/` |
| Paletas instaladas | `~/.local/share/krita/palettes/` |
| Packs de pincel da comunidade | `~/.local/share/krita/{paintoppresets,brushes,patterns,palettes}` |

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
- **Atalhos de pincel não aparecem**: quem instalou pelo ZIP precisa copiar
  o `hq_tools.action` para a pasta `actions` (passo 6 da instalação rápida).
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