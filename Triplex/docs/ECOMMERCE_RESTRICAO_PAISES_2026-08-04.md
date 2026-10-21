# Loja Online — Restrição de Venda a Países Específicos

**Versão:** 1.1
**Data:** 04/08/2026
**Autor:** João Barros — Parâmetro Global
**Estado:** Rascunho para revisão interna
**Ambiente analisado:** Odoo 17.0, Enterprise, on-premise

---

## 1. Objectivo funcional e dor de negócio

O requisito confirmado é **permitir a venda online apenas para um conjunto de países específicos**. Não é esconder a loja a visitantes estrangeiros: o catálogo pode continuar visível a todos, desde que ninguém de fora dos países permitidos consiga concluir uma compra.

Esta distinção decide toda a análise. Restringir *a venda* é configuração; restringir *o acesso* seria desenvolvimento ou infraestrutura. O que se segue trata a primeira leitura, e trata a segunda apenas como via alternativa documentada (Via C3), para o caso de o requisito evoluir.

---

## 2. Contexto técnico confirmado

`FACTO OBSERVADO` — ambiente do projecto, lido do espelho `.pg/projects/odoo-triplex/project/odoo_env.json`:

| Item | Valor |
|---|---|
| Versão Odoo | 17.0 |
| Edição | Enterprise |
| Ambiente | on-premise |
| Módulos instalados | 487 |
| Módulos relevantes já instalados | `website_sale`, `delivery`, `payment`, `website_sale_stock`, `website_sale_loyalty`, `website_sale_subscription`, `base_geolocalize` |

Toda a evidência técnica deste documento foi verificada no source da série activa, em `vendor/odoo_src` (Odoo 17.0), com indicação de ficheiro e linha.

---

## 3. O funil de compra, etapa a etapa

Esta é a parte que costuma gerar expectativas erradas: **a configuração standard não actua no catálogo, actua no fecho da encomenda**. A tabela mostra onde cada via intervém.

| Etapa | Rota | Via A — Configuração standard | Via B — Módulo App Store | Via C — Desenvolvimento `pg_` |
|---|---|---|---|---|
| Catálogo | `/shop`, `/shop/page/<n>` | Visível a todos. O preço, a moeda e o imposto **já mudam** conforme o país detectado por GeoIP | Webkul consegue esconder produtos indisponíveis; Aktiv não esconde | Pode filtrar produtos ou fechar a rota |
| Ficha de produto | `/shop/<product>` | Visível a todos, com preço e imposto da região do visitante | Idem | Idem |
| Adicionar ao carrinho | `/shop/cart/update`, `/shop/product/is_add_to_cart_allowed` | **Sempre permitido.** A regra é `active and sale_ok and website_published` — não há qualquer verificação de país | Aktiv permite adicionar e avisa no cesto | Pode bloquear |
| Cesto | `/shop/cart` | Sem restrição. O template recebe `cart_ready` | Aviso configurável nas linhas do cesto | Ponto de extensão natural (`_is_cart_ready`) |
| Endereço | `/shop/address` | **Primeiro travão.** O dropdown de país da entrega mostra apenas os países cobertos pelos métodos de entrega publicados | Também restringe o dropdown (função duplicada) | — |
| Checkout / confirmação | `/shop/checkout`, `/shop/confirm_order` | Sem método de entrega compatível, não há nada para selecionar | — | — |
| Pagamento | `/shop/payment` | Provedores de pagamento filtrados pelo país do parceiro | Botão de pagamento desactivado | — |
| Criação da transacção | `/shop/payment/transaction/<id>`, `/shop/payment/validate` | **Travão duro.** `ValidationError("No shipping method is selected.")` | — | — |

### Evidência das afirmações da tabela

- Adicionar ao carrinho sem verificação de país: `vendor/odoo_src/community/addons/website_sale/models/product_product.py:101-103` (`_is_add_to_cart_allowed`), consumido em `controllers/main.py:696` e `models/sale_order.py:187`.
- Dropdown de país da entrega filtrado pelos métodos de entrega publicados: `website_sale/models/res_country.py:10-22` (`get_website_sale_countries(mode='shipping')`), consumido em `controllers/main.py:1602-1603` e na rota `/shop/country_infos` (`controllers/main.py:2022-2026`).
- Travão duro no pagamento: `website_sale/models/sale_order.py:384-385`, invocado em `controllers/main.py:1888` (`/shop/payment/validate`) e `controllers/main.py:2090` (`/shop/payment/transaction/<id>`).
- Filtro de país nos provedores de pagamento: `payment/models/payment_provider.py:99-107` (campo `available_country_ids`) e `:532-540` (aplicação do domínio).
- Preço e moeda por GeoIP: `website_sale/models/website.py:179-198` e `product/models/product_pricelist.py:39` (`country_group_ids`); imposto por GeoIP em `website_sale/models/website.py:488-493`.

**Leitura de negócio:** um cliente espanhol navega a loja, vê preços, adiciona ao cesto — e é travado no passo do endereço, porque Espanha não aparece na lista de países de entrega. Se ainda assim chegar ao pagamento (por exemplo com uma encomenda criada por outra via), o Odoo recusa a transacção.

---

## 4. Via A — Configuração standard

**Classificação:** `Configuracao standard`
**Custo de licença:** zero
**Custo de desenvolvimento:** zero

### O que configurar

1. **Métodos de entrega** — *Inventário → Configuração → Métodos de Entrega*. Em **cada** método publicado no website, preencher o campo `Countries` com os países permitidos. O campo é `many2many`, pelo que um conjunto de países (por exemplo Portugal e Espanha) é a mesma configuração que um só.
2. **Provedores de pagamento** — *Facturação → Configuração → Provedores de Pagamento*. Preencher `Countries` em cada provedor publicado.
3. **Coerência comercial (recomendado)** — pricelist com `country_group_ids` e posição fiscal por região, para que quem vem de fora não veja preços ou impostos que não lhe são aplicáveis.

### O que isto implica

- **O catálogo permanece público.** Quem está fora dos países permitidos continua a ver produtos e preços. Para SEO isto é positivo; para uma expectativa de "loja fechada" é uma surpresa que convém antecipar junto de quem pediu.
- **A mensagem de erro é genérica.** O cliente estrangeiro percebe que não há entrega disponível, mas não recebe uma explicação comercial. Se for preciso uma mensagem própria ("Não entregamos no seu país; contacte-nos"), isso já é a Via C1.
- **Aplica-se a todos os produtos por igual.** Não há granularidade por produto.
- **Sobrevive a upgrades.** É configuração, não código: não há nada para migrar entre séries.

### O que não cobre — três furos a fechar

Todos se fecham na própria configuração, mas nenhum se fecha por si.

1. **Métodos de entrega deixados sem países.** É o esquecimento mais comum, e o mais grave: a recolha em loja também é um método de entrega, e a verificação de país corre antes de qualquer lógica específica do tipo de entrega (`delivery/models/delivery_carrier.py:131-135` → `_match_address` em `:145-155`). Um único método publicado sem `Countries` preenchido reabre a loja ao mundo inteiro. **Regra: todos os métodos publicados, sem excepção.**
2. **Carrinhos apenas com serviços ou produtos digitais.** A validação da entrega tem a excepção `only_services` (`website_sale/models/sale_order.py:384`): um cesto sem produtos físicos não é travado por nenhum método de entrega. Se o catálogo tiver serviços, o passo 2 (provedores de pagamento) deixa de ser opcional e passa a ser a única barreira.
3. **Parceiro sem país definido.** O filtro dos provedores de pagamento só se aplica quando o cliente tem país preenchido — o próprio comentário do standard di-lo: *"The partner country must either not be set or be supported"* (`payment/models/payment_provider.py:532-540`). No checkout do website o país é obrigatório, mas encomendas criadas por importação, API ou backoffice podem escapar.

### Cobertura do requisito

**TOTAL** para produtos com entrega física. **TOTAL** para serviços e digitais desde que os provedores de pagamento sejam restringidos. **PARCIAL** se algum método de entrega publicado ficar sem países.

### Validação recomendada

Em ambiente de teste, três cenários: (a) escolher um endereço de entrega de país não permitido — o país não deve constar do dropdown; (b) forçar um endereço estrangeiro pelo backoffice e tentar pagar no site — deve bloquear; (c) repetir (b) com um cesto apenas de serviços — é o cenário que revela o furo nº 2.

---

## 5. Via B — Módulo da Odoo App Store

Módulo avaliado: `ecommerce_country_product_restriction`, Aktiv Software, €21, licença OPL-1, séries 12.0 a 19.0.

### O que faz

- Restrição **por produto**, não pela loja: cada produto tem a lista de países onde está disponível; sem países definidos, fica disponível em todos.
- A detecção é pelo **endereço de entrega declarado**, não por GeoIP. Os avisos aparecem depois de o cliente preencher o endereço.
- Desactiva o botão de pagamento quando o cesto tem produtos indisponíveis para o país da entrega.
- Acrescenta mensagens de aviso configuráveis no cesto e no checkout, e a configuração dos países visíveis no dropdown do checkout.

### O que acrescenta face à Via A

Apenas duas coisas: **granularidade por produto** e **mensagens personalizadas**. O bloqueio da compra e a restrição do dropdown de países já existem em standard, pelo que nessa parte o módulo duplica o que a configuração faz.

### O que custa

- **€21 por série do Odoo.** Cada versão é um build próprio do fornecedor. Na migração de série, o porte **não é uma opção interna**: adaptar o módulo para a série seguinte cria uma *modified copy*, e instalá-la no servidor do cliente — entidade jurídica distinta — é distribuí-la, precisamente o que a cláusula OPL-1 citada abaixo proíbe. Restam duas saídas, ambas com custo: comprar o build novo se o fornecedor o publicar, ou substituí-lo por módulo `pg_` próprio. Não é, portanto, um risco de terceiros que se possa absorver com trabalho próprio — é um custo recorrente com um limite legal.
- **Superfície de conflito elevada.** O módulo intervém no cesto, no checkout e no botão de pagamento — a zona mais disputada de uma instalação com 487 módulos, que já inclui `website_sale_stock`, `website_sale_loyalty`, `website_sale_subscription` e módulos `pg_`.
- **Instalação manual no on-premise**, com o risco conhecido neste projecto de o módulo ficar no servidor e fora do repositório.
- **Não é adaptável.** A licença OPL-1 é explícita: *"It is forbidden to publish, distribute, sublicense, or sell copies of the Software or modified copies of the Software."* Acrescentar-lhe uma função própria cria uma "modified copy" — que, no nosso caso, iria para o repositório e para o servidor. O que a licença permite é o padrão inverso: *"You may develop Odoo modules that use the Software as a library (...) but without copying any source code or material from the Software."* Ou seja, um módulo `pg_` que dependa dele e o estenda — nunca uma alteração dentro dele.

### Quando se justifica

Só se o requisito passar a ser **produtos diferentes disponíveis em países diferentes**. Para o requisito actual — vender apenas para países específicos — o módulo é redundante e introduz uma dependência proprietária para replicar configuração.

**Classificação:** `Nao recomendado / alto risco` para o requisito actual. Reavaliável como `Customizacao leve com dependência externa` se o requisito mudar para granularidade por produto.

---

## 6. Via C — Desenvolvimentos possíveis

Nenhum destes é necessário para o requisito actual. Ficam documentados porque são os caminhos legítimos se o âmbito evoluir, e porque todos assentam em métodos que o Odoo expõe **para serem sobrepostos** — o que os torna razoavelmente seguros em upgrade.

As estimativas são `INFERENCIA` — indicação de ordem de grandeza para decisão, não orçamento.

### C1 — Regra global de país no checkout, com mensagem própria

**Quando:** quando a Via A resolve o bloqueio mas se quer uma mensagem comercial em vez do erro genérico, ou a regra aplicada de forma central em vez de método a método.

**Como:** módulo `pg_` que sobrepõe `_is_cart_ready()` e `_check_cart_is_ready_to_be_paid()` (`website_sale/models/sale_order.py:367-385`). O primeiro devolve `True` no standard e existe precisamente para ser estendido; o resultado chega ao template como `cart_ready` (`controllers/main.py:938`), pelo que o aviso aparece no cesto sem tocar em QWeb. Os países permitidos ficam num campo no modelo `website`, configurável e compatível com multi-website.

**Esforço:** 6,5 a 9,0 horas — decomposição na secção 7.

### C2 — Restrição por produto sem dependência de terceiros

**Quando:** se o requisito passar a ser produtos diferentes por país.

**Como:** campo `many2many` de países em `product.template` e verificação no mesmo ponto de extensão de C1, mais o aviso na linha de cesto. Note-se que existe já em standard uma alternativa sem código: **multi-website**, um website por país com catálogo próprio, via `website.published.multi.mixin` em `website_sale/models/product_template.py:15-20`. Não é imposta por geolocalização — nada impede um visitante de abrir o domínio do outro país — mas é gratuita e imune a upgrades.

**Esforço:** 13,5 a 20,0 horas — decomposição na secção 7.

### C3 — Fecho do catálogo por GeoIP

**Quando:** apenas se o requisito mudar para esconder a loja a visitantes estrangeiros.

**Como:** `ir.http._frontend_pre_dispatch()` ou `_pre_dispatch()` (`website/models/ir_http.py:178` e `:201`), com o país do visitante já resolvido em `request.geoip.country_code` (`website/models/ir_http.py:403-408`).

**Reserva importante:** não é a via recomendada. O GeoIP falha com VPN e com IPs corporativos estrangeiros, gerando falsos positivos em clientes legítimos, e afecta a indexação (os crawlers vêm de IPs de fora). Para geo-bloqueio efectivo, a camada correcta é a infraestrutura — nginx com módulo GeoIP, ou Cloudflare — onde o bloqueio é mais barato, não interfere com o Odoo e não tem de ser migrado em cada série.

**Esforço:** 7,0 a 11,5 horas no Odoo; 2,0 a 4,0 horas na alternativa de infraestrutura — decomposição na secção 7.

---

## 7. Estimativa de esforço para orçamentação

### Base de calibração

As estimativas abaixo não são valores de referência genéricos: foram calibradas contra o esforço **real registado neste projecto**, lido de `.pg/projects/odoo-triplex/PG_EFFORT_SYNC.json` — **676,7 horas em 154 tarefas**, entre 26/01/2024 e 31/07/2026. A distribuição por tarefa tem mediana de 1,0 h, p75 de 3,0 h e média de 4,4 h.

Âncoras usadas, todas tarefas reais deste projecto:

| Tarefa real | Horas | Serve de âncora a |
|---|---|---|
| [6349] Analytics Website Odoo — configuração Google Analytics | 3,2 | Configuração de website sem código (Via A) |
| [330] Módulo Whatsapp — instalação e configuração | 2,5 | Instalação e configuração de módulo de terceiros (Via B) |
| [966] Moradas de facturação e entrega | 1,5 | Ajuste de configuração no fluxo de venda (Via A) |
| Etiquetas A4 — adaptação do módulo A5 para A4 e instalação | 5,0 | Módulo `pg_` pequeno, com testes (Via C1) |
| [856] Adaptação Módulo Tecidos — estudo, implementação e testes | 9,0 | Módulo `pg_` com lógica de negócio e testes (Via C1) |
| [964] Packing List e Catálogo | 36,9 | Limite superior de módulo `pg_` com interface e relatório (Via C2) |

`INFERENCIA` — as estimativas são projecções por analogia com estas âncoras. Não substituem um orçamento formal, mas o intervalo é defensável perante o histórico.

### Via A — Configuração standard

| Actividade | Tipo | Horas (mín–máx) |
|---|---|---|
| Inventário por API dos métodos de entrega e provedores publicados | Investigação | 0,5 – 1,0 |
| Configuração dos países nos métodos de entrega | Parametrização | 0,5 – 1,0 |
| Configuração dos países nos provedores de pagamento | Parametrização | 0,5 – 0,5 |
| Pricelist e posição fiscal por grupo de países (opcional) | Parametrização | 0,5 – 1,0 |
| Testes dos três cenários da secção 4 | Validação | 1,0 – 1,5 |
| Registo da configuração e actualização do `PG_CONTEXT.md` | Consultadoria | 0,5 – 0,5 |
| **Total** | | **3,5 – 5,5 h** |

### Via B — Módulo da App Store

| Actividade | Tipo | Horas (mín–máx) |
|---|---|---|
| Compra e obtenção do build da série 17.0 | Consultadoria | 0,5 – 0,5 |
| Instalação em ambiente de teste | Parametrização | 0,5 – 1,0 |
| Configuração de países por produto | Parametrização | 1,0 – 2,0 |
| Testes de regressão no checkout (`website_sale_stock`, `website_sale_loyalty`, `website_sale_subscription`, módulos `pg_`) | Validação | 2,0 – 4,0 |
| Promoção a produção e registo no repositório | Suporte | 0,5 – 1,0 |
| **Total** | | **4,5 – 8,5 h** + €21 de licença |
| *Recorrente, por cada migração de série* | *Consultadoria* | *2,0 – 4,0 + nova licença* |

`FACTO OBSERVADO` — a Via B custa **mais horas que a Via A** e entrega o mesmo resultado para o requisito actual. As horas de configuração por produto dependem do número de produtos na loja, que está por validar.

### Via C1 — Regra global no checkout com mensagem própria

| Actividade | Tipo | Horas (mín–máx) |
|---|---|---|
| Análise e desenho (campo de configuração, âmbito multi-website) | Consultadoria | 1,0 – 1,0 |
| Módulo `pg_`: modelo, campo no `website`, override dos dois métodos | Desenvolvimento | 2,0 – 3,0 |
| Mensagem no cesto e no checkout | Desenvolvimento | 1,0 – 1,5 |
| Testes, incluindo o cenário de cesto só com serviços | Validação | 1,5 – 2,5 |
| Documentação e deploy | Suporte | 1,0 – 1,0 |
| **Total** | | **6,5 – 9,0 h** |

### Via C2 — Restrição por produto

| Actividade | Tipo | Horas (mín–máx) |
|---|---|---|
| Análise e desenho do modelo de dados | Consultadoria | 1,5 – 2,0 |
| Campo de países em `product.template` e vistas | Desenvolvimento | 2,0 – 3,0 |
| Verificação no cesto e no checkout, com avisos | Desenvolvimento | 3,0 – 4,0 |
| Filtro opcional no catálogo | Desenvolvimento | 2,0 – 4,0 |
| Testes | Validação | 3,0 – 4,0 |
| Documentação, formação e deploy | Formação | 2,0 – 3,0 |
| **Total** | | **13,5 – 20,0 h** |

### Via C3 — Fecho do catálogo por GeoIP

| Actividade | Tipo | Horas (mín–máx) |
|---|---|---|
| Módulo `pg_` no `ir.http` e configuração | Desenvolvimento | 3,0 – 5,0 |
| Instalação e validação da base GeoIP no servidor on-premise | Suporte | 1,0 – 2,0 |
| Testes com VPN e IPs estrangeiros | Validação | 2,0 – 3,0 |
| Documentação e deploy | Suporte | 1,0 – 1,5 |
| **Total no Odoo** | | **7,0 – 11,5 h** |
| **Alternativa em infraestrutura (nginx ou Cloudflare)** — recomendada | Suporte | **2,0 – 4,0 h** |

### Quadro-resumo para orçamentação

| Via | Horas | Licença | Recorrente por série |
|---|---|---|---|
| A — Configuração standard | 3,5 – 5,5 | 0 € | 0 |
| B — Módulo App Store | 4,5 – 8,5 | 21 € | 2,0 – 4,0 h + nova licença |
| C1 — Regra global `pg_` | 6,5 – 9,0 | 0 € | 0,5 – 1,0 h (revisão em migração) |
| C2 — Restrição por produto `pg_` | 13,5 – 20,0 | 0 € | 1,0 – 2,0 h (revisão em migração) |
| C3 — GeoIP no Odoo | 7,0 – 11,5 | 0 € | 0,5 – 1,0 h |
| C3 — GeoIP em infraestrutura | 2,0 – 4,0 | 0 € | 0 |

### Premissas da estimativa

- Horas de consultor e de desenvolvimento; não inclui gestão de projecto.
- Existe ambiente de teste disponível e representativo antes de configurar ou desenvolver.
- Não inclui formação a utilizadores finais, excepto onde indicado na Via C2.
- Não inclui a migração de série do Odoo em si, apenas o esforço incremental atribuível a esta funcionalidade.
- As vias não são cumulativas: A é a recomendada e as restantes só entram se o âmbito mudar.

### Conversão em valor

`PONTO POR VALIDAR` — a tarifa não vem do espelho do projecto. O modelo `doc_templates/assets/Estrutura Orçamentação.xlsx` traz, na aba `artigos`, 65 €/h para consultor e formador e 90 €/h para gestor de projecto, e um horizonte de 520 na aba `DB`. A aba `tarefas` tem, em todas as linhas, um **factor de dificuldade a 2** — que duplica o valor face a `horas × tarifa`. O próprio template de orçamentação avisa que este factor tem de ser confirmado como margem intencional antes de fechar valores, caso contrário deve ser posto a 1. Enquanto isso não estiver confirmado, este documento entrega **horas, não valores**.

---

## 8. Comparação e recomendação

| Critério | Via A — Standard | Via B — App Store | Via C1 — Dev `pg_` |
|---|---|---|---|
| Resolve o requisito actual | Sim | Sim, com redundância | Sim |
| Custo de licença | 0 € | 21 € por série | 0 € |
| Esforço inicial | 3,5 – 5,5 h | 4,5 – 8,5 h | 6,5 – 9,0 h |
| Custo por migração de série | 0 | 2,0 – 4,0 h + nova licença, **e o porte próprio é vedado pela licença** | 0,5 – 1,0 h, feito por nós |
| Granularidade por produto | Não | Sim | Não (ver C2) |
| Mensagem personalizada | Não | Sim | Sim |
| Código sob controlo da PG | n/a | Não | Sim |

**Recomendação final: `Configuracao standard` (Via A).**

Justificação da ordem obrigatória de decisão:

1. **Standard já disponível no projecto** — `delivery`, `payment` e `website_sale` estão instalados e resolvem o requisito na totalidade. É aqui que a análise fecha.
2. **Módulo standard adicional** — não existe, em 17.0 nem em 19.0, módulo standard Odoo para restrição de venda por país; a função vive nos módulos já instalados. Nada a adoptar.
3. **Odoo Studio** — não aplicável. Nenhuma das camadas envolvidas (disponibilidade de métodos de entrega, domínio de provedores de pagamento) se configura por Studio, e o `website_studio` instalado serve páginas e vistas, não routing nem disponibilidade.
4. **Custom** — desnecessário. Só entra se o requisito evoluir para mensagem própria (C1), granularidade por produto (C2) ou fecho do catálogo (C3).

---

## 9. Riscos, impactos e próximos passos

### Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Método de entrega publicado sem países preenchidos | Loja aberta a todos os países, sem aviso | Inventário completo dos métodos publicados antes de configurar; validação (c) da secção 4 |
| Catálogo com serviços ou digitais | Encomendas estrangeiras não travadas pela entrega | Restringir também os provedores de pagamento |
| Encomendas criadas por API ou importação sem país | Escapam ao filtro de pagamento | Validar na origem dos dados; fora do âmbito do website |
| Expectativa de "loja fechada" não alinhada | Cliente esperava não ser visto de fora | Explicar a distinção da secção 1 antes de configurar |

### Impacto no negócio

Nulo em SEO e em tráfego: o catálogo mantém-se indexável e visível. O impacto é no fecho da encomenda, que é exactamente o objectivo.

### Próximos passos

1. Confirmar a lista de países permitidos.
2. Inventariar por API os métodos de entrega e provedores de pagamento **publicados** no ambiente real — ver ponto por validar nº 2.
3. Configurar em ambiente de teste e correr os três cenários de validação da secção 4.
4. Promover a configuração e registar a decisão no `PG_CONTEXT.md`.

---

## 10. Pontos por validar

- [ ] **Países permitidos** — lista fechada, por confirmar com o negócio.
- [ ] **Módulos de recolha em loja** — o espelho `odoo_env.json` lista `website_sale_collect` e `website_sale_collect_wishlist` como instalados, mas esses módulos **não existem no source 17.0**; na série 17 o equivalente é `website_sale_picking` (que existe e está no source). Confirmar por API o que está realmente instalado, para não deixar um método de entrega fora da configuração. Encaixa no padrão já conhecido neste projecto: o que está no on-premise não coincide sempre com o repositório.
- [ ] **Composição do catálogo** — existem produtos de serviço ou digitais na loja? Determina se o passo 2 da Via A é obrigatório.
- [ ] **Série de destino** — esta análise foi validada em 17.0. Na 19.0 os mesmos mecanismos existem e o de entrega é mais rico (separador de disponibilidade com países, peso e volume máximos e etiquetas de produto), mas o detalhe do filtro no checkout não foi verificado em source 19.

---

## 11. Referências consultadas

**Projecto**
- `projects/odoo-triplex/PG_CONTEXT.md`
- `.pg/projects/odoo-triplex/project/odoo_env.json` — versão, edição, ambiente e módulos instalados
- `.pg/PREFLIGHT.json`

**Source Odoo 17.0 (`vendor/odoo_src`)**
- `community/addons/website_sale/models/res_country.py`
- `community/addons/website_sale/models/sale_order.py`
- `community/addons/website_sale/models/product_product.py`
- `community/addons/website_sale/models/product_template.py`
- `community/addons/website_sale/models/website.py`
- `community/addons/website_sale/controllers/main.py`
- `community/addons/delivery/models/delivery_carrier.py`
- `community/addons/payment/models/payment_provider.py`
- `community/addons/product/models/product_pricelist.py`
- `community/addons/website/models/ir_http.py`

**Documentação oficial**
- Odoo 17.0 — https://www.odoo.com/documentation/17.0/
- Métodos de entrega 17.0 — https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/inventory/shipping_receiving/setup_configuration/delivery_method.html
- Métodos de entrega 19.0 — https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/shipping_receiving/setup_configuration/new_delivery_method.html
- Licenças Odoo, OPL-1 — https://www.odoo.com/documentation/17.0/legal/licenses.html

**Odoo App Store (avaliados e descartados)**
- `ecommerce_country_product_restriction` — Aktiv Software, €21, OPL-1
- `website_country_restriction` — Webkul, €39,51, proprietário
- `bc_geolocation_restriction` — Barg Cloud, €24,01 — restringe logins de utilizadores do backend, não visitantes do site
- Geolocation IP Redirect — Webkul — redirecciona por idioma e moeda, não bloqueia

---

## Histórico de Versões

| Versão | Data | Autor | Alterações |
|---|---|---|---|
| 1.0 | 04/08/2026 | João Barros | Versão inicial. Análise das três vias, funil etapa a etapa, recomendação `Configuracao standard` |
| 1.1 | 04/08/2026 | João Barros | Nova secção 7 com estimativa de esforço decomposta por via, calibrada contra as 676,7 h reais registadas no projecto. Corrigido o enquadramento do custo de migração da Via B: não é dependência do fornecedor, é custo recorrente com o porte próprio vedado pela licença OPL-1 |
