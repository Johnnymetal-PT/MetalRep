# Tutorial — Criar categorias de despesa (HMD)

> Como criar e manter **categorias de despesa** no módulo Despesas (*Expenses*) do
> Odoo 18. As categorias são o que o colaborador escolhe ao lançar uma despesa
> (ex.: refeições, deslocações, ou **por tipo de cartão**).
> Serve também de guião para o vídeo curto HMD-specific.

## O que é uma "categoria de despesa"

No Odoo, cada categoria de despesa é um **produto marcado como despesa**. Define o
**nome**, a **conta contabilística** onde o gasto é lançado e os **impostos**
aplicáveis. Já existem várias criadas na HMD; este guia mostra como **acrescentar**
ou **editar**.

---

## Passo 1 — Abrir as categorias

Vai a **Despesas → Configuração → Categorias de Despesa**
(*Expenses → Configuration → Expense Categories*).

Vês a lista das categorias existentes. Para criar uma nova, carrega em **Novo**.

---

## Passo 2 — Preencher a categoria

| Campo | O que pôr |
|---|---|
| **Nome do Produto** | O nome que o colaborador vê (ex.: `Refeições`, `Cartão BCP — Combustível`) |
| **Pode ser uma despesa** | Deve estar **ativo** (é o que a torna uma categoria de despesa) |
| **Custo** | `0` se o valor é variável (o colaborador escreve o valor ao lançar) |
| **Unidade de Medida** | normalmente `Unidades` |
| **Referência** | opcional (código interno) |
| **Conta de Despesa** | a **conta contabilística** onde o gasto é lançado ← importante |
| **Impostos do fornecedor** | o IVA aplicável (ou nenhum), conforme o tipo de gasto |
| **Orientação** | texto de ajuda opcional (ex.: "Só dias úteis, almoço") |

Guarda.

> **Conta de Despesa** é o campo que garante que o gasto vai para o sítio certo na
> contabilidade — confirma-o com a contabilidade quando crias uma categoria nova.

---

## Passo 3 — Categorias por tipo de cartão (objetivo HMD)

Para separar gastos por **cartão de crédito**, cria categorias com nome que
identifique o cartão, por exemplo:

- `Cartão BCP — Combustível`
- `Cartão BCP — Refeições`
- `Cartão Santander — Deslocações`

Assim, ao lançar a despesa, o colaborador escolhe logo a categoria do cartão certo,
e os relatórios ficam organizados por cartão.

> A regra de nomes deve ser **consistente** (mesmo prefixo por cartão) para
> facilitar filtros e relatórios.

---

## Passo 4 — Usar a categoria (lançar despesa)

Em **Despesas → As minhas despesas → Novo**: escolhe a **categoria**, escreve o
**valor** e a **data**, anexa o comprovativo, e submete para aprovação.

---

## Boas práticas

- **Poucas e claras:** evita categorias a mais; agrupa por tipo de gasto/cartão.
- **Conta de despesa sempre preenchida:** sem ela, o gasto pode ir para a conta
  errada.
- **Nomes consistentes:** mesma convenção para todos (ex.: `Cartão X — Tipo`).
- **Arquivar em vez de apagar** categorias que deixam de se usar.
- **Tudo standard:** é configuração nativa do Odoo, sem programação.

---

## Resumo em 3 linhas

1. **Despesas → Configuração → Categorias de Despesa → Novo**.
2. Preenche **Nome**, **Conta de Despesa** e **Impostos** (custo `0` se variável).
3. Para cartões, usa nomes consistentes tipo **`Cartão X — Tipo`**.
