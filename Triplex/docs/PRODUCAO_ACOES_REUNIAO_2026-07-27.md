# Triplex — Produção / Chão de Fábrica: ações da reunião de 27/07/2026

**Versão:** 1.1
**Data:** 27/07/2026
**Tarefas no Odoo:** [PRODUCAO_TAREFAS_2026-07-27.md](PRODUCAO_TAREFAS_2026-07-27.md) — 14 tarefas, ids 6627 a 6640
**Autor:** João Barros (Parâmetro Global)
**Fonte:** `docs/Produção Oficinna22.docx` (transcrição automática Teams, 43m17s)
**Estado:** Rascunho — a validar com a Triplex
**Ambiente de referência:** Odoo 17.0 Enterprise, on-premise

> Nota de leitura: a transcrição é automática e tem ruído significativo de reconhecimento de voz. Este documento é a interpretação do que foi acordado, cruzada com o código dos módulos `pg_*` do repositório e com o source Odoo 17.0. Os pontos em que a transcrição não é conclusiva estão marcados como `POR VALIDAR`.

---

## 1. Conclusão central da reunião

O Chão de Fábrica (Shop Floor) tal como está hoje não serve o processo da Triplex, porque **assume um fluxo linear** (uma operação a seguir à outra) e a Triplex **não trabalha de forma linear**: a mesma peça pode começar pela espuma, pelo corte ou pelo corte e costura, e volta várias vezes a secções anteriores.

Decisão: **inverter a lógica** — as operações de fabrico passam a estar todas abertas e independentes, com uma única fase obrigatoriamente final (Embalagem).

Fluxo acordado:

```
CORTE ─┐
COSTURA├── (4 operações independentes, sem ordem imposta,
ESPUMA │    tempos contados em separado, podem estar activas em simultâneo)
ESTOFO ─┘
            │
            └──► EMBALAGEM (única fase final) ──► Fechar produção
```

---

## 2. Ações no Chão de Fábrica

### A1 — Operações todas disponíveis, sem ordem imposta
**Pedido:** ter a lista geral das ordens de fabrico e cada secção entra, registra o tempo e marca como concluído, independentemente da ordem das outras. Só a Embalagem é obrigatoriamente a última.

**FACTO OBSERVADO (código):** o módulo `pg_mrp_default_workorders` semeia as 5 ordens de trabalho em todas as OFs com `state = 'pending'` ([mrp_production.py:35](../pg_mrp_default_workorders/models/mrp_production.py#L35)); o Shop Floor **esconde do cartão** todas as operações em `pending` ou `waiting` (`enterprise/mrp_workorder/static/src/mrp_display/mrp_display_record.js`, getter `workorders`, linhas 223-229). No standard 17.0, `_compute_state` só promove a operação a `ready` quando `production_availability == 'assigned'`, isto é, **quando o material está reservado** (`community/addons/mrp/models/mrp_workorder.py:150-166`).

**Consequência:** é esta a causa técnica de duas queixas da reunião ao mesmo tempo — as operações "não aparecem" e o fluxo "parece linear".

**Ação:** garantir que as 4 operações (Corte, Costura, Espuma, Estofo) ficam visíveis e iniciáveis em qualquer ordem, independentemente da reserva de material, e **não** usar dependências entre ordens de trabalho (`blocked_by_workorder_ids`).

**Natureza:** `Customizacao leve` (patch ao Shop Floor, na linha do que os módulos `pg_mrp_shopfloor_*` já fazem).

---

### A2 — Cronómetro independente por operação, com paragens e simultaneidade
**Pedido:** iniciar/parar tempo em qualquer operação, de forma aleatória e quantas vezes for preciso; poder ter a mesma peça a contar tempo em Espuma e em Corte ao mesmo tempo; o tempo é contabilizado separadamente por operação.

**Ação:** validar em ambiente de teste que o standard permite várias operações da mesma OF em `progress` simultaneamente (o bloqueio identificado em A1 é de visibilidade, não de exclusividade). Confirmar iniciar/parar repetido sem perda de tempo registado.

**Natureza:** `Configuracao standard` — `POR VALIDAR` em teste.

---

### A3 — Número de pessoas por operação e tempo por pessoa
**Pedido:** saber quantas pessoas estiveram em cada peça, em que centro de trabalho e quanto tempo demoraram, para os tempos serem próximos da realidade. Aceite pelo cliente que **a conta de utilizador é independente do centro de trabalho** — pode haver 30/40 operadores na mesma conta, identificando-se por código.

**FACTO OBSERVADO (source):** o Shop Floor Enterprise suporta nativamente múltiplos operadores por ordem de trabalho — `employee_ids` ("Working employees"), `employee_assigned_ids`, `allowed_employees` e painel de empregados com PIN (`enterprise/mrp_workorder/models/mrp_workorder.py:56-68`; `mrp_display/employees_panel.js`). O tempo é registado por empregado.

**Ação:** activar e configurar os Empregados em Fabrico, associar empregados aos centros de trabalho e distribuir os códigos/PIN. Depois, ligar ao planeamento: relatório por peça → centro de trabalho → pessoas → tempo.

**Natureza:** `Configuracao standard` para a recolha; o relatório ligado ao planeamento é `Customizacao leve`.

---

### A4 — "Fechar produção" só depois de todas as fases concluídas
**Pedido:** o botão de fechar a produção fica visível mas **não clicável** até as 5 fases estarem concluídas.

**Ação:** bloquear o botão enquanto existirem operações não concluídas na OF.

**Natureza:** `Customizacao leve`.

---

### A5 — Embalagem mantém os dois passos (confirmado, sem trabalho novo)
**Confirmado na reunião:** a Embalagem tem dois momentos distintos e é assim que deve ficar:
1. marcar a operação de embalagem como concluída (peça embalada e encostada);
2. **fechar a produção** mais tarde, quando a peça desce ao armazém para expedição.

Ficou também esclarecido que o fecho é **por produto/ordem de fabrico**, não por encomenda: numa encomenda com 5 produtos, fecha-se cada um à medida que fica pronto e a encomenda é fechada pelo back office quando o último produto fecha.

**Natureza:** comportamento nativo — nada a desenvolver. Fica como ponto de **formação**.

---

### A6 — Fotografia do produto no cartão do Chão de Fábrica
**Pedido:** o operador tem de ver a fotografia do produto no cartão, para saber o que está a produzir/embalar, **sem** que alguém tenha de a carregar manualmente em cada ordem.

**FACTO OBSERVADO (código):** o `pg_mrp_shopfloor_cards` já mostra os botões "Preview PDF" e "Preview Image" no cartão, mas lê os campos Studio da ordem de fabrico `x_studio_imagem_estofo` e `x_studio_ficheiro_pdf` ([mrp_display_action_patch.js:8-12](../pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js#L8-L12)), que são de **preenchimento manual**. É por isso que nas ordens abertas durante a reunião (2367, 2505, 2565, 2646) não aparecia imagem.

**Ação:**
- passar a herdar automaticamente a imagem do produto, mantendo o campo Studio como excepção manual;
- **atualizar todos os módulos no ambiente de teste** — durante a reunião a base estava com módulos desatualizados e a dar erros, o que impediu a demonstração.

**Natureza:** `Customizacao leve`.

---

### A7 — Tecido identificado no cartão de produção
**Pedido:** o cartão tem de mostrar **qual o tecido** da peça. Caso concreto trazido pelo cliente: várias cadeiras iguais na estrutura, quantidades e polimento, diferindo **só no tecido** (A, B, C) — hoje os três cartões mostram apenas a referência da cadeira, com risco de se dar baixa do tecido errado. Confirmado em reunião como viável ("é pacífico").

**FACTO OBSERVADO (código):** a informação já existe na ordem de fabrico — o `pg_tecidos` extrai os materiais da descrição da linha de venda para `description_sale` e constrói uma BoM dedicada por OF ([mrp_production.py:41-148](../pg_tecidos/models/mrp_production.py#L41-L148)). Falta expor esse dado no cartão do Shop Floor.

**Natureza:** `Customizacao leve`.

---

### A8 — Fotografia da embalagem obrigatória antes de fechar a produção
**Pedido:** antes de carregar em "Fechar produção", obrigar a registar **dimensões, peso e fotografia da embalagem final**.
**Razão de negócio:** a logística (Sandra) consulta estes dados para organizar a expedição, e evita-se ter de ir ao armazém pesar, medir e reimprimir etiquetas.

**FACTO OBSERVADO (código):** o `pg_mrp_shopfloor_packing` já intercepta o fecho da produção e **já obriga** volumes, peso e dimensões C/A/L por volume ([__manifest__.py:12-38](../pg_mrp_shopfloor_packing/__manifest__.py#L12-L38); o diálogo tem `packing_volumes`, `packing_weight` e as linhas de dimensões). **Falta apenas o campo de fotografia da embalagem.**

**Ação:** acrescentar o campo de fotografia (obrigatório) ao diálogo de packing list do Shop Floor.

**Natureza:** `Customizacao leve` — extensão de módulo já existente.

---

## 3. Ações em materiais, receção e planeamento

### B1 — Ver a ordem de fabrico mesmo sem material, com aviso do que falta
**Pedido:** hoje a ordem só fica utilizável quando o material está recepcionado, o que impede planear. O cliente quer ver a ordem sempre, com um sinal (asterisco/aviso) a indicar se o material — casco, tecido, metal — já chegou ou não.

**FACTO OBSERVADO:** mesma causa técnica de **A1** (`production_availability` e o filtro de `pending`/`waiting` no cartão). Resolve-se em conjunto.

**Natureza:** `Customizacao leve` (visibilidade) + `Configuracao standard` (indicador de disponibilidade).

---

### B2 — Receção marca a disponibilidade e liberta o planeamento
**Fluxo acordado:** encomenda de venda → compras derivadas dessa encomenda (casco, latão, tecido, metal) → quem recebe marca a receção no Odoo → o material passa a disponível e a produção/planeamento actualizam-se automaticamente, sem intervenção adicional.

**Natureza:** `Configuracao standard` + formação de quem faz a receção.

---

### B3 — Painel de planeamento por encomenda e por tipo de material
**Pedido:** manter a leitura do Excel actual: por encomenda, o estado de cada tipo de material (tecido, casco, inox/metal, embalagens) como encomendado / recebido, com as respectivas datas, mais a lista de produção e a lista de compras.

**FACTO OBSERVADO (código):** o `pg_planeamento_oficina` já replica esta vista (modelos `pg.planeamento.semana` / `pg.planeamento.line`, relatório e XLSX). Foi mostrado na reunião e reconhecido como "o vosso Excel".

**Ação:** validar campo a campo contra o Excel e completar o que faltar.

**Natureza:** já implementado — falta validação com o cliente.

---

### B4 — Definir quem faz a receção
**FACTO OBSERVADO:** na reunião não ficou claro quem recebe o material ("alguém deve estar a receber, não sei a quem é que vai receber"). Ficou o acordo de designar um **responsável de receção e um suplente**.

**Natureza:** organizacional, do lado da Triplex — `POR VALIDAR`.

---

### B5 — Fotografias e histórico anexados à compra
**Pedido:** quem recebe o material tira 2/3 fotografias (ex.: do casco) e anexa-as. O cliente quer explicitamente que os anexos fiquem **na compra** — é aí que o processo se fecha — e que a ligação à venda e à ordem de fabrico seja automática, para poder consultar anos depois como foi feita uma peça específica (metais, acabamentos, quem recebeu, em que data).

Aceite que a consulta a partir da venda seja em dois cliques (venda → compras → receção).

**Natureza:** nativo (anexos em compras/receções) + **formação**. Nada a desenvolver.

---

## 4. Etiquetas — diagnosticado em produção em 27/07/2026

As duas dúvidas que ficaram em aberto na reunião foram fechadas por consulta à base de produção. A etiqueta em uso é a **ZPL do `pg_print_zpl_label`**, enviada para a Zebra pela IoT Box — e não os relatórios A4 do repositório (o `PG_Etiquetas_A4` está instalado mas não tem nenhum `ir.actions.report` em produção).

### C1 — A etiqueta tem de sair com o número da venda → **defeito confirmado**
**Pedido:** quando se manda material para um prestador (ex.: polidor) ou se recebe material, a etiqueta sai com o **número da compra** e devia sair com o **número da venda**.

**FACTO OBSERVADO:** a etiqueta imprime `so_id.name` → senão `group_id.name` → senão `origin` ([stock_picking.py:81](../pg_print_zpl_label/models/stock_picking.py#L81)). O `so_id` é calculado pela cadeia `picking.origin` → compra → `po.origin` → OF → `mo.origin` → venda ([pg_backtrack_fields/stock_picking.py:17-43](../pg_backtrack_fields/models/stock_picking.py#L17-L43)). **Quando uma compra cobre várias ordens de fabrico, o `po.origin` é uma lista separada por vírgulas** (a compra `P03376` tem `origin = "Ofici/MO/04323, Ofici/MO/04324"`) e a pesquisa é feita com a string inteira — nunca encontra a OF.

**Medido em produção:** o `so_id` está vazio em **1891 de 2195 receções de 2026 (86 %)**. Sem ele, a etiqueta cai no `group_id`, que nessas compras é o número da compra.

Nas compras geradas pela cadeia de procurement da venda, o `group_id` já é a venda (ex.: `S02662`) e a etiqueta sai correcta. Nas compras para stock, sem qualquer origem (`P03430`, `P03437`), **não existe venda para imprimir** — esse caso só se resolve por processo, não por código.

→ Tarefa **T11** (Odoo 6637), 6 h.

---

### C2 — Imprimir uma etiqueta em vez de uma por unidade → **já existe**
**Pedido:** imprimir **uma só etiqueta** quando o artigo é rolo/lote (20 m de tecido = 1 etiqueta, não 20).

**FACTO OBSERVADO:** a funcionalidade existe e é a que o cliente descreveu de memória. O `pg_print_zpl_label` lê a marca Studio `x_studio_tecido` no picking e imprime `label_count = 1` em vez de uma etiqueta por unidade ([stock_picking.py:77](../pg_print_zpl_label/models/stock_picking.py#L77) e [:96](../pg_print_zpl_label/models/stock_picking.py#L96)). O campo existe em `stock.picking` e está no formulário (vista Studio id 3511). O caso das 50 cadeiras com mais de 100 etiquetas acontece quando a marca **não é activada**.

→ Tarefa **T12** (Odoo 6638), 2 h — confirmação e formação, não desenvolvimento.

---

## 5. Acessos e utilizadores

### D1 — Acesso ao planeamento para a oficina
Dar acesso à app de planeamento/produção ao pessoal da oficina. Confirmado que **conta partilhada é aceitável** (Nunes e Ângelo já usam a mesma), porque a conta é independente do centro de trabalho e o operador identifica-se por código. Motivo assumido: cada login por pessoa acarreta custo de licença.

### D2 — Sem valores visíveis nessa conta
**Condição imposta pelo cliente:** o acesso pode ser de leitura, mas **não pode mostrar valores/preços** — só estruturas, origem e informação de produção. Ficou acordado ocultar os valores nessa conta.

**Ação:** definir o perfil de acesso da oficina (leitura, sem valores). Avaliar reutilização do que já existe no projeto (`pg_hide_price_snippet`, `pg_comercial_order_visibility` e o grupo de leitura já criado para o acesso a ordens de venda).

**Natureza:** `Configuracao standard` (grupos/ACL) com apoio dos módulos existentes.

---

## 6. Fases posteriores (fora do âmbito imediato)

| Item | Nota da reunião |
|---|---|
| Controlo de qualidade com fotografia obrigatória antes de fechar | Reconhecido como necessidade distinta da fotografia da embalagem; existe módulo nativo de Qualidade. Fase posterior. |
| Monitor por secção na oficina | "Meter só um monitorzinho" pendurado por zona. Fase posterior. |
| Folha manual em papel | **Mantém-se** a acompanhar a peça — confirmado pelo cliente. Não é para eliminar nesta fase. |

---

## 7. Calendário acordado

| Quando | O quê |
|---|---|
| Antes das férias | Parâmetro Global envia a versão de teste, com **todos os módulos atualizados**, para o Nunes olhar e dizer o que serve e o que não serve |
| 15 a 31 (agosto — `POR VALIDAR`) | Triplex fechada para férias |
| Dia 1 de setembro | Retoma; reunião no arranque do mês para decidir o que fica e o que muda, e avançar diretamente |

---

## 8. Pontos por validar

- [ ] Mês do fecho de férias (transcrição diz "de 15 a 31" sem indicar o mês) — Triplex
- [ ] Quem é o responsável de receção de material e o suplente — Triplex
- [x] ~~Estado real das etiquetas: sai o número da compra ou da venda? (C1)~~ — resolvido em 27/07/2026: defeito confirmado, ver secção 4
- [x] ~~Existe hoje a opção de imprimir uma única etiqueta para tecido/rolo? (C2)~~ — resolvido em 27/07/2026: existe, ver secção 4
- [ ] Perfil de acesso da oficina: só leitura de produção e planeamento, sem valores — a confirmar com a Triplex antes de aplicar
- [ ] Participantes exactos da reunião: a transcrição atribui todas as falas a um único canal ("Parâmetro + João Barros"); identificados por nome no diálogo: João Barros (PG), Nunes (produção), com referências a Ângelo, Sara e Sandra

---

## 9. Referências consultadas

**Projeto**
- `docs/Produção Oficinna22.docx` — transcrição de origem
- [PG_CONTEXT.md](../PG_CONTEXT.md) — Odoo 17.0 Enterprise on-premise; marco "Produção"
- [pg_mrp_default_workorders/models/mrp_production.py](../pg_mrp_default_workorders/models/mrp_production.py)
- [pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js](../pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js)
- [pg_mrp_shopfloor_packing/__manifest__.py](../pg_mrp_shopfloor_packing/__manifest__.py)
- [pg_tecidos/models/mrp_production.py](../pg_tecidos/models/mrp_production.py)
- `pg_planeamento_oficina/` — planeamento da oficina (modelos, vistas, relatório, XLSX)

**Source Odoo 17.0** (`vendor/odoo_src`, resolvido em `C:\Users\Utilizador\.pg\odoo_src\17.0`)
- `community/addons/mrp/models/mrp_workorder.py` — `_compute_state`, `blocked_by_workorder_ids`
- `enterprise/mrp_workorder/models/mrp_workorder.py` — `employee_ids`, `employee_assigned_ids`, `allowed_employees`
- `enterprise/mrp_workorder/static/src/mrp_display/mrp_display_record.js` — getter `workorders` (filtro de `pending`/`waiting`)
- `enterprise/mrp_workorder/static/src/mrp_display/mrp_display.js` — ordenação e filtros do Shop Floor

**Documentação oficial**
- https://www.odoo.com/documentation/17.0/applications/inventory_and_mrp/manufacturing.html

---

## Histórico de versões

| Versão | Data | Autor | Alterações |
|---|---|---|---|
| 1.0 | 27/07/2026 | João Barros | Versão inicial, a partir da transcrição de 27/07/2026 |
| 1.1 | 27/07/2026 | João Barros | Secção 4 (etiquetas) reescrita com o diagnóstico feito na base de produção; C1 e C2 saem dos pontos por validar |
