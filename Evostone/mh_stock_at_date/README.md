# mh_stock_at_date — Inventário a uma Data

Relatório interactivo + protecções de stock para Stone Trading.

## Funcionalidades

### 1. Relatório "Inventário a uma Data"

- **Menu**: Inventário → Reporting → Inventário a uma Data
- **Algoritmo**: parte de `stock.quant` e reverte os `stock.move.line` posteriores à data alvo (mesma lógica do Odoo nativo `stock.quantity.history`).
- **Granularidade**: localização → produto → lote, expandível em accordion.
- **Filtros**: data, localização, produto, classificação do artigo, lote.
- **Exports**: HTML interactivo + PDF, CSV, XLSX.
- Apenas localizações `usage='internal'` (transit excluído).

### 2. Endurecimentos a `stock.*`

#### `stock.move._unlink_except_done_or_cancel`
Bloqueia eliminação de `stock.move` em estados `done`/`cancel`. **Gap do Odoo nativo** — o core não protege unlink de moves done; só `stock.move.line` tem essa protecção (`_unlink_except_done_or_cancel`).

#### Vistas read-only (sem create / edit / delete)
Inherits para:
- `stock.view_stock_quant_tree_editable` — desactiva `editable` + esconde botões `action_stock_quant_relocate` (header) e `action_view_orderpoints` (linha "Replenishment").
- `stock.view_move_line_tree` — sem create/edit/delete.

#### Filtro forçado de localização
`stock.dashboard_open_quants` (action "Update Quantity") com domain fixo `[('location_id.usage', '=', 'internal')]` — esconde quants de localizações não-internas independentemente do search.

### 3. Menus restritos a `base.group_system`

Visíveis apenas para Administradores (Configurações):

- `stock.stock_move_line_menu` — Reporting → Moves History
- `stock.stock_move_menu` — Reporting → Stock Moves
- `stock.stock_picking_type_menu` — Overview (dashboard kanban dos picking types)
- `stock_account.menu_valuation` — Reporting → Valuation
- `stock_enterprise.stock_dashboard_menuitem` — Reporting → Performance (Enterprise)
- `stock.menu_product_stock` — Reporting → Stock

**Nota:** o XML data file (`views/stock_menus.xml`) por vezes não aplica no upgrade incremental (cache do registry). Se acontecer, aplicar manualmente via XMLRPC:

```python
import xmlrpc.client
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, login, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

grp_sys = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read',
    [[('module','=','base'),('name','=','group_system')]], {'fields':['res_id']})[0]['res_id']

for xid in ['stock.stock_move_line_menu', 'stock.stock_move_menu',
            'stock.stock_picking_type_menu', 'stock_account.menu_valuation',
            'stock_enterprise.stock_dashboard_menuitem', 'stock.menu_product_stock']:
    mod, name = xid.split('.')
    rec = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read',
        [[('module','=',mod),('name','=',name)]], {'fields':['res_id']})
    if not rec:
        print(f'SKIP {xid} (não encontrado)')
        continue
    models.execute_kw(db, uid, password, 'ir.ui.menu', 'write',
        [[rec[0]['res_id']], {'groups_id': [(6, 0, [grp_sys])]}])
    print(f'OK {xid}')
```

## Estrutura do módulo

```
mh_stock_at_date/
├── __manifest__.py
├── __init__.py
├── controllers/
│   └── stock_at_date.py            # /stock_at_date/export/ (PDF/CSV/XLSX)
├── data/
│   ├── client_action.xml           # ir.actions.client (HTML interactivo)
│   └── report_action.xml           # ir.actions.report qweb-pdf
├── models/
│   ├── stock_at_date_report.py     # AbstractModel + SQL CTE
│   └── stock_move.py               # _unlink_except_done_or_cancel
├── reports/
│   └── stock_at_date_templates.xml # QWeb (HTML + PDF wrapper)
├── static/src/js/
│   ├── stock_at_date.js            # OWL Component
│   └── stock_at_date.xml           # OWL template
├── views/
│   ├── menus.xml                   # Menu Reporting → Inventário a uma Data
│   ├── stock_menus.xml             # Restrição admin nos 4 menus core
│   └── stock_quant_views.xml       # Read-only + esconder botões + domain
└── README.md
```

## Dependências

- `stock` (core)
- Para o filtro `Classificação` funcionar: campo `product_template.product_classification` (vem de `mh_inventory`).

## SQL — query histórica

```sql
WITH current_quants AS (
    SELECT product_id, location_id, lot_id, SUM(quantity) AS qty
    FROM stock_quant q
    JOIN product_product pp ON pp.id = q.product_id
    JOIN product_template pt ON pt.id = pp.product_tmpl_id
    WHERE q.location_id IN (...) AND pt.is_storable = TRUE
    GROUP BY product_id, location_id, lot_id
),
revert_moves AS (
    -- Subtrai entradas e soma saídas APÓS target_date
    SELECT product_id, location_id, lot_id, SUM(qty) FROM (
        SELECT product_id, location_dest_id, lot_id, -quantity
        FROM stock_move_line WHERE state='done' AND date > target_date AND ...
        UNION ALL
        SELECT product_id, location_id, lot_id, quantity
        FROM stock_move_line WHERE state='done' AND date > target_date AND ...
    ) t GROUP BY ...
)
SELECT * FROM current_quants
FULL OUTER JOIN revert_moves USING (product_id, location_id, lot_id)
WHERE qty > 0
```

Para `target_date >= now()`, `revert_moves` é vazio → resultado = `stock.quant` actual = match exacto com o Odoo nativo.
