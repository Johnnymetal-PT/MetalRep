# Tutorial — Adiantamentos de cliente na encomenda (HMD)

> Como registar um **adiantamento** pago pelo cliente diretamente na encomenda de
> venda e tê-lo **automaticamente abatido na fatura**. Usa o módulo de
> adiantamentos já instalado (`sale_advance_payment`).
> Serve também de guião para o vídeo curto HMD-specific.

## Quando usar

Quando o cliente paga **antes da faturação** (sinal / adiantamento, ex.: 40% na
adjudicação). O adiantamento fica ligado à encomenda e, quando a fatura sair, é
descontado sozinho — sem lançamentos manuais.

---

## Passo 1 — Registar o adiantamento na encomenda

1. Abre a **encomenda de venda** (idealmente já confirmada).
2. Carrega no botão **Pagar adiantamento** (*Pay sale advanced*).
3. No assistente, preenche:
   - **Diário** — o banco/diário onde **entra** o dinheiro;
   - **Montante adiantado** — o valor recebido;
   - **Data** — a data do recebimento;
   - **Referência** — opcional (ex.: nº da transferência).
4. Confirma.

> Fica criado um **pagamento de adiantamento** associado a esta encomenda.

---

## Passo 2 — Ver o adiantamento na encomenda

Na própria encomenda passas a ver:
- a lista de **adiantamentos** recebidos (separador/página *Adiantamentos*);
- o **valor residual** (quanto falta receber);
- o **estado de adiantamento** (sem / parcial / totalmente adiantado).

> Com o acesso PG (`pg_sale_advance_payment_access`), os adiantamentos são
> visíveis no orçamento **sem expor o diário restrito**.

---

## Passo 3 — Faturar (o abatimento é automático)

1. Cria a **fatura** a partir da encomenda, como habitualmente.
2. **Confirma/Publica** a fatura.
3. O adiantamento é **reconciliado automaticamente** contra a fatura ao publicar
   — o valor em dívida da fatura já vem deduzido do adiantamento.

> Não é preciso conciliar à mão: o módulo faz a ligação do pagamento de
> adiantamento à fatura no momento da publicação.

---

## Nota — Adiantamento intracomunitário

Para clientes intracomunitários, o **mecanismo do adiantamento é igual** ao acima.
O que muda é o **tratamento de IVA** (operação intracomunitária):

- **[VALIDAR com a contabilidade]** confirmar a **posição fiscal** do cliente
  (intracomunitário) e o efeito no IVA do adiantamento/fatura, para garantir que
  o adiantamento não gera IVA indevido.

> O passo-a-passo de registo não muda; a diferença é apenas fiscal e depende da
> posição fiscal configurada no cliente.

---

## Resumo em 3 linhas

1. Na encomenda: **Pagar adiantamento** → diário + valor + data.
2. A encomenda mostra **adiantamentos** e **valor residual**.
3. Ao **publicar a fatura**, o adiantamento é **abatido automaticamente**.
