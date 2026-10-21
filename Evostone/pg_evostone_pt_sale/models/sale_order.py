# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

# Resumo que marca as actividades criadas por este módulo, para as voltar a
# encontrar sem duplicar e para as fechar quando o crédito for aprovado.
PT_CREDIT_ACTIVITY_SUMMARY = 'Validar conta corrente do cliente'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mh_stone_flow = fields.Boolean(
        string='Fluxo Stone Trading',
        compute='_compute_mh_stone_flow',
        help='Falso nas empresas portuguesas, onde a confirmação segue o '
             'standard do Odoo. Usado nas vistas para esconder a interface '
             'do fluxo de Moçambique.',
    )

    @api.depends('company_id', 'company_id.country_id.code')
    def _compute_mh_stone_flow(self):
        for order in self:
            order.mh_stone_flow = order._mh_stone_gates_apply()

    def _mh_stone_gates_apply(self):
        """Desliga os gates de Moçambique nas empresas portuguesas.

        Em Portugal os lotes e a disponibilidade de stock são tratados na
        entrega (stock.picking), como no standard do Odoo, e não na
        confirmação da ordem de venda.
        """
        self.ensure_one()
        if self.company_id.country_id.code == 'PT':
            return False
        return super()._mh_stone_gates_apply()

    def _check_proforma_receipt_company(self):
        for order in self:
            if order.company_id.country_id.code == 'PT':
                raise UserError(_(
                    'A emissão de recibos pró-forma na encomenda de venda '
                    'não se aplica às empresas portuguesas.'
                ))

    def action_create_proforma_payment(self):
        self._check_proforma_receipt_company()
        return super().action_create_proforma_payment()

    # =============================================
    # VALIDAÇÃO DA CONTA CORRENTE (PORTUGAL)
    # =============================================

    def _pt_credit_validator_users(self):
        """Utilizadores que validam a conta corrente."""
        group = self.env.ref(
            'pg_evostone_pt_sale.group_pt_credit_validation',
            raise_if_not_found=False,
        )
        return group.users if group else self.env['res.users']

    def _pt_open_credit_activities(self):
        """Actividades de validação de crédito ainda por fechar nesta ordem."""
        self.ensure_one()
        return self.env['mail.activity'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id),
            ('summary', '=', PT_CREDIT_ACTIVITY_SUMMARY),
        ])

    def _pt_credit_activity_note(self):
        """Corpo da actividade: o que está em dívida e o que fazer a seguir."""
        self.ensure_one()
        return _(
            'A confirmação da ordem %(order)s foi travada pela conta corrente '
            'do cliente %(partner)s.\n\n'
            '%(motivos)s\n\n'
            'Valide a situação e, se decidir avançar, aprove o bloqueio em '
            '"Resolver Bloqueio de Crédito" na própria ordem.'
        ) % {
            'order': self.name,
            'partner': self.partner_id.display_name,
            'motivos': self._pt_credit_block_reasons(),
        }

    def _pt_create_credit_activities(self, note):
        """Cria a actividade de validação, uma por validador.

        Uma por validador, para que qualquer um deles a veja na sua lista — a
        validação é feita por um ou por outro. Idempotente: se o validador já
        tiver actividade aberta nesta ordem, não cria outra.
        """
        self.ensure_one()
        validators = self._pt_credit_validator_users()
        already_assigned = self._pt_open_credit_activities().mapped('user_id')

        for validator in validators - already_assigned:
            self.activity_schedule(
                act_type_xmlid='mail.mail_activity_data_todo',
                summary=PT_CREDIT_ACTIVITY_SUMMARY,
                note=note,
                user_id=validator.id,
            )

    def _pt_log_credit_activity(self):
        """Lança a actividade de validação para quem faz a validação.

        A actividade é criada num cursor próprio e comprometida aí. A
        confirmação termina em UserError, que faz rollback da transacção; sem
        cursor separado a actividade desaparecia com ela e ninguém seria
        avisado.
        """
        self.ensure_one()
        if not self._pt_credit_validator_users():
            return

        note = self._pt_credit_activity_note()
        with self.pool.cursor() as cr:
            order = self.with_env(self.env(cr=cr))
            order._pt_create_credit_activities(note)

    def _pt_close_credit_activities(self):
        """Fecha as actividades de validação — a conta corrente ficou limpa."""
        self.ensure_one()
        activities = self._pt_open_credit_activities()
        if activities:
            activities.action_feedback(
                feedback=_('Conta corrente validada; ordem confirmada.'))

    def _pt_credit_block_reasons(self):
        """Texto com os bloqueios activos, para a mensagem ao utilizador."""
        self.ensure_one()
        reasons = []
        if self.has_credit_limit_block and not self.credit_limit_approved:
            reasons.append(_(
                '- Limite de crédito excedido '
                '(limite %(limite).2f, em dívida %(credito).2f)'
            ) % {
                'limite': self.partner_credit_limit,
                'credito': self.partner_current_credit,
            })
        if self.has_overdue_block and not self.overdue_approved:
            reasons.append(_(
                '- %(n)s factura(s) vencida(s), no total de %(valor).2f'
            ) % {
                'n': self.partner_overdue_count,
                'valor': self.partner_overdue_amount,
            })
        if self.has_pending_block and not self.pending_approved:
            reasons.append(_(
                '- %(n)s factura(s) pendente(s), no total de %(valor).2f'
            ) % {
                'n': self.partner_pending_count,
                'valor': self.partner_pending_amount,
            })
        return '\n'.join(reasons)

    def _pt_check_customer_account(self):
        """Única regra de negócio portuguesa na confirmação.

        Conta corrente limpa (sem limite excedido, sem facturas vencidas, sem
        facturas pendentes) → confirma. Caso contrário → actividade para quem
        valida e a ordem não avança.
        """
        self.ensure_one()

        # Os campos de bloqueio do mh_credit_control são armazenados e o seu
        # @api.depends não cobre a evolução das facturas do cliente: uma
        # factura que vence depois de o orçamento ser criado não os actualiza.
        # Em Moçambique havia outros gates a apanhar o caso; em Portugal esta é
        # a única regra da confirmação, por isso avalia-se contra a situação
        # actual. Os campos do parceiro (has_overdue_invoices e companhia) não
        # são armazenados, logo estes computes lêem sempre dados frescos.
        self._compute_credit_blocks()
        self._compute_credit_blocked()

        if not self.credit_blocked:
            self._pt_close_credit_activities()
            return

        self._pt_log_credit_activity()

        validators = self._pt_credit_validator_users()
        if validators:
            encaminhamento = _(
                'Foi lançada uma actividade para: %s.'
            ) % ', '.join(validators.mapped('name'))
        else:
            # Grupo por preencher: o bloqueio não pode ficar silencioso.
            encaminhamento = _(
                'ATENÇÃO: o grupo "Validação de Crédito PT" não tem '
                'utilizadores, por isso não foi possível lançar a actividade. '
                'Peça a um administrador que preencha o grupo.')

        raise UserError(_(
            'Não é possível confirmar a ordem %(order)s.\n\n'
            'A conta corrente do cliente %(partner)s não está regularizada:\n'
            '%(motivos)s\n\n'
            '%(encaminhamento)s'
        ) % {
            'order': self.name,
            'partner': self.partner_id.display_name,
            'motivos': self._pt_credit_block_reasons(),
            'encaminhamento': encaminhamento,
        })

    def action_confirm(self):
        """Em Portugal, valida a conta corrente antes de tudo o resto."""
        if not self.env.context.get('bypass_credit'):
            for order in self:
                if order._mh_stone_gates_apply():
                    continue
                order._pt_check_customer_account()
        return super().action_confirm()
