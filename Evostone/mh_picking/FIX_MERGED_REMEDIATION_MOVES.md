# Fix de Remediações com Moves Fundidos

## Problema

Em remediações com **2+ outputs idênticos** (mesmo `lot_name`, `length`, `width`, `thickness`),
o Odoo funde os `stock.move` num único movimento (resultado do `_prepare_merge_moves_distinct_fields`).

**Sintomas no SP afectado:**
- Move único no picking de entrada (em vez de N moves)
- Move_line com 1 lot mas `units_qty` agregado (`>1`)
- Quant em `MPT/Stock` com qty total e `units_qty=N` (todas as peças partilham 1 lot)

## Causa raiz

Ficheiro: `mh_inventory/models/stock_move.py` — `_prepare_merge_moves_distinct_fields()`
adicionava só `lot_name`, `length`, `width`, `thickness`. 2 strips iguais → 1 move.

## Fix definitivo (já aplicado)

Adicionado campo `scrap_transformation_line_id` em `mh_picking/models/stock_move.py`
e incluído no `_prepare_merge_moves_distinct_fields`. Cada linha de transformação
gera um move distinto.

```python
scrap_transformation_line_id = fields.Many2one(
    'stock.scrap.transformation.line',
    string='Linha de Remediação',
    ondelete='set null',
)

@api.model
def _prepare_merge_moves_distinct_fields(self):
    distinct_fields = super()._prepare_merge_moves_distinct_fields()
    distinct_fields.append('scrap_transformation_line_id')
    return distinct_fields
```

E em `stock_scrap.py::_create_scrap_entry()` cada move criado passa a ter
`'scrap_transformation_line_id': line.id`.

## Como corrigir SPs antigos (dados pré-fix)

### 1. Identificar o caso

```python
# Buscar o scrap
sp = env['stock.scrap'].search([('name','=','SP/00xxx')])
print(sp.scrap_line_ids)  # devem ser N linhas
print(sp.entry_picking_id.move_ids)  # mas só há 1 move (merged)
```

### 2. Recolher dados do estado actual

- `move_id` do picking (o "merged")
- `move_line_id` correspondente
- `quant` em `MPT/Stock` (com `units_qty>1`)
- `lot_id` actual (o que ficou ligado a todas as peças)
- `price_group_id` desse lot

### 3. Plano de correcção (para cada strip extra além da 1ª)

**Passo 1 — Reduzir o existente para 1 strip:**

```python
# Move
env['stock.move'].browse(EXISTING_MOVE_ID).write({
    'product_uom_qty': AREA_DE_1_STRIP,
    'scrap_transformation_line_id': PRIMEIRA_SCRAP_LINE_ID,
})

# Move line
env['stock.move.line'].browse(EXISTING_ML_ID).write({
    'quantity': AREA_DE_1_STRIP,
})

# Quant em MPT/Stock
env['stock.quant'].browse(EXISTING_QUANT_ID).write({
    'quantity': AREA_DE_1_STRIP,
    'units_qty': 1,
})
# NÃO mexer no quant da Remediações (deixar como está)
```

**Passo 2 — Criar novo lot ANTES** (com todos os campos, copiando do irmão):

```python
new_lot_id = env['stock.lot'].create({
    'name': '#NOVOCODIGO/PRODUTO/PARENT_LOT',
    'code': 'NOVOCODIGO',
    'base_lot_name': 'PARENT_LOT',
    'product_id': PRODUCT_ID,
    'company_id': COMPANY_ID,
    'length': L, 'width': W, 'thickness': T,
    'price_group_id': PRICE_GROUP_ID,
    'pcmp': PRECO, 'standard_price': PRECO, 'list_price_lot': PRECO,
}).id
```

**Passo 3 — Criar stock.move + move_line apontando ao novo lot:**

```python
new_move = env['stock.move'].create({
    'picking_id': PICKING_ID,
    'product_id': PRODUCT_ID,
    'product_uom_qty': AREA_DE_1_STRIP,
    'product_uom': UOM_ID,
    'location_id': REMEDIACOES_ID,
    'location_dest_id': MPT_STOCK_ID,
    'lot_name': 'PARENT_LOT',
    'length': L, 'width': W, 'thickness': T,
    'units_qty': 1,
    'price_unit': PRECO,
    'scrap_transformation_line_id': SECOND_SCRAP_LINE_ID,
    'name': PRODUCT_DISPLAY_NAME,
})

env['stock.move.line'].create({
    'move_id': new_move.id,
    'picking_id': PICKING_ID,
    'product_id': PRODUCT_ID,
    'product_uom_id': UOM_ID,
    'location_id': REMEDIACOES_ID,
    'location_dest_id': MPT_STOCK_ID,
    'lot_id': new_lot_id,
    'quantity': AREA_DE_1_STRIP,
    'length': L, 'width': W, 'thickness': T,
    'units_qty': 1,
})
```

**Passo 4 — Marcar move como done** (Odoo auto-cria os quants):

```python
new_move.write({'state': 'done', 'quantity': AREA_DE_1_STRIP})
```

**Passo 5 — Ajustar quants auto-criados** (units_qty + dimensões):

Os quants criados pelo Odoo vêm com `units_qty=0` e dimensões `0`. Actualizar:

```python
quants = env['stock.quant'].search([('lot_id', '=', new_lot_id)])
for q in quants:
    units = 1 if q.location_id.id == MPT_STOCK_ID else -1
    q.write({
        'units_qty': units,
        'length': L, 'width': W, 'thickness': T,
    })
```

## Avisos importantes

1. **NÃO criar quants manualmente** — o Odoo auto-cria quando se faz `state='done'`.
   Criar à mão = duplicação. Caso aconteça, zerar os manuais (Odoo merge automaticamente).

2. **NÃO chamar `_action_confirm` ou `_action_done` via RPC** — são private (prefixo `_`).
   O fluxo é escrever directamente `state='done'` + `quantity`.

3. **Não tocar nos quants da Remediações** com lot original (parent), excepto no caso
   especial em que a Remediações fica desbalanceada — verificar com `quants_filtered_by_lot`.

4. **SVLs e account.moves** são auto-criados pelo Odoo:
   - SVL existente: qty original (ex: 5.2164) + AM original
   - SVL "ajuste": -qty (-2.6082) + AM compensação
   - SVL novo move: +qty (+2.6082) + AM novo
   Net total bate certo.

## Casos corrigidos

| SP | Picking | Lot pai | Lots filhos finais |
|---|---|---|---|
| SP/00038 | MPT/IN/00051 | 30776 | 30860 + 30863 |
| SP/00039 | MPT/IN/00052 | 30777 | 30861 + 30864 |
| SP/00040 | MPT/IN/00053 | 30778 | 30862 + 30865 |

Cada um: 5.2164 m² (2 strips × 2.6082 m²), produto Slab MarmiStone PA Branco Super 20mm.
