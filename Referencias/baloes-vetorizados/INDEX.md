# Balões e onomatopeias vetorizados (desenho do autor, 02 e 03/10/2026)

22 SVGs desenhados pelo Ricardo no Inkscape, substituindo o lote de 29/09 que
era gerado a partir das pranchas de `Referencias/baloes/` pelos scripts
`scripts/vetorizar-baloes.py` e `scripts/vetorizar-lote.py`. Os scripts ficam
no repositório como ferramenta para pranchas futuras, mas o kit agora é
desenhado à mão.

## Convenções do lote

- **Sem texto**: tudo é `path`, inclusive as onomatopeias (a fonte Bangers foi
  convertida em contorno).
- **Preenchimento branco e traço preto**, com uma exceção: `Fala_Speak_03_`
  é vazado (sem preenchimento), um quadro para usar sobre a arte.
- **Traço entre 0,68 mm e 1,01 mm** (viewBox em milímetros); dois arquivos
  usam o padrão do SVG (1).
- **Caudas 01 a 04 com a base aberta** (sem traço no encaixe), para emendar no
  corpo do balão dentro do Krita; 05 e 06 são fechadas.
- Um layer por arquivo ("Camada 1"), sem grupos nomeados.

## Lista

| Arquivo | Tipo | Descrição |
|---|---|---|
| Calda_Tail_01_.svg | cauda | cunha fina diagonal (base aberta) |
| Calda_Tail_02_.svg | cauda | "V" simétrico (base aberta) |
| Calda_Tail_03_.svg | cauda | "V" curvo assimétrico (base aberta) |
| Calda_Tail_04_.svg | cauda | lâmina curva longa (base aberta) |
| Calda_Tail_05_.svg | cauda | raio curto angular |
| Calda_Tail_06_.svg | cauda | raio em zigue-zague |
| Calda_Tail_07_.svg | cauda | três bolhas decrescentes (pensamento) |
| Calda_Tail_08_.svg | cauda | quatro bolhas crescentes (pensamento) |
| Fala_Speak_01_.svg | fala | retangular arredondado |
| Fala_Speak_02_.svg | fala | trapezoidal com perspectiva |
| Fala_Speak_03_.svg | fala | quadrado vazado, sem preenchimento |
| Fala_Speak_04_.svg | fala | circular |
| Fala_Speak_05_.svg | fala | oval levemente irregular |
| Fala_Speak_06_.svg | fala | circular com contorno irregular |
| Fala_Speak_07_.svg | fala | retangular alongado (legenda ou narração) |
| Fala_Speak_08_.svg | fala | explosão de espinhos esparsos |
| Fala_Speak_09_.svg | fala | explosão de espinhos densos |
| Ono_VSFX_01_.svg | onomatopeia | "WHOOSH!" em contorno |
| Ono_VSFX_02_.svg | onomatopeia | "POW!" em contorno |
| Ono_VSFX_03_.svg | onomatopeia | "CRASH!" em contorno |
| Pensa_Think_01_.svg | pensamento | nuvem achatada |
| Pensa_Think_02_.svg | pensamento | nuvem alta |

O `lote.json` guarda tipo e descrição de cada arquivo (o teste usa os dois).

## Status (QA de visão, 03/10/2026)

- Nenhum traço cortado na borda e nenhuma forma quebrada nos 22.
- Pontos para o autor conferir: `Calda_Tail_01_` (a mais ambígua das caudas
  abertas), `Fala_Speak_03_` (sem preenchimento, confirmar se é intencional)
  e `Ono_VSFX_01_` ("WHOOSH!" com W/H e O/O quase encostados).
- Traço mais fino em `Fala_Speak_03_`, `08_` e `09_` (0,68 a 0,70 mm) do que
  no resto (0,90 a 1,01 mm): conferir se é intencional.

## Como ajustar

- Redesenho: Inkscape, mantendo as convenções acima (path, sem texto, fundo
  branco, traço preto; cauda com a base aberta se for para emendar).
- Depois de mexer no lote, atualizar `lote.json` e `INDEX.md`; a suíte
  (`tests/test_vetorizacao.py`) acusa divergência.
