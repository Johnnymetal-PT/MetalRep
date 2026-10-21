# GUIA TÉCNICO DE VALORIZAÇÃO - ODOO 18

## Índice
1. [Visão Geral](#1-visão-geral)
2. [Modelos Principais](#2-modelos-principais)
3. [Métodos de Custeio](#3-métodos-de-custeio)
   - 3.1 [Comparação](#31-comparação)
   - 3.2 [Standard Price](#32-standard-price)
   - 3.3 [AVCO](#33-average-cost-avco)
   - 3.4 [FIFO](#34-fifo-first-in-first-out)
   - 3.5 [FIFO Vacuum](#35-fifo-vacuum-correção-de-stock-negativo)
   - 3.6 [PCMP](#36-pcmp-preço-de-custo-médio-ponderado-por-ano-fiscal) ⭐ **NOVO**
4. [Fluxo de Valorização](#4-fluxo-de-valorização)
5. [Integração Contabilística](#5-integração-contabilística)
6. [Exemplos Práticos](#6-exemplos-práticos)
   - 6.1 [FIFO Completo](#61-exemplo-fifo-completo)
   - 6.2 [AVCO](#62-exemplo-avco)
   - 6.3 [PCMP (Ano Fiscal)](#63-exemplo-pcmp-ano-fiscal) ⭐ **NOVO**
   - 6.4 [Stock Negativo + Vacuum](#64-exemplo-stock-negativo--vacuum)
7. [Queries Úteis](#7-queries-úteis)

---

## 1. Visão Geral

O sistema de valorização do Odoo 18 está estruturado em três camadas:

1. **Camada de Dados** (`stock.valuation.layer`)
   - Armazena histórico completo de valorizações
   - Rastreia quantidades remanescentes para FIFO
   - Vincula movimentos de stock a lançamentos contábeis

2. **Camada de Lógica** (`product.product` / `stock.move`)
   - Implementa algoritmos de custeio (FIFO, AVCO, Standard)
   - Calcula valores e custos unitários
   - Gere correções retroativas (vacuum)

3. **Camada Contabilística** (`account.move`)
   - Cria lançamentos automáticos (real_time)
   - Integração Anglo-Saxon para COGS
   - Reconciliação de contas interinas

---

## 2. Modelos Principais

### 2.1 stock.valuation.layer

O **coração da valorização**. Cada registo representa uma "camada" de custo.

#### Campos Principais:
```python
company_id          # Many2one res.company (obrigatório)
product_id          # Many2one product.product (obrigatório)
categ_id            # Related product.category (armazenado)
product_tmpl_id     # Related product.template

# Quantidade e Valorização
quantity            # Float - quantidade do movimento
uom_id              # Related product UOM
currency_id         # Related company currency
unit_cost           # Float - custo unitário
value               # Monetary - valor total da camada
remaining_qty       # Float - quantidade não consumida (CRÍTICO para FIFO)
remaining_value     # Monetary - valor não consumido

# Relacionamentos
stock_valuation_layer_id    # Many2one para camada pai
stock_valuation_layer_ids   # One2many para camadas filhas
stock_move_id               # Many2one stock.move (indexado)
account_move_id             # Many2one account.move (indexado)
account_move_line_id        # Many2one account.move.line
lot_id                      # Many2one stock.lot

# Campos Adicionais
description         # Text - descrição do movimento
reference           # Related ao stock_move
price_diff_value    # Monetary - correção de valor da fatura
```

#### Índices de Base de Dados:
```sql
-- Índice Primário (performance FIFO)
(product_id, remaining_qty, stock_move_id, company_id, create_date)

-- Índice Secundário
(product_id, company_id, id, value, quantity)
```

### 2.2 stock.move

Movimento de stock (transferência, recepção, expedição).

**Responsabilidades:**
- Dispara a criação das camadas de valorização
- Contém os métodos de cálculo principais
- Cria lançamentos contábeis

### 2.3 stock.move.line

Detalhe do movimento:
- Lotes e números de série
- Localizações específicas
- Quantidades por linha

### 2.4 stock.quant

Quantidade física em cada localização:
```python
quantity    # Qty em stock
value       # Valor do stock (valorização automática)
```

### 2.5 product.category

Define a **estratégia de valorização**:
```python
property_cost_method    # 'standard', 'average', 'fifo'
property_valuation      # 'manual_periodic' ou 'real_time'

# Contas Contabilísticas
property_stock_journal                    # Journal de Stock
property_stock_account_input_categ_id     # Conta Input
property_stock_account_output_categ_id    # Conta Output
property_stock_valuation_account_id       # Conta Valuation
```

---

## 3. Métodos de Custeio

### 3.1 Comparação

| Aspecto | Standard | AVCO | FIFO | PCMP |
|---------|----------|------|------|------|
| **Cálculo** | Fixo (manual) | Média ponderada | Camadas cronológicas | Média por ano fiscal |
| **Atualização** | Manual | Auto (entrada) | Auto (entrada/saída) | Auto (entrada) |
| **Complexidade** | Baixa | Média | Alta | Média |
| **Performance** | Alta | Média | Baixa | Média |
| **remaining_qty** | Não usado | Tracking apenas | Usado (valorização) | Tracking apenas |
| **Vacuum** | Não | Não | Sim | Não |
| **Campo de preço** | standard_price | standard_price | standard_price | pcmp_price |
| **Contexto temporal** | - | - | - | Ano Fiscal |

### 3.2 STANDARD PRICE

```python
# Usa product.standard_price fixo
# Não recalcula automaticamente
# Adequado para produtos com custo estável
```

### 3.3 AVERAGE COST (AVCO)

**Fórmula:**
```python
new_std_price = (
    (old_standard_price * qty_available) +
    (new_unit_cost * qty_new)
) / (qty_available + qty_new)
```

**Método:** `stock.move.product_price_update_before_done()`

```python
def product_price_update_before_done(self, forced_qty=None):
    """Atualiza standard_price usando média ponderada."""

    for move in self:
        if not move._is_in():
            continue

        if move.product_id.cost_method == 'standard':
            continue

        # Quantidade existente
        product_tot_qty_available = move.product_id.quantity_svl

        qty = sum(quantity_by_lot.values())
        move_cost = move._get_price_unit()

        # FÓRMULA AVCO
        if float_is_zero(product_tot_qty_available):
            new_std_price = next(iter(move_cost.values()))
        else:
            new_std_price = (
                (amount_unit * product_tot_qty_available) +
                (next(iter(move_cost.values())) * qty)
            ) / (product_tot_qty_available + qty)

        # Atualiza standard_price
        move.product_id.sudo().write({'standard_price': new_std_price})
```

### 3.4 FIFO (First In First Out)

**Método:** `product.product._run_fifo()`

```python
def _run_fifo(self, quantity, company, lot=False):
    """Processa consumo FIFO iterando através de camadas SVL."""

    qty_to_take_on_candidates = quantity
    candidates = self._get_fifo_candidates(company, lot)  # Ordenadas por data
    tmp_value = 0

    for candidate in candidates:
        # Quantidade a consumir desta camada
        qty_taken = min(qty_to_take_on_candidates, candidate.remaining_qty)

        # Custo unitário da camada
        candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
        value_taken = qty_taken * candidate_unit_cost

        # ATUALIZA remaining da camada
        candidate.write({
            'remaining_qty': candidate.remaining_qty - qty_taken,
            'remaining_value': candidate.remaining_value - value_taken,
        })

        tmp_value += value_taken
        qty_to_take_on_candidates -= qty_taken

        if float_is_zero(qty_to_take_on_candidates):
            break

    # STOCK NEGATIVO - se ainda falta quantidade
    if qty_to_take_on_candidates > 0:
        last_fifo_price = new_standard_price or self.standard_price
        negative_stock_value = last_fifo_price * qty_to_take_on_candidates
        tmp_value += abs(negative_stock_value)

        return {
            'remaining_qty': -qty_to_take_on_candidates,  # NEGATIVO!
            'value': -tmp_value,
            'unit_cost': last_fifo_price,
        }

    return {
        'value': -tmp_value,
        'unit_cost': tmp_value / quantity,
    }
```

### 3.5 FIFO Vacuum (Correção de Stock Negativo)

**Método:** `product.product._run_fifo_vacuum()`

```python
def _run_fifo_vacuum(self, company):
    """Corrige cenários de stock negativo."""

    # 1. Identifica camadas com remaining_qty negativo
    negative_layers = svl.filtered(lambda l: l.remaining_qty < 0)

    for negative_layer in negative_layers:
        # 2. Busca candidatos criados DEPOIS
        candidates = self._get_fifo_candidates_after(negative_layer, company)

        for candidate in candidates:
            qty_matched = min(abs(negative_layer.remaining_qty),
                            candidate.remaining_qty)

            # 3. Calcula diferença de valor
            estimated_value = qty_matched * negative_layer.unit_cost
            actual_value = qty_matched * (candidate.remaining_value /
                                         candidate.remaining_qty)
            value_correction = actual_value - estimated_value

            # 4. Atualiza remaining de ambas camadas
            negative_layer.remaining_qty += qty_matched
            candidate.remaining_qty -= qty_matched
            candidate.remaining_value -= actual_value

            # 5. Cria SVL de correção se há diferença
            if not float_is_zero(value_correction):
                create_correction_svl(value_correction)
```

### 3.6 PCMP (Preço de Custo Médio Ponderado por Ano Fiscal)

O método PCMP é uma variante do AVCO que considera o **contexto do ano fiscal**, mantendo um ponto de partida anual.

#### Características:
- **Campo próprio**: `pcmp_price` (não usa `standard_price`)
- **Ponto de partida**: Definido para cada produto/ano fiscal
- **Recálculo**: Apenas em movimentos de ENTRADA
- **Transição de ano**: Via wizard ou automático

#### Fórmula PCMP:
```python
# Valores iniciais do ano fiscal
initial_value = initial_stock * initial_pcmp

# Valores acumulados do ano fiscal
sales_value = sales_qty * current_pcmp       # Saídas valoradas ao PCMP atual
import_value = import_qty * import_unit_cost # Entradas valoradas ao custo real

# Fórmula
numerator = initial_value - sales_value + import_value
denominator = initial_stock - sales_qty + import_qty
new_pcmp = numerator / denominator
```

#### Modelo de Ponto de Partida (`mh.pcmp.fiscal.year`):
```python
class MhPcmpFiscalYear(models.Model):
    _name = 'mh.pcmp.fiscal.year'

    product_id = fields.Many2one('product.product', required=True)
    fiscal_year = fields.Integer(required=True)    # Ex: 2025, 2026
    company_id = fields.Many2one('res.company')

    # Ponto de partida
    initial_stock = fields.Float('Stock Inicial')
    initial_pcmp = fields.Float('PCMP Inicial')
    initial_value = fields.Float('Valor Inicial', compute='_compute_initial_value')

    # Controlo
    is_new_product = fields.Boolean('Produto Novo no Ano')
    first_entry_date = fields.Date('Data 1ª Entrada')
```

#### Método Principal (`product.product._compute_pcmp()`):
```python
def _compute_pcmp(self, fiscal_year=None, company=None):
    """Calcula PCMP usando a fórmula do ano fiscal."""
    self.ensure_one()

    # Ponto de partida
    initial = self._get_pcmp_initial_values(fiscal_year, company)

    # Movimentos do ano fiscal
    date_from = f'{fiscal_year}-01-01'
    date_to = f'{fiscal_year}-12-31'

    # Entradas do ano (quantidade e valor real)
    in_svls = self.env['stock.valuation.layer'].search([
        ('product_id', '=', self.id),
        ('company_id', '=', company.id),
        ('create_date', '>=', date_from),
        ('create_date', '<=', date_to),
        ('quantity', '>', 0),  # Entradas
    ])
    import_qty = sum(in_svls.mapped('quantity'))
    import_value = sum(in_svls.mapped('value'))

    # Saídas do ano (quantidade * PCMP atual)
    out_svls = self.env['stock.valuation.layer'].search([...])
    sales_qty = abs(sum(out_svls.mapped('quantity')))
    current_pcmp = self.with_company(company).pcmp_price or initial['pcmp']
    sales_value = sales_qty * current_pcmp

    # Fórmula PCMP
    numerator = initial['value'] - sales_value + import_value
    denominator = initial['stock'] - sales_qty + import_qty

    if denominator > 0:
        new_pcmp = numerator / denominator
    else:
        new_pcmp = current_pcmp  # Manter último se stock zero

    return new_pcmp
```

#### Override em `stock.move`:
```python
def product_price_update_before_done(self, forced_qty=None):
    """Override para atualizar PCMP em entradas."""
    super().product_price_update_before_done(forced_qty=forced_qty)

    # Processar PCMP
    pcmp_moves = self.filtered(
        lambda m: m._is_in() and
        m.product_id.cost_method == 'pcmp' and
        m.product_id.is_storable
    )

    for move in pcmp_moves:
        fiscal_year = move.date.year
        pcmp_record = move.product_id._get_pcmp_fiscal_year_record(fiscal_year)

        if not pcmp_record:
            # Primeira entrada do ano - criar ponto de partida
            move.product_id._create_pcmp_initial_from_purchase(
                quantity=move.quantity,
                unit_cost=move._get_price_unit(),
                move_date=move.date,
                company=move.company_id,
            )
        else:
            # Recalcular PCMP
            new_pcmp = move.product_id._compute_pcmp(fiscal_year, move.company_id)
            move.product_id.with_company(move.company_id).pcmp_price = new_pcmp
```

#### Criação de SVL para PCMP:
```python
def _create_in_svl(self, forced_quantity=None):
    """Override para criar SVL de entrada para produtos PCMP."""
    pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
    other_moves = self - pcmp_moves

    svl = self.env['stock.valuation.layer']

    # Processar movimentos PCMP
    if pcmp_moves:
        svl_vals_list = []
        for move in pcmp_moves:
            svl_vals_list += move._get_in_svl_vals(forced_quantity)
        if svl_vals_list:
            svl |= self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    # Processar outros movimentos via super()
    if other_moves:
        svl |= super(StockMove, other_moves)._create_in_svl(forced_quantity)

    return svl

def _create_out_svl(self, forced_quantity=None):
    """Override para criar SVL de saída para produtos PCMP."""
    pcmp_moves = self.filtered(lambda m: m.product_id.cost_method == 'pcmp')
    other_moves = self - pcmp_moves

    svl = self.env['stock.valuation.layer']

    # Processar movimentos PCMP
    if pcmp_moves:
        svl_vals_list = []
        for move in pcmp_moves:
            svl_vals_list += move._get_out_svl_vals(forced_quantity)
        if svl_vals_list:
            svl |= self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    # Processar outros movimentos via super()
    if other_moves:
        svl |= super(StockMove, other_moves)._create_out_svl(forced_quantity)

    return svl
```

#### Transição de Ano Fiscal:
```python
class MhPcmpYearTransition(models.TransientModel):
    _name = 'mh.pcmp.year.transition'

    def action_execute_transition(self):
        """Copia PCMP final do ano anterior como inicial do novo ano."""
        for product in products:
            final_stock = self._get_final_stock(product, self.from_year)
            final_pcmp = product.with_company(company).pcmp_price

            self.env['mh.pcmp.fiscal.year'].create({
                'product_id': product.id,
                'fiscal_year': self.to_year,
                'initial_stock': final_stock,
                'initial_pcmp': final_pcmp,
                'company_id': company.id,
                'is_new_product': False,
            })
```

---

## 4. Fluxo de Valorização

### 4.1 Diagrama Principal

```
Confirmação do Picking
        ↓
stock.move._action_done()
        ↓
_get_valued_types()  → Separa movimentos IN/OUT
        ↓
┌─────────────────────────────────────────┐
│  ENTRADAS:                              │
│  1. product_price_update_before_done()  │ ← Atualiza AVCO
│  2. _create_in_svl()                    │ ← Cria camadas
├─────────────────────────────────────────┤
│  SAÍDAS:                                │
│  1. _create_out_svl()                   │ ← Cria camadas
│     └─ _run_fifo() interno              │
└─────────────────────────────────────────┘
        ↓
_run_fifo_vacuum()  → Corrige stock negativo
        ↓
_validate_accounting_entries()  → Cria account.move
        ↓
_validate_analytic_accounting_entries()
```

### 4.2 Criação de SVL para Entradas

**Método:** `stock.move._create_in_svl()`

```python
def _create_in_svl(self, forced_quantity=None):
    svl_vals_list = self._get_in_svl_vals(forced_quantity)
    return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

def _get_in_svl_vals(self, forced_quantity):
    # Agregação de quantidades por lote
    for move_line in self._get_in_move_lines():
        quantity_by_lot[move_line.lot_id] += move_line.quantity_product_uom

    # Determinação do custo unitário
    if product.cost_method == 'standard':
        unit_cost = product.standard_price
    else:
        unit_cost = self._get_price_unit()

    # Construção dos valores
    for lot, qty in quantity_by_lot.items():
        vals = product._prepare_in_svl_vals(qty, unit_cost, lot)
        vals.update(self._prepare_common_svl_vals())
        svl_vals_list.append(vals)
```

### 4.3 Criação de SVL para Saídas

**Método:** `stock.move._create_out_svl()`

```python
def _create_out_svl(self, forced_quantity=None):
    svl_vals_list = self._get_out_svl_vals(forced_quantity)
    return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

def _get_out_svl_vals(self, forced_quantity):
    for lot, qty in quantity_by_lot.items():
        # Delega para o produto
        vals = product._prepare_out_svl_vals(qty, company, lot=lot)
        vals.update(self._prepare_common_svl_vals())
        svl_vals_list.append(vals)
```

### 4.4 Preparação de Valores (Produto)

```python
def _prepare_in_svl_vals(self, quantity, unit_cost, lot=False):
    """Valores para camadas de entrada."""
    value = company.currency_id.round(unit_cost * quantity)

    return {
        'product_id': self.id,
        'value': value,
        'unit_cost': unit_cost,
        'quantity': quantity,
        'remaining_qty': quantity,      # Disponível para FIFO
        'remaining_value': value,
        'company_id': company_id,
        'lot_id': lot.id if lot else False,
    }

def _prepare_out_svl_vals(self, quantity, company, lot=False):
    """Valores para camadas de saída."""
    quantity = -1 * quantity  # Negativo!

    vals = {
        'product_id': self.id,
        'value': currency.round(quantity * cost),
        'unit_cost': cost,
        'quantity': quantity,
    }

    # Executa FIFO para todos os métodos
    fifo_vals = self._run_fifo(abs(quantity), company, lot)
    vals['remaining_qty'] = fifo_vals.get('remaining_qty')

    # FIFO: override completo
    if self.cost_method == 'fifo':
        vals.update(fifo_vals)

    return vals
```

---

## 5. Integração Contabilística

### 5.1 Contas Configuradas na Categoria

```python
property_stock_journal                    # Journal de Stock
property_stock_account_input_categ_id     # Stock Input (contrapartida entrada)
property_stock_account_output_categ_id    # Stock Output (contrapartida saída)
property_stock_valuation_account_id       # Stock Valuation (valor atual)
```

### 5.2 Matriz de Lançamentos

| Operação | Débito | Crédito |
|----------|--------|---------|
| **Entrada Normal** | Stock Input | Stock Valuation |
| **Saída Normal** | Stock Valuation | Stock Output |
| **Devolução de Entrada** | Stock Output | Stock Valuation |
| **Devolução de Saída** | Stock Valuation | Stock Input |

### 5.3 Método de Criação de Lançamentos

**Método:** `stock.move._account_entry_move()`

```python
def _account_entry_move(self, qty, description, svl_id, cost):
    """Cria lançamentos contábeis de valorização."""

    # Obtém contas
    journal_id, acc_src, acc_dest, acc_valuation = \
        self._get_accounting_data_for_valuation()

    # Lançamentos para ENTRADA
    if self._is_in():
        if self._is_returned(valued_type='in'):
            # Devolução: DR Output / CR Valuation
            am_vals.append(self._prepare_account_move_vals(
                acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
        else:
            # Normal: DR Input / CR Valuation
            am_vals.append(self._prepare_account_move_vals(
                acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

    # Lançamentos para SAÍDA
    if self._is_out():
        cost = -1 * cost

        if self._is_returned(valued_type='out'):
            # Devolução: DR Valuation / CR Input
            am_vals.append(self._prepare_account_move_vals(
                acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
        else:
            # Normal: DR Valuation / CR Output
            am_vals.append(self._prepare_account_move_vals(
                acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))

    return am_vals
```

### 5.4 Anglo-Saxon Accounting (COGS)

Quando fatura de venda é publicada:
```
DR  Expense Account (COGS)        XXX
    CR  Stock Output (Interim)          XXX
```

Reconciliação automática zera as contas interinas.

---

## 6. Exemplos Práticos

### 6.1 Exemplo FIFO Completo

```
ENTRADA #1: 100 un @ 10.00
├─ SVL-001 criado:
│  ├─ quantity: 100
│  ├─ value: 1000.00
│  ├─ unit_cost: 10.00
│  ├─ remaining_qty: 100 ✓
│  └─ remaining_value: 1000.00 ✓
└─ Lançamento: DR Input 1000 / CR Valuation 1000

ENTRADA #2: 50 un @ 12.00
├─ SVL-002 criado:
│  ├─ quantity: 50
│  ├─ value: 600.00
│  ├─ unit_cost: 12.00
│  ├─ remaining_qty: 50 ✓
│  └─ remaining_value: 600.00 ✓
└─ Lançamento: DR Input 600 / CR Valuation 600

SAÍDA: 120 un
├─ _run_fifo(120) executa:
│
│  CONSOME SVL-001 (100 un):
│  ├─ qty_taken = 100
│  ├─ unit_cost = 10.00
│  ├─ value_taken = 1000.00
│  └─ SVL-001.remaining_qty: 100 → 0
│
│  CONSOME SVL-002 (20 un dos 50):
│  ├─ qty_taken = 20
│  ├─ unit_cost = 12.00
│  ├─ value_taken = 240.00
│  └─ SVL-002.remaining_qty: 50 → 30
│
├─ Total: 1240.00 (custo médio: 10.33)
├─ SVL-003 criado:
│  ├─ quantity: -120
│  ├─ value: -1240.00
│  └─ unit_cost: 10.33
└─ Lançamento: DR Valuation 1240 / CR Output 1240

STOCK FINAL:
├─ qty: 30 un
├─ value: 360.00
└─ unit_cost: 12.00
```

### 6.2 Exemplo AVCO

```
ENTRADA #1: 100 un @ 10.00
├─ standard_price = 10.00
├─ SVL: qty=100, value=1000
└─ Stock: 100 un @ 10.00 = 1000.00

ENTRADA #2: 50 un @ 12.00
├─ CÁLCULO AVCO:
│  new_price = (10.00 * 100 + 12.00 * 50) / (100 + 50)
│  new_price = (1000 + 600) / 150 = 10.67
├─ standard_price = 10.67
├─ SVL: qty=50, value=600
└─ Stock: 150 un @ 10.67 = 1600.00

SAÍDA: 60 un
├─ Usa standard_price = 10.67
├─ Valor = 60 * 10.67 = 640.20
├─ SVL: qty=-60, value=-640.20
└─ Stock: 90 un @ 10.67 = 959.80
```

### 6.3 Exemplo PCMP (Ano Fiscal)

```
ANO FISCAL 2025 - PONTO DE PARTIDA
├─ initial_stock = 200 un
├─ initial_pcmp = 10.00
└─ initial_value = 2000.00

ENTRADA #1 (15/02/2025): 100 un @ 12.00
├─ SVL criado:
│  ├─ quantity: 100
│  ├─ value: 1200.00
│  └─ unit_cost: 12.00
├─ CÁLCULO PCMP:
│  ├─ import_qty = 100
│  ├─ import_value = 1200.00
│  ├─ sales_qty = 0 (ainda sem saídas)
│  ├─ sales_value = 0
│  ├─ numerator = 2000 - 0 + 1200 = 3200
│  ├─ denominator = 200 - 0 + 100 = 300
│  └─ new_pcmp = 3200 / 300 = 10.67
└─ pcmp_price atualizado: 10.67

SAÍDA #1 (20/03/2025): 80 un
├─ Usa pcmp_price = 10.67
├─ SVL criado:
│  ├─ quantity: -80
│  ├─ value: -853.60
│  └─ unit_cost: 10.67
└─ pcmp_price NÃO RECALCULADO (só em entradas)

ENTRADA #2 (10/04/2025): 50 un @ 11.00
├─ SVL criado:
│  ├─ quantity: 50
│  ├─ value: 550.00
│  └─ unit_cost: 11.00
├─ CÁLCULO PCMP:
│  ├─ import_qty = 100 + 50 = 150
│  ├─ import_value = 1200 + 550 = 1750
│  ├─ sales_qty = 80
│  ├─ sales_value = 80 * 10.67 = 853.60
│  ├─ numerator = 2000 - 853.60 + 1750 = 2896.40
│  ├─ denominator = 200 - 80 + 150 = 270
│  └─ new_pcmp = 2896.40 / 270 = 10.73
└─ pcmp_price atualizado: 10.73

ESTADO FINAL ANO 2025:
├─ Stock: 270 un
├─ pcmp_price: 10.73
└─ Valor estimado: 2897.10

TRANSIÇÃO PARA 2026:
├─ Wizard copia para mh.pcmp.fiscal.year:
│  ├─ fiscal_year: 2026
│  ├─ initial_stock: 270
│  ├─ initial_pcmp: 10.73
│  └─ initial_value: 2897.10
└─ Novo ano começa com este ponto de partida
```

### 6.4 Exemplo Stock Negativo + Vacuum

```
SAÍDA SEM STOCK: 40 un (stock = 0)
├─ Usa último preço conhecido: 12.00
├─ SVL-NEG criado:
│  ├─ quantity: -40
│  ├─ value: -480.00
│  ├─ remaining_qty: -40 (NEGATIVO!)
└─ Stock: -40 un

ENTRADA POSTERIOR: 100 un @ 11.00
├─ SVL-NEW criado normalmente
│
├─ VACUUM executa:
│  ├─ Detecta SVL-NEG com remaining_qty = -40
│  ├─ Usa SVL-NEW para corrigir
│  ├─ Diferença: (11.00 - 12.00) * 40 = -40.00
│  ├─ Cria SVL-CORRECTION: value = -40.00
│  ├─ SVL-NEG.remaining_qty: -40 → 0
│  └─ SVL-NEW.remaining_qty: 100 → 60
│
└─ Stock Final: 60 un @ 11.00
```

---

## 7. Queries Úteis

### 7.1 Ver Camadas de Valorização

```sql
-- Todas camadas de um produto
SELECT
    id, create_date, quantity, unit_cost, value,
    remaining_qty, remaining_value
FROM stock_valuation_layer
WHERE product_id = [PRODUCT_ID]
ORDER BY create_date;

-- Camadas com stock disponível (FIFO)
SELECT * FROM stock_valuation_layer
WHERE product_id = [PRODUCT_ID]
AND remaining_qty > 0
ORDER BY create_date;

-- Camadas negativas (precisam vacuum)
SELECT * FROM stock_valuation_layer
WHERE remaining_qty < 0;

-- Pontos de partida PCMP por ano fiscal
SELECT
    p.default_code,
    pfy.fiscal_year,
    pfy.initial_stock,
    pfy.initial_pcmp,
    pfy.initial_value,
    pfy.is_new_product
FROM mh_pcmp_fiscal_year pfy
JOIN product_product p ON p.id = pfy.product_id
ORDER BY pfy.fiscal_year DESC, p.default_code;
```

### 7.2 Valor Total em Stock

```sql
-- Por produto
SELECT
    product_id,
    SUM(remaining_qty) as qty_total,
    SUM(remaining_value) as value_total
FROM stock_valuation_layer
GROUP BY product_id;

-- Custo médio real
SELECT
    product_id,
    SUM(remaining_value) / NULLIF(SUM(remaining_qty), 0) as avg_cost
FROM stock_valuation_layer
GROUP BY product_id;
```

### 7.3 Verificar Consistência

```sql
-- Comparar SVL com stock.quant
SELECT
    p.id,
    p.default_code,
    COALESCE(svl.qty, 0) as svl_qty,
    COALESCE(sq.qty, 0) as quant_qty,
    COALESCE(svl.qty, 0) - COALESCE(sq.qty, 0) as diff
FROM product_product p
LEFT JOIN (
    SELECT product_id, SUM(remaining_qty) as qty
    FROM stock_valuation_layer GROUP BY product_id
) svl ON svl.product_id = p.id
LEFT JOIN (
    SELECT product_id, SUM(quantity) as qty
    FROM stock_quant
    WHERE location_id IN (SELECT id FROM stock_location WHERE usage = 'internal')
    GROUP BY product_id
) sq ON sq.product_id = p.id
WHERE COALESCE(svl.qty, 0) != COALESCE(sq.qty, 0);
```

---

## Referências

### Odoo 18 Nativo
- **Módulo:** `stock_account` (Odoo 18)
- **Ficheiros principais:**
  - `addons/stock_account/models/stock_move.py`
  - `addons/stock_account/models/stock_valuation_layer.py`
  - `addons/stock_account/models/product.py`
- **GitHub:** https://github.com/odoo/odoo/tree/18.0/addons/stock_account

### Módulo PCMP (mh_stock_valuation)
- **Ficheiros PCMP:**
  - `mh_stock_valuation/models/mh_pcmp_fiscal_year.py` - Modelo de ponto de partida
  - `mh_stock_valuation/models/product_category.py` - Extensão cost_method
  - `mh_stock_valuation/models/product_product.py` - Métodos _compute_pcmp(), pcmp_price
  - `mh_stock_valuation/models/stock_move.py` - Overrides valorização
  - `mh_stock_valuation/wizard/mh_pcmp_year_transition.py` - Transição de ano fiscal

---

*Documentação criada para o módulo mh_stock_valuation*
*Odoo 18 - Sistema de Valorização de Inventário com suporte PCMP*
