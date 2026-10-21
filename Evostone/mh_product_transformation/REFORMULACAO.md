# mh_product_transformation — Proposta de Reformulação

> Objectivo: reformular o módulo com o conhecimento actual, alinhando o
> **custo/valorização ao padrão do `import.document`** (mh_purchase).
> Decisões: **mesmo módulo** (refactor no sítio, sem migração — não está em
> produção), **mesmos 5 estados**, custo **= como o import.document**.

---

## 1. Princípio central (o que muda)

**Antes (errado):** o custo do input era **capturado à mão no wizard** (`preco_custo`)
e o output recebia um custo proporcional desse valor. Frágil e desligado da
valorização real.

**Agora (correcto, = import.document):**
1. O **input é CONSUMIDO ao seu PCMP real** (custo do `base.lot.group`), via SVL
   de saída — tal como o stock sai numa venda. **Não há captura manual de custo.**
2. O **valor consumido do input** é o **custo base** dos outputs (como o FOB/PO é o
   custo base no import).
3. Os **serviços de transformação** (corte, polimento, supervisão do transformador)
   entram como **landed cost** sobre o picking de entrada dos outputs — **exactamente
   como o despachante/frete no import.document**.
4. O **PCMP dos outputs** é calculado pelo `mh_stock_valuation` ao validar o picking
   + landed cost (`compute_landed_cost()` → `button_validate()` → `_update_pcmp_prices()`).

**Analogia directa:**

| import.document | transformation (novo) |
|---|---|
| Custo FOB / preço da PO | **Valor do input consumido (ao PCMP)** |
| Recepção da mercadoria (picking IN) | Picking IN dos **outputs** (placas/bandas) |
| Serviços despachante/frete (landed) | **Serviços do transformador (landed)** |
| `_create_landed_cost` → validate | igual |
| Ajuste CMV (vendas no provisório) | igual (se output vendido antes de custo final) |

---

## 2. Modelo de custo/valorização

### 2.1 Saída do input (consumo)
- No `action_start`, o **picking OUT** consome cada linha de input.
- O SVL de saída usa o **PCMP actual do lot_group** do input (custo médio real),
  **não** um valor capturado. Isto **retira do stock** o valor correcto.
- **Valor total consumido** = Σ (qty_input × PCMP_lot_group_input).

### 2.2 Entrada dos outputs (custo base)
- No `action_done`, o **picking IN** cria os outputs.
- O **custo base de cada output** = rateio do **valor consumido do input** por
  **área/volume** (o critério físico), não por um preço manual:
  - bloco→placa: ratear por **volume consumido** (m³);
  - placa→banda: ratear por **área** (m²).
- `move.price_unit` do output = custo base rateado ÷ qty_output.
- Ao validar o picking IN, o `mh_stock_valuation` cria o SVL e o **PCMP por
  lot_group** do output.

### 2.3 Serviços (landed cost)
- Os serviços do transformador (POs de serviço `service_purchase_order_ids`)
  entram como **stock.landed.cost** sobre o picking IN, com `_create_landed_cost`
  no mesmo molde do import.document.
- `compute_landed_cost()` → `button_validate()` → PCMP ajustado automaticamente.
- **Conservação de valor:** valor de saída do input = valor de entrada dos outputs
  (+ serviços). Sem "criar" nem "perder" valor — o que difere fica como
  **ganho/perda** explícito (ver 4).

---

## 3. Fluxo (mantém 5 estados, lógica revista)

| Estado | Acção | Novo comportamento |
|---|---|---|
| draft → transit | `action_start` | Valida; **get-or-create localizações** (fora do compute); cria picking OUT (consome input **ao PCMP**) e picking IN (confirma) |
| transit → transforming | `action_transforming` | Estado |
| transforming → reception | `action_reception` | Estado |
| reception → done | `action_done` | Custo base dos outputs = valor consumido rateado; valida IN (SVL/PCMP); **cria+valida landed cost** (serviços); ajuste CMV se preciso; **tudo com tratamento de erro (idempotente)** |
| → cancel / reset | `action_cancel` / `action_reset_draft` | Reverter SVLs/pickings de forma limpa |

---

## 4. Ganho / Perda de transformação

- Diferença entre **valor de entrada (outputs)** e **valor de saída (input)** quando
  as quantidades físicas não "fecham" (quebra, pó, corte).
- Em vez de só um flag + aprovação, **reconhecer contabilisticamente**:
  - **perda** → conta de gasto (quebra de transformação);
  - **ganho** → conta de proveito/redução de custo.
- Manter a **aprovação admin** para diferenças acima de uma **tolerância**.

---

## 5. Correcções de bugs (da revisão do FLUXO.md)

🔴 **Multi-empresa:** localização "Transformação - Fornecedor" passa a procurar/criar
**com `company_id`** (igual à do cliente). Remover criação de registos de **dentro do
compute** → método `_get_or_create_transformation_locations()` chamado no `action_start`.

🔴 **`action_done` robusto:** envolver validação do picking + landed cost de forma
**idempotente / com try-except**, para um erro a meio não deixar estado parcial
encravado (picking 'done' mas documento não).

🟠 **Distribuição de custo/landed:** usar a **mesma base** no total e no rateio
(evitar a última linha absorver desequilíbrios).

🟡 **`_update_move_base_costs`:** se custo ≤ 0 ou move sem output_line → **log/erro**,
não passar em silêncio.

🟡 **Performance:** `_distribute_*` em **batch**, não a cada write de linha.

🟡 **`admin_approved`:** só repor a aprovação se a diferença **mudar significativamente**.

---

## 6. Fases de implementação (mesmo módulo)

1. **Localizações** (multi-empresa + tirar do compute) — base segura.
2. **Consumo do input ao PCMP** no `action_start` (substitui o `preco_custo` do wizard).
3. **Custo base dos outputs** = valor consumido rateado por área/volume.
4. **Landed cost dos serviços** no molde do import.document (`_create_landed_cost`).
5. **`action_done` idempotente** + ganho/perda contabilístico.
6. **Limpeza:** remover `preco_custo` manual e código morto do wizard.

> Cada fase testada no Stone teste antes de seguir. Sem deploy em produção.

---

> Rascunho inicial (2026-06-11) — a validar/iterar com o chefe antes de implementar.
