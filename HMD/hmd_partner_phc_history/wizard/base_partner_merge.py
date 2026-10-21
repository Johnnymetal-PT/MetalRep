from odoo import models


class MergePartnerAutomatic(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    def _get_summable_fields(self):
        """Ao fundir contactos duplicados, o volume histórico do PHC soma-se em vez de se perder."""
        return super()._get_summable_fields() + ["phc_history_amount"]
