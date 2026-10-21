{
    "name": "HMD Sale Payment State",
    "version": "18.0.1.1.0",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "category": "Sales",
    "summary": "Estado de pagamento automatico na Ordem de Venda, derivado das faturas e dos adiantamentos.",
    "license": "LGPL-3",
    "description": """
HMD Sale Payment State
======================

a) Objetivo de negocio
----------------------
A HMD quer que a Ordem de Venda mostre automaticamente se ja foi paga,
sem ninguem ter de alterar nada a mao. O fluxo real e:
Nina envia/regista o pagamento -> Sergio confirma -> a encomenda passa
a refletir o estado. No Odoo standard o `sale.order` nao tem estado
"pago" (so draft/sent/sale/cancel); o pagamento vive na fatura
(`account.move.payment_state`). Este modulo faz a ponte.

Origem: tarefa C11 ("Alerta pagamento cliente -> mudar estado SO").
Substitui o prototipo feito em Studio (campo + regra de automacao),
por decisao de gestao de projeto (Bruno Pinheiro): deve ser modulo, para
ser versionavel e portavel em migracoes de versao.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `sale` e `account`.
- Modulo `sale_advance_payment` (Comunitea/OCA), que ja esta instalado na
  HMD: e ele que da o separador "Payment advances" na encomenda e o campo
  `account.payment.sale_id`. Sem ele o modulo nao instala — e uma
  dependencia dura de proposito, porque metade da regra de negocio da HMD
  (adiantamento sem fatura) vive nesses pagamentos.

c) Como funciona (tecnico)
--------------------------
`sale.order` (`models/sale_order.py`):
  - Campo novo `hmd_payment_state` (Selection, store=True, computed):
      not_paid -> "Nao pago"
      partial  -> "Adiantamento recebido"
      paid     -> "Pago"
  - `_compute_hmd_payment_state` le DUAS fontes de dinheiro:
      * faturas de cliente publicadas
        (`invoice_ids`, move_type == 'out_invoice', state == 'posted');
      * adiantamentos registados na propria encomenda
        (`account_payment_ids`, o separador "Payment advances").
    A ordem de decisao e:
      1. ha faturas e estao todas 'paid'   -> "Pago";
      2. nao ha faturas e ha adiantamento  -> "Pago" se o adiantamento
         conciliado cobrir o total da encomenda, senao
         "Adiantamento recebido";
      3. ha adiantamento, ou alguma fatura parcial/paga/em pagamento
                                           -> "Adiantamento recebido";
      4. caso contrario                    -> "Nao pago".
  - `_hmd_advance_amounts` soma os `account.payment` ligados a encomenda,
    separando o que esta conciliado ('paid') do que esta lancado mas por
    conciliar ('in_process'), e converte para a moeda da encomenda.
    Pagamentos 'outbound' (devolucao de adiantamento) entram a subtrair.

  Sendo campo calculado e armazenado, recalcula-se sozinho sempre que
  uma fatura muda de payment_state ou e registado um adiantamento - sem
  regra de automacao.

Views (`views/sale_order_views.xml`):
  - Campo no formulario da encomenda, a seguir a `payment_term_id`,
    com widget badge (verde=pago, amarelo=adiantamento).
  - Coluna opcional (escondida por defeito) na lista de encomendas.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_sale_payment_state`.
2. Vendas > Encomendas > abrir uma encomenda.
3. O campo "Estado de Pagamento" mostra o estado atual.
4. Registar/confirmar um pagamento na fatura associada -> o campo
   atualiza-se automaticamente.

e) Migracao a partir do prototipo Studio (fazer na ativacao)
------------------------------------------------------------
O prototipo Studio criou, na BD de teste:
  - campo `x_studio_selection_field_3bt_1k0s2qd61` em sale.order;
  - regra de automacao "[C11] Estado de Pagamento na Encomenda".

Ao instalar este modulo, remover ambos para nao haver dois campos de
estado de pagamento a coexistir.

f) Decisoes fechadas (tarefa C11)
----------------------------------
- Adiantamento sem fatura — RESOLVIDO a partir da questao posta pela HMD
  em 08/09/2026:

    "para clientes de fora, estamos a criar um payment advance mas nao e
     acompanhado de uma fatura. Esta so e feita no final com a entrega
     final da encomenda. Isto significa que enquanto nao houver fatura, o
     estado da encomenda nao e atualizado?"

  A resposta a pergunta era SIM — na versao 18.0.1.0.0 o campo so olhava
  para faturas, e essas encomendas ficavam em "Nao pago" com o dinheiro ja
  recebido. Corrigido em 18.0.1.1.0: o adiantamento registado na encomenda
  passa a contar. Uma encomenda sem fatura com adiantamento recebido mostra
  "Adiantamento recebido", e mostra "Pago" se o adiantamento conciliado
  cobrir o total da encomenda.

  O caso do adiantamento de 100% sem fatura foi confirmado pela HMD em
  15/09/2026 (Nina Hedderich): "pode ficar como pago - da uma ideia clara
  de que o cliente pagou tudo daquela encomenda". Nao alterar sem nova
  decisao do cliente.

As duas duvidas iniciais foram resolvidas:

- Adiantamento de 40% — RESOLVIDO com dados, 31/08/2026.
  A HMD emite fatura pelo valor TOTAL e recebe em duas vezes; nao ha
  faturas de adiantamento. Verificado em quinze encomendas da
  HMD_TESTE (NE A/00059, A/00058 e A/00053 com payment_state
  'partial'). Nao foi preciso ir buscar account.payment, apesar de a
  descricao da tarefa falar em "server action em account.payment".

- Significado de "Pago" — DECIDIDO pela HMD, 31/08/2026, opcao A.
  "Pago" = todas as faturas emitidas estao liquidadas.

  A pergunta foi posta com o caso da NE A/00057: encomenda de 2.987,60,
  fatura de 2.147,60 integralmente paga, diferenca de 840. A HMD
  esclareceu que a diferenca NAO e divida — e um erro de registo na
  encomenda, onde a primeira linha ficou a 2.100 em vez de 1.260 por
  nao ter sido aplicado o desconto de 40%. O valor real da encomenda
  sao os 2.147,60 facturados e pagos.

  Consequencia de desenho: o campo nao tenta detectar valores por
  facturar. Para isso existe a coluna nativa "Estado da Fatura", que
  na vista de lista se le ao lado desta.

g) Alterar a logica depois de instalado (IMPORTANTE)
-----------------------------------------------------
`hmd_payment_state` e um campo calculado ARMAZENADO. Mudar o corpo do
compute e correr `-u hmd_sale_payment_state` recarrega o codigo mas
NAO recalcula os registos existentes: os valores gravados continuam a
ser os da logica antiga, e ninguem da por isso.

Na primeira instalacao nao ha problema (o Odoo calcula tudo ao criar a
coluna). Em qualquer alteracao posterior, forcar:

    recs = env['sale.order'].search([])
    recs._compute_hmd_payment_state()
    recs.flush_recordset(['hmd_payment_state'])
    env.cr.commit()

Verificado na HMD_TESTE a 31/08/2026: 240 encomendas.

h) Pagamentos por conciliar contam como adiantamento
-----------------------------------------------------
Uma fatura com pagamento registado mas ainda NAO conciliado fica em
payment_state 'in_payment' (dinheiro em transito). O campo trata isso
como "Adiantamento recebido", e nao como "Pago" — o dinheiro foi
lancado mas nao esta confirmado no banco.

Consequencia pratica para a HMD: se a conciliacao bancaria estiver em
atraso, encomendas ja pagas aparecem como "Adiantamento recebido" ate
alguem conciliar. Isto e relevante enquanto a sincronizacao com o
Millennium BCP estiver parada (parada desde 18/07/2026, ticket Odoo
#6.417.382): sem extractos importados nao ha conciliacao automatica.

Nao e defeito, e a leitura correcta. Mas convem estar documentado para
nao ser reportado como erro.

j) Porque nao se usa o `advance_payment_status` do sale_advance_payment
------------------------------------------------------------------------
O `sale_advance_payment` ja traz `advance_payment_status` e
`amount_residual`. Nao servem aqui por duas razoes:

1. So contam linhas em conta de clientes (`asset_receivable`). Nesta base
   o `ptplus_sale_advance_payment` (localizacao PT da EXO, auto_install)
   reencaminha o adiantamento para a conta de adiantamentos da categoria
   "All" (`property_account_downpayment_categ_id`). Os adiantamentos da
   HMD nao passam pela conta de clientes, pelo que aquele calculo nao os
   ve. Ler os `account.payment` directamente e independente da
   configuracao contabilistica.
2. `advance_payment_status` so sai de "not_paid" quando ha adiantamentos:
   uma encomenda liquidada so por fatura fica la sempre em "Not Paid".

k) Transicao adiantamento -> fatura final (comportamento esperado)
-------------------------------------------------------------------
Numa encomenda 100% adiantada e ainda sem fatura, o campo diz "Pago".
Quando a fatura final for emitida, a encomenda passa a ter fatura por
liquidar e o campo desce para "Adiantamento recebido" ate a regularizacao
do adiantamento (movimento que o `ptplus_sale_advance_payment` cria ao
publicar a fatura) ser conciliada com a fatura. Nao e defeito: entre a
emissao e a conciliacao a fatura esta mesmo por liquidar. Convem estar
documentado para nao ser reportado como erro.

i) Pontos de atencao / avisos
-----------------------------
- Campo calculado: nao e editavel manualmente. Se a HMD quiser poder
  forcar o estado a mao, mudar para campo normal + regra de automacao.
- So conta faturas publicadas de cliente. Notas de credito e
  rascunhos nao entram no calculo.
- Nos adiantamentos so contam os `account.payment` ligados a encomenda
  pelo separador "Payment advances". Um pagamento registado directamente
  na fatura chega ca pela via da fatura, como sempre; um pagamento solto,
  sem ligacao a encomenda nem a fatura, e invisivel para este campo.
- A atualizacao de 18.0.1.0.0 para 18.0.1.1.0 muda a logica do compute:
  e OBRIGATORIO forcar o recalculo depois do -u, como explica a seccao g).
  Sem isso as encomendas com adiantamento e sem fatura continuam a
  mostrar "Nao pago".
""",
    "depends": ["sale", "account", "sale_advance_payment"],
    "data": [
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
