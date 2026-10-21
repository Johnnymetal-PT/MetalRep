from odoo import models


class SaleCreateProformaWizard(models.TransientModel):
    _inherit = 'sale.create.proforma.wizard'

    def action_create_proforma(self):
        self.ensure_one()
        self.sale_order_id._check_proforma_receipt_company()
        return super().action_create_proforma()
