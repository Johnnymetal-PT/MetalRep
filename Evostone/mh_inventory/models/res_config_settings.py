from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Margin thresholds configuration
    margin_low_threshold = fields.Float(
        string='Margem Baixa (%)', 
        default=10.0,
        config_parameter='mh_inventory.margin_low_threshold',
        help='Produtos com margem abaixo deste valor são considerados de margem baixa'
    )
    
    margin_high_threshold = fields.Float(
        string='Margem Alta (%)',
        default=50.0,
        config_parameter='mh_inventory.margin_high_threshold',
        help='Produtos com margem acima deste valor são considerados de margem alta'
    )

    stone_density = fields.Float(
        string='Densidade Padrão de Pedra (kg/m³)',
        related='company_id.stone_density',
        readonly=False,
        help='Densidade default para cálculo de peso quando o produto não tem '
             'densidade específica. Padrão indústria: 2700 kg/m³.',
    )
