from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    pg_has_early_discount = fields.Boolean(
        string="Tem desconto de pronto pagamento",
        compute="_compute_pg_early_discount",
        help="Verdadeiro quando o termo de pagamento do documento tem desconto "
             "de pronto pagamento aplicável a este tipo de documento.",
    )
    pg_early_discount_amount = fields.Monetary(
        string="Desconto de pronto pagamento",
        compute="_compute_pg_early_discount",
        currency_field="currency_id",
        help="Valor do desconto de pronto pagamento se o documento for pago "
             "dentro do prazo do desconto. Meramente informativo: o total do "
             "documento mantém-se bruto e o desconto só se realiza no pagamento.",
    )
    pg_amount_after_early_discount = fields.Monetary(
        string="Total com desconto p.p.",
        compute="_compute_pg_early_discount",
        currency_field="currency_id",
        help="Total a pagar caso o documento seja pago dentro do prazo do "
             "desconto de pronto pagamento.",
    )
    pg_early_discount_date_formatted = fields.Char(
        string="Data limite do desconto p.p.",
        compute="_compute_pg_early_discount",
        help="Data limite formatada para fruição do desconto de pronto pagamento.",
    )
    pg_amount_residual_after_early_discount = fields.Monetary(
        string="Valor em Dívida",
        compute="_compute_pg_amount_residual_after_early_discount",
        store=True,
        currency_field="currency_id",
        help="Valor em dívida ao fornecedor já com o desconto de pronto "
             "pagamento deduzido, enquanto o documento não tiver pagamentos "
             "nem notas de crédito reconciliadas. A partir do primeiro "
             "movimento reconciliado passa a mostrar o valor em dívida "
             "contabilístico.",
    )
    pg_amount_residual_signed_after_early_discount = fields.Monetary(
        string="Valor em Dívida com desconto p.p. (moeda da empresa)",
        compute="_compute_pg_amount_residual_after_early_discount",
        store=True,
        currency_field="company_currency_id",
        help="Equivalente a 'Valor em Dívida com desconto p.p.' na moeda da "
             "empresa e com sinal contabilístico, para uso em listas e somas.",
    )

    @api.depends(
        "invoice_payment_term_id",
        "invoice_payment_term_id.early_discount",
        "invoice_payment_term_id.discount_percentage",
        "invoice_payment_term_id.discount_days",
        "invoice_payment_term_id.early_pay_discount_computation",
        "amount_total",
        "amount_tax",
        "currency_id",
        "invoice_line_ids.pg_early_discount_eligible",
        "invoice_line_ids.price_subtotal",
        "invoice_line_ids.price_total",
        "move_type",
        "invoice_date",
    )
    def _compute_pg_early_discount(self):
        for move in self:
            term = move.invoice_payment_term_id
            eligible = bool(
                term
                and term.early_discount
                and move.is_invoice(include_receipts=True)
            )
            if eligible:
                discount_base = move._pg_get_early_discount_base_amount()
                discount_amount = move.currency_id.round(
                    discount_base * term.discount_percentage / 100.0
                )
                ref_date = move.invoice_date or fields.Date.context_today(move)
                move.pg_has_early_discount = True
                move.pg_early_discount_amount = discount_amount
                move.pg_amount_after_early_discount = move.currency_id.round(
                    move.amount_total - discount_amount
                )
                move.pg_early_discount_date_formatted = (
                    term._get_last_discount_date_formatted(ref_date)
                    if ref_date
                    else False
                )
            else:
                move.pg_has_early_discount = False
                move.pg_amount_after_early_discount = 0.0
                move.pg_early_discount_amount = 0.0
                move.pg_early_discount_date_formatted = False

    @api.depends(
        "amount_residual",
        "amount_residual_signed",
        "amount_total",
        "invoice_payment_term_id.early_discount",
        "invoice_payment_term_id.discount_percentage",
        "invoice_payment_term_id.early_pay_discount_computation",
        "invoice_line_ids.pg_early_discount_eligible",
        "invoice_line_ids.price_subtotal",
        "invoice_line_ids.price_total",
        "invoice_line_ids.tax_ids",
        "move_type",
        "currency_id",
        "company_currency_id",
    )
    def _compute_pg_amount_residual_after_early_discount(self):
        for move in self:
            discount_currency, discount_company = (
                move._pg_get_pending_early_discount_amounts()
            )
            if not discount_currency and not discount_company:
                move.pg_amount_residual_after_early_discount = move.amount_residual
                move.pg_amount_residual_signed_after_early_discount = (
                    move.amount_residual_signed
                )
                continue

            # O valor em dívida vem sem sinal na moeda do documento e com sinal
            # contabilístico na moeda da empresa (negativo numa fatura de
            # fornecedor). Em ambos os casos o desconto reduz a magnitude.
            residual_sign = -1 if move.amount_residual_signed < 0.0 else 1
            move.pg_amount_residual_after_early_discount = move.currency_id.round(
                move.amount_residual - discount_currency
            )
            move.pg_amount_residual_signed_after_early_discount = (
                move.company_currency_id.round(
                    move.amount_residual_signed - residual_sign * discount_company
                )
            )

    def _pg_get_pending_early_discount_amounts(self):
        """Desconto de pronto pagamento ainda por realizar.

        Devolve o valor na moeda do documento e na moeda da empresa, ou
        ``(0.0, 0.0)`` quando não há desconto a deduzir do valor em dívida.

        O desconto só é deduzido enquanto nada estiver reconciliado no
        documento. A partir do primeiro pagamento ou nota de crédito, o valor
        em dívida real é o do razão: o desconto ou já foi realizado (e está
        lançado) ou foi perdido, e continuar a subtraí-lo mostraria uma dívida
        inferior à real.
        """
        self.ensure_one()
        term = self.invoice_payment_term_id
        if not (
            term.early_discount
            and self.is_invoice(include_receipts=True)
        ):
            return 0.0, 0.0

        currency = self.currency_id
        if not currency:
            return 0.0, 0.0
        if currency.compare_amounts(
            abs(self.amount_residual), abs(self.amount_total)
        ) != 0:
            return 0.0, 0.0

        amounts = self._pg_get_early_discount_eligible_amounts()
        if term.early_pay_discount_computation == "included":
            base_currency = amounts["total_currency"]
            base_company = amounts["total_company"]
        else:
            base_currency = amounts["untaxed_currency"]
            base_company = amounts["untaxed_company"]

        percentage = term.discount_percentage / 100.0
        company_currency = self.company_currency_id or currency
        return (
            currency.round(base_currency * percentage),
            company_currency.round(base_company * percentage),
        )

    def _pg_get_early_discount_eligible_amounts(self):
        """Devolve os totais sem e com imposto das linhas elegíveis.

        É usado o motor fiscal em vez de ``price_subtotal``/``price_total`` para
        que os valores na moeda da empresa e o arredondamento por linha coincidam
        com os lançamentos contabilísticos gerados pelo Odoo.
        """
        self.ensure_one()
        eligible_lines = self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
            and line.pg_early_discount_eligible
        )
        if not eligible_lines:
            return {
                "untaxed_currency": 0.0,
                "total_currency": 0.0,
                "untaxed_company": 0.0,
                "total_company": 0.0,
            }

        base_lines = [
            self._prepare_product_base_line_for_taxes_computation(line)
            for line in eligible_lines
        ]
        account_tax = self.env["account.tax"]
        account_tax._add_tax_details_in_base_lines(base_lines, self.company_id)
        account_tax._round_base_lines_tax_details(base_lines, self.company_id)
        account_tax._add_accounting_data_in_base_lines_tax_details(
            base_lines, self.company_id
        )

        return {
            "untaxed_currency": sum(
                line["tax_details"]["total_excluded_currency"]
                for line in base_lines
            ),
            "total_currency": sum(
                line["tax_details"]["total_included_currency"]
                for line in base_lines
            ),
            "untaxed_company": sum(
                line["tax_details"]["total_excluded"] for line in base_lines
            ),
            "total_company": sum(
                line["tax_details"]["total_included"] for line in base_lines
            ),
        }

    def _pg_get_early_discount_base_amount(self):
        """Devolve a base elegível na moeda da fatura para apresentação."""
        self.ensure_one()
        amounts = self._pg_get_early_discount_eligible_amounts()
        if self.invoice_payment_term_id.early_pay_discount_computation == "included":
            return amounts["total_currency"]
        return amounts["untaxed_currency"]

    def _pg_check_customer_vat(self):
        """Impede confirmar faturas e notas de crédito de cliente sem NIF.

        O cliente genérico "Consumidor Final" do ptplus_partner é a exceção:
        é o único que pode ser faturado sem NIF.
        """
        end_consumer = self.env.ref(
            "ptplus_partner.l10n_pt_end_consumer", raise_if_not_found=False
        )
        missing = self.filtered(
            lambda move: move.state != "posted"
            and move.move_type in ("out_invoice", "out_refund")
            and move.partner_id
            and not move.partner_id.commercial_partner_id.vat
            and move.partner_id.commercial_partner_id != end_consumer
        )
        if missing:
            partners = ", ".join(
                sorted(set(missing.partner_id.commercial_partner_id.mapped("name")))
            )
            raise UserError(_(
                "Não é possível confirmar o documento: o cliente %(partners)s não "
                "tem NIF preenchido. Preencha o NIF na ficha do cliente ou use o "
                "cliente Consumidor Final.",
                partners=partners,
            ))

    def _post(self, soft=True):
        self._pg_check_customer_vat()
        return super()._post(soft=soft)

    def _pg_has_selective_early_discount(self):
        self.ensure_one()
        return bool(
            self.is_invoice(include_receipts=True)
            and self.invoice_payment_term_id.early_discount
            and self.invoice_line_ids.filtered(
                lambda line: line.display_type == "product"
                and not line.pg_early_discount_eligible
            )
        )

    @api.depends(
        "invoice_payment_term_id",
        "invoice_date",
        "currency_id",
        "amount_total_in_currency_signed",
        "invoice_date_due",
        "invoice_line_ids.pg_early_discount_eligible",
        "invoice_line_ids.price_subtotal",
        "invoice_line_ids.price_total",
        "invoice_line_ids.tax_ids",
    )
    def _compute_needed_terms(self):
        """Limita o montante com desconto às linhas selecionadas pelo utilizador."""
        super()._compute_needed_terms()
        for invoice in self:
            if not invoice._pg_has_selective_early_discount() or not invoice.needed_terms:
                continue

            amounts = invoice._pg_get_early_discount_eligible_amounts()
            payment_term = invoice.invoice_payment_term_id
            if payment_term.early_pay_discount_computation == "included":
                base_currency = amounts["total_currency"]
                base_company = amounts["total_company"]
            else:
                base_currency = amounts["untaxed_currency"]
                base_company = amounts["untaxed_company"]

            percentage = payment_term.discount_percentage / 100.0
            needed_terms = dict(invoice.needed_terms)
            for key, values in needed_terms.items():
                values = dict(values)
                amount_currency = values["amount_currency"]
                balance = values["balance"]
                currency_sign = 1 if amount_currency >= 0.0 else -1
                balance_sign = 1 if balance >= 0.0 else -1
                discounted_amount_currency = invoice.currency_id.round(
                    amount_currency - currency_sign * base_currency * percentage
                )
                discounted_balance = invoice.company_currency_id.round(
                    balance - balance_sign * base_company * percentage
                )

                cash_rounding = invoice.invoice_cash_rounding_id
                if cash_rounding:
                    rounding_difference = cash_rounding.compute_difference(
                        invoice.currency_id, discounted_amount_currency
                    )
                    if not invoice.currency_id.is_zero(rounding_difference):
                        discounted_amount_currency += rounding_difference
                        rate = abs(amount_currency / balance) if balance else 0.0
                        discounted_balance = invoice.company_currency_id.round(
                            discounted_amount_currency / rate
                        ) if rate else 0.0

                values["discount_amount_currency"] = discounted_amount_currency
                values["discount_balance"] = discounted_balance
                needed_terms[key] = values
            invoice.needed_terms = needed_terms

    def _get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line(self):
        """Mantém as linhas excluídas quando o desconto também reduz o imposto."""
        self.ensure_one()
        if (
            self._pg_has_selective_early_discount()
            and self.invoice_payment_term_id.early_pay_discount_computation == "included"
        ):
            contextual_self = self.with_context(pg_selective_early_discount=True)
            return super(
                AccountMove, contextual_self
            )._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()
        return (
            super()
            ._get_invoice_counterpart_amls_for_early_payment_discount_per_payment_term_line()
        )

    def _prepare_product_base_line_for_taxes_computation(self, product_line):
        base_line = super()._prepare_product_base_line_for_taxes_computation(
            product_line
        )
        if (
            self.env.context.get("pg_selective_early_discount")
            and not product_line.pg_early_discount_eligible
        ):
            percentage = self.invoice_payment_term_id.discount_percentage / 100.0
            remaining_percentage = 1.0 - percentage
            if remaining_percentage:
                # O motor standard multiplica depois todas as bases por esta
                # percentagem. O aumento inverso neutraliza essa multiplicação
                # nas linhas excluídas pelo utilizador.
                base_line["price_unit"] /= remaining_percentage
        return base_line
