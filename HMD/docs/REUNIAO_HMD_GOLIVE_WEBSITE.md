# Website HMD 2026 — pontos pendentes e sequência de passagem a produção

Documento de apoio à reunião. Parâmetro Global · setembro de 2026

---

## 1. Objetivo desta reunião

Sair com três coisas fechadas:

1. A validação da visibilidade dos produtos para visitantes não registados
2. A lista dos pontos que faltam, revista em conjunto
3. Uma data para a passagem a produção

---

## 2. O que existe em cada ambiente

Convém fixar isto antes de mais, porque condiciona tudo o resto.

| | Site atual | Site novo |
|---|---|---|
| **Produção** (`intranet.hmdfurniture.com`) | em funcionamento | website criado e **vazio** |
| **Teste** (`hmd.parametro.pt`) | cópia do atual, com a nova regra de preços | **site novo completo** |

O desenho novo existe **apenas no ambiente de teste**, e não só na parte dos
produtos: cabeçalho, menu de categorias, página inicial, Quem Somos, Portfolio,
Tecidos, Materiais, Contactos, catálogo e páginas de produto.

**A produção não tem ainda nem o desenho novo nem a nova regra de preços.** A
passagem implica aplicar as duas coisas.

## 3. O que já está pronto

**O site novo pode ser visto em <https://novo.hmd.parametro.pt>**, sem conta e
sem sessão iniciada, de qualquer computador ou telemóvel. Endereço criado a
03/09/2026 exatamente para a HMD poder validar o site tal como um cliente o
verá. O navegador apresenta um aviso de certificado, por o certificado ser do
`hmd.parametro.pt` — pode ser aceite sem receio. É um endereço temporário, que
sai na passagem a produção (passo 8).

Preparado e disponível para verificação:

- **Estrutura e desenho** — cabeçalho, mega-menu de categorias e rodapé,
  construídos a partir do desenho fornecido
- **Páginas** — Home, Quem Somos, Portfolio, Tecidos, Materiais e Contactos
- **Catálogo** — grelha de produtos conforme o desenho
- **Página de produto** — apresentação, galeria, bloco de compra e produtos
  alternativos
- **Visibilidade dos produtos** — quem não tem conta vê os produtos, sem preço
  e sem possibilidade de adicionar ao carrinho, com indicação de que é sob
  consulta; os clientes registados continuam a ver preços e a comprar
  normalmente. Verificado a 31/08/2026.
- **Navegação em telemóvel** — cabeçalho, menu de categorias com os dois níveis
  do desenho, catálogo em duas colunas e página de produto empilhada.
  Verificado em ecrã de telemóvel a 02/09/2026.
- **Edição pelo Construtor de Website** — todas as páginas continuam editáveis
  pela HMD, sem intervenção técnica

---

## 4. Pontos pendentes

| Ponto | De quem depende |
|---|---|
| Aplicação do tema ao website de produção | Parâmetro |
| Configuração de base de dados associada ao tema | Parâmetro |
| Fotografias definitivas para as páginas editoriais | **HMD** |
| Imagem principal dos produtos em formato vertical, conforme o desenho | **HMD** |
| Revisão dos textos das páginas | **HMD** |
| Validação final do conteúdo antes da passagem | **HMD** |
| Produtos opcionais na janela de configuração — ver ponto 6 | **decisão conjunta** |
| Duas páginas novas pedidas pela HMD — ver ponto 10 | **decisão conjunta** |

As imagens atualmente no site são as maquetas do desenho original. Substituí-las
é trabalho de conteúdo, feito no Construtor de Website, e pode ser executado
pela HMD antes ou depois da passagem.

---

## 5. Sequência da passagem a produção

### Situação atual do domínio

A transferência do domínio está concluída. Verificado a 01/09/2026:

| Endereço | Aponta para |
|---|---|
| `hmdfurniture.com` | Cloudflare (`104.21.71.10`) → **Shopify** |
| `www.hmdfurniture.com` | Cloudflare → **Shopify** |
| `intranet.hmdfurniture.com` | Cloudflare (**os mesmos IPs**) → servidor Parâmetro |

**O domínio já é vosso, mas continua encaminhado para o Shopify.** A passagem
consiste em alterar esse encaminhamento — a mesma operação que já está feita
para o `intranet.hmdfurniture.com`, que passa pela Cloudflare nos mesmos
endereços e chega ao novo alojamento.

### O que isto significa para o risco da passagem

Como o domínio permanece nos **mesmos endereços da Cloudflare**, a alteração
não é uma mudança de DNS mas uma mudança de origem dentro da Cloudflare.
Em consequência:

- **Não há período de propagação.** A passagem tem efeito em segundos, não em
  horas.
- **Não há visitantes a ver dois sites diferentes** durante uma janela de
  transição.
- **A reversão é igualmente imediata**, bastando repor a origem anterior.

Isto reduz substancialmente o risco em relação a uma mudança de DNS clássica.

### Confirmado com o Hugo a 01/09/2026

| Questão | Resposta |
|---|---|
| Quem tem acesso à conta Cloudflare | Hugo |
| Quem configurou o encaminhamento do `intranet` | Hugo — a operação já foi feita nesta conta |
| A passagem é alteração de origem, não de DNS | Confirmado |
| A emissão do certificado precisa de desligar o proxy | Não — funciona com o proxy activo, como no `intranet` |
| Quem executa no dia, e com que antecedência | Hugo, no próprio dia, sem antecedência necessária |

**Não há incógnitas técnicas por resolver na sequência de passagem.** A data
depende apenas da revisão de conteúdo e das correcções de desenho em curso.

### Os oito passos

| # | Passo | Afeta o site atual? |
|---|---|---|
| 1 | Aplicar o tema ao website de produção | Não |
| 2 | Aplicar a configuração de base de dados associada | Não |
| 3 | Revisão do conteúdo pela HMD, ainda sem domínio | Não |
| 4 | Associar o domínio ao novo website no Odoo | Não |
| 5 | Configurar o servidor web e emitir o certificado | Não |
| 6 | **Alterar o encaminhamento de DNS na Cloudflare** | **Sim** |
| 7 | Verificação e período de acompanhamento | — |
| 8 | **Retirar o endereço temporário de validação** | Não |

**Os passos 1 a 5 não alteram nada do que está online.** Podem ser executados
com o Shopify a funcionar normalmente.

**Só o passo 6 muda o que os visitantes veem.** Por se tratar de uma alteração
de origem na Cloudflare e não de uma mudança de DNS, o efeito é imediato e
igual para todos os visitantes — não há período em que uns vejam um site e
outros o outro. É reversível a qualquer momento, repondo a origem anterior.

**O Shopify mantém-se intacto** durante o período de acompanhamento, como
retaguarda.

**O passo 8 não é opcional.** Para a HMD poder validar o site novo antes da
passagem, criou-se a 03/09/2026 um endereço temporário —
`novo.hmd.parametro.pt`, registo A para `154.58.193.71` na zona do
`parametro.pt`, mais o domínio correspondente no website e um `ServerAlias` no
servidor web. Concluída a passagem, os três têm de ser retirados: caso
contrário fica um endereço público, fora do domínio do cliente, a servir o
ambiente de teste indefinidamente.

Os passos 1 e 2 exigem reinício do serviço Odoo e serão executados fora do
horário de trabalho, com cópia de segurança prévia da base de dados.

---

## 6. Decisões necessárias nesta reunião

**Quando decorre a revisão de conteúdo** e quem a faz do lado da HMD.

**Até onde vão as correcções de desenho antes da passagem** — ver ponto 8.
Algumas das correcções recebidas a 01/09 são ajustes; outras são páginas novas.
A distinção determina a data.

**A data da passagem**, definida em função das respostas acima e **condicionada
à verificação de visitante descrita no ponto 9**.

**~~O título repetido na página de produto~~ — RESOLVIDO a 03/09/2026,
deixa de ser decisão.**

O nome e a fotografia apareciam duas vezes na página de produto: uma pelo
desenho novo, outra por um bloco montado na galeria do produto. Estavam
identificadas duas saídas, ambas com custo — ou o site novo deixava de desenhar
o título, ou o conteúdo passava a ser distinto por site, com mais manutenção
para a HMD.

Existia uma terceira, que foi a aplicada: **o bloco é escondido apenas no site
novo, sem alterar dados.** O site atual continua exatamente como está, e a HMD
não ganha trabalho de manutenção. O conteúdo permanece na ficha do produto e
pode ser reposto a qualquer momento.

**Os produtos opcionais na janela de configuração.**

> **Desfecho (04/09/2026):** a análise abaixo ficou sem objeto. A HMD
> esclareceu que não quer retirar os opcionais — quer poder escolher os
> acabamentos do produto selecionado dentro da janela, que era o que não
> dava. Resolvido a 16/09 sem tocar em dados nem esconder nada, e sem
> qualquer efeito no site atual. Fica o registo por causa do que se aprendeu:
> o pedido original tinha três saídas, todas com custo, e a leitura literal
> teria levado a mexer em dados partilhados com a produção.

A HMD pediu, a 01/09, que
a secção "Available options" deixasse de aparecer ao adicionar ao carrinho.
Parecia o mais simples dos seis pedidos e não é: essa secção não é uma página
nem um bloco editável — é desenhada pelo próprio Odoo a partir dos produtos
opcionais associados a cada artigo, e não tem definição por site. Há três
saídas e nenhuma é gratuita:

- retirar os produtos opcionais das fichas dos artigos — resolve de forma
  limpa, mas é uma alteração de dados **partilhada com o site atual**, onde a
  secção continuaria a fazer falta;
- esconder por estilos — rápido, mas a janela é desenhada fora das páginas do
  tema novo, pelo que ficaria escondida também no site atual;
- alterar o comportamento por código — correto tecnicamente, com o mesmo
  alcance sobre os dois sites.

**A pergunta para a HMD é de negócio, não técnica:** os produtos opcionais
devem deixar de ser propostos em todo o lado, ou apenas no site novo? A segunda
resposta tem custo de desenvolvimento e deve ser orçamentada.

**A página de entrada de parceiro.** O mesmo tipo de decisão, pela mesma razão
técnica: a página de início de sessão não distingue websites, pelo que
desenhá-la à maneira da HMD altera também o site atual. Ver ponto 10.

---

## 7. Compromissos que assumimos

- O novo website **não fica online automaticamente**. A passagem é executada
  manualmente pela Parâmetro e não avança sem validação da HMD.
- A alteração é **reversível**.
- O Shopify **não é desligado** no momento da passagem.

---

## 8. Alterações pedidas pela HMD — registo cronológico

| Data | Pedido | Natureza | Estado |
|---|---|---|---|
| 27/08 | Página de tecidos com categoria, composição básica e descarga de ficha técnica | **página nova** | **feito** (16/09) — falta o conteúdo, ver abaixo |
| 01/09 | "Specifications" apenas na versão sem sessão iniciada | ajuste | **feito e verificado** (02/09) |
| 01/09 | Retirar a aba "Available options" da janela de configuração | ajuste | **pedido retirado a 04/09** — ver esclarecimentos |
| 01/09 | Bloco B2B na página de produto para visitantes, com dois botões | marcação nova | **feito** (03/09) |
| 01/09 | Página de pedido de conta de parceiro, com formulário | **página nova** | **feito** (16/09), com aprovação no CRM |
| 01/09 | Página de entrada de parceiro com o desenho da HMD | estilização | **feito** (16/09), decisão da HMD a 04/09 |

Além destes, e por nossa iniciativa, foram corrigidos no mesmo período: a
duplicação da secção "Other options" na página de produto (01/09), a proteção
de preços a visitantes no novo website (02/09) e o menu de navegação em
telemóvel, incluindo o segundo nível previsto no desenho e nunca implementado
(02/09).

### Detalhe das correções de 01/09/2026

A HMD começou a enviar correções ao desenho, com anexos, e anunciou mais até
04/09. Registadas aqui separadas por natureza, porque a distinção é o que
determina a data da passagem.

### Ajustes ao que já existe — não afetam a data

| Correção | Onde | Nota |
|---|---|---|
| ~~Retirar a aba "Available options"~~ — pedido retirado a 04/09 | janela do carrinho | substituído pela escolha de acabamento no modal |
| Mostrar "Specifications" apenas na versão sem sessão iniciada | página de produto | decidido com a HMD a 01/09 |

### Páginas e funcionalidades novas — afetam a data

| Correção | Nota |
|---|---|
| Bloco B2B na página de produto para quem não tem sessão: texto de apresentação e botões "Log in as a HMD partner" e "Request an HMD account" | marcação nova, pequena |
| Página de pedido de conta de parceiro, com formulário (nome, email, telefone, empresa, NIF, website, morada, código postal, país, notas) | **página nova** — o item de maior peso |
| Página de entrada de parceiro com o desenho da HMD | estilização da página de sessão do Odoo |

### O que isto significa

O comportamento base já está garantido: **quem não tem sessão iniciada já não vê
preços nem carrinho.** Isso não é trabalho novo, é o que o site já faz.

O que é novo é a **camada de captação de parceiros** — convidar o visitante a
pedir conta, e receber esse pedido. Não constava do desenho inicial e não é um
ajuste gráfico.

### Decisão fechada a 01/09/2026

A secção "Specifications" aparece **apenas** na versão sem sessão iniciada. Na
versão com sessão o acabamento escolhe-se no seletor FINISH junto ao preço, e a
lista repetida seria informação a dobrar. Confirmado pela HMD.

---

### Esclarecimentos da HMD a 04/09/2026

Quatro dos pontos acima estavam em aberto à espera de decisão do cliente.
Ficaram fechados nesta reunião:

| Ponto | O que a HMD respondeu |
|---|---|
| Aba "Available options" | **O pedido de 01/09 estava mal interpretado.** Os opcionais mantêm-se; o que faltava era poder escolher os acabamentos do produto selecionado dentro da janela. Feito a 16/09 |
| Página de entrada de parceiro | Não faz mal alterar também o login da produção, desde que o que mude seja só o estilo. Feito a 16/09, tudo em CSS |
| Página de tecidos | Carregam elas os produtos, incluindo as fotografias das variantes. Querem clicar num tecido e chegar a uma página com as especificações, parecida com a dos tecidos. Feito a 16/09 |
| Página de pedido de conta | Aprova a Nina. **Não querem tempo de resposta definido.** Feito a 16/09, sem qualquer prazo no fluxo |

Pediram ainda que, ao selecionar os acabamentos, apareça o nome de cada
variante e não só "select finish", porque alguns produtos têm mais que um
acabamento — feito a 16/09. E deixaram o site da Gubi como referência.

Dois pontos da ata ficaram sem conteúdo escrito: "Espaçamento no Menu",
resolvido a 16/09 a partir das medidas do XD, e "Categorias de Tecido", que
continua por esclarecer.

---

## 9. Achado de 02/09/2026 — a proteção de preços estava inativa no site novo

**O que se encontrou.** Um visitante sem sessão iniciada, no site novo, via o
preço, o botão de adicionar ao carrinho e o seletor de quantidade. A regra
central do negócio da HMD — preços visíveis apenas a parceiros com conta — não
estava a ser aplicada no website 7.

**Porque ninguém o tinha visto.** Até 02/09 não existia forma de abrir o site
novo sem sessão iniciada. O website 7 não tinha domínio associado, e alcançá-lo
exigia uma rota reservada a utilizadores autenticados com permissões de editor.
Todas as verificações feitas até aqui — nossas e da HMD — foram feitas com
sessão iniciada, ou na cópia do site atual. A cópia do site atual está
corretamente protegida, o que reforçou a impressão de que o site novo também
estaria.

**Como foi encontrado.** Atribuindo ao website 7 um domínio de teste e pedindo a
página como visitante anónimo.

**A causa.** Não é um defeito de programação. São quatro definições de website
que não acompanharam a criação do website 7:

| Definição | Site atual | Site novo |
|---|---|---|
| Esconder preço quando é zero | ativa | **inativa** |
| Texto em vez do preço | "Price on request" | "Not Available For Sale" |
| Utilizador público | 4 | 13 |
| Lista de preços do público | "Público — Preço sob consulta" | **nenhuma** |

O mecanismo do site atual: o visitante recebe uma lista de preços que devolve
zero para tudo, e a definição de esconder preços transforma esse zero em "Price
on request". No site novo faltam ambas as peças, pelo que o visitante recebe o
preço de tabela.

**Estado: corrigido e verificado a 02/09/2026.** Quatro alterações de
configuração, sem desenvolvimento:

- o utilizador público do website 7 passou a ser o utilizador público do
  sistema; era uma conta de contacto **arquivada**, com as mesmas permissões
  mas sem lista de preços associada;
- a lista de preços do público foi ligada ao website 7 — já existia, criada e
  deixada a meio, e sozinha não produzia efeito;
- a definição de esconder preços foi ativada;
- o texto "Price on request" foi copiado do site atual, com as traduções.

Verificado por pedido anónimo à página de produto: preço ausente, "Price on
request" presente, botão de carrinho e seletor de quantidade escondidos. O
website 2 (Fria) não foi afetado — mantém os preços visíveis, como antes.

**Nota de segurança, para não ficar exagerada:** a conta arquivada tinha
exatamente os mesmos grupos e o mesmo tipo de utilizador que o utilizador
público do sistema. Não houve acesso indevido a dados. O efeito era o da lista
de preços em falta.

### A consequência para o método, não só para este defeito

Este não pode ser tratado como um caso isolado. **Nenhuma página do site novo
foi vista por um visitante sem conta** — nem a página inicial, nem o catálogo,
nem as páginas editoriais. O que se encontrou na página de produto pode
repetir-se noutras.

Propõe-se, por isso, uma condição à fixação da data: **a passagem não é agendada
antes de uma verificação de visitante, página a página, no site novo.** É uma
verificação de horas, não de dias, e agora é possível fazê-la.

### Verificação de visitante, página a página — 02/09/2026

Feita por pedido anónimo a cada página do site novo, sem sessão e sem cookies,
após as correções acima.

| Página | Preços visíveis | Valores monetários |
|---|---|---|
| Início | 0 | 0 |
| Catálogo (`/shop/page/1`, 20 produtos) | 0 | 0 |
| Categorias (mesas de centro, sofás) | 0 | 0 |
| Portfolio | 0 | 0 |
| Tecidos | 0 | 0 |
| Materiais | 0 | 0 |
| Contactos | 0 | 0 |
| Quem Somos | 0 | 0 |
| Private / Professional | 0 | 0 |
| Política de cookies | 0 | 0 |
| Carrinho e lista de desejos | 0 | 0 |
| Página de produto | 0 | 0 |

Verificou-se também que não há fuga de preços por vias menos óbvias: nos dados
estruturados que o Odoo escreve para os motores de busca, o preço servido ao
visitante é **zero**, e não o preço real escondido por estilos. Os únicos
números encontrados nas páginas são identificadores de produto e o ano.

**Conclusão: a regra de preços só para parceiros está aplicada em todo o site
novo.** A condição colocada à fixação da data no ponto 6 fica satisfeita.

Nota menor, sem risco: nos cartões do catálogo o texto "Price on request" não
aparece em todos os produtos. Não é fuga de preço — é uma questão de desenho, a
confirmar com a HMD se deve aparecer em cada cartão ou em nenhum.

---

## 10. Estimativa das duas páginas novas — 03/09/2026

Dos seis pedidos registados no ponto 8, quatro são ajustes ou marcação pequena
e não pesam no prazo. Dois são páginas novas, não constavam do desenho inicial
e não têm orçamento atribuído. Seguem estimadas.

### Página de tecidos, com composição e ficha técnica — 1 a 1,5 dias

A página existe e funciona. O pedido é acrescentar-lhe, por tecido: categoria,
composição básica e descarga de ficha técnica.

**O peso não está no desenho, está nos dados.** Hoje não existe onde guardar a
composição de um tecido nem onde anexar a sua ficha técnica. É preciso decidir
primeiro se um tecido é um produto, um atributo de produto ou um modelo próprio
— e essa escolha determina quem carrega o conteúdo depois, e com que esforço.
Aproximadamente metade da estimativa é essa modelação; a outra metade é a
página.

### Página de pedido de conta de parceiro — 2 a 3 dias

É o pedido mais pesado dos seis, e não é pelo formulário.

Os dez campos resolvem-se numa manhã. O peso está no que acontece **depois** da
submissão: quem recebe o pedido, onde é que ele aparece, quem aprova, e o que a
aprovação desencadeia — criar o utilizador, associá-lo à lista de preços de
parceiro, notificar a pessoa. Sem isso definido, entrega-se um formulário que
enche uma caixa de correio e não cria conta a ninguém.

**Depende de decisões da HMD, não de trabalho técnico:** quem aprova pedidos de
conta, e em quanto tempo se compromete a responder.

### Página de entrada de parceiro com o desenho da HMD — decisão antes de estimativa

Estimada inicialmente em meio dia, por se assumir que era estilização. **Essa
estimativa estava errada** e foi corrigida a 03/09/2026, depois de tentada.

A página de início de sessão do Odoo não é servida com contexto de website — a
sua rota está declarada sem essa indicação. Isso tem duas consequências
verificadas:

- as alterações feitas pelo tema, que normalmente ficam limitadas ao website
  onde o tema está aplicado, **aplicam-se a todos os websites** nesta página;
- em consequência, alterar esta página altera também o início de sessão do
  site que está no ar, o que está fora do que foi acordado para este projeto.

Há dois caminhos, e ambos precisam de decisão antes de estimativa:

- **alterar globalmente** — a página passa a ter o desenho da HMD em todo o
  lado, incluindo para a equipa interna. Barato, mas muda o ambiente atual.
- **módulo próprio** que torne a rota consciente do website — mantém o site
  atual intocado, mas é desenvolvimento e não estilização.

### Total das duas páginas novas: 3 a 4,5 dias

A página de entrada não está incluída, por depender da decisão acima.

### Recomendação da Parâmetro

**Que nenhuma das duas páginas novas entre antes da passagem a produção.**

Não por serem difíceis, mas porque ambas dependem de decisões que não se tomam
bem sob pressão de calendário: como se modela um tecido, e quem aprova um
parceiro. Decididas depressa, ficam mal decididas e paga-se a correção depois.

A passagem é reversível e o site continua a poder evoluir já online. Prender a
data a estas duas páginas é trocar semanas de espera por funcionalidades que
hoje não estão em uso, porque hoje não existem.
