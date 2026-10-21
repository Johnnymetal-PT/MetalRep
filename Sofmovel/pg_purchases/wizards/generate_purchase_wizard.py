"""Wizard de confirmacao quando a SO ja gerou POs anteriormente.

Pertence ao modulo `pg_purchases`. So apresentado quando `purchase_created`
ja esta True. Confirmar gera novamente sem apagar as anteriores - o operador
tem de tratar de eventuais duplicados manualmente.
"""
from odoo import api, fields, models

class GeneratePurchaseWizard(models.TransientModel):
    """Wizard transitorio que confirma a regeneracao de POs a partir da SO."""

    _name = 'generate.purchase.wizard'
    _description = 'Confirmar Geração de Compras'

    sale_order_id = fields.Many2one('sale.order', string="Encomenda de Venda", required=True)

    def confirm_generate_po(self):
        # Reutiliza o metodo da SO; este wizard so trata da confirmacao de UI.
        return self.sale_order_id.action_generate_purchase_orders()
