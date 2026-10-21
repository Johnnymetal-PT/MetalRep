from odoo import fields, models

from .sale_order_line import DEFAULT_MAX_DIMENSAO, PARAM_MAX_DIMENSAO


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pg_m2_max_dimensao = fields.Float(
        string="Dimensão máxima admitida (m)",
        config_parameter=PARAM_MAX_DIMENSAO,
        default=DEFAULT_MAX_DIMENSAO,
        help="Comprimento ou largura acima deste valor são recusados na linha de"
             " venda.\n"
             "Serve para apanhar dimensões introduzidas em centímetros. A 0"
             " desliga a validação.",
    )
