from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    apuramento_model_id = fields.Many2one('apuramento.model', string='Apuramento Passo1')
    apuramento_step2_model_id = fields.Many2one('apuramento.model', string='Apuramento Passo2')
    apuramento_step3_model_id = fields.Many2one('apuramento.model', string='Apuramento Passo3')
    payment_state = fields.Selection([], string='Status In Payment')
