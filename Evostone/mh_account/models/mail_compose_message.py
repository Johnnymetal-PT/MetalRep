from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.depends('composition_mode', 'model', 'parent_id', 'res_domain', 'res_ids')
    def _compute_record_name(self):
        super()._compute_record_name()
        for composer in self:
            if (composer.model == 'account.payment'
                    and composer.composition_mode == 'comment'
                    and not composer.composition_batch):
                res_ids = composer._evaluate_res_ids()
                if len(res_ids) == 1:
                    payment = self.env['account.payment'].browse(res_ids)
                    if payment.receipt_number:
                        composer.record_name = payment.receipt_number
