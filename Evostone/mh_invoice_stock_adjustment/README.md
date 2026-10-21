# MH Acerto Stock na Factura

Modulo Odoo 18 que trata automaticamente as diferencas entre a quantidade recebida (picking) e a quantidade facturada numa factura de fornecedor.

## Problema

Quando se valida uma factura de fornecedor, pode haver diferenca entre a quantidade recebida no armazem e a quantidade facturada. Isso cria um desequilibrio na conta intermedia de mercadorias (211xx).

## Cenarios

### Surplus (recebeu mais do que facturou)
Exemplo: PO de 10 un, recebeu 12, facturou 10.
As 2 unidades extra estao em stock mas nao foram facturadas.

**Accao do modulo:**
- Cria lancamento STJ: Debito 211xx / Credito 789003
- A 789003 acumula o proveito (ganho de existencias)

### Deficit (recebeu menos do que facturou)
Exemplo: PO de 10 un, recebeu 8, facturou 10.
Foram facturadas 2 unidades que nao existem em stock.

**Accao do modulo:**
- Cria lancamento STJ: Debito conta deficit / Credito 211xx
- A factura nao e alterada (o fornecedor e pago na totalidade)
- A conta deficit e determinada por: 1) artigo manual com acerto_de_stock, ou 2) conta definida nos Settings
- A quebra fica registada como saldo na conta deficit (ex: 6842)

### Misto (surplus e deficit na mesma factura)
Exemplo: PO com Produto A (recebeu 12, facturou 10) e Produto B (recebeu 8, facturou 10).

**Accao do modulo:**
- Cada linha e tratada individualmente
- Surplus: Debito 211xx / Credito 789003
- Deficit: Debito conta deficit / Credito 211xx

## Moeda estrangeira

O modulo suporta facturas em moeda estrangeira (ex: EUR com empresa em MZN):

- **Surplus**: O STJ usa a taxa de recepcao (stock move price_unit), porque as unidades excedentes estao em stock ao custo de recepcao
- **Deficit**: O STJ usa a taxa da factura (conversao na data da factura), para corresponder exactamente ao valor que a factura debitou na 21123
- **Desconto na factura**: O calculo considera o desconto aplicado na linha (price_unit * (1 - discount/100))

Isto garante que a conta 21123 fica saldada a zero em todos os cenarios.

## Conta deficit: automatica vs manual

O modulo determina a conta deficit pela seguinte prioridade:

1. **Manual**: Se o utilizador adicionou um produto de servico com a checkbox "Acerto de Stock" marcada na factura, o modulo usa a conta desse artigo como conta deficit no STJ. Neste caso a 6842 fica a zero (desconto compensa a quebra).
2. **Automatica**: Se nao existe artigo manual, usa a conta definida nos Settings. A factura nao e alterada e a 6842 fica com saldo (perda real).

Para configurar um produto de acerto manual:
- Criar produto do tipo Servico
- Marcar a checkbox "Acerto de Stock" na ficha do produto
- Adicionar este produto como linha na factura com o valor pretendido (negativo)

## Contas utilizadas

| Conta | Descricao | Funcao |
|-------|-----------|--------|
| 211xx | Conta intermedia de mercadorias | Vem da categoria do produto (`property_stock_account_input_categ_id`) |
| 789003 | Proveito Existencias | Contrapartida surplus (credito). Acumula proveito de existencias |
| Configuravel (ex: 6842) | Quebras / Deficit | Contrapartida deficit (debito). Definida nos Settings ou pelo artigo manual |

## Configuracao da conta deficit

A conta de deficit e determinada pela seguinte prioridade:
1. Se o utilizador adicionou manualmente um artigo com `acerto_de_stock=True` na factura → usa a conta desse artigo
2. Se automatico → usa a conta definida em **Definicoes → Contabilidade → Acerto de Stock → Conta Deficit**
3. Se nenhuma configurada → erro

Para configurar:
- Ir a Definicoes → Contabilidade → Acerto de Stock
- Definir a conta deficit (ex: 6842 Quebras)

## Diario

O modulo usa o diario **STJ** (Valorizacao de Inventario) para os lancamentos de acerto.

## Campos adicionados

### account.move (Factura)
- `stock_adjustment_move_id` - Many2one para o lancamento STJ gerado
- `stock_adjustment_state` - Estado do acerto: Sem ajuste / Excedente / Defice / Misto

### product.template (Produto)
- `acerto_de_stock` - Boolean, visivel apenas em produtos de servico. Indica que o produto e usado como linha de acerto manual.

### res.company (Empresa)
- `stock_adjustment_deficit_account_id` - Many2one para account.account. Conta a debitar para defices de stock.

## Dependencias

- `account`
- `purchase_stock`
- `stock_account`

## Exemplo pratico (MZN)

PO com 2 linhas:
- Slab Marmore: 10 un x 4.350 MZN, recebeu 12 (surplus +2)
- Slab Calcario: 10 un x 3.500 MZN, recebeu 8 (deficit -2)

Resultado apos postar a factura:

**Factura (nao alterada):**
- Marmore: 10 x 4.350 = 43.500 (debit 21123)
- Calcario: 10 x 3.500 = 35.000 (debit 21123)
- Fornecedor: -78.500 (credit payable, pago na totalidade)

**STJ:**
- Marmore surplus: 8.700 debit 21123 / 8.700 credit 789003
- Calcario deficit: 7.000 credit 21123 / 7.000 debit 6842

**Saldo final:**
- 21123: 0 (saldada)
- 789003: 8.700 credit (proveito do surplus)
- 6842: 7.000 debit (quebra do deficit)
