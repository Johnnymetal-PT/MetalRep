from odoo import models, api
from . res_company import barcode_to_grf


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _get_rendering_context(self, report, docids, data):
        """Adiciona barcode_to_grf ao contexto de rendering dos relatórios QWeb."""
        res = super()._get_rendering_context(report, docids, data)
        res['barcode_to_grf'] = barcode_to_grf
        return res
