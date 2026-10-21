# -*- coding: utf-8 -*-
{
    "name": "PG Purchase Advance Payment",
    "version": "17.0.1.1.0",
    "summary": "Mostra na encomenda de compra quanto já foi pago ao fornecedor (adiantamentos e faturas)",
    "description": """
PG Purchase Advance Payment
===========================

Objetivo de negócio
-------------------
Nas vendas, o adiantamento de um cliente (fatura de adiantamento) fica visível na própria
encomenda como uma linha de adiantamento. Nas compras o Odoo 17 não tem nada equivalente:
o pagamento adiantado ao fornecedor fica como crédito em aberto na conta do fornecedor e a
encomenda de compra não mostra nada. Para saber quanto já foi adiantado era preciso ir aos
pagamentos e fazer contas.

Este módulo resolve só a **visibilidade**: a encomenda de compra mostra quanto já foi pago
ao fornecedor e quanto falta, quer o pagamento seja um adiantamento antes da fatura, quer
um pagamento (total ou parcial) feito pela própria fatura. A contabilização continua a ser
a standard.

Pré-requisitos
--------------
- Módulos: `purchase`, `account`.
- Para registar e consultar os adiantamentos a partir da compra: grupo
  Contabilidade / Faturação (`account.group_account_invoice`). Os valores no rodapé são
  visíveis a todos os utilizadores de Compras.

Como funciona
-------------
- `account.payment` ganha o campo `pg_purchase_order_id` ("Encomenda de compra"), visível
  nos pagamentos a fornecedores. Pode ser preenchido também em pagamentos já lançados, o que
  permite ligar pagamentos registados antes da instalação.
- O campo é preenchido automaticamente em dois casos:
    * botão "Registar adiantamento" na compra;
    * "Registar pagamento" numa fatura de fornecedor (`account.payment.register`), quando as
      faturas pagas vêm de **uma só** encomenda (pelas linhas `purchase_line_id`). Se o
      pagamento juntar faturas de várias encomendas, fica vazio.
- `purchase.order` ganha, calculados (não armazenados, em sudo):
    * `pg_advance_amount` ("Pago ao fornecedor"): soma dos pagamentos **lançados**
      ligados à encomenda, convertidos para a moeda da encomenda à data do pagamento.
      Reembolsos do fornecedor (pagamentos recebidos) ligados à encomenda abatem.
    * `pg_amount_after_advance` ("Por pagar"): total da encomenda menos o pago.
- Não há dupla contagem: um adiantamento reconciliado depois com a fatura continua a ser um
  só pagamento, e pela fatura só se paga o que ela ainda tem em aberto.
- Formulário da compra:
    * botão "Registar adiantamento" (encomendas confirmadas), que abre um pagamento a
      fornecedor já preenchido com o fornecedor, a moeda, o valor por pagar, a referência
      da encomenda no Memo e a ligação à encomenda;
    * smart button "Pago" com o valor pago, que abre a lista dos pagamentos;
    * as duas linhas no rodapé, por baixo dos totais, só quando há pagamentos.
- Lista de pagamentos a fornecedores: coluna opcional "Encomenda de compra".

Passo a passo de utilização
---------------------------
1. Abrir uma encomenda de compra confirmada e clicar em "Registar adiantamento".
2. Acertar o valor (vem proposto o que está por pagar), o diário e a data. Confirmar o
   pagamento.
3. Voltar à encomenda: o rodapé mostra "Pago ao fornecedor" e "Por pagar", e aparece o
   smart button "Pago".
4. Quando chegar a fatura do fornecedor, reconciliar o adiantamento como habitualmente (na
   fatura, "Débitos pendentes" → "Adicionar").

Se a fatura já existir: na fatura, "Registar pagamento" com o valor pretendido (parcial ou
total). O pagamento fica ligado à encomenda sozinho.

Para um pagamento já existente: abrir o pagamento e preencher "Encomenda de compra".

Exemplo prático
---------------
Encomenda P04500 de 10.000 € a um fornecedor que pede 30 % adiantado. Regista-se um
adiantamento de 3.000 € a partir da encomenda: a encomenda mostra "Pago ao fornecedor:
3.000,00 €" e "Por pagar: 7.000,00 €".

Outro caso: a encomenda P04501 já tem uma fatura de 100 €. Na fatura, regista-se um
pagamento de 50 €. A encomenda mostra "Pago ao fornecedor: 50,00 €" e "Por pagar: 50,00 €".

FAQ / Resolução de problemas
----------------------------
- P: Registei o pagamento e a encomenda não o mostra.
  R: Só contam pagamentos lançados (Confirmados); um rascunho aparece no smart button mas
     não soma ao valor. Se o pagamento foi feito pela fatura, confirmar que a fatura foi
     criada a partir da encomenda (linhas ligadas à compra) e que o pagamento não juntou
     faturas de várias encomendas. Em último caso, preencher "Encomenda de compra" no
     pagamento.
- P: Não vejo o botão "Registar adiantamento" nem o smart button.
  R: São só para utilizadores com Faturação. O botão aparece apenas em encomendas
     confirmadas.
- P: A encomenda não aparece na lista ao escolher "Encomenda de compra" no pagamento.
  R: A lista mostra só encomendas confirmadas do mesmo fornecedor (ou contactos dele) e da
     mesma empresa do pagamento. Confirmar o fornecedor do pagamento.
Pontos de atenção
-----------------
- A ligação é informativa: não altera lançamentos nem a reconciliação. Ligar um pagamento à
  encomenda errada só muda o que a encomenda mostra.
- Os valores são calculados na leitura (não armazenados), por isso não servem para filtrar
  ou agrupar listas de compras.
- O botão "Registar adiantamento" cria o pagamento na empresa ativa do utilizador. Em
  encomendas de outra empresa, mudar primeiro de empresa.
- Só pagamentos registados **depois** da instalação ficam ligados sozinhos. Pagamentos de
  faturas anteriores não são ligados retroativamente.
- Pagamentos por "Conciliação bancária" diretamente contra a fatura (sem passar por
  "Registar pagamento") não criam `account.payment` e não aparecem na encomenda.
""",
    "category": "Inventory/Purchase",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "depends": ["purchase", "account"],
    "data": [
        "views/purchase_order_views.xml",
        "views/account_payment_views.xml",
    ],
    "installable": True,
    "application": False,
}
