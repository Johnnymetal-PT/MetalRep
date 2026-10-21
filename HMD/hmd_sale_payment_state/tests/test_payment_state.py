# -*- coding: utf-8 -*-
"""Testes do estado de pagamento da Ordem de Venda (tarefa C11).

Os casos vieram de dados reais da HMD_TESTE (31/08/2026), nao de
hipoteses. Em especial o test_fatura_emitida_por_menos, que reproduz a
NE A/00057 — o unico caso em que o Odoo considera a encomenda
totalmente facturada e mesmo assim falta dinheiro por receber.

NOTA sobre a classe base: usa-se TransactionCase e nao o
AccountTestInvoicingCommon do Odoo. Este ultimo cria uma empresa nova
em setUpClass, o que rebenta nesta base com
"Access Denied by ACLs for operation: create, uid: 30, model: res.partner"
— os modulos de seguranca da HMD (pg_account_journal_access e afins)
nao deixam o utilizador de teste criar empresas. Com TransactionCase
corremos como superutilizador sobre a empresa que ja existe.

NOTA sobre o produto: e um SERVICO. Com um consumivel, o
action_confirm arrasta sale_stock -> mrp -> purchase_stock e exige
fornecedor, rota e regras de abastecimento. Nada disso interessa ao
que estamos a testar.

NOTA sobre os adiantamentos: os testes novos (08/09/2026) criam
`account.payment` ligados a encomenda pelo campo `sale_id`, como faz o
assistente "Pay sale advanced" do `sale_advance_payment`. Nao se usa o
assistente para nao depender do seu wizard nem da conta de adiantamentos
da localizacao PT — o que interessa e o pagamento ficar ligado a
encomenda e publicado.

NOTA sobre o IVA: as linhas NAO podem ficar sem imposto. A localizacao
portuguesa (ptplus, da EXO) recusa a confirmacao com
"tem uma linha de produto que nao esta associada a qualquer IVA. Note
que mesmo quando a taxa de IVA e zero, e necessario utilizar uma conta
de IVA na linha". Por isso escolhe-se um imposto de venda existente —
de preferencia um de 0% — e os valores esperados sao derivados da
propria encomenda, nunca fixados a mao.
"""
from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHmdPaymentState(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.empresa = cls.env.company
        cls.cliente = cls.env["res.partner"].create({"name": "Cliente teste C11"})
        Imposto = cls.env["account.tax"]
        dominio = [("type_tax_use", "=", "sale"),
                   ("company_id", "=", cls.empresa.id)]
        # preferimos 0% para as contas ficarem redondas; se nao houver,
        # serve qualquer imposto de venda, porque nada aqui e fixado a mao
        cls.imposto = (Imposto.search(dominio + [("amount", "=", 0.0)], limit=1)
                       or Imposto.search(dominio, limit=1))
        # SERVICO, e nao bem consumivel, de proposito: um consumivel faz o
        # action_confirm disparar a cadeia sale_stock -> mrp ->
        # purchase_stock, que rebenta com "Nao ha preco de fornecedor
        # correspondente para gerar a encomenda". O que queremos testar e o
        # calculo do estado de pagamento, nao o aprovisionamento.
        cls.produto = cls.env["product.product"].create({
            "name": "Servico de teste C11",
            "type": "service",
            "invoice_policy": "order",
            "list_price": 1000.0,
            "taxes_id": [Command.set(cls.imposto.ids)],
        })
        cls.diario = cls.env["account.journal"].search([
            ("type", "in", ("bank", "cash")),
            ("company_id", "=", cls.empresa.id),
        ], limit=1)

    # -- auxiliares ------------------------------------------------------

    def _encomenda(self, price=1000.0):
        order = self.env["sale.order"].create({
            "partner_id": self.cliente.id,
            "order_line": [Command.create({
                "product_id": self.produto.id,
                "product_uom_qty": 1.0,
                "price_unit": price,
            })],
        })
        order.action_confirm()
        return order

    def _facturar(self, order, price=None):
        """Cria a fatura da encomenda. Se `price` vier, altera o valor da
        linha antes de publicar — e assim que se reproduz a NE A/00057."""
        invoice = order._create_invoices()
        if price is not None:
            invoice.invoice_line_ids[0].price_unit = price
        invoice.action_post()
        return invoice

    def _pagar(self, invoice, amount=None):
        """Liquida a fatura por lancamento manual + conciliacao.

        NAO se usa o assistente account.payment.register: nesta base os
        diarios tem conta de pagamentos pendentes, e o pagamento deixa a
        fatura em 'in_payment' (dinheiro em transito) em vez de 'paid'.
        O compute trata 'in_payment' como adiantamento — e bem, porque o
        dinheiro ainda nao esta confirmado — mas isso impedia o teste de
        chegar ao estado "Pago".

        Conciliando a mao ficamos independentes da configuracao do
        diario: conciliacao total -> 'paid', parcial -> 'partial'.
        """
        a_receber = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable"
        )
        valor = amount if amount is not None else a_receber.debit
        contrapartida = (
            self.diario.default_account_id
            or self.env["account.account"].search([
                ("account_type", "=", "asset_cash"),
                ("company_id", "=", self.empresa.id),
            ], limit=1)
        )
        lancamento = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.diario.id,
            "line_ids": [
                Command.create({
                    "account_id": a_receber.account_id.id,
                    "partner_id": invoice.partner_id.id,
                    "credit": valor, "debit": 0.0,
                }),
                Command.create({
                    "account_id": contrapartida.id,
                    "partner_id": invoice.partner_id.id,
                    "debit": valor, "credit": 0.0,
                }),
            ],
        })
        lancamento.action_post()
        contra_receber = lancamento.line_ids.filtered(
            lambda l: l.account_id == a_receber.account_id
        )
        (a_receber + contra_receber).reconcile()

    # -- casos -----------------------------------------------------------

    def test_sem_faturas(self):
        """Encomenda confirmada sem faturas -> Nao pago."""
        order = self._encomenda()
        self.assertEqual(order.hmd_payment_state, "not_paid")

    def test_fatura_por_pagar(self):
        """Fatura publicada mas por liquidar -> Nao pago."""
        order = self._encomenda()
        self._facturar(order)
        self.assertEqual(order.hmd_payment_state, "not_paid")

    def test_adiantamento(self):
        """Fatura pelo total, paga em parte -> Adiantamento recebido.

        E o fluxo real da HMD: nao ha fatura de adiantamento, ha fatura
        total recebida em duas vezes (confirmado nas NE A/00059,
        A/00058 e A/00053)."""
        order = self._encomenda()
        invoice = self._facturar(order)
        self._pagar(invoice, amount=round(invoice.amount_total * 0.4, 2))
        self.assertEqual(order.hmd_payment_state, "partial")

    def test_totalmente_pago(self):
        """Facturado o total da encomenda e liquidado -> Pago."""
        order = self._encomenda()
        invoice = self._facturar(order)
        self._pagar(invoice)
        self.assertEqual(order.hmd_payment_state, "paid")

    def test_fatura_emitida_por_menos(self):
        """Fatura emitida por menos que a encomenda, e paga -> Pago.

        Reproduz a NE A/00057. A HMD decidiu (31/08/2026, opcao A) que
        "Pago" significa "todas as faturas emitidas estao liquidadas".
        A diferenca entre o total da encomenda e o facturado nao e
        divida: no caso real era um desconto de 40% por aplicar na
        linha da encomenda.

        Este teste existe para fixar essa decisao: se alguem voltar a
        exigir que o valor facturado cubra o total da encomenda, falha
        aqui e tem de ir buscar a decisao do cliente primeiro."""
        order = self._encomenda(price=1000.0)
        invoice = self._facturar(order, price=600.0)
        self._pagar(invoice)

        # facturou-se menos do que o total da encomenda...
        self.assertLess(order.amount_invoiced, order.amount_total)
        # ...mas tudo o que foi facturado esta liquidado
        self.assertEqual(order.hmd_payment_state, "paid")

    def _adiantar(self, order, amount, conciliado=True):
        """Regista um adiantamento na encomenda, como o "Pay sale advanced".

        `conciliado=False` deixa o pagamento em 'in_process' (lancado mas
        por conciliar no banco); a True forca 'paid', que e o estado com
        que aparece depois da conciliacao — ou logo a seguir ao
        lancamento, quando o diario nao tem conta de pagamentos pendentes.
        """
        pagamento = self.env["account.payment"].create({
            "date": fields.Date.context_today(self.env.user),
            "amount": amount,
            "payment_type": "inbound",
            "partner_type": "customer",
            "memo": order.name,
            "journal_id": self.diario.id,
            "partner_id": order.partner_invoice_id.commercial_partner_id.id,
        })
        order.account_payment_ids |= pagamento
        pagamento.action_post()
        if conciliado and pagamento.state != "paid":
            # o estado depende da configuracao do diario (conta de
            # pagamentos pendentes); forca-se para testar a regra, nao a
            # configuracao contabilistica da base
            pagamento.state = "paid"
        return pagamento

    # -- casos com adiantamento (sem fatura) -----------------------------

    def test_adiantamento_sem_fatura(self):
        """Adiantamento parcial e nenhuma fatura -> Adiantamento recebido.

        E o fluxo dos clientes estrangeiros, comunicado pela HMD em
        08/09/2026: cria-se o payment advance e a fatura so sai com a
        entrega final. Antes da 18.0.1.1.0 esta encomenda aparecia como
        "Nao pago" com 40% do dinheiro ja recebido."""
        order = self._encomenda()
        self.assertFalse(order.invoice_ids)
        self._adiantar(order, round(order.amount_total * 0.4, 2))
        self.assertEqual(order.hmd_payment_state, "partial")

    def test_adiantamento_total_sem_fatura(self):
        """Adiantamento que cobre o total, sem fatura -> Pago."""
        order = self._encomenda()
        self._adiantar(order, order.amount_total)
        self.assertEqual(order.hmd_payment_state, "paid")

    def test_adiantamento_por_conciliar(self):
        """Adiantamento total ainda por conciliar -> Adiantamento recebido.

        Mesma leitura que o 'in_payment' das faturas (seccao h do
        manifesto): o dinheiro foi lancado mas nao esta confirmado no
        banco. Relevante enquanto a sincronizacao com o BCP estiver
        parada."""
        order = self._encomenda()
        pagamento = self._adiantar(order, order.amount_total, conciliado=False)
        if pagamento.state == "paid":
            self.skipTest("o diario nao tem conta de pagamentos pendentes; "
                          "nao ha estado 'in_process' para testar")
        self.assertEqual(pagamento.state, "in_process")
        self.assertEqual(order.hmd_payment_state, "partial")

    def test_adiantamento_com_fatura_por_liquidar(self):
        """Fatura emitida por liquidar, mas com adiantamento -> Adiantamento.

        Sem o adiantamento este caso seria "Nao pago"
        (test_fatura_por_pagar). Com ele, o dinheiro entrou."""
        order = self._encomenda()
        self._adiantar(order, round(order.amount_total * 0.4, 2))
        self._facturar(order)
        self.assertEqual(order.hmd_payment_state, "partial")

    def test_devolucao_de_adiantamento(self):
        """Adiantamento devolvido ao cliente -> volta a Nao pago."""
        order = self._encomenda()
        valor = round(order.amount_total * 0.4, 2)
        self._adiantar(order, valor)
        devolucao = self.env["account.payment"].create({
            "date": fields.Date.context_today(self.env.user),
            "amount": valor,
            "payment_type": "outbound",
            "partner_type": "customer",
            "memo": "Devolucao %s" % order.name,
            "journal_id": self.diario.id,
            "partner_id": order.partner_invoice_id.commercial_partner_id.id,
        })
        order.account_payment_ids |= devolucao
        devolucao.action_post()
        if devolucao.state != "paid":
            devolucao.state = "paid"
        self.assertEqual(order.hmd_payment_state, "not_paid")
