# Reconciliação Bancária — Odoo vs Primavera/PHC, Implicações Fiscais em MZ

## Visão geral

Em Odoo 18 há **dois fluxos** para registar entradas/saídas no banco:

1. **2-step (default)** — payment regista directamente no Banco; reconciliação com extracto é informativa
2. **3-step (Outstanding Receipts/Payments)** — payment regista numa conta de trânsito; só vai ao Banco após reconciliação

Em **Primavera/PHC** (padrão MZ), o equivalente é sempre 2-step: 1 recibo = 1 lançamento no diário do Banco.

---

## Como Odoo cria movimentos contabilísticos

### `account.payment` (Recibo/Pagamento)

Quando postado, cria **1** `account.move` no diário do banco.

**2-step:**
```
Debit:  Banco BIM (121001)      +1000
Credit: Receivable Cliente      -1000
```
O dinheiro entra imediatamente na conta do Banco.

**3-step:**
```
Debit:  Outstanding Receipts (1281)   +1000
Credit: Receivable Cliente            -1000
```
O dinheiro fica em **trânsito**. Só vai para o Banco quando a linha do extracto for reconciliada.

### `account.bank.statement.line` (Linha de extracto bancário)

Importada do banco. Cria **1** `account.move` no diário do banco (excepto se for matching directo com RC existente em 2-step).

Padrão inicial (antes de reconciliação):
```
Debit:  Banco BIM        +X
Credit: Suspense Account -X  (placeholder)
```

A conta `Suspense` é uma placeholder até saberes a contrapartida real.

### Reconciliação

**Não cria** um novo `account.move`. Apenas:

- Emparelha linhas existentes (`account.partial.reconcile`)
- Pode substituir a conta `Suspense` pela contrapartida real (Receivable, gasto, etc.)

---

## Fluxos comparados

### 2-step (recomendado para MZ)

```
Dia 1: Cliente paga 1000 MT, fazes RC
   → account.move (RC):
        Banco BIM +1000 ↔ Receivable Cliente -1000
   → Saldo Banco BIM: +1000 (já contabilizado)

Dia 5: Recebes extracto do BIM com linha de +1000
   → Importas extracto / criar bank.statement
   → Matching automático ou manual encontra o RC do dia 1
   → "Reconcile" → NÃO cria novo move
   → Apenas marca a statement.line como reconciliada
```

**Total:** 1 lançamento contabilístico.

### 3-step

```
Dia 1: Cliente paga, fazes RC
   → account.move (RC):
        Outstanding Receipts +1000 ↔ Receivable Cliente -1000
   → Saldo Banco BIM: 0 (dinheiro em trânsito)

Dia 5: Extracto do BIM com linha de +1000
   → bank.statement.line cria account.move:
        Banco BIM +1000 ↔ Suspense Account -1000
   → "Reconcile" com o RC: Suspense vira Outstanding Receipts
        Banco BIM +1000 ↔ Outstanding Receipts -1000
   → Saldo Banco BIM: +1000 (agora sim)
```

**Total:** 2 lançamentos contabilísticos para o mesmo RC.

### Linha de extracto SEM RC (comissões, juros)

Em **ambos os modos**, é igual:

```
Statement.line "Comissão BIM 50 MT" sem RC associado
   → Validar via wizard de reconciliação
   → Cria account.move:
        Banco BIM -50 ↔ 6224 Comissões bancárias +50
```

**1 lançamento adicional** no diário do banco.

---

## Tabela resumo

| Cenário | 2-step | 3-step |
|---|---|---|
| Cliente paga, lanças RC | 1 move (Banco ↔ Recv) | 1 move (Outstanding ↔ Recv) |
| Importas extracto, matching c/ RC | 0 moves extra (marca) | 1 move (Banco ↔ Outstanding) |
| Linha de extracto sem RC | 1 move (Banco ↔ Gasto) | 1 move (Banco ↔ Gasto) |
| **Total: 1 RC + 1 comissão** | **2 moves** | **3 moves** |

---

## Implicações fiscais em Moçambique

### Quadro legal

- **PGC-NIRF** (Plano Geral de Contabilidade alinhado com IFRS/IAS)
- **SAF-T MZ**: cada `AccountTransaction` tem ID único; auditor fiscal lê este ficheiro
- **Lei nº 7/2014 (IVA)** e **Código Comercial**: exigem rastreabilidade documento ↔ lançamento

### 3-step é legal em MZ?

**Tecnicamente sim**, se mapeares correctamente a conta `Outstanding`:

| Conta Odoo | Conta PGC-MZ | Natureza |
|---|---|---|
| Outstanding Receipts | `1281 – Outros depósitos à ordem` ou `2762 – Devedores diversos` | Disponibilidade em trânsito |
| Outstanding Payments | Idem | Idem |

A norma **IAS 7** (que MZ segue) reconhece "cash in transit / equivalentes de caixa" como conceito válido.

### Atrito prático em MZ

1. **Auditores locais** habituados a Primavera/PHC: 1 RC = 1 lançamento. Estranham 2 movimentos para um único recibo.

2. **Conciliação bancária externa**: extracto do BIM/BCI bate uma a uma com lançamentos do diário. Em 3-step, o `Outstanding` aparece "a mais" antes da conciliação.

3. **SAF-T**: cada move é uma `AccountTransaction` distinta. Auditor fiscal verá 2 transactions referenciando o mesmo `SourceDocumentID` (RC). Não é ilegal, mas é incomum no contexto MZ.

4. **IVA**: não afecta. IVA é gerado na factura, não no recibo.

### Quando 3-step justifica-se

- Cartão de crédito como meio de pagamento (delay real entre cliente pagar e banco creditar)
- Múltiplos bancos com transferências internas frequentes
- Operação multi-moeda complexa
- Cheques (período entre depósito e compensação)

Para operação normal com BIM/BCI/ABSA em MZ, **2-step é suficiente e familiar**.

---

## Reconciliação com extractos: funciona em ambos os modos

A reconciliação com extractos bancários **não exige 3-step**. São conceitos separados:

- **2-step vs 3-step**: define **quando** o dinheiro entra na conta do Banco
- **Reconciliação**: acto de **emparelhar** linha de extracto com RC já lançado

Em 2-step podes:
- Importar extractos bancários (CSV, OFX, etc.) normalmente
- Fazer matching automático/manual com RCs
- Validar e marcar como reconciliado

Sem criar lançamentos contabilísticos duplicados.

---

## Recomendação para Stone Trading / Pemaro

**Usar 2-step (default)** — alinhado com Primavera/PHC:
- 1 lançamento por RC/PG
- Sem contas intermediárias estranhas ao auditor local
- Reconciliação com extractos funciona normalmente
- Comissões/juros lançam-se na altura do matching

**Não activar Outstanding Receipts/Payments** nos métodos de pagamento dos diários BIM, BCI, CSH, ABSA, MOZ.

---

## Onde verificar a configuração em Odoo

```
Settings > Accounting > Journals > [Bank Journal]
   > Incoming Payments / Outgoing Payments
   > Outstanding Account = (vazio para 2-step; preenchido para 3-step)
```

Ver também:
- `account.payment.method.line` (modelo)
- `payment_account_id` (campo da journal)
