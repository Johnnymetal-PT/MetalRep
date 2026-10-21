from odoo import api, fields, models


class PurchaseConfirmWizard(models.TransientModel):
    _name = 'purchase.confirm.wizard'
    _description = 'Wizard de Confirmação de Tipo de Receção'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Pedido de Compra',
        required=True,
        readonly=True
    )

    reception_type = fields.Selection([
        ('direct', 'Sem importação'),
        ('import', 'Com Importação')
    ], string='Tipo de Receção', required=True, default='direct')

    def action_confirm(self):
        """Gravar escolha do utilizador e confirmar PO"""
        self.ensure_one()

        # Gravar no_cost_validation baseado na escolha
        no_cost = self.reception_type == 'direct'
        self.purchase_order_id.write({'no_cost_validation': no_cost})

        # Confirmar PO
        return self.purchase_order_id.button_confirm_final()
