# Tutorial — Lançar gastos com pessoal (salários) via fatura de fornecedor (HMD)

> Como registar no Odoo um gasto que **não tem produto de catálogo** — caso típico:
> **salários / gastos com pessoal** — através de uma **fatura de fornecedor com
> uma linha sem produto**, lançando diretamente o valor.
> Serve também de guião para o vídeo curto HMD-specific.

## Quando usar

Sempre que precisas de registar um custo para o qual **não faz sentido criar um
produto** (é só um valor a lançar). O exemplo principal é o **salário**, mas a
mesma técnica serve para outros gastos sem produto de catálogo.

> A conta contabilística e o contacto necessários **já estão criados** — este
> guia foca-se no lançamento.

---

## Passo 1 — Abrir uma nova fatura de fornecedor

1. Vai a **Contabilidade → Fornecedores → Faturas** → **Novo**.
2. No **Fornecedor**, escolhe o contacto da **Autoridade Tributária (AT)**.
3. Confirma a **data da fatura** (e o vencimento, se aplicável).

---

## Passo 2 — Adicionar a linha SEM produto (o ponto-chave)

No separador **Linhas da fatura**, carrega em **Adicionar uma linha** e preenche
**sem escolher produto**:

| Campo | O que pôr |
|---|---|
| **Produto** | **deixar vazio** ← é isto que distingue este lançamento |
| **Etiqueta / Descrição** | ex.: `Salário — João Silva — Junho 2026` |
| **Conta** | a **conta de gastos com pessoal já criada** |
| **Quantidade** | `1` |
| **Preço unitário** | o **valor a lançar** |
| **Impostos** | **com ou sem imposto, conforme o caso** (ver nota abaixo) |

> O segredo é **não pôr produto**: a linha fica a ser só "valor contra conta", que
> é exatamente o que queremos.

**Sobre o imposto:** o campo de impostos da linha é opcional.
- **Sem imposto** — para valores que não têm IVA associado (ex.: o salário em si).
- **Com imposto** — quando o lançamento tem uma componente de imposto a refletir.

Define com a contabilidade qual o caso de cada tipo de lançamento e aplica sempre
da mesma forma.

---

## Passo 3 — Confirmar e pagar

1. Revê o total (deve corresponder ao valor pretendido).
2. Carrega em **Confirmar** para validar a fatura.
3. Quando for pago, usa **Registar pagamento** e escolhe o **banco** de onde sai
   o dinheiro.

---

## Verificação final

- A fatura fica **Publicada** e o valor lança na **conta de gastos com pessoal**.
- O **pagamento** concilia com o movimento de banco.
- O histórico do contacto (AT) mostra os lançamentos.

---

## Resumo em 3 linhas

1. **Fatura de fornecedor → Novo**, escolher o contacto da **AT** e a data.
2. **Linha sem produto**: descrição + conta de pessoal + valor (com ou sem imposto,
   conforme o caso).
3. **Confirmar** e **Registar pagamento** quando pago.

---

### Nota interna (Parâmetro, não para o cliente)
Método simplificado (fatura de fornecedor sem produto) escolhido pela HMD para
lançar gastos com pessoal sem usar o módulo de Processamento Salarial
(`hr_payroll`). Decisão do cliente — documentar como está. A linha sem produto é
suportada em standard (`account.move.line` sem `product_id`, com `account_id`
definido manualmente). Fornecedor usado: contacto da Autoridade Tributária (AT).
