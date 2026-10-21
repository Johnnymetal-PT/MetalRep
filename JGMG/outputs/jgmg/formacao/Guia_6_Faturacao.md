# Sessão 6 — Faturação e pagamentos

**Cliente:** JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA · **Projeto:** Implementação Odoo · **Data:** 10/2026 · **Formadora:** Lara Cunha (Parâmetro Global)

> A interface do Odoo está em português do Brasil. Os nomes de menus e botões aparecem **a negrito, exatamente como no ecrã**.

## O que se vai ver e porquê

Registar as faturas no Odoo permite saber o que se deve receber e pagar, a quem e quando — e confirmar que cada fornecedor faturou o que foi encomendado. No Odoo, as faturas de fornecedores chamam-se **Contas**.

> ⚠️ **Regra durante a formação:** nenhuma fatura de exercício é confirmada. Uma fatura confirmada entra na numeração e **não se apaga** — corrige-se com nota de crédito. Os exercícios ficam em rascunho e são eliminados no fim.

## Parte A — Fatura ao cliente

1. Abrir o pedido de venda confirmado (**Vendas › Pedidos › Pedidos**).
2. **Criar fatura** — faturar o total, uma percentagem ou um valor fixo (adiantamento/sinal).
3. Rever o rascunho: cliente com NIF, linhas, IVA, total.
4. **Confirmar** — a partir daqui a fatura não se altera.
5. **Enviar** — por email ao cliente.
6. Quando o cliente pagar: **Pagar** (data, valor, banco).
7. Erro numa fatura confirmada: **Nota de crédito**.

## Parte B — Fatura de fornecedor

Menu: **Faturamento › Fornecedores › Contas** → **Novo**.

- **A partir de uma compra (recomendado):** escolher o fornecedor em **Parceiro** e, em **Compra - Conta de fornecedor**, o pedido de compra — as linhas vêm preenchidas.
- **Sem compra associada** (transportes, pequenas despesas): **Adicionar uma linha** em **Linhas da fatura**.
- **A partir do PDF:** **Digitalizar documento** — o Odoo lê o documento e propõe os dados. **Conferir sempre.**

Depois, em todos os casos:

1. **Referência** = número da fatura do fornecedor (evita duplicados).
2. **Data da fatura/conta** e **Condições de pagamento** ou **Data de vencimento**.
3. Conferir impostos e total com o documento; anexar o PDF.
4. **Confirmar** (passa de **Provisório** a **Lançado**).
5. Quando for paga: **Pagar**. Notas de crédito do fornecedor: **Faturamento › Fornecedores › Reembolsos**.

## Acompanhar

- **Status do pagamento**: Não pago / Parcialmente pago / Em pagamento / Pago.
- **Faturamento › Clientes › Faturas** e **Faturamento › Fornecedores › Contas** — filtrar por vencidas.

## Exercício (tudo em rascunho)

1. A partir do pedido de compra de teste da sessão 5, preparar a conta do fornecedor — **não confirmar**.
2. A partir do orçamento de teste da sessão 3, preparar a fatura ao cliente — **não confirmar**.
3. Eliminar os dois rascunhos.

## O que o Odoo passa a dar

- Valores a receber e a pagar, sempre atualizados.
- Ligação entre orçamento, fatura e pagamento; e entre encomenda, receção e fatura do fornecedor.

## O que fica fora e o que falta decidir

- Faturação certificada AT: **não aplicável** — decisão de 29/09/2026 (só Odoo SaaS).
- `[POR VALIDAR]` Se as faturas a clientes são emitidas no Odoo — decisão do cliente.
- `[POR VALIDAR]` Dados da empresa (NIF, morada, IBAN) — têm de estar completos antes da primeira fatura real.
- Contabilidade (fecho, declarações de IVA): fora desta formação.

## Próximos passos

1. Completar os dados da empresa.
2. Começar a registar as faturas de fornecedores recebidas.
