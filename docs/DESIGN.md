# Design System do HQ Tools

Rascunho no formato do catálogo do Open Design (design system primeiro; os
assets de ícone, banner e página saem daqui). Direção sugerida, aguardando
aprovação do autor.

> Categoria: quadrinho impresso (nanquim e retícula)
> Oficina de quadrinhos: tinta preta sobre papel quente, trama de retícula
> como textura, alto contraste e tipografia de capa.

## 1. Tema visual e atmosfera

- **Estilo:** nanquim sobre papel, traço grosso, retícula visível de perto.
- **Intenção:** parecer ferramenta de quem desenha HQ: tinta, papel, carimbo.
- **Texturas:** retícula (pontos) só como textura de apoio, nunca atrás de
  texto pequeno.

## 2. Cor

- **Tinta (primary):** `#141414`
- **Papel (surface):** `#F4EFE6`
- **Retícula (muted):** `#9B9B93`
- **Carimbo (accent):** `#D7263D`
- **Texto:** `#141414` sobre papel; papel sobre tinta.
- **Uso:** fundo de papel, títulos em tinta, accent só em um elemento por
  peça (o "carimbo" do selo, um número, um link).

## 3. Tipografia

- **Display:** Bangers (SIL OFL, vem no kit do plugin) para o nome e
  chamadas curtas.
- **Alternativa display:** Londrina Solid (OFL, kit) para um tom mais
  quadrinho brasileiro.
- **Texto:** Inter ou fonte de sistema, peso 400/600.
- **Escala:** 14/16/18/24/32/48/64.

## 4. Espaçamento e grade

- **Escala:** 4/8/12/16/24/32/48.
- **Margens de página:** 5% de cada lado, sarjeta de 2% entre painéis
  (mesmos números que o plugin usa nas guias).
- **Traço de quadro:** 2 px de tinta em bordas de painel e cartão.

## 5. Layout e composição

- Blocos com borda de tinta grossa e cantos retos (sem sombra difusa).
- Hierarquia: nome grande, uma linha de resumo, ação principal.
- Retícula em faixas ou cantos, com área limpa para leitura.

## 6. Componentes

- **Botão primário:** fundo tinta, texto papel, cantos retos.
- **Botão secundário:** fundo papel, borda de tinta.
- **Etiqueta/selo:** accent com texto papel (usar com parcimônia).
- **Cartão:** papel, borda de tinta 2 px, título em display.

## 7. Ícone do plugin

- **Board base:** 512 x 512, área de segurança de 10% (o ícone pequeno não
  corta).
- **Marca:** balão de fala (contorno de tinta) com trama de retícula no
  interior e uma gota de tinta na ponta.
- **Exportações:** 512, 256, 128, 64, 32 e 16 px (PNG) mais o SVG.
- **Fundo:** papel na versão clara; tinta na versão escura (GitHub).
- **Regra:** precisa ler a 32 px, então uma forma só, traço grosso.

## 8. Banner (prévia social)

- **Board:** 1280 x 640.
- **Composição:** nome à esquerda em Bangers, uma linha de resumo, faixa de
  retícula no rodapé e 1 a 2 capturas do plugin à direita.
- **Evitar:** texto pequeno, excesso de elementos, foto de fundo.

## 9. Página de exemplo (ricolandia.com)

- Cabeçalho com o ícone, nome e resumo; três blocos de capturas com legenda;
  botão para o repositório e para o INSTALL.md; bloco do autor.
- Mesma paleta e tipografia; imagens em PNG com moldura de tinta.

## 10. Processo (Open Design primeiro)

1. Aprovar ou ajustar este DESIGN.md.
2. Criar ícone e banner no Penpot (MCP) seguindo as seções 7 e 8.
3. QA de cada export com o modelo de visão; corrigir contraste e leitura.
4. Publicar: assets no repositório, banner no README e página no site.
