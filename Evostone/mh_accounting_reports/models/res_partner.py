from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_due_invoices = fields.Monetary(
        string='Dívida de Facturas',
        compute='_compute_amount_due_invoices',
        currency_field='currency_id',
    )

    amount_due_bills = fields.Monetary(
        string='Dívida a Fornecedores',
        compute='_compute_amount_due_bills',
        currency_field='currency_id',
    )

    @api.depends_context('company')
    def _compute_amount_due_invoices(self):
        for partner in self:
            partner.amount_due_invoices = 0.0

        if not self.ids:
            return

        self.env['account.move'].flush_model(['move_type', 'state', 'amount_residual_signed', 'partner_id'])
        self.env.cr.execute("""
            SELECT partner_id, SUM(amount_residual_signed)
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted'
              AND payment_state NOT IN ('paid', 'reversed')
              AND partner_id IN %s
              AND company_id = %s
            GROUP BY partner_id
        """, (tuple(self.ids), self.env.company.id))

        for partner_id, total in self.env.cr.fetchall():
            self.browse(partner_id).amount_due_invoices = total

    @api.depends_context('company')
    def _compute_amount_due_bills(self):
        for partner in self:
            partner.amount_due_bills = 0.0

        if not self.ids:
            return

        self.env['account.move'].flush_model(['move_type', 'state', 'amount_residual_signed', 'partner_id'])
        self.env.cr.execute("""
            SELECT partner_id, SUM(amount_residual_signed)
            FROM account_move
            WHERE move_type IN ('in_invoice', 'in_refund')
              AND state = 'posted'
              AND payment_state NOT IN ('paid', 'reversed')
              AND partner_id IN %s
              AND company_id = %s
            GROUP BY partner_id
        """, (tuple(self.ids), self.env.company.id))

        for partner_id, total in self.env.cr.fetchall():
            self.browse(partner_id).amount_due_bills = abs(total or 0.0)

    def open_collection_map(self):
        """Abrir Mapa de Cobranças filtrado por este cliente."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mh_accounting_reports.action_aged_customer_invoices"
        )
        action['params'] = {
            'options': {
                'partner_ids': (self | self.commercial_partner_id).ids,
                'unfold_all': len(self.ids) == 1,
            },
            'ignore_session': True,
        }
        return action

    def action_partner_statement_choice(self):
        """Abre o wizard que pergunta se o utilizador quer abrir o mapa
        interactivo ou enviar o PDF por e-mail."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mapa de Cobranças'),
            'res_model': 'mh.partner.statement.action.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }

    def open_payment_map(self):
        """Abrir Mapa de Pagamentos filtrado por este fornecedor."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "mh_accounting_reports.action_aged_supplier_invoices"
        )
        action['params'] = {
            'options': {
                'partner_ids': (self | self.commercial_partner_id).ids,
                'unfold_all': len(self.ids) == 1,
            },
            'ignore_session': True,
        }
        return action

    def action_partner_payment_choice(self):
        """Abre o wizard que pergunta se o utilizador quer abrir o mapa de
        pagamentos interactivo ou enviar o PDF por e-mail."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mapa de Pagamentos'),
            'res_model': 'mh.partner.payment.action.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
