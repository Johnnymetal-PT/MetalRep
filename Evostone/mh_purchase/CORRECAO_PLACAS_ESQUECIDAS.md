# Correcção — Placas esquecidas em IMP fechada

Procedimento para adicionar placas a um `import.document` já em estado `done`,
sem reabrir o documento, preservando audit trail e PCMP.

## Quando aplicar

- O IMP está em `done` (fechado, com PCMP calculado)
- Faltam 1 ou mais placas físicas (chegaram à empresa mas não foram registadas)
- As placas pertencem a um `base.lot.group` que já existe (mesmo `base_lot_name`,
  mesmo produto, mesma company)

## Bypass flags activos

Duas protecções precisam de `context` para serem ignoradas pontualmente:

1. **`bypass_duplicate_lot_check`** (`mh_picking/stock_picking.py`)
   - Salta `_check_duplicate_lot_groups`
   - Permite criar lots novos com `base_lot_name` que já existe

2. **`bypass_manual_picking_check`** (`mh_purchase/stock_picking.py`)
   - Salta o bloqueio "Este picking de entrada não pode ser validado manualmente"
   - Permite validar pickings IN sem PO/IMP/scrap/return como origem

## Procedimento (passo a passo)

### 1. Criar picking manual

UI: **Inventário → Operações → Recebimentos** → "Novo"

- **Tipo de Operação:** Maputo: Recebimentos
- **Localização de origem:** Partners/Vendors
- **Localização de destino:** MPT/Stock
- **Adicionar Linhas** (uma por placa):
  - Produto: ex. `[118101180413] Stripe Granito (800 mm)`
  - L (comprimento), W (largura), **T (espessura)** — **NÃO esquecer T!**
  - units_qty: 1
  - lot_name: `260127008` (= `base_lot_name` do lote existente)

### 2. Preencher campos críticos via XMLRPC

```python
import xmlrpc.client
url = 'http://11.3.0.18:8070'
db = 'stone-trading-mhc-main-090126'
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, login, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Origin (audit trail)
models.execute_kw(db, uid, password, 'stock.picking', 'write',
    [[picking_id], {
        'origin': 'IMP/2026/00009 - P00118: MPT/IN/00061 (N placas esquecidas)',
    }])

# 2. Para cada move: thickness, quantity e price_unit
# PCMP exacto vem do base.lot.group (manter PCMP estável)
blg = models.execute_kw(db, uid, password, 'base.lot.group', 'search_read',
    [[('base_lot_name','=','260127008'),('product_id','=',product_id)]],
    {'fields':['pcmp']})[0]
pcmp = blg['pcmp']  # ex: 3386.234052793557 (precisão TOTAL!)

models.execute_kw(db, uid, password, 'stock.move', 'write',
    [move_ids, {
        'thickness': 0.018,
        'price_unit': pcmp,
    }])
# quantity deve ser L × W × units (preenchida pela UI ou via write)
```

### 3. Validar com os 2 bypass flags

```python
models.execute_kw(db, uid, password, 'stock.picking', 'button_validate',
    [[picking_id]],
    {'context': {
        'bypass_duplicate_lot_check': True,
        'bypass_manual_picking_check': True,
    }})
```

### 4. ⚠️ Bug conhecido — corrigir thickness pós-validação

Durante a validação, **a propagação de `thickness` do `stock.move` para
`stock.move.line` / `stock.lot` / `lot.price.group` falha**. Resultado: novos
`lot.price.group` criados com `T=0` (nome sem sufixo de thickness).

**Sempre corrigir após validação:**

```python
# IDs criados pela validação (ver button_validate result)
move_line_ids = [...]
lot_ids = [...]
lpg_ids = [...]

T = 0.018  # thickness correcto do produto

models.execute_kw(db, uid, password, 'stock.move.line', 'write', [move_line_ids, {'thickness': T}])
models.execute_kw(db, uid, password, 'stock.lot',        'write', [lot_ids,      {'thickness': T}])
models.execute_kw(db, uid, password, 'lot.price.group',  'write', [lpg_ids,      {'thickness': T}])
```

Side-effect: nome do `lot.price.group` recomputa para incluir T.
Side-effect: `peso` do grupo recomputa via depends.

### 5. ⚠️ Deduplicação de `lot.price.group`

Após fix de thickness, podem aparecer `lot.price.group` **duplicados** com mesmas
dimensões (existente + novo criado em validação com T=0 e depois corrigido).

**Verificar e fundir:**

```python
for L, W, T in dimensions_corrigidas:
    groups = models.execute_kw(db, uid, password, 'lot.price.group', 'search_read',
        [[('base_lot_name','=','260127008'),
          ('product_id','=',product_id),
          ('length','=',L),
          ('width','=',W),
          ('thickness','=',T)]],
        {'fields':['id','name']})
    if len(groups) > 1:
        # Manter o original (lot mais antigo, ID menor)
        original_id = min(g['id'] for g in groups)
        duplicate_ids = [g['id'] for g in groups if g['id'] != original_id]
        # Re-apontar lots dos duplicados → original
        lots_to_fix = models.execute_kw(db, uid, password, 'stock.lot', 'search',
            [[('price_group_id','in',duplicate_ids)]])
        if lots_to_fix:
            models.execute_kw(db, uid, password, 'stock.lot', 'write',
                [lots_to_fix, {'price_group_id': original_id}])
        # Apagar duplicados (após re-apontar)
        models.execute_kw(db, uid, password, 'lot.price.group', 'unlink',
            [duplicate_ids])
```

## Verificação final

Confirmar que tudo bate certo:

```python
# PCMP do base.lot.group — deve estar invariante (drift residual <0.001)
blg = models.execute_kw(db, uid, password, 'base.lot.group', 'read',
    [[base_lot_group_id]], {'fields':['pcmp','lot_count']})
print(f'PCMP: {blg[0]["pcmp"]} | Lots: {blg[0]["lot_count"]}')

# Lots ligados aos grupos correctos
lots = models.execute_kw(db, uid, password, 'stock.lot', 'read',
    [new_lot_ids], {'fields':['name','peso','price_group_id','thickness']})
for l in lots:
    print(l)
```

## Caso de exemplo: IMP/2026/00009 — 2 placas Stripe Granito 800

- IMP `done` desde 14/05/2026
- 2 placas físicas chegaram mas não registadas:
  - 2.91 × 0.82 × 0.018 m (Stripe 800, lot 260127008)
  - 2.95 × 0.82 × 0.018 m (Stripe 800, lot 260127008)
- Picking criado: `MPT/IN/00065`
- Origin: `IMP/2026/00009 - P00118: MPT/IN/00061 (2 placas esquecidas)`
- price_unit: `3386.234052793557` (= PCMP exacto do base.lot.group)
- PCMP pós: `3386.2340234813296` (drift `≈ 3e-5`, irrelevante)

## TODO / Melhorias futuras

- [ ] Corrigir o bug de propagação de `thickness` no flow de validação
  (`mh_inventory/stock_move._prepare_move_line_vals` ou `mh_stock_valuation`
  `find_or_create_group`) para evitar o passo 4 manual.
- [ ] Auto-deduplicação de `lot.price.group` no upgrade ou via cron.
- [ ] Botão dedicado na UI ("Adicionar placa esquecida") que aplica este flow
  automaticamente — evita XMLRPC manual.
