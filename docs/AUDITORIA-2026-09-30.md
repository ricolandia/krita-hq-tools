# Auditoria de 2026-09-30

Auditoria do HQ Tools feita por quatro especialistas (correção, desempenho,
robustez, testes/documentação), com os achados aplicados em quatro lotes. Este
documento é o índice do que foi encontrado, do que foi corrigido e do que
continua aberto. O changelog tem o detalhe por lote; aqui fica o mapa.

**Estado:** 177 testes verdes, com e sem PyQt instalado. **Nenhuma correção foi
validada dentro do Krita ainda** (ver *Validação pendente* no fim), então a
versão não sobe de 0.6.2.

## Como a auditoria foi feita

Quatro frentes, cada uma lendo o código com um foco, e depois o achado foi
confirmado antes de virar mudança:

1. **Correção** — o que quebra o autor: dado sobrescrito, ação irreversível,
   exceção derruba o plugin.
2. **Desempenho** — o que trava a interface: laço na thread da interface,
   reconstrução de cache do sistema, refazer o mesmo trabalho.
3. **Robustez** — o que quebra na máquina do autor: exceção engolida, caminho
   inacessível, arquivo em outra codificação.
4. **Testes e documentação** — o que não estava coberto, e o que o README
   promete e o código não cumpre.

Regra de ouro: **reproduzir o defeito antes de corrigir**. Achado que não dava
para escrever teste ficou anotado como pendência em vez de virar mudança por
convicção.

## Lote A — dados do autor

O achado mais grave da auditoria: em três pontos o plugin escrevia por cima do
trabalho do autor sem aviso.

| Achado | Onde | Gravidade |
|---|---|---|
| Criar projeto em pasta existente sobrescreve `comicConfig.json` | `core/cpmt.py` | crítica |
| `.cpmt` escrito por cima; falha no meio deixa arquivo pela metade | `core/cpmt.py` | crítica |
| Preset do autor alterado sem releitura; JSON ilegível vira erro fatal | `modules/screentone` | alta |
| Pack sobrescreve destino e só depois faz backup | `modules/brushes/packs.py` | alta |
| Página duplicada some do modelo em falha de escrita (`.kra` órfão) | `modules/pages` | alta |
| Biblioteca criada sem `present_document`, fica escondida | `plugin.py` | média |

Correção: reler antes de alterar, escrever em temporário e trocar, backup do
anterior, e o que não dá para salvar vira `.bak` em vez de ser apagado.

## Lote B — isolamento, desfazer, frequência

| Achado | Onde | Gravidade |
|---|---|---|
| Um docker com erro no import derrubava **os sete** | `plugin.py` | crítica |
| Caminhos do registro errados (`screentone.docker`), registro nunca funcionava | `plugin.py` | crítica |
| `screentone` importado no topo do plugin | `plugin.py` | alta |
| Retícula, efeito, balão e onomatopeia fora de macro de desfazer | 4 módulos | alta |
| `showFloatingMessage` com `priority` errado (4º argumento) | 3 módulos | média |
| LPI↔LPC convertido duas vezes; ID de edição do alvo não limpo | `screentone` | média |
| Seleção vazia não detectada (`byteCount()`) | `screentone/effects` | média |
| Pasta de preset inacessível / arquivo em Latin-1 derrubavam a ação | `screentone` | média |
| `compat.py` só tentava PyQt5 e caía para o outro binding | `core/compat.py` | média |

A correção do registro de módulos e do import tardio do `screentone` merece
nota: o `screentone` era importado no topo do `plugin.py`, ou seja, o plugin
dependia do módulo mais pesado para carregar. Agora ele entra quando as ações
são criadas, dentro de try/except.

O `qt_probe` nasceu do achado do `compat.py`: a escolha de binding virou uma
função testável, com a ordem de decisão explícita (Krita, depois processo,
depois instalação).

## Lote C — desempenho

O achado mais caro da auditoria, e o mais fácil de não ver: **o gerenciador de
páginas decodifica uma miniatura por item a cada refresh**, na thread da
interface. Trocar de pasta, reordenar, criar ou excluir página dispara tudo de
novo; um projeto de 40 páginas são 40 aberturas de `.kra` e 40 decodificações
de `preview.png` por refresh.

Correção: cache dos bytes e do `QPixmap`, com a chave (caminho, mtime, tamanho)
e limite de 256 entradas. Salvar a página invalida a entrada sozinho, porque o
mtime muda.

Os outros dois achados do lote:

- **Instalar as fontes** recoprava o diretório inteiro e rodava `fc-cache -f`,
  que reconstrói o cache de fontes do sistema e trava a interface por segundos.
  Agora copia só o que mudou (mesmo tamanho e mtime, que o `copy2` preserva) e
  usa o `fc-cache` incremental.
- **Gerar modelos de página** não tinha indicador de espera. O cursor de espera
  entrou com `finally` obrigatório: cursor de espera esquecido trava o Krita
  inteiro até reiniciar.

## Lote D — empacotamento, release, scripts

| Achado | Onde | Gravidade |
|---|---|---|
| `build-zip.sh` **avisava** e gerava o ZIP sem licença e créditos | `scripts/` | crítica |
| Release publica sem conferir se a tag é a versão do plugin | `.github/workflows/` | alta |
| Release com notas automáticas de commit, em vez do CHANGELOG | `.github/workflows/` | média |
| `dilatar`/`erodir` com `np.roll` traz pixels da borda oposta | `scripts/vetorizar-baloes.py` | média |
| Galho morto prometendo cauda sem suavização, comentário mentindo | `scripts/vetorizar-baloes.py` | média |
| `EADDRINUSE` ao reiniciar o servidor do Penpot | `scripts/servir-para-penpot.py` | média |
| Bloco 7 do Scripter com `PyQt5` fixo (não existe no Krita 6) | `scripts/descoberta_scripter.py` | média |

O `build-zip` era o achado mais importante do lote, e o mais silêncio: o aviso
saía no log e o build seguia. Publicar esse ZIP é distribuir fontes de terceiros
(13 fontes sob OFL, brushes de packs comunitários) sem declarar autoria e
licença. Agora o build **quebra**, e depois de gerar o ZIP ele confere o
conteúdo.

O galho morto da cauda merece registro porque a correção é contraintuitiva: a
versão óbvia (cortar antes de suavizar) **muda a geometria do lote já
entregue**, porque o pescoço passa a ser escolhido em outra sequência de
pontos. Foi medido nos 14 balões: a cauda mudava de 9 para até 37 segmentos em
`balao-04b`. A solução foi manter o comportamento e corrigir o comentário, com
`tests/test_vetorizacao.py` travando a reprodução byte a byte do lote.

## Testes

De 76 para 161. Duas descobertas sobre a própria suíte:

1. **A suíte não rodava no CI.** Sem PyQt instalado, 18 testes quebravam com
   `ImportError` — o `compat` importa PyQt no topo. O CI nunca tinha rodado
   verde com esta suíte.
2. **O CI não conferia o lote de balões.** `test_vetorizacao.py` precisa de
   numpy e Pillow e pulava em silêncio: 5 dos 7 testes, incluindo a conferência
   de que os 15 SVGs continuam reproduzíveis byte a byte. O CI agora instala as
   duas dependências e quebra se aparecer `skipped`.
3. **A suíte rodava diferente na máquina do autor.** Com PyQt6 instalado, o
   `qt_probe` escolhe o binding já carregado, e o teste do cache de miniaturas
   pegava o PyQt6 de verdade: lia bytes que não eram PNG e recebia `None` — o
   teste "passava" porque comparava `None` com `None`.

O falso de Qt foi para `tests/qt_falso.py`, registrado nos dois nomes, com
`QPixmap` comparável, `QImage` que sempre decodifica e `QApplication` que
registra o cursor. A suíte agora dá o mesmo resultado com e sem PyQt, e cada
arquivo também verde sozinho.

## Interface (2026-10-01) — camada compartilhada, lotes 1 e 2

Achado por inspeção, no mesmo espírito da auditoria: **não havia camada de
interface**, e sim 7 decisões independentes tomadas separadamente. 52 botões, 11
com ícone, 22 com tooltip; o docker de páginas (o mais cuidado) com 10 tooltips
e 5 ícones, o de retículas (o maior) com 1 e nenhum. Nenhum `addSpacing`,
`setContentsMargins` ou `setIndent` nos dockers. Um `QGroupBox` com a cor de borda
fixa (`#666`) enquanto o resto segue o tema. As ações destrutivas já pediam
confirmação, e o de páginas já tinha reordenação por arrastar — ou seja, o que
faltava era só a camada visual.

Aplicado em `hq_tools/core/ui.py` (`botao`, `rotulo`, `rotulo_info`,
`separador`, `icone`, `espacamento`, `painel`):

- **52 botões** migrados para `ui.botao`, que exige o tooltip como 2º argumento
  (sem padrão). `dica` obrigatória é a regra; a trava contra regressão é o
  `tests/test_ui.py`, que por `ast` proíbe `QPushButton` direto e
  `setFixedHeight`/`setFixedWidth` nos dockers. Isso segura a future.
- **Rótulo de estado** (`lbl_info` da aba Retículas): o Qt reserva a largura da
  linha inteira como largura mínima, então o aviso de célula/DPI/LPI estufava o
  docker. Agora quebra linha e não reserva largura mínima.
- **Alturas fixas** dos 2 botões de cor removidas; a borda `#666` do `QGroupBox`
  não existia mais nesta versão e a identidade segue o tema.
- Ícones por chave semântica com fallback `SP_FileIcon` (chave errada perde o
  ícone, não o botão); espaçamento pela escala do `DESIGN.md` (4/8/12) via
  `ui.painel`/`ui.espacamento`; divisórias com `ui.separador()` nos pontos onde
  os grupos separam de verdade.

Fora do escopo, de propósito: `QToolButton` dos slots e dos cartões (reordenação
por arrastar + clique direito é comportamento), tipografia das listas de
miniaturas, tamanho dos ícones da lista, e a API de ícones do **tema** do Krita
(não verificada; hoje o plugin usa `QStyle.StandardPixmap` via
`standard_icon`, que respeita o tema do Qt).

Suíte: 161 → **177**, com e sem PyQt. Nota de verificação (2026-10-01): o
import de `KRITA_PALETTES_DIR` em `palettes/docker.py` existe desde o commit
original `d718877`, junto com `QtCore`/`QtGui`; não houve correção de nome não
definido nesse arquivo.

**A conferir no Acer** (sem PyQt aqui, não dá para provar layout): se o aviso de
célula ainda empurra a largura do docker de Retículas, falta relaxar a política
horizontal do rótulo; e a API de ícones do tema do Krita, se for usada depois,
precisa ser verificada para Krita 5 e 6.

## Ferramentas de auditoria

- `scripts/auditar-packs.py` — acha referência órfã nos packs, lendo o XML do
  preset dentro do PNG (tEXt, zTXt e iTXt). `--estrito` sai com erro se houver,
  `--detalhe` lista também os presets com pincel embutido.
- `tests/test_packs_recursos.py` — trava o resultado atual (11 testes).
- `tests/test_tiles.py` — os 11 PNGs do kit (`resources/patterns`) batem byte a
  byte com o gerador (`TestTilesDoKit`), para tile editado no código não deixar
  o arquivo defasado.

## Validação pendente (bloqueia a release)

Tudo acima foi verificado fora do Krita. Falta, com o app aberto:

- [ ] `bash scripts/install-dev.sh`, ativar o plugin, confirmar os **7 dockers**
      na listagem.
- [ ] Excluir um preset do usuário (não pode derrubar o Krita).
- [ ] "Editar selecionada" + Aplicar: a mesma camada e a mesma máscara mudam,
      não nasce uma nova; alternar LPI/LPC não deixa camada de edição órfã.
- [ ] Aplicar retícula, linha de efeito, balão e onomatopeia: **um Ctrl+Z
      desfaz** (era irreversível).
- [ ] Gerenciador de páginas: reordenar/criar/excluir com 40+ páginas e
      observar que não trava a interface.
- [ ] Instalar fontes do kit duas vezes: a segunda não deve arrastar a
      interface (o `fc-cache` sem `-f`).
- [ ] "Definir modelo": gerar um modelo e ver o cursor de espera.
- [ ] "Novo projeto..." numa pasta com `comicConfig.json` → recusa, não
      sobrescreve.
- [ ] Importar um SVG do lote (`Referencias/baloes-vetorizados/balao-02a.svg`):
      dois grupos (`cauda`, `balao`), camada não vazia.
- [ ] Desligar um módulo em Configurar Krita e reabrir: os outros seis
      continuam aparecendo.
- [ ] No Krita 6 (PyQt6): repetir o essencial (o `qt_probe` decide o binding).
- [ ] Os 15 balões revisados na tela, com a união das caudas feita à mão.

## Pendências de conteúdo (não são bug)

- **Origem das referências** em `Referencias/baloes/` e
  `Referencias/vetores-teste/`: não confirmada pelo autor. Não declarar IA,
  terceiros ou desenho próprio até ele dizer.
- **3 presets que citavam textura de pincel inexistente — resolvido no mesmo
  dia.** A medição (`python3 scripts/auditar-packs.py`) achou 3 arquivos citados
  que não vinham no pack:

  | Arquivo citado | Preset que dependia dele | Destino |
  |---|---|---|
  | `deevad_bristle.png` | `deevad 2d expressive thin.kpp` (Deevad v8.2) | removido |
  | `flat-tip-dirty.gbr` | `deevad 6n stamp floor particles.kpp` (Deevad v8.2) | removido |
  | `T_Texture_7.gih` | `X9AI_WC_Scattered_Sharp.kpp` (Watercolor Set) | removido |

  A hipótese inicial era que o pacote de origem tivesse escapado. Não é o caso:
  em 2026-09-30 foi medido o histórico inteiro dos dois repositórios
  (`Deevad/deevad-krita-brushpresets`, 103 arquivos, no `master` e na tag
  `8.2`; `vascoalexander/krita-watercolor-set`, 42 arquivos, com as duas versões
  de preset, Krita 2.7 e 2.8) e **nenhum dos três arquivos existe em versão
  alguma** — estão quebrados desde a origem. Os três `.kpp` são ponteiro puro
  para a textura (nem pincel nem textura embutidos), e reapontar para a textura
  de outro preset trocaria o pincel que o autor escolheu.

  Decisão do autor: remover os 3 presets do kit, com o motivo registrado no
  `FONTE.md` de cada pack (que passa a declarar a alteração, em vez de
  "nenhuma"). Cada pack corrigiu a contagem: Deevad 64 → 62 presets, Watercolor
  13 → 12. `tests/test_packs_recursos.py` não trava mais uma lista de
  pendência: passa a exigir **zero** referências quebradas, e a constante
  `PRESETS_REMOVIDOS` fica só como documentação do caso.

  A primeira medição tinha falhado por dois motivos, ambos corrigidos no
  `scripts/auditar-packs.py`: 4 presets do Deevad gravam o XML em chunk `zTXt`
  (comprimido), e 32 presets têm o pincel inteiro embutido, sem arquivo
  externo. Sem tratar isso, a auditoria acusa problema onde não há.

- **Os PNGs em `patterns/` não são textura de pincel.** Na medição, nenhuma
  definição de preset embute `<Pattern>`, e a instalação já manda cada tipo para
  a pasta certa do Krita (`~/.local/share/krita/<tipo>`). Os `patterns/` são
  tiles das retículas, não dependência dos presets.
- **Penpot:** o plugin do Penpot deu timeout de 30 s na primeira grade, e pode
  ter ficado estado parcial. Retentar em lotes pequenos, conferindo antes se
  não duplicou.
