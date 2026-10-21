# MH — Conta de Devoluções de Compras — `mh_purchase_return_account`

Encaminha as **devoluções a fornecedor** para uma **conta própria de devoluções**
(ex.: **217**), **em ambos os lados** (movimento de stock **e** nota de crédito),
**mantendo o inventário perpétuo** e a reconciliação intactos.

---

## 1. O problema

Numa devolução a fornecedor com valorização **perpétua** (real_time), o Odoo
lança a contrapartida na **conta de entrada de stock** (a mesma das compras, ex.:
`212111`). Isto porque:

- o **picking de devolução** reverte a receção → usa `_get_src_account`, que
  devolve a *stock input* da categoria;
- a **nota de crédito** (`in_refund`) espelha a fatura → o
  `_compute_account_id` usa a conta de **gasto** do produto, e **não distingue**
  `in_invoice` de `in_refund`.

Resultado: as devoluções ficam misturadas com as compras na `212`, em vez de numa
conta dedicada de **Devoluções de compras (217)** como o PGC-NIRF pede.

> **Nativamente não há solução:** o Odoo **não tem** conta de devoluções de compra
> separada; em perpétuo a devolução passa sempre pela conta de entrada de stock.

## 2. A solução (perpétuo-consistente)

Uma **conta de devolução na categoria** que alimenta **os dois lados**, para
ambos baterem na mesma conta e reconciliarem:

| Lado | Como | Lançamento |
|---|---|---|
| **Stock** (picking devolução) | override do `_get_src_account` | Déb **217** / Créd 261 |
| **Nota de crédito** (`in_refund`) | override do `_compute_account_id` | Créd **217** / Déb 421 |

Como **os dois** usam a 217, reconciliam entre si; a **261** continua a ser
reduzida → **perpétuo intacto**.

## 3. Como funciona (ancorado no código nativo do Odoo 18)

**a) Campo na categoria** (`product.category`), à imagem das contas de stock
nativas (`company_dependent`, obrigatório em `real_time`):
```
property_stock_account_return_categ_id  →  ex.: 217 (Devoluções de compras)
```

**b) Injeção no dicionário de contas** (`product.template._get_product_accounts`):
acrescenta a chave `stock_return` com a conta da categoria.

**c) Lado do stock** (`stock.move._get_src_account`): **só** em devoluções a
fornecedor —
```python
if self._is_returned('out') and accounts_data.get('stock_return'):
    return (self.location_id.valuation_out_account_id.id
            or accounts_data['stock_return'].id
            or accounts_data['stock_input'].id)
```
`_is_returned('out')` é verdadeiro **apenas** para saídas com destino `supplier`
→ só devoluções de compra.

**d) Lado da nota de crédito** (`account.move.line._compute_account_id`): quando a
NC é uma **devolução de mercadoria** (flag `mh_purchase_return`), a linha do
produto usa a conta de devolução, **aplicando o mapa da posição fiscal**
(mercado/regime), tal como o `mh_market_stock` faz no stock.

**e) Flag `mh_purchase_return`** (`account.move`, computada **readonly**): é
`True` quando a NC de compra (`in_refund`) está ligada a um **picking de
devolução** (`return_picking_id`). Automática — sem UI. Assim distingue-se uma
**devolução física** de uma **NC de correção de preço/desconto** (que fica na 212).

## 4. Mercado / regime (composição com `mh_market_stock`)

A conta de devolução base (ex.: `21711` MN IVA 16%) é remapeada por **posição
fiscal**, como as compras:

- **Lado do stock:** tratado pelo **`mh_market_stock`** (remapeia `acc_src` pela
  posição fiscal do movimento original).
- **Lado da NC:** tratado por **este módulo** (aplica `fiscal_position_id.map_account`).

Exemplo (posições fiscais):
```
Import/Export:  21711 → 21723 (MN IVA 16% → ME Isento) · 21713 → 21723
Domestic:       21723 → 21711 · 21722 → 21711 (ME → MN)
```
→ Cada devolução cai na subconta do **seu mercado/regime**, tal como a compra.

## 5. Âmbito — SÓ devoluções de compra

Não interfere em mais nada:
- **Compras normais** → conta de compras (`212…`). Intacto.
- **Vendas** e **devoluções de venda** (`out_refund`, entrada de cliente) →
  contas de venda. Intacto (o override do stock só dispara em `_is_returned('out')`;
  o da NC só em `in_refund`).
- **NC de correção/desconto** (sem picking) → flag `False` → fica na `212`.

## 6. Configuração

1. **Plano de contas:** criar a(s) conta(s) de devoluções (ex.: `217` como grupo,
   com `21711`/`21713`/`21722`/`21723` por mercado/regime).
2. **Categoria de produto** (perpétua): definir a **"Conta de Devolução de
   Compras"** (o campo é **obrigatório** quando `real_time`).
3. **Posições fiscais:** acrescentar o mapa das contas de devolução
   (`21711 → 21723`, etc.), a espelhar o mapa das compras.
4. Requer o **`mh_market_stock`** para o remapeamento por mercado do lado do stock.

## 7. Cenários validados (teste)

| Caso | Resultado |
|---|---|
| Devolução de compra **nacional** | conta **MN** (ex.: 21711) — stock + NC |
| Devolução de compra **importada** | conta **ME** (ex.: 21723) via posição fiscal |
| **NC de correção** (manual, sem picking) | fica na **212** (intacto) |
| **Compra normal** | fica na **212** (intacto) |
| **Devolução de venda** | contas de venda (intacto) |

Em todos, o **perpétuo** mantém-se (261 reduzido) e os dois lados **reconciliam**
na conta de devoluções.

## 8. Ficheiros

```
models/  product_category.py  — campo property_stock_account_return_categ_id
         product_template.py  — _get_product_accounts (chave 'stock_return')
         stock_move.py        — _get_src_account (devolução → 217)
         account_move.py      — flag mh_purchase_return (auto, readonly)
         account_move_line.py — _compute_account_id (NC → 217 + mapa fiscal)
views/   product_category_views.xml — campo na ficha da categoria (obrigatório real_time)
```

Depende de `stock_account`, `account`, `mh_return_credit_note` (reaproveita o
`return_picking_id`) e compõe com `mh_market_stock`.
