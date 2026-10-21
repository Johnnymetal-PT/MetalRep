# Guião Interno — Resposta às 4 Questões Técnicas da HMD (23/07/2026)

**Uso:** interno Parâmetro Global — apoio à reunião de 27/07/2026, 10h00. **Não enviar ao cliente.**
**Autor:** Bruno Pinheiro · **Data:** 27 de julho de 2026
**Origem das questões:** email da Nina Hedderich de 23/07/2026 (chatter da tarefa "Validar ponto de situação com o cliente")
**Método:** ordem obrigatória de decisão — standard já instalado → módulo standard adicional → Odoo Studio → custom.

> **Nível de validação.** B1 e B2 foram **verificados no Odoo de produção da HMD** (`https://intranet.hmdfurniture.com/`, BD `HMD`) a 27/07/2026 às 09h40, pelo canal de cliente (`read_mode=api`, finalidade *production*), depois de a ligação ter sido registada em *Brodoo > Repositório > Ligações Odoo do cliente*. Os números e configurações abaixo marcados como `FACTO OBSERVADO (produção)` são leitura direta do ambiente real. **Limitação:** o utilizador de API não tem acesso ao modelo `website.website` ("Object website.website doesn't exist"), pelo que as definições de *checkout* e de acesso ao eCommerce por website ficam `PONTO POR VALIDAR` — verificar em ecrã. B4 mantém-se fundamentado em source e requer demonstração no ambiente.

---

## B1 — Área de cliente B2B: controlo de acesso e informação visível a quem não tem conta

### Dor de negócio
A HMD quer saber exatamente **o que um visitante não registado vê** e como se controla o acesso à área de cliente B2B — é a base para poderem publicar o site com confiança, sem exporem preços ou catálogo a quem não deve.

### `FACTO OBSERVADO`
- Estão instalados no ambiente da HMD os módulos que suportam integralmente este controlo: `website_sale`, `portal`, `auth_totp_portal`, `website_sale_stock`, `website_sale_comparison`, `website_sale_wishlist`.
- Não existe, na lista de módulos instalados, qualquer módulo custom de controlo de acesso ao portal — o mecanismo em uso é o standard.

### `FACTO OBSERVADO (produção, 27/07 09h40)` — a constatação central deste ponto
- **O registo de novos utilizadores está aberto a qualquer visitante:** `auth_signup.invitation_scope = "b2c"`. Ou seja, hoje o site permite **auto-registo livre** — não é um comportamento B2B. Para o modelo que a HMD descreve, o valor deve ser **`b2b` ("Apenas por convite")**, passando as contas de cliente a ser criadas por convite.
- `auth_signup.reset_password = True` (recuperação de palavra-passe ativa) — coerente, manter.
- Existem **2 websites** no ambiente: *HMD Furniture* (website 1) e *Fria* (website 2) — relevante porque qualquer definição de acesso tem de ser aplicada **ao website correto**.
- **276 modelos de produto publicados** no site.

**Como dizer isto na reunião:** não é um defeito nem um pedido novo — é uma **definição que está no valor errado para o modelo de negócio pretendido**. É alteração de configuração, imediata, mas tem consequência operacional: a partir daí, os clientes B2B passam a precisar de convite/conta criada.

### Alavancas standard a explicar (Odoo 18)
1. **Registo de novos utilizadores** — o site define se o registo é livre ou apenas por convite. Em modelo B2B, o normal é **apenas por convite**: o cliente só tem conta depois de nós/HMD a criarmos.
2. **Visibilidade do catálogo e dos preços** — controlada por artigo/website (publicado vs. não publicado) e pelas listas de preços associadas ao cliente; existe também a opção de exigir sessão iniciada para ver preços e para finalizar a compra.
3. **Checkout** — pode exigir conta obrigatória, o que é o comportamento habitual em B2B.
4. **Grupos de utilizador do portal** — o que cada cliente vê dos seus próprios documentos (encomendas, faturas, projetos) é standard do portal, sem desenvolvimento.

### `INFERÊNCIA`
A necessidade da HMD é coberta por **configuração**, sem desenvolvimento. O que falta não é funcionalidade, é a decisão de política: catálogo visível a todos com preços só para autenticados, ou catálogo integralmente fechado.

### `PONTO POR VALIDAR`
- Qual a política pretendida pela HMD: (a) catálogo visível, preços só autenticados; (b) tudo fechado a quem não tem conta; (c) misto por categoria de produto.
- Definição de **conta no checkout** e de **acesso ao eCommerce** por website — não legível pelo utilizador de API (sem acesso a `website.website`); confirmar em ecrã.
- Em que website (HMD Furniture vs. Fria) aplicar cada definição.

### Verificação em partilha de ecrã *(≈2 min, para os pontos que faltam)*
`Website > Configuração > Definições` — selecionar o website **HMD Furniture** → secção **Privacidade / Clientes** (modo de registo: mostrar que está em livre e passar a "Apenas por convite") e secção **Loja** (conta no checkout, exibição de preços).

### Opções pela ordem obrigatória
1. **Standard já instalado** — resolve. Configuração de registo, publicação e checkout.
2. Módulo standard adicional — não necessário.
3. Studio — não necessário.
4. Custom — não justificável.

### Recomendação: `Configuracao standard` — cobertura **TOTAL**
**Implicações:** definir a política em conjunto e aplicá-la; a mudança de registo livre para "por convite" implica que a HMD (ou nós) passe a criar os acessos dos clientes B2B.

---

## B2 — "Todos os produtos" no menu e opções do produto que não se comportam como na app Vendas

Esta é, na prática, **a questão mais importante das quatro** — é onde a HMD sente uma inconsistência entre o site e o Odoo interno, e é onde há maior risco de a interpretarmos como defeito quando é configuração.

### B2.1 — Retirar o "Todos os produtos" da navegação

**`FACTO OBSERVADO (produção, 27/07 09h40)`:** o menu principal do website *HMD Furniture* tem apenas — **INICIO, COLLECTION** (`/shop/category/colecao-60`)**, PORTFOLIO, TECIDOS, MATERIAIS, CONTACTE-NOS, ABOUT US**. **Não existe qualquer item de menu "Todos os produtos" nem "Shop"** neste website (os itens `/shop` que existem pertencem ao menu-modelo por defeito e ao segundo website, *Fria*).

**`FACTO OBSERVADO` (source):** o "Todos os produtos" que a HMD vê é, quase certamente, a **primeira entrada da barra lateral de Categorias da loja** — `vendor/odoo_src/community/addons/website_sale/views/templates.xml:932-939`, onde a lista de categorias começa com a linha *All Products* a apontar para `/shop` sem categoria (e repetida na navegação móvel, linhas ~1271 e ~1291). É parte integrante do bloco de categorias, não um item de menu.

**Consequência prática:** não se resolve "removendo um menu" — resolve-se **desligando a barra lateral de categorias da loja** (`Website > Configuração > Definições > Loja - Produtos`, opção de categorias), o que retira a lista inteira. Retirar **apenas** a linha "Todos os produtos" mantendo as restantes categorias implica personalizar o template — `Customizacao leve`, a evitar se a HMD aceitar uma das duas alternativas standard.

**Recomendação:** `Configuracao standard` — cobertura **PARCIAL**. Confirmar primeiro, em ecrã, se é isto que a Nina quer dizer, e decidir entre: (a) desligar a barra de categorias; (b) manter a barra e aceitar a linha; (c) personalização leve do template.

**`PONTO POR VALIDAR`:** pedir à Nina que aponte no ecrã o elemento exato — é a diferença entre configuração imediata e uma pequena personalização.

### B2.2 — Opções do produto no carrinho ≠ aplicação de Vendas

#### O que a HMD descreve
Ao colocar um produto no carrinho, "os produtos alternativos não aparecem como na app Vendas": o produto que está a ser selecionado deixa de mostrar as opções disponíveis, e depois aparecem opções nos produtos abaixo. Na construção de uma proposta interna com o mesmo produto, o comportamento é o esperado.

#### `FACTO OBSERVADO` — o Odoo tem dois conceitos distintos, e não são intercambiáveis
1. **Produtos alternativos** (`alternative_product_ids`) — renderizados na **página do produto, depois da descrição**, como bloco/carrossel de sugestões. Evidência: `vendor/odoo_src/community/addons/website_sale/views/templates.xml` (template `alternative_products`, linhas ~1527-1535), onde o bloco é declarado com `oe_unmovable oe_unremovable` e contentor `o_not_editable`.
2. **Produtos opcionais** (`optional_product_ids`) — apresentados no **configurador de produto**, no momento de adicionar ao carrinho, exatamente como as opções aparecem numa proposta de venda. Evidência: `vendor/odoo_src/community/addons/website_sale/controllers/main.py` (~linha 677, passagem de `optional_product_ids`) e `vendor/odoo_src/community/addons/website_sale/controllers/product_configurator.py` (~linha 35, `has_optional_products` a decidir a abertura do configurador).

#### `FACTO OBSERVADO (produção, 27/07 09h40)` — a inferência confirma-se nos dados
No Odoo da HMD, dos artigos configurados:
- **205 modelos de produto** têm **produtos alternativos** preenchidos;
- **80 modelos de produto** têm **produtos opcionais** preenchidos;
- **276 modelos de produto** estão publicados no site.

Ou seja, a configuração do catálogo está **dominada pelos alternativos** (205 contra 80). É exatamente isso que produz o efeito descrito pela Nina: na página do produto aparece o carrossel de sugestões (alternativos), e não as opções no momento de adicionar ao carrinho.

#### `INFERÊNCIA` (agora com base factual)
O comportamento que a HMD quer no site é o dos **produtos opcionais**; a maioria dos artigos está configurada com **produtos alternativos**. Não é defeito do site nem do nosso desenvolvimento: são dois campos diferentes, com dois comportamentos diferentes, ambos standard.

#### `PONTO POR VALIDAR`
- No artigo concreto que a Nina apontar: tem alternativos, opcionais, ou ambos? (Há 80 artigos com opcionais — pode ser que o exemplo dela esteja entre os que não têm.)
- Se a intenção for opções configuráveis do mesmo artigo (e não produtos adicionais), a via correta pode ser **variantes/atributos** e não produtos opcionais — a distinguir com o caso concreto.
- **Dimensão do trabalho de correção:** se for para uniformizar, falamos de rever até ~205 artigos — não é um clique. Quantificar antes de assumir prazo.

#### Verificação em partilha de ecrã *(≈3 min)*
Pedir um artigo concreto que exemplifique o problema → `Vendas > Produtos > Produtos` → separador **Vendas**: comparar os campos **Produtos opcionais** e **Produtos alternativos**. Depois abrir a página pública do mesmo artigo e adicionar ao carrinho, para mostrar lado a lado a diferença.

#### Opções pela ordem obrigatória
1. **Standard já instalado** — resolve, se a necessidade for opções no momento da compra: preencher produtos opcionais nos artigos (ou modelar como variantes, se aplicável).
2. Módulo standard adicional — não necessário.
3. Studio — não necessário para o comportamento; apenas se quiserem alterar campos/vistas internas.
4. Custom — apenas se a HMD exigir um comportamento visual que o standard não oferece (ex.: apresentar alternativos dentro do configurador). Nesse caso, avaliação e orçamento próprios, com impacto em upgrade.

#### Recomendação: `Configuracao standard` — cobertura **PARCIAL COM ADAPTACAO DE PROCESSO**
**Implicações:** a HMD passa a distinguir, na gestão de artigos, "opções" de "alternativos"; isso implica revisitar os artigos já configurados. Se, após ver o caso concreto, se confirmar que querem os alternativos dentro do configurador, isso é **desenvolvimento adicional** e deve ser dito na reunião como tal — sem prometer prazo.

### B2.3 — Bloco da página de produto não editável (tag e bloco amarelo do 3D)

**`FACTO OBSERVADO`:** a não-editabilidade **é intencional no standard** — o bloco de produtos alternativos é declarado como não movível e não removível, com o contentor marcado como não editável (mesma evidência de B2.2, ponto 1). Não é limitação da formação nem defeito de configuração.
**`FACTO OBSERVADO`:** o **bloco amarelo com erro do 3D** decorre do visualizador 3D, que é uma capacidade **implementada por nós** e que extravasou o âmbito protocolado.
**Recomendação:** para o bloco não editável, `Configuracao standard` (explicar o comportamento e, se necessário, alternativas de colocação de conteúdo próprio fora do bloco). Para o erro do 3D, **correção nossa** — abrir tarefa e tratar como defeito, com pedido do artigo/URL onde ocorre.
**`PONTO POR VALIDAR`:** em que artigos surge o erro do 3D e se é dependência do ficheiro do modelo ou do módulo.

---

## B3 — Tutoriais de Projetos: o que foi enviado vs. o que a HMD recebeu

### Contexto
A 22/07 informámos que "foram já enviados tutoriais formativos" para fases, templates e automações de projeto, desde o CRM até ao fecho de encomendas. A 23/07 a Nina responde que **pensa ter recebido apenas o tutorial de criação de template** e pede confirmação.

### `FACTO OBSERVADO`
Existem, produzidos no repositório do projeto (`docs/`), entre outros: tutorial de **template de projeto**, **adiantamentos de cliente**, **cash-flow e aging**, **categorias de despesa**, **custo/hora por colaborador**, **confirming**, **gastos de pessoal**, **modelos de orçamento**, **email marketing**, **verificação de qualidade (QC)** e **WhatsApp Business**. Vários têm versão em PDF e DOCX.

### `PONTO POR VALIDAR` — a resolver antes ou durante a reunião
Quais destes documentos foram **efetivamente enviados** à HMD, por que via e em que data. Não afirmar na reunião que "foi tudo enviado" sem esta confirmação: a divergência é factual e assumir o contrário custa credibilidade.

### Recomendação
Assumir o ponto sem defensiva: **reenviar o conjunto completo e pertinente numa única mensagem**, com índice, logo após a reunião — e enquadrar a sessão de formação (cadeia CRM → encomenda + painéis) como o complemento natural desses materiais.

---

## B4 — Ligar os lançamentos do empréstimo à fatura/nota de lançamento do banco

### Dor de negócio
No empréstimo já registado (BCP 0000000400490701), o pagamento ocorre ao dia 5 e a saída bancária vem acompanhada dos **documentos do banco (juros e comissões)** e do **lançamento de amortização de capital**. A Nina quer que o lançamento do empréstimo seja **ajustado automaticamente** por esse documento.

### `FACTO OBSERVADO` — como funciona o módulo instalado (`account_loans`, Odoo 18 Enterprise)
- O módulo **gera os seus próprios lançamentos** a partir do plano do empréstimo: cada linha do plano (`account.loan.line`) tem `principal` e `interest` e mantém `generated_move_ids`; o lançamento gerado guarda a origem em `generating_loan_line_id` e é marcado com `is_loan_payment_move`. Evidência: `vendor/odoo_src/enterprise/account_loans/models/account_move.py` e `.../account_loan_line.py`.
- O empréstimo **fecha automaticamente** quando todas as linhas do plano têm o respetivo lançamento de pagamento publicado (lógica em `_post`, `vendor/odoo_src/enterprise/account_loans/models/account_move.py`).
- Existe navegação direta do lançamento para o empréstimo de origem (ação `open_loan`).

### `INFERÊNCIA`
Não existe, no standard, um mecanismo que **ajuste o plano do empréstimo a partir de uma fatura do banco**. A lógica standard é a inversa e correta contabilisticamente: o plano é a fonte do lançamento de juros e amortização, e o **extrato bancário é reconciliado contra esse lançamento**. Registar em paralelo a fatura do banco como documento de compra cria duplicação de custo financeiro — é provavelmente aí que está a dificuldade sentida pela HMD.

### Consequência prática a propor
1. O lançamento mensal do empréstimo (juros + amortização) passa a ser o **documento contabilístico de referência**, gerado pelo plano.
2. A linha do **extrato bancário** do dia 5 é reconciliada contra esse lançamento.
3. **Comissões e encargos que não estejam no plano** são tratados à parte, no seu próprio documento/conta de gastos — não devem "ajustar" o plano.
4. Se houver alteração real das condições (taxa, prazo, capital), o caminho é **revisão do plano** do empréstimo, não a correção manual dos lançamentos.

### `PONTO POR VALIDAR` (a validar em ambiente antes de fechar)
- Se os documentos do banco (juros/comissões) estão hoje a ser registados como faturas de compra em paralelo aos lançamentos do empréstimo — se sim, há duplicação a corrigir.
- Se as comissões e encargos foram incluídos no plano do empréstimo ou ficam fora.
- Comportamento concreto da reconciliação bancária contra o lançamento gerado, no ambiente da HMD, com o caso BCP.

### Verificação/demonstração *(a fazer no ambiente da HMD)*
`Contabilidade > Empréstimos` → abrir o contrato BCP → ver o plano e os lançamentos gerados → abrir um lançamento e mostrar a ligação ao empréstimo → mostrar a reconciliação da linha de extrato do dia 5 contra esse lançamento.

### Opções pela ordem obrigatória
1. **Standard já instalado** (`account_loans` + reconciliação bancária) — resolve o registo e a ligação ao banco, mediante **adaptação do processo atual** da HMD.
2. Módulo standard adicional — não necessário.
3. Studio — não necessário.
4. Custom — apenas se exigirem ajuste automático do plano a partir do documento do banco. Não recomendado: mexe em fluxo contabilístico core, com risco em upgrade e sem ganho real face à reconciliação standard.

### Recomendação: `Configuracao standard` — cobertura **PARCIAL COM ADAPTACAO DE PROCESSO**
**Implicações:** a HMD altera o hábito de lançar o documento do banco como origem do custo financeiro; ganha o plano do empréstimo como fonte única, com fecho automático do contrato. Como ainda não está validado no ambiente, **apresentar na reunião como caminho recomendado a demonstrar**, agendando uma sessão curta de validação com o caso BCP — não como ponto fechado.

---

## Resumo para a reunião

| Questão | Classificação | Cobertura | O que dizer hoje |
|---|---|---|---|
| B1 — Acesso B2B / visitantes | `Configuracao standard` | TOTAL | **Verificado:** o registo está aberto a qualquer visitante (`b2c`); passar a "Apenas por convite" resolve, com a consequência de as contas passarem a ser criadas por convite |
| B2.1 — "Todos os produtos" | `Configuracao standard` | PARCIAL | **Verificado:** não é um menu (não existe no site HMD) — é a 1.ª linha da barra de categorias da loja; pedir para apontar no ecrã e escolher entre desligar a barra ou personalizar |
| B2.2 — Opções vs. alternativos no carrinho | `Configuracao standard` | PARCIAL COM ADAPTACAO DE PROCESSO | **Verificado:** 205 artigos com alternativos vs. 80 com opcionais; explicar a distinção e não prometer prazo antes de dimensionar |
| B2.3 — Bloco não editável | `Configuracao standard` | TOTAL | Comportamento intencional do Odoo, não é limitação nossa |
| B2.3 — Erro do bloco 3D | Correção nossa | — | Assumimos como defeito; pedir artigo/URL |
| B3 — Tutoriais | Serviço | — | Não afirmar que foi tudo enviado; reenviar conjunto com índice |
| B4 — Empréstimo ↔ banco | `Configuracao standard` | PARCIAL COM ADAPTACAO DE PROCESSO | Caminho recomendado, a demonstrar com o caso BCP |

## Regras de conduta na reunião

- **Não prometer** o que depende de verificação: B1, B2.2 e B4 fecham-se com ecrã aberto, não por afirmação.
- **Não abordar** o modelo de acompanhamento continuado nem valores; se a Nina o levantar, remeter para depois do fecho do âmbito protocolado (ver nota interna do mesmo dia).
- **Não expor** qualquer número de horas.
- Separar sempre, em voz alta, **standard / configuração / defeito nosso / âmbito adicional** — é isso que evita que tudo caia no mesmo saco.

## Referências consultadas

- `.pg/projects/odoo-hmd/project/odoo_env.json` (Odoo 18.0 Enterprise on-premise, 487 módulos instalados)
- `.pg/projects/odoo-hmd/chatter/chatter.json` (email da HMD de 23/07/2026)
- **Odoo de produção da HMD** (`https://intranet.hmdfurniture.com/`, BD `HMD`), canal de cliente `production`, `read_mode=api`, 27/07/2026 09h40: `ir.config_parameter` (`auth_signup.invitation_scope`, `auth_signup.reset_password`), `website.menu` (menus dos 2 websites), `product.template` (contagens de alternativos, opcionais e publicados). Sem acesso a `website.website` (ACL do utilizador de API).
- `vendor/odoo_src/community/addons/website_sale/views/templates.xml` (template `alternative_products`)
- `vendor/odoo_src/community/addons/website_sale/controllers/main.py`, `.../controllers/product_configurator.py` (produtos opcionais / configurador)
- `vendor/odoo_src/enterprise/account_loans/models/account_move.py`, `.../models/account_loan_line.py`
- Documentação oficial Odoo 18.0: https://www.odoo.com/documentation/18.0/
