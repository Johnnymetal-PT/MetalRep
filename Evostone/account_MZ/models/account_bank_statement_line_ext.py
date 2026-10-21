from odoo import models, fields, api


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    apuramento_model_id = fields.Many2one(related='move_id.apuramento_model_id', string='Apuramento Model', store=False)
    bank_statement_id = fields.Many2one('bank.statement', string='Extrato de fluxo de caixa')
    contra_valor = fields.Many2one(related='move_id.contra_valor', string='ContraValor', store=False)
    is_avenca = fields.Boolean(related='move_id.is_avenca', string='é Avenca', store=False)
    is_vd = fields.Boolean(related='move_id.is_vd', string='é VD', store=False)
    journal_code = fields.Char(related='move_id.journal_code', string='Codigo do diario', store=False)
    passo = fields.Char(related='move_id.passo', string='Passo', store=False)
    run_sale = fields.Boolean(related='move_id.run_sale', string='executado na ordem de venda', store=False)
    taxa_cambio = fields.Float(related='move_id.taxa_cambio', string='Taxa de Cambio', store=False)
    total_amount_vd = fields.Float(related='move_id.total_amount_vd', string='Valor total pago', store=False)
    total_contra_valor = fields.Float(related='move_id.total_contra_valor', string='Total ContraValor', store=False)
    total_por_extenso = fields.Char(related='move_id.total_por_extenso', string='Total por Extenso', store=False)
    
    # vd_line_ids is accessed via move_id.vd_line_ids - no need to redefine
