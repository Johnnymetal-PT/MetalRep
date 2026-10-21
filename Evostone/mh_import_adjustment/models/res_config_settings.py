from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    import_adjustment_cmv_journal_id = fields.Many2one(
        'account.journal',
        string='Diário de Ajuste CMV (Importações)',
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        config_parameter='mh_import_adjustment.cmv_journal_id',
        help='Diário usado para os lançamentos de ajuste CMV gerados ao aplicar '
             'um Ajuste de Importação (ADJ). Recomendado: diário "Valorização de Inventário".',
    )
