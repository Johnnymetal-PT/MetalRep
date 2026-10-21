from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # =============================================
    # CAMPOS DE DETECÇÃO DE BLOQUEIO
    # =============================================

    # Bloqueios detectados (computados do partner)
    has_credit_limit_block = fields.Boolean(
        string='Bloqueio Limite Crédito',
        compute='_compute_credit_blocks',
        store=True,
    )
    has_overdue_block = fields.Boolean(
        string='Bloqueio Facturas Vencidas',
        compute='_compute_credit_blocks',
        store=True,
    )
    has_pending_block = fields.Boolean(
        string='Bloqueio Facturas Pendentes',
        compute='_compute_credit_blocks',
        store=True,
    )

    # Campo geral de bloqueio (True se qualquer bloqueio activo E não aprovado)
    credit_blocked = fields.Boolean(
        string='Bloqueado por Crédito',
        compute='_compute_credit_blocked',
        store=True,
        help='Indica se a ordem está bloqueada por questões de crédito não aprovadas',
    )

    # =============================================
    # CAMPOS DE APROVAÇÃO - LIMITE DE CRÉDITO
    # =============================================
    credit_limit_approved = fields.Boolean(
        string='Limite Aprovado',
        tracking=True,
    )
    credit_limit_approved_by = fields.Many2one(
        'res.users',
        string='Aprovado Por',
        readonly=True,
    )
    credit_limit_approved_date = fields.Datetime(
        string='Data Aprovação',
        readonly=True,
    )
    # Info no momento da aprovação
    credit_limit_at_approval = fields.Float(
        string='Limite no Momento',
        readonly=True,
    )
    current_credit_at_approval = fields.Float(
        string='Crédito no Momento',
        readonly=True,
    )

    # =============================================
    # CAMPOS DE APROVAÇÃO - FACTURAS VENCIDAS
    # =============================================
    overdue_approved = fields.Boolean(
        string='Vencidas Aprovado',
        tracking=True,
    )
    overdue_approved_by = fields.Many2one(
        'res.users',
        string='Aprovado Por',
        readonly=True,
    )
    overdue_approved_date = fields.Datetime(
        string='Data Aprovação',
        readonly=True,
    )
    overdue_amount_at_approval = fields.Float(
        string='Valor Vencido no Momento',
        readonly=True,
    )
    overdue_count_at_approval = fields.Integer(
        string='Nº Facturas no Momento',
        readonly=True,
    )

    # =============================================
    # CAMPOS DE APROVAÇÃO - FACTURAS PENDENTES
    # =============================================
    pending_approved = fields.Boolean(
        string='Pendentes Aprovado',
        tracking=True,
    )
    pending_approved_by = fields.Many2one(
        'res.users',
        string='Aprovado Por',
        readonly=True,
    )
    pending_approved_date = fields.Datetime(
        string='Data Aprovação',
        readonly=True,
    )
    pending_amount_at_approval = fields.Float(
        string='Valor Pendente no Momento',
        readonly=True,
    )
    pending_count_at_approval = fields.Integer(
        string='Nº Facturas no Momento',
        readonly=True,
    )

    # =============================================
    # CAMPOS RELACIONADOS DO PARTNER
    # =============================================
    partner_has_overdue = fields.Boolean(
        related='partner_id.has_overdue_invoices',
        string='Cliente com Facturas Vencidas',
    )
    partner_has_pending = fields.Boolean(
        related='partner_id.has_pending_invoices',
        string='Cliente com Facturas Pendentes',
    )
    partner_credit_limit = fields.Float(
        related='partner_id.credit_limit',
        string='Limite de Crédito',
    )
    partner_current_credit = fields.Monetary(
        related='partner_id.credit',
        string='Crédito Actual',
        currency_field='currency_id',
    )
    partner_overdue_amount = fields.Monetary(
        related='partner_id.overdue_invoice_amount',
        string='Total Vencido',
        currency_field='currency_id',
    )
    partner_overdue_count = fields.Integer(
        related='partner_id.overdue_invoice_count',
        string='Nº Facturas Vencidas',
    )
    partner_pending_amount = fields.Monetary(
        related='partner_id.pending_invoice_amount',
        string='Total Pendente',
        currency_field='currency_id',
    )
    partner_pending_count = fields.Integer(
        related='partner_id.pending_invoice_count',
        string='Nº Facturas Pendentes',
    )

    # =============================================
    # CAMPOS DE PERMISSÃO (computados)
    # =============================================
    can_approve_credit_limit = fields.Boolean(
        compute='_compute_can_approve',
    )
    can_approve_overdue = fields.Boolean(
        compute='_compute_can_approve',
    )
    can_approve_pending = fields.Boolean(
        compute='_compute_can_approve',
    )

    # =============================================
    # MÉTODOS COMPUTE
    # =============================================

    @api.depends('partner_id', 'partner_invoice_id', 'amount_total', 'state')
    def _compute_credit_blocks(self):
        """Detecta quais bloqueios existem baseado na situação do partner"""
        for order in self:
            has_credit_limit = False
            has_overdue = False
            has_pending = False

            if order.state in ('draft', 'sent') and order.partner_invoice_id:
                partner = order.partner_invoice_id.commercial_partner_id

                if partner.credit_block_enabled:
                    # 1. Limite de crédito
                    exceeded, limit, current = partner._check_credit_limit_exceeded(order.amount_total)
                    if exceeded:
                        has_credit_limit = True

                    # 2. Facturas vencidas
                    if partner.has_overdue_invoices:
                        has_overdue = True

                    # 3. Facturas pendentes
                    if partner.has_pending_invoices:
                        has_pending = True

            order.has_credit_limit_block = has_credit_limit
            order.has_overdue_block = has_overdue
            order.has_pending_block = has_pending

    @api.depends('has_credit_limit_block', 'has_overdue_block', 'has_pending_block',
                 'credit_limit_approved', 'overdue_approved', 'pending_approved')
    def _compute_credit_blocked(self):
        """Calcula se ordem está bloqueada (bloqueio existe E não está aprovado)"""
        for order in self:
            blocked = False

            # Bloqueado se existe bloqueio E não está aprovado
            if order.has_credit_limit_block and not order.credit_limit_approved:
                blocked = True
            if order.has_overdue_block and not order.overdue_approved:
                blocked = True
            if order.has_pending_block and not order.pending_approved:
                blocked = True

            order.credit_blocked = blocked

    def _compute_can_approve(self):
        """Verifica permissões do utilizador actual"""
        user = self.env.user
        can_credit = user.has_group('mh_credit_control.group_approve_credit_limit')
        can_overdue = user.has_group('mh_credit_control.group_approve_overdue')
        can_pending = user.has_group('mh_credit_control.group_approve_pending')

        for order in self:
            order.can_approve_credit_limit = can_credit
            order.can_approve_overdue = can_overdue
            order.can_approve_pending = can_pending

    # =============================================
    # MÉTODOS DE APROVAÇÃO
    # =============================================

    def action_approve_credit_limit(self):
        """Aprovar/Desaprovar bloqueio de limite de crédito"""
        self.ensure_one()
        if not self.env.user.has_group('mh_credit_control.group_approve_credit_limit'):
            raise UserError(_("Não tem permissão para aprovar bloqueios de limite de crédito."))

        if self.credit_limit_approved:
            # Desaprovar
            self.write({
                'credit_limit_approved': False,
                'credit_limit_approved_by': False,
                'credit_limit_approved_date': False,
                'credit_limit_at_approval': False,
                'current_credit_at_approval': False,
            })
            self.message_post(body=_('Aprovação de limite de crédito removida por %s') % self.env.user.name)
        else:
            # Aprovar
            partner = self.partner_invoice_id.commercial_partner_id
            self.write({
                'credit_limit_approved': True,
                'credit_limit_approved_by': self.env.uid,
                'credit_limit_approved_date': fields.Datetime.now(),
                'credit_limit_at_approval': partner.credit_limit,
                'current_credit_at_approval': partner.credit,
            })
            self.message_post(body=_('Limite de crédito aprovado por %s') % self.env.user.name)

        return True

    def action_approve_overdue(self):
        """Aprovar/Desaprovar bloqueio de facturas vencidas"""
        self.ensure_one()
        if not self.env.user.has_group('mh_credit_control.group_approve_overdue'):
            raise UserError(_("Não tem permissão para aprovar bloqueios de facturas vencidas."))

        if self.overdue_approved:
            # Desaprovar
            self.write({
                'overdue_approved': False,
                'overdue_approved_by': False,
                'overdue_approved_date': False,
                'overdue_amount_at_approval': False,
                'overdue_count_at_approval': False,
            })
            self.message_post(body=_('Aprovação de facturas vencidas removida por %s') % self.env.user.name)
        else:
            # Aprovar
            partner = self.partner_invoice_id.commercial_partner_id
            self.write({
                'overdue_approved': True,
                'overdue_approved_by': self.env.uid,
                'overdue_approved_date': fields.Datetime.now(),
                'overdue_amount_at_approval': partner.overdue_invoice_amount,
                'overdue_count_at_approval': partner.overdue_invoice_count,
            })
            self.message_post(body=_('Facturas vencidas aprovado por %s') % self.env.user.name)

        return True

    def action_approve_pending(self):
        """Aprovar/Desaprovar bloqueio de facturas pendentes"""
        self.ensure_one()
        if not self.env.user.has_group('mh_credit_control.group_approve_pending'):
            raise UserError(_("Não tem permissão para aprovar bloqueios de facturas pendentes."))

        if self.pending_approved:
            # Desaprovar
            self.write({
                'pending_approved': False,
                'pending_approved_by': False,
                'pending_approved_date': False,
                'pending_amount_at_approval': False,
                'pending_count_at_approval': False,
            })
            self.message_post(body=_('Aprovação de facturas pendentes removida por %s') % self.env.user.name)
        else:
            # Aprovar
            partner = self.partner_invoice_id.commercial_partner_id
            self.write({
                'pending_approved': True,
                'pending_approved_by': self.env.uid,
                'pending_approved_date': fields.Datetime.now(),
                'pending_amount_at_approval': partner.pending_invoice_amount,
                'pending_count_at_approval': partner.pending_invoice_count,
            })
            self.message_post(body=_('Facturas pendentes aprovado por %s') % self.env.user.name)

        return True

    def action_approve_all_credit(self):
        """Aprovar todos os bloqueios que o utilizador tem permissão"""
        self.ensure_one()
        approved_any = False

        if self.has_credit_limit_block and not self.credit_limit_approved:
            if self.env.user.has_group('mh_credit_control.group_approve_credit_limit'):
                self.action_approve_credit_limit()
                approved_any = True

        if self.has_overdue_block and not self.overdue_approved:
            if self.env.user.has_group('mh_credit_control.group_approve_overdue'):
                self.action_approve_overdue()
                approved_any = True

        if self.has_pending_block and not self.pending_approved:
            if self.env.user.has_group('mh_credit_control.group_approve_pending'):
                self.action_approve_pending()
                approved_any = True

        if not approved_any:
            raise UserError(_("Não tem permissão para aprovar nenhum dos bloqueios pendentes."))

        return True

    def action_reset_credit_approvals(self):
        """Resetar todas as aprovações de crédito"""
        self.ensure_one()

        if self.state not in ['draft', 'sent']:
            raise UserError(_('Não é possível resetar aprovações de ordens já confirmadas.'))

        self.write({
            'credit_limit_approved': False,
            'credit_limit_approved_by': False,
            'credit_limit_approved_date': False,
            'credit_limit_at_approval': False,
            'current_credit_at_approval': False,
            'overdue_approved': False,
            'overdue_approved_by': False,
            'overdue_approved_date': False,
            'overdue_amount_at_approval': False,
            'overdue_count_at_approval': False,
            'pending_approved': False,
            'pending_approved_by': False,
            'pending_approved_date': False,
            'pending_amount_at_approval': False,
            'pending_count_at_approval': False,
        })

        self.message_post(body=_('Aprovações de crédito resetadas por %s') % self.env.user.name)
        return True

    # =============================================
    # OVERRIDE ACTION_CONFIRM
    # =============================================

    def action_confirm(self):
        """Override para garantir que crédito foi aprovado antes de confirmar"""
        # Se bypass_credit está no contexto, ignorar verificações
        if self.env.context.get('bypass_credit'):
            return super().action_confirm()

        for order in self:
            # Verificar se há bloqueios não aprovados
            if order.credit_blocked:
                raise UserError(_(
                    'Esta ordem tem bloqueios de crédito não aprovados.\n\n'
                    'Use o botão "Resolver Bloqueio de Crédito" para aprovar os bloqueios.'
                ))

        return super().action_confirm()

    # =============================================
    # WIZARD
    # =============================================

    def action_open_credit_wizard(self):
        """Abrir wizard de bloqueio de crédito"""
        self.ensure_one()
        return {
            'name': _('Bloqueio de Crédito'),
            'type': 'ir.actions.act_window',
            'res_model': 'credit.block.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
        }
