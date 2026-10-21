# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hmd_payment_state = fields.Selection(
        selection=[
            ("not_paid", "Não pago"),
            ("partial", "Adiantamento recebido"),
            ("paid", "Pago"),
        ],
        string="Estado de Pagamento",
        compute="_compute_hmd_payment_state",
        store=True,
        help="Estado de pagamento da encomenda, derivado automaticamente das "
        "faturas de cliente (account.move) associadas e dos adiantamentos "
        "registados na propria encomenda (separador «Payment advances»). "
        "Atualiza-se sozinho quando uma fatura muda de estado de pagamento "
        "ou quando e registado um adiantamento.",
    )

    # -- adiantamentos registados na encomenda ---------------------------

    def _hmd_advance_amounts(self):
        """Devolve (confirmado, anunciado) dos adiantamentos da encomenda.

        Os adiantamentos vivem em `account.payment` ligados a encomenda pelo
        campo `sale_id` (modulo `sale_advance_payment`), e nao em faturas.
        E o fluxo que a HMD usa com clientes estrangeiros: recebe-se o
        adiantamento, a fatura so e emitida com a entrega final.

        Distinguem-se dois totais, pela mesma razao que 'in_payment' nas
        faturas nao conta como "Pago" (ver seccao h do manifesto):
          - confirmado: pagamentos em 'paid', ja conciliados no banco;
          - anunciado: confirmado + os que estao em 'in_process', ou seja,
            lancados mas ainda por conciliar (dinheiro em transito).

        NOTA: nao se usa `amount_residual` nem `advance_payment_status` do
        `sale_advance_payment`. Esses campos so contam linhas em conta de
        clientes (`asset_receivable`), e nesta base o `ptplus_sale_advance_
        payment` (localizacao PT da EXO, auto_install) encaminha o
        adiantamento para a conta de adiantamentos da categoria, nao para a
        conta de clientes. Ler os `account.payment` directamente e
        independente dessa configuracao contabilistica.
        """
        self.ensure_one()
        confirmado = 0.0
        anunciado = 0.0
        for pagamento in self.account_payment_ids:
            if pagamento.state not in ("paid", "in_process"):
                # draft, canceled, rejected: nao ha dinheiro nenhum
                continue
            valor = pagamento.amount
            if pagamento.payment_type != "inbound":
                # devolucao de adiantamento ao cliente
                valor = -valor
            moeda = pagamento.currency_id or self.company_id.currency_id
            if moeda != self.currency_id:
                valor = moeda._convert(
                    valor,
                    self.currency_id,
                    self.company_id,
                    pagamento.date or fields.Date.today(),
                )
            anunciado += valor
            if pagamento.state == "paid":
                confirmado += valor
        return confirmado, anunciado

    @api.depends(
        "invoice_ids",
        "invoice_ids.state",
        "invoice_ids.move_type",
        "invoice_ids.payment_state",
        "amount_total",
        "currency_id",
        "account_payment_ids",
        "account_payment_ids.state",
        "account_payment_ids.amount",
        "account_payment_ids.payment_type",
        "account_payment_ids.currency_id",
        "account_payment_ids.date",
    )
    def _compute_hmd_payment_state(self):
        for order in self:
            invoices = order.invoice_ids.filtered(
                lambda m: m.move_type == "out_invoice" and m.state == "posted"
            )
            states = invoices.mapped("payment_state")
            confirmado, anunciado = order._hmd_advance_amounts()
            arredondamento = (
                order.currency_id or order.company_id.currency_id
            ).rounding
            ha_adiantamento = (
                float_compare(anunciado, 0.0, precision_rounding=arredondamento) > 0
            )

            # "Pago" = todas as faturas emitidas estao liquidadas.
            #
            # DECIDIDO pela HMD em 31/08/2026, opcao A.
            #
            # A pergunta foi posta com o caso concreto da NE A/00057: total
            # da encomenda 2.987,60, fatura de 2.147,60 integralmente paga,
            # diferenca de 840. A leitura alternativa — "Pago" so quando o
            # valor facturado cobre o total da encomenda — foi RECUSADA, com
            # este esclarecimento da HMD:
            #
            #   "o valor da encomenda esta errado pois na primeira linha nao
            #    assumiu os 40% de desconto e o valor total da linha e 2100
            #    quando deveria ser 1260, conforme a fatura. Logo, o valor
            #    total da encomenda sao os 2147,6 faturados que ja foram
            #    liquidados, logo, podemos assumir a opcao A."
            #
            # Ou seja: os 840 nao sao divida, sao um erro de registo na
            # encomenda (desconto por aplicar). O campo nao deve tentar
            # adivinhar erros de dados — para saber se falta facturar existe
            # a coluna nativa "Estado da Fatura", que se le ao lado desta.
            #
            # Nao alterar sem nova decisao do cliente.
            if invoices and all(s == "paid" for s in states):
                order.hmd_payment_state = "paid"
            elif not invoices and ha_adiantamento:
                # Encomenda ainda sem fatura, paga por adiantamento. E o
                # fluxo dos clientes estrangeiros, comunicado pela HMD em
                # 08/09/2026: cria-se o adiantamento e a fatura so sai com a
                # entrega final. So se considera "Pago" quando o adiantamento
                # conciliado cobre o total da encomenda; ate la, e
                # "Adiantamento recebido". A HMD confirmou este criterio
                # em 15/09/2026: "pode ficar como pago - da uma ideia clara
                # de que o cliente pagou tudo daquela encomenda".
                cobre_o_total = (
                    float_compare(
                        confirmado,
                        order.amount_total,
                        precision_rounding=arredondamento,
                    )
                    >= 0
                )
                order.hmd_payment_state = "paid" if cobre_o_total else "partial"
            elif ha_adiantamento or any(
                s in ("partial", "paid", "in_payment") for s in states
            ):
                # Qualquer pagamento parcial coloca a encomenda em
                # "Adiantamento recebido". Confirmado com dados reais em
                # 31/08/2026: a HMD emite fatura pelo TOTAL e recebe em duas
                # vezes (NE A/00059, A/00058, A/00053), pelo que o adiantamento
                # de 40% chega aqui como payment_state 'partial'. Nao ha
                # faturas de adiantamento nesta base.
                #
                # Desde 08/09/2026 tambem chega por aqui a encomenda que ja
                # tem fatura por liquidar mas tem adiantamento registado: o
                # dinheiro entrou, mesmo que a fatura ainda nao o reflicta
                # enquanto a regularizacao nao for conciliada.
                order.hmd_payment_state = "partial"
            else:
                order.hmd_payment_state = "not_paid"
