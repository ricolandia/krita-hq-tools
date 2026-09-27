# Ideias novas


Parabéns, é um plugin bem mais completo do que eu imaginei quando sugeri o de retículas. A cobertura de retículas/halftone com chaves reais do Krita, a biblioteca do projeto e o gerador de páginas a partir de roteiro já fecham boa parte do que eu tinha listado como faltante. Avaliando contra o Clip Studio Paint, o que eu vejo como as lacunas que mais pesam no dia a dia, em ordem de impacto:

## 1. Preenchimento de cor por área fechada (o maior buraco)

O que falta mais, na minha avaliação, é o equivalente ao "Enclose and Fill" / "Combine Similar Colors" / camada de referência para balde de tinta do CSP: preencher regiões fechadas de lineart mesmo com pequenas falhas no contorno, e recolorir várias áreas da mesma cor de uma vez. É o gargalo clássico de quem colore HQ: sem isso, cada buraco na linha vira retrabalho manual. O Krita tem a ferramenta de balde nativa (com opção de preenchimento por região fechada e limiar de similaridade), mas não tem o modo "fechar gaps automaticamente" nem uma camada de referência dedicada. Um docker que rodasse um fechamento morfológico leve (dilatar/erodir a lineart) antes do flood fill, como pré-processamento, cobriria boa parte disso sem reinventar o algoritmo do zero. Precisaria de acesso a pixel data via `numpy`/`scipy` (ou implementação própria), o que é viável pela API (`Node.pixelData`/`setPixelData`) mas mais pesado que os módulos que você já tem.

## 2. Balão com cauda paramétrica e texto que redimensiona o balão

Pelo README, os balões são SVGs de catálogo inseridos como vetor — modelos fixos, não uma forma que se adapta ao texto e aponta para o personagem. No CSP a cauda é reposicionável e o balão cresce com o texto. No Krita 6 existe texto que flui dentro de formas (fluxo em forma), que a sua `DESCOBERTA.md` já registra como incerto (texto SVG chegando como shape, não editável, no 5.3.4). Se isso for resolvido — ou se você mirar primeiro o Krita 6 —, dá para fazer um balão de duas peças: uma forma elíptica com o texto fluindo dentro, mais uma cauda triangular separada que o usuário arrasta até o alvo. Ainda não é dinâmico como no CSP, mas fecha a maior parte da distância.

## 3. Modelos 3D posáveis no canvas

Isso o Krita simplesmente não tem e não é razoável simular via plugin sem reescrever um motor 3D dentro dele. Onde isso doer, a resposta continua sendo o Blender por fora (como no pipeline que já montamos), não um módulo do HQ Tools.

## 4. Apagador vetorial por interseção

Meu palpite antigo se confirma pela sua própria arquitetura: você não tentou, e eu concordo que não vale a pena — a API de vetores do Krita (`VectorLayer`/shapes) não expõe operação booleana de trim por interseção de forma acessível o bastante para justificar o esforço.

## 5. Réguas/assistentes de perspectiva como parte do fluxo do plugin

O Krita já tem assistentes de perspectiva e vanishing point nativos, mas fora do escopo do HQ Tools — o usuário tem que configurá-los manualmente a cada painel. Um módulo pequeno que salvasse e reaplicasse presets de assistente por painel (2 pontos, 3 pontos, régua de simetria) seria barato de fazer e economizaria tempo repetitivo, algo que o CSP resolve com "regra" salva por camada.

## 6. Exportação para publicação segmentada (webtoon, redes sociais)

O Batch Exporter nativo já cobre exportação em lote genérica, mas o CSP tem presets pensados para tirinha vertical infinita (corte automático em segmentos de altura fixa) e formatos de rede social. Se seu público incluir webtoon, isso valeria um módulo dedicado; senão, é dispensável.

## 7. Preflight de impressão (sangria, numeração, marcas de corte)

Você já cobre CMYK por canal no halftone, mas faltam marcas de corte/sangria e numeração automática de página — coisas que hoje ficam para o Scribus no seu pipeline. Dá para deixar assim, já que reimplementar diagramação de miolo dentro do Krita seria redundante.

## Resumo de prioridade

Se eu tivesse que escolher só um para o próximo ciclo, seria o **preenchimento de cor com fechamento de gaps** — é o que mais separa "plugin de HQ" de "estúdio de coloração" no uso real, e é o único item da lista que ainda não tem nem workaround razoável no seu fluxo atual. O balão paramétrico vem em segundo, mas depende de resolver primeiro a incerteza do texto-em-forma no Krita 6 que sua própria `VALIDACAO.md`/`DESCOBERTA.md` já sinalizou.

Quer que eu esboce o algoritmo de fechamento de gaps (o pré-processamento de morfologia antes do flood fill) como um módulo novo, no mesmo padrão de `core/` + `modules/` que você já usa?
