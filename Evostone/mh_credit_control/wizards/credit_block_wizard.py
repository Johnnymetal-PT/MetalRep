from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreditBlockWizard(models.TransientModel):
    _name = 'credit.block.wizard'
    _description = 'Wizard de Bloqueio de Crédito'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Ordem de Venda',
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sale_order_id.partner_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='sale_order_id.currency_id',
    )
    order_amount = fields.Monetary(
        string='Valor do Pedido',
        related='sale_order_id.amount_total',
        currency_field='currency_id',
    )

    # Campos do partner via sale_order
    partner_credit_limit = fields.Float(
        string='Limite de Crédito',
        related='sale_order_id.partner_credit_limit',
    )
    partner_current_credit = fields.Monetary(
        string='Crédito Actual',
        related='sale_order_id.partner_current_credit',
        currency_field='currency_id',
    )
    partner_overdue_amount = fields.Monetary(
        string='Total Vencido',
        related='sale_order_id.partner_overdue_amount',
        currency_field='currency_id',
    )
    partner_overdue_count = fields.Integer(
        string='Nº Facturas Vencidas',
        related='sale_order_id.partner_overdue_count',
    )
    partner_pending_amount = fields.Monetary(
        string='Total Pendente',
        related='sale_order_id.partner_pending_amount',
        currency_field='currency_id',
    )
    partner_pending_count = fields.Integer(
        string='Nº Facturas Pendentes',
        related='sale_order_id.partner_pending_count',
    )

    # Bloqueios detectados (da ordem)
    has_credit_limit_block = fields.Boolean(
        related='sale_order_id.has_credit_limit_block',
    )
    has_overdue_block = fields.Boolean(
        related='sale_order_id.has_overdue_block',
    )
    has_pending_block = fields.Boolean(
        related='sale_order_id.has_pending_block',
    )

    # Aprovações (da ordem)
    credit_limit_approved = fields.Boolean(
        related='sale_order_id.credit_limit_approved',
        readonly=False,
    )
    overdue_approved = fields.Boolean(
        related='sale_order_id.overdue_approved',
        readonly=False,
    )
    pending_approved = fields.Boolean(
        related='sale_order_id.pending_approved',
        readonly=False,
    )

    # Permissões do utilizador
    user_id = fields.Many2one(
        'res.users',
        string='Utilizador',
        default=lambda self: self.env.user,
        readonly=True,
    )
    can_approve_credit_limit = fields.Boolean(
        compute='_compute_permissions',
    )
    can_approve_overdue = fields.Boolean(
        compute='_compute_permissions',
    )
    can_approve_pending = fields.Boolean(
        compute='_compute_permissions',
    )
    can_approve_any = fields.Boolean(
        compute='_compute_permissions',
    )

    @api.depends('user_id')
    def _compute_permissions(self):
        for wizard in self:
            user = wizard.user_id or self.env.user
            can_credit = user.has_group('mh_credit_control.group_approve_credit_limit')
            can_overdue = user.has_group('mh_credit_control.group_approve_overdue')
            can_pending = user.has_group('mh_credit_control.group_approve_pending')

            wizard.can_approve_credit_limit = can_credit
            wizard.can_approve_overdue = can_overdue
            wizard.can_approve_pending = can_pending
            wizard.can_approve_any = can_credit or can_overdue or can_pending

    def action_approve_credit_limit(self):
        """Aprovar bloqueio de limite de crédito"""
        self.ensure_one()
        self.sale_order_id.action_approve_credit_limit()
        return self._reload_wizard()

    def action_approve_overdue(self):
        """Aprovar bloqueio de facturas vencidas"""
        self.ensure_one()
        self.sale_order_id.action_approve_overdue()
        return self._reload_wizard()

    def action_approve_pending(self):
        """Aprovar bloqueio de facturas pendentes"""
        self.ensure_one()
        self.sale_order_id.action_approve_pending()
        return self._reload_wizard()

    def action_approve_all(self):
        """Aprovar todos os bloqueios que o utilizador tem permissão"""
        self.ensure_one()
        self.sale_order_id.action_approve_all_credit()
        return self._reload_wizard()

    def _reload_wizard(self):
        """Recarregar o wizard para mostrar estado actualizado"""
        if not self.sale_order_id.credit_blocked:
            # Todos aprovados - fechar wizard
            return {'type': 'ir.actions.act_window_close'}

        # Ainda há pendentes - reabrir wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'credit.block.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.sale_order_id.id,
            },
        }

    def action_reset_all(self):
        """Resetar todas as aprovações"""
        self.ensure_one()
        self.sale_order_id.action_reset_credit_approvals()
        return self._reload_wizard()

    def action_close(self):
        """Fechar wizard"""
        return {'type': 'ir.actions.act_window_close'}
