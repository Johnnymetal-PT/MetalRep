# mh_product_transformation — Fluxo e Notas de Revisão

> Módulo de **transformação de pedra**: blocos → placas, placas → bandas/tiras.
> Gere transformadores externos, movimentos de stock, landed costs e PCMP (custo médio).
> Depende de: `mh_base`, `mh_inventory`, `mh_stock_valuation`, `stock_landed_costs`, `mail`.
> `auto_install: True`.

---

## 1. Modelos principais

| Modelo (`_name`) | Ficheiro | Papel |
|---|---|---|
| `transformation.document` | transformation_document.py | Documento mestre da transformação |
| `transformation.line.input` | transformation_line_input.py | Linhas de **entrada** (o que se transforma) |
| `transformation.line.output` | transformation_line_output.py | Linhas de **saída** (o que resulta) |
| `transformation.document.pcmp` | transformation_document_pcmp.py | Mixin p/ criar o landed cost e actualizar PCMP |
| `transformation.stock.wizard` (+ line) | transformation_stock_wizard*.py | Wizard p/ selecionar stock/quants a transformar |

**Inherits:** `stock.move` (+`transformation_output_line_id`, `transformation_id`), `stock.picking` (+`transformation_id`), `product.product`/`product.template` (`can_be_transformed`, `product_form`), `res.partner` (`is_transformer`/`is_carrier`), `purchase.order` (`transformation_document_ids`).

**Relações chave:** documento → `input_line_ids` / `output_line_ids` (One2many, cascade); output → `input_line_id` (M2o) e `stock_move_id`; documento → `picking_ids`, `service_purchase_order_ids` (M2m), `landed_cost_id`.

---

## 2. Máquina de estados

`draft` → `transit` → `transforming` → `reception` → `done` (e `cancel`).

| De → Para | Método | O que faz |
|---|---|---|
| draft → transit | `action_start()` (~584) | Valida linhas e aprovações; gera sequência; cria **picking OUT (valida já)** + **picking IN (confirma, não valida)** |
| transit → transforming | `action_transforming()` (~775) | Só muda estado |
| transforming → reception | `action_reception()` (~815) | Só muda estado |
| reception → done | `action_done()` (~846) | Actualiza custos dos moves; **valida picking IN** (cria SVL/PCMP); cria+valida **landed cost** dos serviços; actualiza PCMP |
| qualquer → cancel | `action_cancel()` (~952) | Cancela pickings, muda p/ cancel |
| cancel → draft | `action_reset_draft()` (~988) | Volta a draft |

---

## 3. Fluxo de stock

- **Picking OUT** (`action_start`, ~667): origem = `location_origin_id`, destino = `Transformação - Cliente` (auto-criada). Um `stock.move` por linha de input (qty = volume/área; copia dimensões; `pcmp_operation_type='transformation_out'`; `restrict_lot_id`). **Validado de imediato** (`button_validate`).
- **Picking IN** (`action_start`, ~705): origem = `Transformação - Fornecedor` (auto-criada), destino = `location_dest_id`. Um `stock.move` por linha de output (qty computada das dimensões; `pcmp_operation_type='transformation_in'`; `price_unit` = custo base **sem** landed; `lot_name`). **Só confirmado** — validado mais tarde no `action_done`.
- **Localizações de trânsito** "Transformação - Cliente" (customer) e "Transformação - Fornecedor" (supplier) são auto-criadas/procuradas em `_compute_transformation_locations` (~398).

---

## 4. Custo / PCMP / Landed cost

1. **Custo de entrada** capturado no wizard a partir do quant (`preco_custo`). `subtotal = quantity × preco_custo`.
2. **Custo base do output** (`_compute_price_unit`, output ~407): proporcional ao **volume consumido**
   - bloco: `consumido = qty_output × espessura` (m³); placa: `consumido = qty_output` (m²)
   - `custo_unit_input = subtotal_input / qty_input`; `price_unit = (consumido × custo_unit_input) / qty_output`
   - → espessura maior ⇒ custo/m² maior.
3. **Serviços (landed cost)** distribuídos por `_distribute_service_costs` (doc ~467) **por volume consumido**; última linha leva o resto.
4. **`final_unit_cost` = `price_unit` + `landed_cost / qty`**.
5. Em `action_done`: `_update_move_base_costs` põe `move.price_unit = output.price_unit` (base) → validar entrada cria **SVL** com custo base → cria/valida **landed cost** (sobre o picking IN já validado) → `_update_output_lines_pcmp` lê o PCMP final para auditoria.

---

## 5. Validações principais

- **Documento:** origem e destino são armazéns internos (**podem ser iguais** — o trânsito real é pela localização de **Produção** auto-gerida, por isso não há regra origem≠destino); PO não em importação nem noutra transformação; datas logísticas coerentes.
- **Input:** qty>0; não aceita `strip` como entrada; lote obrigatório se tracking=lot; lote **não** em venda activa nem noutra transformação activa; dimensões obrigatórias (bloco: L/W/T; placa: L/W).
- **Output:** qty>0; espessura obrigatória se input=bloco; sem linhas duplicadas; lógica bloco→placa / placa→banda; `lot_name` obrigatório se tracking lote/série.
- **`action_start`:** exige inputs e outputs; valida lotes; **exige `admin_approved`** em qualquer linha com diferença (ganho/perda) de volume.

---

## 5b. Tracking Logístico (KPI)

> Indicador de gestão do tempo/custo em que o material está fora, no transformador.
> **É só KPI — não entra no custo dos produtos.**

**Entradas:** `carrier_id` (transportador), `date_expected_departure`, `date_expected_arrival`, `daily_cost` (custo/dia de armazenamento/espera).

**Calculados (`_compute_logistics_tracking`, não-stored / live):**
- **`days_stopped` — cumulativo:** desde `date_transit` (saída real) até **hoje** (em curso) ou até `date_done` (concluído). **Não reinicia por fase.**
- **`logistics_status` — prazo único (`date_expected_arrival`):**
  - Em curso (`transit`/`transforming`/`reception`): `delayed` se `hoje > date_expected_arrival`, senão `waiting`.
  - `done`: `on_time` se `date_done ≤ date_expected_arrival`, senão `delayed`.
- **`total_waiting_cost` = `days_stopped × daily_cost`** (só se ambos > 0).

**Notas:** campos **não-stored** porque dependem de `today` (senão o valor congelava). `date_expected_departure` fica só como informação (não influencia o status). *(Corrigido em 2026-07 — antes reiniciava o contador por fase, usava prazos diferentes por fase e era `stored` sem refresh diário.)*

---

## 5c. Protecção dos pickings (não editar/validar directamente)

Os pickings de **saída** (input) e de **entrada** (placas) são gerados e geridos pelo documento — a sincronização é só forward (documento → picking). Para o utilizador não os alterar por fora:

- **UI readonly** (`mh_picking`): `is_picking_readonly = bool(sale_id) or bool(transformation_id)` torna readonly o **cabeçalho** *e* as **linhas** (`move_ids_without_package`) quando o picking pertence a uma venda ou transformação.
- **Guarda de backend — `button_validate`** (`mh_product_transformation/models/stock_picking.py`): bloqueia (`UserError`) validar directamente um picking com `transformation_id`, a menos que a chamada venha do fluxo com o contexto `from_transformation_document=True`. O `action_start` (picking OUT) e o `action_done` (picking IN) passam esse contexto.
- **Banner de aviso** na ficha do picking (`views/stock_picking_views.xml`, estilo `import.document`): avisa que é gerido pelo Documento de Transformação e como proceder.
- **Nota (decisão):** `write`/`unlink` genéricos dos moves **não** são bloqueados — o Odoo escreve nos moves no processamento normal de stock; um guard cego partiria isso. A readonly da UI + a guarda de `button_validate` cobrem o risco real (edição de linhas e criação de SVL/PCMP fora do fluxo).

**⚠️ Dependência com o `mh_purchase`:** o `mh_purchase` tem um guard próprio no `button_validate` que **bloqueia qualquer entrada `incoming` sem origem reconhecida** (`purchase_id`/`scrap_id`/`return_id`/`is_initial_stock`). O picking de entrada da transformação não tem nenhuma dessas, por isso **o `transformation_id` foi acrescentado como origem legítima** nesse guard (`mh_purchase/models/stock_picking.py`) — senão nem o `action_done` conseguiria validar o IN. As duas guardas coexistem: o `mh_purchase` deixa passar a transformação (origem válida) e a guarda deste módulo é que distingue **fluxo** (permitido, com `from_transformation_document=True`) de **validação manual** (bloqueada).

---

## 6. ⚠️ Pontos a rever (por prioridade)

> Identificados em revisão de fluxo — **a confirmar/decidir**, não são todos necessariamente bugs.

### 🔴 Alta
- ✅ **RESOLVIDO — Multi-empresa:** a localização de transformação (agora **única**, tipo `production` "Transformação - Produção") é procurada/criada **sempre com `company_id`** em `_get_or_create_transformation_locations()`. *(O modelo evoluiu para uma só localização de produção, estilo MRP — ver secção 3/4, que ainda descrevem o modelo antigo de duas localizações de trânsito e precisam de refresh.)*
- **Sequência do landed cost em `action_done` (~879–888):** valida-se a entrada (cria SVL com custo base) e **só depois** se cria/valida o landed cost, **sem `try/except`**. Se o landed cost falhar, fica SVL **só com custo base** e estado parcial. *(Envolver em transacção / tratamento de erro.)*

### 🟠 Média
- **Arredondamento na distribuição do landed cost (~498–513):** a última linha leva o "resto"; com muitas linhas/proporções pode ficar desequilibrada (ou negativa). *(Adicionar verificação do total.)*
- **Sem validação volume total output vs input:** só existe o flag ganho/perda + aprovação admin; nada impede 1 m³ → 10 m³ se aprovado. *(Confirmar se é intencional; talvez tolerância máxima.)*
- **`admin_approved` reseta a cada edição de output** (output ~486–493): aprova-se a perda, mexe-se numa linha, perde-se a aprovação. *(UX — repor só se a diferença mudar significativamente.)*

### 🟡 Baixa
- **`move.transformation_output_line_id` usado sem garantir link (~941):** se um move ficar sem ligação, o `price_unit` não actualiza **em silêncio**. *(Log/erro se faltar.)*
- **`_distribute_service_costs` dispara a cada write** de qty/espessura/dimensão (output ~485–501) → recalcula N vezes ao editar N linhas. *(Performance — batch.)*
- **`product_form`** definido em `mh_inventory` e usado via related — dependência implícita; documentar.
- **`landed_cost_id`** pode ficar órfão se o landed cost for apagado/recriado. *(Integridade referencial.)*

---

## 7. Diagrama resumido

```
draft ──action_start──▶ transit ──action_transforming──▶ transforming ──action_reception──▶ reception ──action_done──▶ done
  │  (cria/valida OUT, cria IN)                                                                  │ (valida IN: SVL/PCMP;
  │                                                                                              │  cria/valida landed cost)
  └────────────────────────────── action_cancel ──────────────────────────────────────────────▶ cancel ──reset──▶ draft
```

> Mapa gerado em revisão de fluxo (2026-06-10). Referências de linha aproximadas — confirmar no código antes de alterar.
