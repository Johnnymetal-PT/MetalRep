# Triplex — Produção: tarefas a criar no projeto (reunião de 27/07/2026)

**Versão:** 1.1
**Data:** 27/07/2026
**Autor:** João Barros (Parâmetro Global)
**Origem:** [PRODUCAO_ACOES_REUNIAO_2026-07-27.md](PRODUCAO_ACOES_REUNIAO_2026-07-27.md)
**Projeto Odoo:** `Odoo-Triplex` (`project.project` id **62**)
**Etapas em uso no projeto:** Backlog → Sprint Backlog → Sprint in Progress → Sprint Complete

> Estado: **as 14 tarefas foram criadas no Odoo** (ids 6627 a 6640). Estimativas indicativas, para dimensionar o esforço — não são compromisso contratual. Referência de calibração: a tarefa `[2255] Etiquetas Oficinna22` consumiu 30,4 h.

---

## Resumo

| # | Tarefa | Odoo | Etapa | Est. | Depende de |
|---|---|---|---|---|---|
| T1 | Ambiente de teste com todos os módulos atualizados | 6627 | Sprint in Progress | 3 h | — |
| T2 | Shop Floor: operações independentes e sempre visíveis | 6628 | Sprint Backlog | 10 h | T1 |
| T3 | Shop Floor: cronómetros simultâneos por operação | 6629 | Sprint Backlog | 4 h | T2 |
| T4 | Empregados por operação (quantas pessoas, quanto tempo) | 6630 | Sprint Backlog | 6 h | T1 |
| T5 | Relatório de tempos por peça, operação e pessoa | 6631 | Backlog | 8 h | T4 |
| T6 | "Fechar produção" bloqueado até as 5 fases concluídas | 6632 | Sprint Backlog | 4 h | T2 |
| T7 | Fotografia do produto automática no cartão | 6633 | Sprint Backlog | 4 h | T1 |
| T8 | Tecido identificado no cartão | 6634 | Sprint Backlog | 4 h | T1 |
| T9 | Fotografia obrigatória da embalagem antes de fechar | 6635 | Sprint Backlog | 6 h | T1 |
| T10 | Perfil de acesso da oficina, sem valores | 6636 | Sprint Backlog | 6 h | — |
| T11 | Etiqueta de receção: sair o número da venda, não da compra | 6637 | Sprint Backlog | 6 h | T1 |
| T12 | Etiqueta de tecido: confirmar e formar a opção de etiqueta única | 6638 | Sprint Backlog | 2 h | T1 |
| T13 | Validar o planeamento da oficina contra o Excel | 6639 | Backlog | 4 h | — |
| T14 | Receção de material: responsável, fluxo e fotografias | 6640 | Backlog | 4 h | — |
| T15 | Simplificar o login de operador no Chão de Fábrica | 6653 | Sprint in Progress | 4 h | T1 |
| | **Total estimado** | | | **75 h** | |

> A T15 foi criada a 28/07/2026, depois das 14 iniciais (6627-6640), a pedido do cliente e fora da reunião de levantamento.

Caminho crítico: **T1 → T2 → T3/T6**. A T2 é a tarefa estruturante — resolve, de uma vez, a linearidade e o desaparecimento das operações sem material.

---

## T1 — Ambiente de teste com todos os módulos atualizados
**Etapa:** Sprint in Progress · **Estimativa:** 3 h · **Prazo:** antes das férias de agosto

Atualizar todos os módulos na base de teste e disponibilizá-la ao Nunes para avaliação antes da paragem de agosto.

**Porquê:** durante a reunião a base estava com módulos desatualizados, a dar erros, o que impediu demonstrar o comportamento em discussão. Sem isto, nada do resto é demonstrável nem testável.

**Critérios de aceitação**
- Todos os módulos `pg_*` atualizados na base de teste, sem erros no arranque
- Nunes com acesso confirmado e capaz de abrir o Chão de Fábrica
- Lista enviada ao cliente do que já deve ser avaliado

---

## T2 — Shop Floor: operações independentes e sempre visíveis
**Etapa:** Sprint Backlog · **Estimativa:** 10 h · **Depende de:** T1

As quatro operações (Corte, Costura, Espuma, Estofo) passam a estar visíveis e iniciáveis em qualquer ordem, independentemente da reserva de material. A Embalagem mantém-se como única fase final.

**Causa-raiz identificada (FACTO OBSERVADO):** o `pg_mrp_default_workorders` cria as ordens de trabalho com `state='pending'` ([mrp_production.py:35](../pg_mrp_default_workorders/models/mrp_production.py#L35)) e o Shop Floor esconde do cartão tudo o que esteja em `pending`/`waiting` (getter `workorders` em `enterprise/mrp_workorder/static/src/mrp_display/mrp_display_record.js:223-229`). No standard, `_compute_state` só promove a `ready` quando `production_availability == 'assigned'`, ou seja, com material reservado (`community/addons/mrp/models/mrp_workorder.py:150-166`).

**Terceira causa, encontrada a 28/07/2026 — a linearidade está nos dados:** o standard **acorrenta as operações em cadeia** quando as dependências de BoM não estão activas. Em `_link_workorders_and_moves` (`community/addons/mrp/models/mrp_production.py:1479-1484`), com `allow_workorder_dependencies` a False, cada ordem de trabalho recebe `blocked_by_workorder_ids = [ordem anterior]`. Não é obra de nenhum módulo `pg_`: é o comportamento por omissão do Odoo.

Medido em `triplex_test`: **1236** das 1985 ordens de trabalho em OFs abertas estão bloqueadas por outra, e são precisamente as semeadas pelo `pg_mrp_default_workorders` (sem `operation_id`). As operações de BoM têm **zero** dependências declaradas (`blocked_by_operation_ids`) e o grupo `mrp.group_mrp_workorder_dependency` nem existe na base — confirmando que a cadeia vem do ramo `else`. É esta cadeia que produz os 585 em `waiting`.

Logo a tarefa tem três frentes: (1) impedir a cadeia na criação, (2) limpar as 1236 já existentes, (3) tornar as operações visíveis mesmo sem material reservado.

**Critérios de aceitação**
- As 4 operações aparecem no cartão da OF mesmo sem material reservado
- Qualquer uma pode ser iniciada primeiro, sem ordem imposta
- Nenhuma dependência entre ordens de trabalho (`blocked_by_workorder_ids` vazio)
- O cartão indica se falta material (casco, tecido, metal) sem esconder as operações

**Tarefa existente relacionada:** `[775] TRP - Shop Floor` (Backlog) — candidata a absorver esta tarefa em vez de se criar nova

---

## T3 — Shop Floor: cronómetros simultâneos por operação
**Etapa:** Sprint Backlog · **Estimativa:** 4 h · **Depende de:** T2

Validar e corrigir o que for necessário para que a mesma peça possa contar tempo em duas operações ao mesmo tempo (ex.: Espuma e Corte), com iniciar/parar repetido e contagem separada por operação.

**FACTO OBSERVADO a 28/07/2026 — a simultaneidade já funciona.** Em `triplex_test` há **42 ordens de fabrico com tempos sobrepostos em operações diferentes**. Exemplo: a OF 1475 tem a operação 1739 a contar de 11/06/2026 11:49 a 17:04 e a 1738 de 13:34 a 17:04 — quase três horas e meia em paralelo. Não há exclusividade a corrigir no standard.

O que restava do bloqueio era **visibilidade**, não simultaneidade, e resolve-se na T2. Esta tarefa reduz-se a validar o iniciar/parar repetido e a leitura por operação no back office, mais formação. A estimativa de 4 h deve baixar.

**Critérios de aceitação**
- Duas operações da mesma OF em curso simultaneamente, cada uma com o seu tempo
- Iniciar/parar várias vezes sem perda do tempo já registado
- Tempo de cada operação consultável em separado no back office

---

## T4 — Número de pessoas por registo de tempo
**Etapa:** Sprint Backlog · **Estimativa:** 6 h · **Depende de:** T1

> **Corrigido a 28/07/2026** face à versão 1.1, que assumia a criação de um empregado por operador. Não é isso que o cliente quer.

Ao registar o tempo, o responsável indica **a quantas pessoas** aquele tempo corresponde. O tempo continua a ser registado de forma natural (iniciar/parar); acrescenta-se apenas o número de pessoas. Essa informação tem de chegar à **App de Planeamento Oficinna22**.

**Porquê assim e não com a funcionalidade nativa:** os únicos empregados registados no Odoo são os **responsáveis de cada centro de trabalho** — `FACTO OBSERVADO` em `triplex_test`: os `hr.employee` com PIN são `Corte e Costura`, `Espuma`, `Estofo`, `Embalagem`, `Armazém` e `Receção de Material`, um por centro de trabalho (mais 4 pessoas de back office sem PIN). A funcionalidade nativa de múltiplos operadores (`employee_ids`, painel com PIN) exigiria um `hr.employee` por operador, o que o cliente não quer. Sem o número de pessoas, o tempo registado diz "a Espuma levou 3 h", não "3 pessoas × 1 h".

**FACTO OBSERVADO:** o registo de tempo já grava o responsável — 222 dos 252 registos de `mrp.workcenter.productivity` têm `employee_id` preenchido. Falta só a contagem de pessoas.

**Critérios de aceitação**
- Ao parar/registar tempo, é possível indicar o número de pessoas
- O número fica associado ao registo de tempo, não à operação inteira (o mesmo centro pode ter 2 pessoas numa sessão e 4 na seguinte)
- Horas-pessoa por peça e centro de trabalho visíveis na App de Planeamento Oficinna22
- Sem criar empregados novos nem exigir login individual (não acarreta licenças)

**Ponto por decidir:** o valor por omissão do número de pessoas — 1, ou obrigar sempre a indicar. Com omissão a 1 nunca há registos vazios, mas passa a ser possível esquecer e subcontar.

---

## T15 — Simplificar o login de operador no Chão de Fábrica
**Odoo:** 6653 · **Etapa:** Sprint in Progress · **Estimativa:** 4 h (indicativa) · **Depende de:** T1
**Pedido em:** 28/07/2026, fora da reunião

Chegar ao login de operador exige demasiados cliques. O objectivo é encurtar o caminho, idealmente com o teclado de PIN à distância de um toque.

**FACTO OBSERVADO (source):** o fluxo actual passa pelo painel lateral de empregados (`enterprise/mrp_workorder/static/src/mrp_display/employees_panel.xml`). Entrar com um operador novo implica: abrir o painel → botão **"Add Operator"** (`popupAddEmployee`) → escolher o empregado numa lista → introduzir o PIN (`components/pin_popup.js`). Trocar de operador já ligado é um clique no painel (`setSessionOwner`).

**POR VALIDAR:** como é aberto o painel neste ecrã (o `control_panel.xml` não o referencia, pelo que a visibilidade é controlada noutro sítio) e quantos toques são no tablet real da oficina. Sem medir isso não há estimativa honesta.

**O problema real é de acessibilidade, não de contagem de cliques** (esclarecido pelo cliente a 28/07/2026): o `Add Operator` está escondido atrás de um ícone pequeno e pouco legível, num tablet, para operadores mais velhos e sem prática com tecnologia. Um caminho com menos cliques mas ainda dependente de um ícone pequeno **não resolve**.

Critério de aceitação, portanto: o ponto de entrada tem de ser **grande, com texto e sempre visível** — não um símbolo. Alvo de toque adequado a dedo em tablet.

**Direcções possíveis, por ordem de custo:** painel de empregados aberto por omissão, com o botão em tamanho e texto legíveis; pré-selecionar o responsável do centro de trabalho e pedir apenas o PIN num teclado grande; ou entrada por leitura de cartão, que elimina o ecrã — nenhum dos 10 empregados tem `barcode` preenchido hoje, e o Shop Floor suporta-o (`get_employee_barcode` em `mrp_workcenter.py:35`).

---

## T5 — Relatório de tempos por peça, operação e pessoa
**Etapa:** Backlog · **Estimativa:** 8 h · **Depende de:** T4

Expor no planeamento a leitura pedida na reunião: por peça, que pessoas trabalharam, em que centro de trabalho e quanto tempo.

**Critérios de aceitação**
- Vista/relatório por ordem de fabrico com operação, operadores e tempo
- Acessível a partir do planeamento da oficina
- Totais por peça e por centro de trabalho

---

## T6 — "Fechar produção" bloqueado até as 5 fases concluídas
**Etapa:** Sprint Backlog · **Estimativa:** 4 h · **Depende de:** T2

O botão de fechar a produção fica visível mas não clicável enquanto existirem operações não concluídas.

**Critérios de aceitação**
- Botão presente e inactivo com operações em aberto; activo quando as 5 estão concluídas
- Mantém-se o comportamento nativo dos dois passos da Embalagem: concluir a operação (peça embalada e encostada) e, mais tarde, fechar a produção
- O fecho continua a ser por produto/OF; a encomenda fecha pelo back office quando o último produto fecha

---

## T7 — Fotografia do produto automática no cartão
**Etapa:** Sprint Backlog · **Estimativa:** 4 h · **Depende de:** T1

O cartão passa a mostrar a fotografia do produto sem preenchimento manual por ordem.

**Causa identificada (FACTO OBSERVADO):** o `pg_mrp_shopfloor_cards` lê os campos Studio `x_studio_imagem_estofo` e `x_studio_ficheiro_pdf` da OF ([mrp_display_action_patch.js:8-12](../pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js#L8-L12)), de preenchimento manual — foi por isso que nas ordens abertas na reunião (2367, 2505, 2565, 2646) não aparecia imagem.

**Critérios de aceitação**
- A imagem do produto aparece por defeito, sem intervenção manual
- O campo Studio continua a poder sobrepor-se, quando preenchido
- Funciona em ordens já existentes, não só nas criadas depois da alteração

---

## T8 — Tecido identificado no cartão
**Etapa:** Sprint Backlog · **Estimativa:** 4 h · **Depende de:** T1

Mostrar no cartão qual o tecido da peça.

**Caso de negócio (do cliente):** várias cadeiras iguais em estrutura, quantidades e polimento, diferindo só no tecido (A, B, C) — hoje os cartões mostram apenas a referência da cadeira, com risco real de se dar baixa do tecido errado.

**FACTO OBSERVADO:** o dado já existe na OF — o `pg_tecidos` extrai os materiais da descrição da linha de venda para `description_sale` e constrói uma BoM dedicada por ordem ([mrp_production.py:41-148](../pg_tecidos/models/mrp_production.py#L41-L148)). Falta apenas expô-lo.

**Critérios de aceitação**
- Tecido (e restantes materiais relevantes) visível no cartão
- Em peças com vários tecidos, cada um identificado pela sua parte (costa exterior, interior e assento, vivos)

---

## T9 — Fotografia obrigatória da embalagem antes de fechar
**Etapa:** Sprint Backlog · **Estimativa:** 6 h · **Depende de:** T1

Acrescentar a fotografia da embalagem final ao diálogo obrigatório de fecho da produção.

**Estado (FACTO OBSERVADO):** o `pg_mrp_shopfloor_packing` já intercepta o fecho e já obriga volumes, peso e dimensões C/A/L por volume ([__manifest__.py:12-38](../pg_mrp_shopfloor_packing/__manifest__.py#L12-L38)). **Falta só a fotografia.**

**Razão de negócio:** a logística consulta estes dados para organizar a expedição; evita ter de ir ao armazém pesar, medir e reimprimir etiquetas.

**Critérios de aceitação**
- Fotografia da embalagem obrigatória, sem ela a produção não fecha
- Fotografia consultável a partir da OF e da expedição
- Peso e dimensões mantêm o comportamento actual

---

## T10 — Perfil de acesso da oficina, sem valores
**Etapa:** Sprint Backlog · **Estimativa:** 6 h

Perfil de leitura para a oficina: produção, planeamento, estruturas e origem — **sem valores nem preços**. Condição expressa do cliente para dar acesso.

**Critérios de aceitação**
- Conta da oficina abre planeamento e produção sem ver preços em nenhum ecrã (venda, compra, produto, OF)
- Conta partilhada mantida (Nunes/Ângelo), identificação do operador por código
- Reutilizar o que já existe no projeto antes de criar novo: `pg_hide_price_snippet`, `pg_comercial_order_visibility` e o grupo de leitura já criado para ordens de venda

---

## T11 — Etiqueta de receção: sair o número da venda, não da compra
**Etapa:** Sprint Backlog · **Estimativa:** 6 h · **Depende de:** T1

Corrigir a resolução da venda de origem na etiqueta ZPL de receção de material. Hoje, na maior parte das receções, sai o número da compra — e a compra sozinha não diz a que peça pertence.

**DIAGNÓSTICO CONFIRMADO** na base de produção (27/07/2026):

A etiqueta imprime `enc_val` = `so_id.name` → senão `group_id.name` → senão `origin` ([stock_picking.py:81](../pg_print_zpl_label/models/stock_picking.py#L81)). O `so_id` vem do `pg_backtrack_fields`, calculado pela cadeia `picking.origin` → `purchase.order` → `po.origin` → `mrp.production` → `mo.origin` → `sale.order` ([stock_picking.py:17-43](../pg_backtrack_fields/models/stock_picking.py#L17-L43)).

**O defeito:** quando uma compra cobre **várias** ordens de fabrico, o `po.origin` é uma lista separada por vírgulas — a compra `P03376` tem `origin = "Ofici/MO/04323, Ofici/MO/04324"` — e a pesquisa é feita com a string inteira, pelo que nunca encontra a OF.

**Medido em produção:** `so_id` está vazio em **1891 de 2195 receções de 2026 (86 %)**. Com o `so_id` vazio, a etiqueta cai no `group_id`, que nessas compras é o número da compra.

Três situações distintas, e só uma é corrigível por código:

| Situação | Exemplo | Hoje imprime | Depois da correção |
|---|---|---|---|
| Compra que cobre uma ou várias OF | `P03376` → `Ofici/MO/04323, Ofici/MO/04324` | compra ✗ | venda ✓ |
| Compra gerada pela cadeia de procurement da venda | picking com `group_id = S02662` | venda ✓ (pela alternativa) | venda ✓ |
| Compra para stock, sem origem nenhuma | `P03430`, `P03437` (`origin` vazio) | compra | compra — **não há venda para imprimir** |

O terceiro caso não é um defeito: só se resolve com alteração de processo (o comprador registar a venda na compra).

**Nota de desenho:** uma compra pode cobrir várias OF e várias vendas, pelo que a venda deve ser resolvida **por linha de movimento**, não por picking — o ZPL já percorre os movimentos um a um.

**Interação a ter em conta:** o `pg_sale_purchase_link` (já instalado em produção) faz as compras criadas à mão nascerem com `origin = S0xxxx`, isto é, a **venda** e não a OF. O `_compute_so_fields` actual não sabe resolver esse caso — a correção tem de cobrir os dois caminhos.

**Critérios de aceitação**
- Receção de uma compra que cobre uma ou várias OF resolve a venda e imprime o número da venda
- Compra com `origin` a apontar directamente para a venda também resolve
- Compra para stock, sem ligação a venda, mantém o comportamento actual e isso fica documentado
- Etiqueta validada em impressão real na Zebra

**Tarefa existente relacionada:** `[867] Etiquetas A4` (Sprint Backlog)

---

## T12 — Etiqueta de tecido: confirmar e formar o uso da opção de etiqueta única
**Etapa:** Sprint Backlog · **Estimativa:** 2 h · **Depende de:** T1

**JÁ IMPLEMENTADO** — confirmado na base de produção (27/07/2026). Não é desenvolvimento: é confirmação e formação.

A funcionalidade existe e é a que o cliente descreveu de memória ("acho que há um botãozinho"): o `pg_print_zpl_label` lê a marca Studio `x_studio_tecido` no picking e imprime `label_count = 1` quando está activa, em vez de uma etiqueta por unidade ([stock_picking.py:77](../pg_print_zpl_label/models/stock_picking.py#L77) e [:96](../pg_print_zpl_label/models/stock_picking.py#L96)). O campo existe em `stock.picking` (booleano, "Tecido") e está no formulário (vista *Odoo Studio: stock.picking.form customization*, id 3511).

O caso relatado — 50 e tantas cadeiras a gerar mais de 100 etiquetas — acontece quando a marca **não é activada**.

**Critérios de aceitação**
- Demonstrado em teste: com a marca "Tecido" activa sai 1 etiqueta; sem ela sai uma por unidade
- Equipa de receção informada de onde está a marca e quando a usar
- Avaliar renomear a marca (ex.: "imprimir etiqueta única"), já que se aplica a qualquer artigo e não só a tecido

---

## T13 — Validar o planeamento da oficina contra o Excel
**Etapa:** Backlog · **Estimativa:** 4 h

Validar campo a campo o planeamento já implementado (`pg_planeamento_oficina`) contra o Excel do cliente: por encomenda, estado de cada tipo de material (tecido, casco, inox/metal, embalagens) como encomendado/recebido, com datas, mais lista de produção e lista de compras.

**Critérios de aceitação**
- Todas as colunas do Excel têm correspondência, ou está registado o que se decidiu não replicar
- Validado pelo Nunes sobre dados reais

---

## T14 — Receção de material: responsável, fluxo e fotografias
**Etapa:** Backlog · **Estimativa:** 4 h

Fechar o procedimento de receção: quem recebe (responsável + suplente), como marca a receção para libertar a produção, e anexar as fotografias do material recebido.

**Decisão do cliente a respeitar:** os anexos ficam **na compra** — é aí que o processo se fecha — com a ligação à venda e à OF a ser automática, para consulta anos depois (metais, acabamentos, quem recebeu, em que data). A consulta em dois cliques (venda → compras → receção) foi aceite.

**Natureza:** nativo (anexos em compras/receções) + procedimento + formação. Nada a desenvolver.

**Tarefa existente relacionada:** `[6011] Formação na Produção` (Sprint in Progress)

---

## Fase posterior (registar em Backlog, sem estimativa)

| Item | Nota |
|---|---|
| Controlo de qualidade com fotografia obrigatória antes de fechar | Necessidade distinta da fotografia da embalagem; existe módulo nativo de Qualidade |
| Monitor por secção na oficina | "Meter só um monitorzinho" pendurado por zona |

**Não convertido em tarefa:** a folha manual em papel **mantém-se** a acompanhar a peça (decisão do cliente, não é para eliminar); e a reunião de arranque de setembro, que cabe em `[292] Acompanhamento`.

---

## Canal de acesso à produção da Triplex (resolvido)

O diagnóstico das etiquetas exigiu acesso à base de produção, porque a etiqueta em uso vive na base de dados e no módulo instalado, não nos relatórios do repositório. Ficou criada a ligação sancionada:

- `pg.odoo.connection` **id 23**, repositório `Triplex` (id 91), finalidade `production`, `https://intranet.triplexgroup.pt`, base `triplex`
- consultas a partir de agora: `pg_odoo_client_query.ps1 -ProjectKey odoo-triplex -Purpose production ...`

**Constatação com valor para o projeto:** `PG_Etiquetas_A4` está instalado em produção mas **não tem lá nenhum `ir.actions.report`** — os relatórios de picking em uso são cinco "Relatório de Transferência" do Studio, dois deles `qweb-text` (ZPL). A etiqueta que a produção realmente usa é a do `pg_print_zpl_label`, gerada em ZPL e enviada para a Zebra via IoT Box. Confirma o padrão já conhecido de que o que está em produção não se deduz do repositório.

---

## Histórico de versões

| Versão | Data | Autor | Alterações |
|---|---|---|---|
| 1.0 | 27/07/2026 | João Barros | Divisão em tarefas a partir da reunião de 27/07/2026 |
| 1.1 | 27/07/2026 | João Barros | Diagnóstico de T11 e T12 confirmado em produção; T12 reclassificada como já implementada; tarefas criadas no Odoo (6627-6640) |
