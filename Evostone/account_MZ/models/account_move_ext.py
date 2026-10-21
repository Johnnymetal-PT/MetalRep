from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    apuramento_model_id = fields.Many2one('apuramento.model', string='Apuramento Model')
    contra_valor = fields.Many2one('res.currency', string='ContraValor')
    is_avenca = fields.Boolean(string='é Avenca')
    is_vd = fields.Boolean(string='é VD')
    journal_code = fields.Char(related='journal_id.code', string='Codigo do diario', store=False)
    passo = fields.Char(string='Passo')
    run_sale = fields.Boolean(string='executado na ordem de venda')
    taxa_cambio = fields.Float(string='Taxa de Cambio', compute='_compute_taxa_cambio', store=False)
    total_amount_vd = fields.Float(string='Valor total pago', compute='_compute_total_vd', store=False)
    total_contra_valor = fields.Float(string='Total ContraValor', compute='_compute_contra_valor', store=False)
    total_por_extenso = fields.Char(string='Total por Extenso')
    vd_line_ids = fields.One2many('vd.line.model', 'invoice_id', string='Linhas de VD')
    migration = fields.Boolean(string='Movimento da migração', default=False)
    
    def _compute_taxa_cambio(self):
        for rec in self:
            rec.taxa_cambio = 0.0

    def _compute_total_vd(self):
        for rec in self:
            rec.total_amount_vd = 0.0

    def _compute_contra_valor(self):
        for rec in self:
            rec.total_contra_valor = 0.0

    # NOTA: o método action_debit_note foi REMOVIDO daqui.
    # O account_MZ redefinia-o para abrir uma factura em branco (sem
    # debit_origin_id), o que partia as notas de débito: ficavam como facturas
    # normais na série FT, sem o prefixo "D". Ao remover o override, volta a
    # valer o método standard do account_debit_note, que abre o assistente
    # account.debit.note (cria a nota de débito com debit_origin_id → DFT...).
    # O botão "Nota de débito" das vistas do account_MZ passa a chamar esse
    # método standard e funciona correctamente.
