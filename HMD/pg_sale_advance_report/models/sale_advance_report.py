# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleAdvanceReportWizard(models.TransientModel):
    _name = 'sale.advance.report.wizard'
    _description = 'Assistente do Relatorio de Controlo de Adiantamentos'

    date_from = fields.Date(string='De')
    date_to = fields.Date(string='Ate')
    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
    )

    def action_print(self):
        self.ensure_one()
        data = {
            'date_from': str(self.date_from) if self.date_from else False,
            'date_to': str(self.date_to) if self.date_to else False,
            'company_id': self.company_id.id,
        }
        return self.env.ref(
            'pg_sale_advance_report.action_report_sale_advances'
        ).report_action(self, data=data)


class ReportSaleAdvances(models.AbstractModel):
    _name = 'report.pg_sale_advance_report.report_advances'
    _description = 'Relatorio de Controlo de Adiantamentos'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        company_id = data.get('company_id') or self.env.company.id

        domain = [('state', 'in', ('sale', 'done')), ('company_id', '=', company_id)]
        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            # date_order e datetime; incluir o dia inteiro de date_to
            domain.append(('date_order', '<=', date_to + ' 23:59:59'))

        orders = self.env['sale.order'].search(domain, order='date_order, name')

        lines = []
        totals = dict(untaxed=0.0, total=0.0, adv_inv_unt=0.0, adv_inv_tot=0.0,
                      adv_paid=0.0, adv_total=0.0, residual=0.0)

        for so in orders:
            # Fonte 1: faturas PURAS de adiantamento.
            # Em Odoo 18 as linhas de produto tem display_type == 'product'
            # (as de seccao/nota tem 'line_section'/'line_note'). A fatura e
            # de adiantamento quando TODAS as suas linhas de produto sao is_downpayment.
            def _is_downpayment_invoice(move):
                product_lines = move.invoice_line_ids.filtered(
                    lambda line: line.display_type == 'product'
                )
                return bool(product_lines) and all(product_lines.mapped('is_downpayment'))

            dp_invoices = so.invoice_ids.filtered(
                lambda m: m.state == 'posted'
                and m.move_type == 'out_invoice'
                and _is_downpayment_invoice(m)
            )
            adv_inv_unt = sum(dp_invoices.mapped('amount_untaxed'))
            adv_inv_tot = sum(dp_invoices.mapped('amount_total'))

            # Fonte 2: pagamentos de adiantamento (sale_advance_payment)
            adv_paid = sum(so.account_payment_ids.filtered(
                lambda p: p.state not in ('draft', 'cancel', 'canceled', 'rejected')
            ).mapped('amount'))

            adv_total = adv_inv_tot + adv_paid
            if adv_total <= 0.0:
                continue

            pct = (adv_total / so.amount_total * 100.0) if so.amount_total else 0.0
            residual = so.amount_total - adv_total

            lines.append(dict(
                order=so.name,
                partner=so.partner_id.display_name,
                untaxed=so.amount_untaxed,
                total=so.amount_total,
                adv_inv_unt=adv_inv_unt,
                adv_inv_tot=adv_inv_tot,
                adv_paid=adv_paid,
                adv_total=adv_total,
                pct=pct,
                residual=residual,
            ))
            totals['untaxed'] += so.amount_untaxed
            totals['total'] += so.amount_total
            totals['adv_inv_unt'] += adv_inv_unt
            totals['adv_inv_tot'] += adv_inv_tot
            totals['adv_paid'] += adv_paid
            totals['adv_total'] += adv_total
            totals['residual'] += residual

        company = self.env['res.company'].browse(company_id)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.advance.report.wizard',
            'docs': self.env['sale.advance.report.wizard'].browse(docids),
            'lines': lines,
            'totals': totals,
            'date_from': date_from,
            'date_to': date_to,
            'company': company,
            'currency': company.currency_id,
        }
