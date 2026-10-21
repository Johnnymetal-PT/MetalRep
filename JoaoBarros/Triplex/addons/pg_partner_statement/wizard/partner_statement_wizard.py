from collections import defaultdict
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PartnerStatementWizard(models.TransientModel):
    _name = "pg.partner.statement.wizard"
    _description = "Assistente de Extrato Simplificado de Cliente"

    date_from = fields.Date(
        string="Data de",
        required=True,
        default=lambda self: date.today().replace(day=1),
    )
    date_to = fields.Date(
        string="Data até",
        required=True,
        default=fields.Date.context_today,
    )
    partner_ids = fields.Many2many(
        "res.partner",
        string="Clientes",
        domain=[("customer_rank", ">", 0)],
        help="Deixar vazio para incluir todos os clientes ativos.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
    )
    line_ids = fields.One2many(
        "pg.partner.statement.line",
        "wizard_id",
        string="Resultado",
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from > wiz.date_to:
                raise UserError(_("A data inicial não pode ser posterior à data final."))

    def _get_target_partners(self):
        self.ensure_one()
        if self.partner_ids:
            return self.partner_ids
        return self.env["res.partner"].search([
            ("customer_rank", ">", 0),
            ("active", "=", True),
        ])

    @staticmethod
    def _is_downpayment_invoice(move):
        """Classifica como Adiantamento apenas faturas onde TODAS as linhas
        de produto estão ligadas a sale.order.line com is_downpayment=True.

        Faturas finais com dedução de adiantamento (linhas mistas: produtos
        finais positivos + linha negativa de regularização do adiantamento)
        são classificadas como Finais — o seu amount_total já é líquido
        e reflete o valor real cobrado neste momento.
        """
        product_lines = move.invoice_line_ids.filtered(
            lambda l: l.display_type == "product"
        )
        if not product_lines:
            return False
        return all(
            line.sale_line_ids and all(sl.is_downpayment for sl in line.sale_line_ids)
            for line in product_lines
        )

    def _compute_invoice_buckets(self, partners):
        """Faturas e notas de crédito emitidas no período, agrupadas por cliente × moeda.

        Retorna dicts indexados por (partner_id, currency_id):
            final_invoiced_map: faturas finais (excluindo adiantamentos)
            downpayment_map:    faturas de adiantamento
            refunded_map:       notas de crédito
            residual_map:       residual de todas as faturas do período (final + adiantamento)
        """
        AccountMove = self.env["account.move"]
        base_domain = [
            ("company_id", "=", self.company_id.id),
            ("partner_id", "in", partners.ids),
            ("state", "=", "posted"),
            ("invoice_date", ">=", self.date_from),
            ("invoice_date", "<=", self.date_to),
        ]

        final_invoiced_map = defaultdict(float)
        downpayment_map = defaultdict(float)
        refunded_map = defaultdict(float)
        residual_map = defaultdict(float)

        # Faturas (out_invoice) — separadas entre finais e adiantamentos
        invoices = AccountMove.search(base_domain + [("move_type", "=", "out_invoice")])
        for move in invoices:
            key = (move.partner_id.id, move.currency_id.id)
            if self._is_downpayment_invoice(move):
                downpayment_map[key] += move.amount_total
            else:
                final_invoiced_map[key] += move.amount_total
            residual_map[key] += move.amount_residual

        # Notas de crédito (out_refund)
        refunds = AccountMove.search(base_domain + [("move_type", "=", "out_refund")])
        for move in refunds:
            key = (move.partner_id.id, move.currency_id.id)
            refunded_map[key] += move.amount_total

        return final_invoiced_map, downpayment_map, refunded_map, residual_map

    def _compute_balance_buckets(self, partners):
        """Saldo da conta corrente à data final, agrupado por cliente × moeda.

        Soma `amount_residual_currency` das account.move.line em contas a receber
        com data <= date_to, ainda em aberto. Usa moeda do registo se existir,
        caso contrário moeda da empresa.
        """
        AccountMoveLine = self.env["account.move.line"]
        lines = AccountMoveLine.search([
            ("company_id", "=", self.company_id.id),
            ("partner_id", "in", partners.ids),
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "=", "asset_receivable"),
            ("date", "<=", self.date_to),
            ("reconciled", "=", False),
        ])

        balance_map = defaultdict(float)
        company_currency = self.company_id.currency_id
        for line in lines:
            currency = line.currency_id or company_currency
            key = (line.partner_id.id, currency.id)
            if line.currency_id:
                balance_map[key] += line.amount_residual_currency
            else:
                balance_map[key] += line.amount_residual
        return balance_map

    def _build_lines(self):
        self.ensure_one()
        self.line_ids.unlink()

        partners = self._get_target_partners()
        if not partners:
            return

        final_map, dp_map, refunded_map, residual_map = self._compute_invoice_buckets(partners)
        balance_map = self._compute_balance_buckets(partners)

        all_keys = (set(final_map) | set(dp_map) | set(refunded_map)
                    | set(residual_map) | set(balance_map))
        if not all_keys:
            return

        lines_vals = []
        for partner_id, currency_id in all_keys:
            final_amt = final_map.get((partner_id, currency_id), 0.0)
            dp_amt = dp_map.get((partner_id, currency_id), 0.0)
            refunded = refunded_map.get((partner_id, currency_id), 0.0)
            residual = residual_map.get((partner_id, currency_id), 0.0)
            balance = balance_map.get((partner_id, currency_id), 0.0)
            lines_vals.append({
                "wizard_id": self.id,
                "partner_id": partner_id,
                "currency_id": currency_id,
                "final_invoiced_amount": final_amt,
                "downpayment_amount": dp_amt,
                "refunded_amount": refunded,
                "net_invoiced_amount": final_amt + dp_amt - refunded,
                "period_residual": residual,
                "total_balance": balance,
            })
        self.env["pg.partner.statement.line"].create(lines_vals)

    def action_view_lines(self):
        self.ensure_one()
        self._build_lines()
        return {
            "name": _("Extrato Simplificado — %s a %s") % (self.date_from, self.date_to),
            "type": "ir.actions.act_window",
            "res_model": "pg.partner.statement.line",
            "view_mode": "tree",
            "domain": [("wizard_id", "=", self.id)],
            "context": {
                "create": False,
                "delete": False,
                "edit": False,
            },
            "target": "current",
        }

    def action_print_pdf(self):
        self.ensure_one()
        self._build_lines()
        return self.env.ref(
            "pg_partner_statement.action_report_partner_statement"
        ).report_action(self)
