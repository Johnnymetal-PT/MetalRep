from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_stock_geral = fields.Float(
        string="Stock Geral",
        compute="_compute_stock_geral",
        store=False,
        digits="Product Unit of Measure",
    )

    def _compute_stock_geral(self):
        Quant = self.env['stock.quant']

        geral_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

        for product in self:
            if not geral_location:
                product.x_stock_geral = 0.0
                continue

            quants = Quant.search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id', '=', geral_location.id),
            ])

            product.x_stock_geral = sum(quants.mapped('quantity'))
