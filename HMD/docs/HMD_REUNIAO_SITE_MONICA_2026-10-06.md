# Site novo — reunião com a Mónica, 06/10/2026

- **Tarefa:** #7791 (e #6604, #7326, #7327, #7328, #7330)
- **Objectivo:** fechar as últimas modificações e confirmar a passagem do site para `www.hmdfurniture.com`, proposta para quinta, 08/10, às 18h (#7040).
- **Site em revisão:** `https://novo.hmd.parametro.pt`. Desde 30/09 já abre sem aviso de segurança.

---

## 0. Verificação antes da reunião — 02/10/2026

Verificação feita como visitante anónimo no endereço público de teste:

- [x] O site responde por HTTPS e as páginas `/`, `/shop`, `/fabrics`, `/private` e `/professional` devolvem `200 OK`.
- [x] A categoria continua escrita como **«Lightning»** no menu e no título da página. A decisão/correção para **«Lighting»** continua pendente.
- [x] As páginas `/private` e `/professional` estão publicadas e acessíveis diretamente, embora já não apareçam no menu principal.
- [x] Continuam visíveis dois conjuntos de contactos: `info@hmdfurniture.com` com Rua do Tronco/São Mamede da Infesta e, no rodapé, `costumer@hmdfurniture.com` com «Salcol». É necessária uma decisão da HMD sobre a versão correta; confirmar também se `costumer@` é uma gralha de `customer@`.
- [x] O HTML servido contém várias versões responsivas do menu e repete «Home». Confirmar visualmente no telemóvel durante a reunião qual das repetições está efetivamente visível.
- [x] O produto LOLA MEDIUM (id 770) já abre em `/shop/lola-medium-770` (`200 OK`). O título do separador do browser e dos motores de pesquisa continua a dizer **«Lola Small»**: o título SEO do artigo não acompanhou a mudança de nome.
- [x] Visitante sem conta, na página do LOLA MEDIUM: aparece **«Price on request»**, com ligação para `/contactus`, o botão de carrinho está escondido e o preço real não chega ao browser (lista pública «Publico — Preco sob consulta (2026)», que dá 0,00 € escondido). É o comportamento pedido pela Nina no #7040.
- [x] O registo livre continua aberto: `/web/signup` mostra o formulário de criação de conta. Quem se regista sozinho passa a ver preços. A pergunta foi feita a 20/08 e não tem resposta registada.

> Esta verificação confirma conteúdo e respostas HTTP. O alinhamento, os tamanhos dos botões, o transbordo dos carrosséis e outros aspetos visuais devem ser validados num telemóvel real ou nas ferramentas responsivas do browser.

---

## Ordem sugerida para a reunião — 45 a 60 min

1. **Confirmar o objetivo e a data de passagem — 5 min:** fechar se a passagem se mantém para 08/10 às 18h e quem valida o site logo depois.
2. **Percurso em computador — 15 min:** cabeçalho, posição do logótipo, mega-menu, grelha de produtos, páginas Private/Professional, «Lighting» e galeria «Seen in projects».
3. **Percurso em telemóvel — 15 min:** cabeçalho, repetição de «Home», contactos, duas colunas, newsletter, imagem do produto, botões e setas de `/fabrics`.
4. **Conteúdo da responsabilidade da HMD — 10 min:** fotografias definitivas, documentos 2D/3D e fichas técnicas dos tecidos.
5. **Fecho — 5 a 15 min:** separar bloqueantes da passagem de melhorias posteriores e atribuir responsável e data a cada ponto.

Regra de condução: não alterar conteúdo durante a conversa sem registar primeiro a decisão. Para cada ponto, fechar **decisão, responsável, prazo e se bloqueia ou não a passagem**.

## 1. Para validar com a Mónica (fecham tarefas)

- [ ] **Pedidos de 07/09:** espaçamento, fonte e tamanho (#7326), menu do lado direito (#7327), logótipo e cabeçalho (#7328), grelha de produtos (#7330).
- [ ] **Telemóvel**, corrigido a 25/09: loja e categorias em 2 colunas, menu sem Private e Professionals, newsletter legível, imagem de produto a toda a largura.

## 2. Para decidir com a Mónica

- [ ] **Posição do logótipo:** a prancha «MENU LADO DIREITO» mostra-o à esquerda da coluna de atalhos, e hoje está por cima.
- [ ] **Cabeçalho no telemóvel:** o desenho de agosto punha a conta, o carrinho e a pesquisa na primeira linha. Fica como está?
- [ ] **Categorias do mega-menu:** o desenho está em português e o catálogo em inglês. Traduzir?
- [ ] **Páginas `/private` e `/professional`:** continuam publicadas e acessíveis por URL, têm texto provisório e já não estão no menu. Dar-lhes texto definitivo, despublicar ou retirar?
- [ ] **Gralha na categoria «LIGHTNING»:** continua visível no site de teste; deve ser «LIGHTING».
- [ ] **Menu do telemóvel e contactos:** «HOME» aparece repetido na estrutura do menu. Os contactos também não coincidem: `info@hmdfurniture.com` e Rua do Tronco/São Mamede da Infesta numa zona, contra `costumer@hmdfurniture.com` e «Salcol» no rodapé. Quais são os certos? Confirmar se `costumer@` é uma gralha.
- [ ] **Visitantes sem conta (pedido da Nina, #7040):** mostrar a página do produto sem sessão iniciada e confirmar o texto **«Price on request»** (redação e idioma) e o destino do clique, hoje `/contactus`.
- [ ] **Registo de contas:** hoje qualquer visitante cria conta sozinho e passa a ver preços. Fica assim, ou passa a **apenas por convite**, com as contas de parceiro aprovadas pela Nina? É configuração standard, sem desenvolvimento, mas tem de estar decidido **antes da passagem**.
- [ ] **Galeria «Seen in projects»:** os nomes dos projetos estão a branco sobre fundo claro (ex.: HOTEL OCHSENTOR, VILLA TAHITI). Corrige-se no editor do site.

## 3. Conteúdo que é da HMD

- [ ] **Fotografias:** trocar as imagens de demonstração por fotografias reais nas páginas editoriais. A imagem principal dos produtos deve ser vertical, como no desenho.
- [ ] **Documentos 2D/3D dos produtos:** o site já os mostra no fim do bloco de compra. Faltam os ficheiros.
- [ ] **Tecidos:** 40 séries, todas publicadas, com composição (40), gama (39) e instruções de limpeza (39). **Faltam as fichas técnicas: 0 de 40.**

## 4. Técnico, fica com a Parâmetro Global — resolvido a 06/10

Corrigido no site de teste e medido num telemóvel simulado a 393 px:

- [x] **Setas dos carrosséis em `/fabrics`:** passam a caber no ecrã, já não tapam o primeiro tecido e a página deixou de ter deslocamento horizontal.
- [x] **Botões para o dedo no telemóvel:** a lupa, o carrinho, o coração e o MENU têm agora uma área de toque de 44×44 px. O aspeto do cabeçalho não mudou.
- [x] **LOLA MEDIUM (id 770):** a página abre e o título já diz «LOLA MEDIUM». Antes da passagem, confirmar o mesmo título na produção.

## 5. Passagem

- [ ] Confirmar **quinta, 08/10, às 18h**.
- [ ] O que tem de estar pronto antes: os pontos da secção 2 que a Mónica considere obrigatórios. Os restantes podem ir depois da passagem.
- [ ] Quem da HMD verifica o site no dia, logo a seguir à passagem.
- [ ] Lembrar que o email `@hmdfurniture.com` não é afetado: na Cloudflare só mudam três registos (`@`, `www`, `ftp`), e os 17 do Microsoft 365 não se tocam. Ver `HMD_PASSAGEM_WEBSITE_CLOUDFLARE.md`.

**Do lado da Parâmetro Global, antes de 08/10** (não é para discutir na reunião, só para confirmar que está a andar):

- [ ] Cloudflare: ver o modo SSL/TLS e as regras de redireccionamento que já existem.
- [ ] Certificado de origem criado e instalado no Apache; modo «Full (strict)».
- [ ] Cópia de segurança da base `HMD`; tema aplicado ao website «HMD Furniture 2026» fora de horas; domínio `https://www.hmdfurniture.com` definido.
- [ ] Configuração dos visitantes sem conta e do registo aplicada também ao website de produção, tal como ficar decidido.
- [ ] Confirmação do Hugo de que o `ftp` não é usado.

## 6. Registo de decisões da reunião

| Ponto | Decisão | Bloqueia a passagem? | Responsável | Prazo |
|---|---|---|---|---|
| Data e hora da passagem |  |  |  |  |
| Pessoa que valida após a passagem |  |  |  |  |
| Posição do logótipo |  |  |  |  |
| Cabeçalho no telemóvel |  |  |  |  |
| Idioma das categorias |  |  |  |  |
| Páginas Private/Professional |  |  |  |  |
| Lighting |  |  |  |  |
| Contactos e morada |  |  |  |  |
| Seen in projects |  |  |  |  |
| «Price on request» (texto e destino) |  |  |  |  |
| Registo livre ou só por convite |  |  |  |  |
| Fotografias e documentos |  |  |  |  |
| Fichas técnicas dos tecidos |  |  |  |  |
