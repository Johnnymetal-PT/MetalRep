from odoo import api, fields, models


class CreditApproval(models.Model):
    _name = 'credit.approval'
    _description = 'Histórico de Aprovação de Crédito'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Ordem de Venda',
        required=True,
        ondelete='cascade',
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sale_order_id.partner_id',
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        related='sale_order_id.company_id',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='sale_order_id.currency_id',
    )

    block_type = fields.Selection([
        ('credit_limit', 'Limite de Crédito Excedido'),
        ('overdue', 'Facturas Vencidas'),
        ('pending', 'Facturas Pendentes'),
    ], string='Tipo de Bloqueio', required=True, index=True)

    state = fields.Selection([
        ('pending', 'Aguarda Aprovação'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
    ], string='Estado', default='pending', required=True, index=True)

    # Informação do bloqueio
    block_amount = fields.Monetary(
        string='Valor Bloqueado',
        currency_field='currency_id',
        help='Valor da ordem de venda no momento do bloqueio',
    )
    credit_limit = fields.Monetary(
        string='Limite de Crédito',
        currency_field='currency_id',
        help='Limite de crédito do cliente no momento do bloqueio',
    )
    current_credit = fields.Monetary(
        string='Crédito Actual',
        currency_field='currency_id',
        help='Valor actual em aberto do cliente no momento do bloqueio',
    )
    overdue_amount = fields.Monetary(
        string='Valor Vencido',
        currency_field='currency_id',
        help='Total de facturas vencidas no momento do bloqueio',
    )
    pending_amount = fields.Monetary(
        string='Valor Pendente',
        currency_field='currency_id',
        help='Total de facturas pendentes no momento do bloqueio',
    )

    # Aprovação/Rejeição
    approved_by = fields.Many2one(
        'res.users',
        string='Aprovado/Rejeitado Por',
        readonly=True,
    )
    approval_date = fields.Datetime(
        string='Data de Aprovação/Rejeição',
        readonly=True,
    )
    notes = fields.Text(
        string='Notas',
        help='Justificação ou observações da aprovação/rejeição',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('sale_order_id.name', 'block_type', 'state')
    def _compute_display_name(self):
        block_labels = dict(self._fields['block_type'].selection)
        state_labels = dict(self._fields['state'].selection)
        for record in self:
            order_name = record.sale_order_id.name or 'Novo'
            block_label = block_labels.get(record.block_type, '')
            state_label = state_labels.get(record.state, '')
            record.display_name = f"{order_name} - {block_label} ({state_label})"

    def action_approve(self, notes=False):
        """Aprovar o bloqueio"""
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approved_by': self.env.uid,
            'approval_date': fields.Datetime.now(),
            'notes': notes or self.notes,
        })
        # Registar no chatter da ordem de venda
        block_labels = dict(self._fields['block_type'].selection)
        self.sale_order_id.message_post(
            body=f"<b>Aprovação de Crédito</b><br/>"
                 f"Tipo: {block_labels.get(self.block_type)}<br/>"
                 f"Aprovado por: {self.env.user.name}<br/>"
                 f"Notas: {notes or 'N/A'}",
            message_type='notification',
        )
        return True

    def action_reject(self, notes=False):
        """Rejeitar o bloqueio"""
        self.ensure_one()
        self.write({
            'state': 'rejected',
            'approved_by': self.env.uid,
            'approval_date': fields.Datetime.now(),
            'notes': notes or self.notes,
        })
        # Registar no chatter da ordem de venda
        block_labels = dict(self._fields['block_type'].selection)
        self.sale_order_id.message_post(
            body=f"<b>Rejeição de Crédito</b><br/>"
                 f"Tipo: {block_labels.get(self.block_type)}<br/>"
                 f"Rejeitado por: {self.env.user.name}<br/>"
                 f"Notas: {notes or 'N/A'}",
            message_type='notification',
        )
        return True
