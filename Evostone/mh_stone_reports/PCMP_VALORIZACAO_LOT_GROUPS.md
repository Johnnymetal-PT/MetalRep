# PCMP no Relatório de Valorização — Agregação por Lot Groups

Data: 2026-05-16

## Contexto

O modelo `product.product` tem campo `pcmp` (computed) cuja fórmula filtra apenas SVLs com `lot_group_id = False`:

```python
# mh_stock_valuation/models/product_product.py — linha 208
all_svls = self.env['stock.valuation.layer'].sudo().search([
    ('product_id', '=', self.id),
    ('lot_group_id', '=', False),  # ← filtro
    ...
])
```

Por design, a separação é:
- `base.lot.group.pcmp` → SVLs com `lot_group_id = self.id` (por grupo de lote)
- `product.product.pcmp` → SVLs sem `lot_group_id` (produtos "normais", sem dimensões)

## Problema no relatório de valorização

Para produtos com `base.lot.group` (com dimensões), o `product.product.pcmp = 0`. O relatório usa este campo e mostra:
- Valor unitário = 0
- Valor total = 0

Embora o valor real exista nos `base.lot.group` associados ao produto.

## Decisão

**Não alterar o modelo `product.product`** (manter separação por design).
**Aplicar no relatório** (`mh_stone_reports/models/stock_valuation_report.py`) a **Opção B — média ponderada**:

```
Para cada produto, se tem base.lot.groups:
    valor_total_lot_groups = Σ (lot_group.pcmp × lot_group.qty_em_stock)
    qty_total_lot_groups   = Σ lot_group.qty_em_stock
    pcmp_efectivo = valor_total / qty_total   (se qty_total > 0)
    valor_efectivo = valor_total_lot_groups

Caso contrário (sem base.lot.groups):
    pcmp_efectivo = product.pcmp
    valor_efectivo = product.pcmp × qty_em_stock
```

## Implementação proposta

**Ficheiro:** `mh_stone_reports/models/stock_valuation_report.py`

**Função afectada:** método que constrói `groups[]` (calcula `unit_cost` e `total_value` por produto)

**Lógica:**
```python
for product in products:
    base_lot_groups = self.env['base.lot.group'].search([
        ('product_id', '=', product.id),
        ('company_id', '=', company.id),
    ])
    if base_lot_groups:
        # Média ponderada por qty em stock
        total_value = 0.0
        total_qty = 0.0
        for blg in base_lot_groups:
            qty = blg.quantity_svl  # ou outra fonte de qty em stock
            if qty > 0:
                total_value += blg.pcmp * qty
                total_qty += qty
        unit_cost = total_value / total_qty if total_qty > 0 else 0.0
    else:
        unit_cost = product.pcmp
        total_value = product.pcmp * total_qty_from_svls
```

## Impacto

- **Relatório:** produtos com lot.groups passam a mostrar valor real agregado
- **Modelo:** sem mudanças — comportamento separado mantém-se
- **CMV / contabilidade:** sem impacto (relatório é só display)

## Testes a fazer

1. Produto **sem** base.lot.group → relatório igual ao actual ✓
2. Produto **com** 1 base.lot.group → relatório mostra pcmp e valor do grupo
3. Produto **com** N base.lot.groups → relatório mostra média ponderada e valor agregado
4. Produto com base.lot.group **stock zerado** → valor=0, sem dividir por zero

## Decisões pendentes

- [ ] Fonte de quantidade do lot.group: `quantity_svl` (SVL sum) vs stock físico actual via `stock.quant`?
- [ ] Aplicar em ambos os formatos do relatório (PDF, CSV, XLSX) — código está em `controllers/stock_valuation_report.py` e `models/stock_valuation_report.py`?
- [ ] Mostrar breakdown por lot.group no PDF (drill-down) ou só o agregado?
