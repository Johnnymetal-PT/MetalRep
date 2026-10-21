from odoo import api, fields, models

class GeneratePurchaseWizard(models.TransientModel):
    _name = 'generate.purchase.wizard'
    _description = 'Confirmar Geração de Compras'

    sale_order_id = fields.Many2one('sale.order', string="Encomenda de Venda", required=True)

    def confirm_generate_po(self):
        return self.sale_order_id.action_generate_purchase_orders()
