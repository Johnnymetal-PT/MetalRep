from odoo import models, fields

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    product_description_variants = fields.Text(
        related='production_id.product_description_variants',
        store=True,
        readonly=True,
    )