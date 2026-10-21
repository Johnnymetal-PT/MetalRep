from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    reinvoice_credit_note_default = fields.Boolean(
        "Re-faturar notas de crédito por defeito", default=False
    )
