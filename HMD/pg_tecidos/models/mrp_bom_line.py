from odoo import api, fields, models

class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    # Read-only mirror of the product.template attachments
    product_template_attachment_ids = fields.Many2many(
        'ir.attachment',
        compute="_compute_product_template_attachment_ids",
        string="Documents",
        readonly=True,
    )

    @api.depends('product_tmpl_id')
    def _compute_product_template_attachment_ids(self):
        for line in self:
            template = line.product_tmpl_id
            if template and 'attachment_ids' in template._fields:
                line.product_template_attachment_ids = template.attachment_ids
            else:
                line.product_template_attachment_ids = self.env['ir.attachment']

