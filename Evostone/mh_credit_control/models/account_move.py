from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        """
        Override para recalcular bloqueios de crédito quando o estado
        de pagamento de uma factura muda.
        """
        # Verificar se payment_state está a mudar
        if 'payment_state' in vals:
            # Guardar partners afectados antes da alteração
            partners_to_update = self.filtered(
                lambda m: m.move_type in ('out_invoice', 'out_refund') and m.partner_id
            ).mapped('partner_id.commercial_partner_id')
        else:
            partners_to_update = self.env['res.partner']

        result = super().write(vals)

        # Recalcular bloqueios para os partners afectados
        if partners_to_update:
            partners_to_update._recompute_sale_order_credit_blocks()

        return result

    def _compute_amount(self):
        """
        Override para recalcular bloqueios quando amount_residual muda.
        """
        result = super()._compute_amount()

        # Recalcular bloqueios para facturas de clientes
        partners_to_update = self.filtered(
            lambda m: m.move_type in ('out_invoice', 'out_refund') and m.partner_id
        ).mapped('partner_id.commercial_partner_id')

        if partners_to_update:
            partners_to_update._recompute_sale_order_credit_blocks()

        return result
