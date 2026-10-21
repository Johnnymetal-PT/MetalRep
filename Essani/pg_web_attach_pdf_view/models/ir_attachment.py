"""Ligacao opcional entre anexos e variantes para filtrar documentos no website."""
from odoo import models, fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    variant_ids = fields.Many2many(
        'product.product',
        'ir_attachment_product_variant_rel',
        'attachment_id',
        'product_id',
        string='Variants'
    )
