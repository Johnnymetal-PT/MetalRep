# Entendimento do Saldo de Caixa no Odoo 18

## Estrutura de Contas

### Contas Envolvidas no Fluxo de Caixa

| Conta | Nome | Tipo | Descrição |
|-------|------|------|-----------|
| 11101 | Caixa - Geral | Conta Principal | Onde o dinheiro "vive" contabilmente |
| 12402 | Recebimentos Pendentes | Outstanding (Inbound) | Conta de trânsito para recebimentos |
| 12403 | Pagamentos Pendentes | Outstanding (Outbound) | Conta de trânsito para pagamentos |

## Fluxo de Reconciliação

### 1. Quando um Pagamento/Recebimento é Registado

```
Recebimento em Caixa:
    Débito:  12402 (Recebimentos Pendentes)
    Crédito: Conta de Receita/Cliente

Pagamento em Caixa:
    Débito:  Conta de Despesa/Fornecedor
    Crédito: 12403 (Pagamentos Pendentes)
```

### 2. Quando é Reconciliado (via Bank Statement)

```
Reconciliação de Recebimento:
    Débito:  11101 (Caixa - Geral)
    Crédito: 12402 (Recebimentos Pendentes)  --> Fecha a pendência

Reconciliação de Pagamento:
    Débito:  12403 (Pagamentos Pendentes)    --> Fecha a pendência
    Crédito: 11101 (Caixa - Geral)
```

## Cálculo do Saldo Total do Caixa

O **saldo total** de um caixa específico é:

```
SALDO TOTAL = Saldo conta 11101 (filtrado pelo diário) + Saldo contas Outstanding (12402/12403)
```

### Exemplo Prático (Caixa 06 - CSH2)

| Componente | Débito | Crédito | Saldo |
|------------|--------|---------|-------|
| Conta 11101 (reconciliado) | 22,548.00 | 7,000.00 | 15,548.00 |
| Contas Outstanding (pendente) | 20,500.00 | 10,200.00 | 10,300.00 |
| **TOTAL CAIXA 06** | | | **25,848.00** |

## Módulo mh_cash_reconcile_import

### O que Exporta

O módulo exporta apenas os movimentos das **contas Outstanding** (12402/12403):
- Filtra por `journal.inbound_payment_method_line_ids.payment_account_id`
- Filtra por `journal.outbound_payment_method_line_ids.payment_account_id`

### Porque Exporta Apenas Outstanding

1. São os movimentos **pendentes de reconciliação**
2. Movimentos já reconciliados têm saldo zero nas contas outstanding
3. O objectivo é confirmar fisicamente e reconciliar esses movimentos

### Cálculo do Amount na Importação

```python
amount = debit - credit
# Débito em 12402 (Recebimentos) = positivo (entrada de dinheiro)
# Crédito em 12403 (Pagamentos) = negativo (saída de dinheiro)
```

## Resumo Importante

- **Conta 11101**: Saldo já confirmado/reconciliado
- **Contas 12402/12403**: Movimentos pendentes de confirmação
- **Saldo no Excel**: Mostra apenas pendentes (outstanding)
- **Saldo Total**: Soma de 11101 + Outstanding

## Queries Úteis

### Ver saldo de um caixa específico na conta 11101

```python
lines = env['account.move.line'].search([
    ('account_id', '=', cash_account.id),
    ('journal_id', '=', journal.id),  # Filtrar pelo diário específico
    ('parent_state', '=', 'posted'),
])
saldo = sum(l.debit - l.credit for l in lines)
```

### Ver movimentos outstanding de um caixa

```python
outstanding_accounts = (
    journal.inbound_payment_method_line_ids.mapped('payment_account_id') |
    journal.outbound_payment_method_line_ids.mapped('payment_account_id')
)
lines = env['account.move.line'].search([
    ('journal_id', '=', journal.id),
    ('parent_state', '=', 'posted'),
    ('account_id', 'in', outstanding_accounts.ids),
])
```

---
*Documentação criada em 04/01/2026*
