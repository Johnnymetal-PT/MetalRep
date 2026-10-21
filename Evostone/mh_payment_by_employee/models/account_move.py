# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    pgf_move_ids = fields.One2many(
        'account.move', 'pgf_source_invoice_id',
        string='Lançamentos PGF',
        readonly=True,
        copy=False,
    )

    pgf_source_invoice_id = fields.Many2one(
        'account.move',
        string='Factura Origem PGF',
        readonly=True,
        copy=False,
    )

    def action_open_pgf_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pago por Funcionário',
            'res_model': 'payment.by.employee.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
            },
        }
