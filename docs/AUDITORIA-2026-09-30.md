# Auditoria de 2026-09-30

Auditoria do HQ Tools feita por quatro especialistas (correção, desempenho,
robustez, testes/documentação), com os achados aplicados em quatro lotes. Este
documento é o índice do que foi encontrado, do que foi corrigido e do que
continua aberto. O changelog tem o detalhe por lote; aqui fica o mapa.

**Estado:** 161 testes verdes, com e sem PyQt instalado. **Nenhuma correção foi
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
2. **A suíte rodava diferente na máquina do autor.** Com PyQt6 instalado, o
   `qt_probe` escolhe o binding já carregado, e o teste do cache de miniaturas
   pegava o PyQt6 de verdade: lia bytes que não eram PNG e recebia `None` — o
   teste "passava" porque comparava `None` com `None`.

O falso de Qt foi para `tests/qt_falso.py`, registrado nos dois nomes, com
`QPixmap` comparável, `QImage` que sempre decodifica e `QApplication` que
registra o cursor. A suíte agora dá o mesmo resultado com e sem PyQt, e cada
arquivo também verde sozinho.

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
- **3 arquivos de pincel** citados por presets do kit não vêm no kit (medido com
  `python3 scripts/auditar-packs.py`):

  | Arquivo citado | Preset que depende dele |
  |---|---|
  | `deevad_bristle.png` | `deevad 2d expressive thin.kpp` (Deevad v8.2) |
  | `flat-tip-dirty.gbr` | `deevad 6n stamp floor particles.kpp` (Deevad v8.2) |
  | `T_Texture_7.gih` | `X9AI_WC_Scattered_Sharp.kpp` (Watercolor Set) |

  Esses presets instalam e aparecem na lista, mas o pincel não carrega: o Krita
  cai no padrão. Não dá para gerar o arquivo (é arte de terceiro) nem editar o
  preset sem perder o que o autor definiu. Decisão do autor: buscar o original
  no pacote de origem ou remover o preset do kit. `tests/test_packs_recursos.py`
  trava a lista: um preset novo com referência quebrada falha, e resolver uma
  das três também pede a atualização (a lista é a documentação).

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
