from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_model_product_product(self):
        return {
            'name': 'Mass Update',
            'type': 'ir.actions.act_window',
            'res_model': 'mass.update.variant.cost.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('eg_mass_update_variant_cost.mass_update_variant_cost_wizard_form_view').id,
            'context': dict(self._context, active_ids=self.ids),
            'target': 'new',
        }


