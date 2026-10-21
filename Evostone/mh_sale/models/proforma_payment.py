from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class ProformaPayment(models.Model):
    _name = 'proforma.payment'
    _description = 'Recibo Pró-forma'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'
    _rec_name = 'name'

    can_cancel = fields.Boolean(
        compute='_compute_can_cancel',
    )

    @api.depends_context('uid')
    def _compute_can_cancel(self):
        is_blocked = self.env.user.has_group('mh_sale.group_block_proforma_cancel')
        for rec in self:
            rec.can_cancel = not is_blocked

    name = fields.Char(
        string='Referência',
        required=True,
        readonly=True,
        default='DRAFT',
        copy=False,
        tracking=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )

    date = fields.Date(
        string='Data',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    amount = fields.Monetary(
        string='Valor',
        required=True,
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True
    )

    payment_method = fields.Selection([
        ('cash', 'Dinheiro'),
        ('bank_transfer', 'Transferência Bancária'),
        ('check', 'Cheque'),
        ('mpesa', 'M-Pesa'),
        ('mkesh', 'Mkesh'),
        ('emola', 'E-Mola'),
        ('deposit_slip', 'Talão de Depósito'),
        ('pos', 'POS/Cartão'),
        ('other', 'Outro')
    ], string='Método de Pagamento (Legado)', tracking=True)

    memo = fields.Text(
        string='Memo/Descrição',
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('posted', 'Confirmado'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', required=True, tracking=True)

    # Campos de alocação
    allocation_ids = fields.One2many(
        'proforma.payment.allocation',
        'payment_id',
        string='Alocações'
    )

    allocation_count = fields.Integer(
        string='Nº de Alocações',
        compute='_compute_allocation_count'
    )

    amount_allocated = fields.Monetary(
        string='Valor Alocado',
        compute='_compute_allocation_stats',
        store=True,
        help='Total alocado para cotações'
    )

    amount_remaining = fields.Monetary(
        string='Valor Remanescente',
        compute='_compute_allocation_stats',
        store=True,
        help='Valor disponível para alocação'
    )

    allocation_type = fields.Selection([
        ('none', 'Sem Alocações'),
        ('proforma', 'Fatura Pró-Forma'),
        ('normal', 'Encomenda Normal')
    ], string='Tipo de Alocação',
       compute='_compute_allocation_stats',
       store=True,
       help='Tipo de encomendas para as quais este recibo está alocado')

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )

    notes = fields.Text(
        string='Observações Internas'
    )

    # Campos de banco (opcionais)
    bank_account_id = fields.Many2one(
        'res.partner.bank',
        string='Conta Bancária',
        domain="[('partner_id', '=', company_id.partner_id.id)]"
    )

    reference = fields.Char(
        string='Referência de Recibo (Legado)',
        help='Número do cheque, referência da transferência, etc. (Campo legado)'
    )

    # Campos para transformação em account.payment
    journal_id = fields.Many2one(
        'account.journal',
        string='Diário',
        required=True,
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        help='Diário de banco ou caixa para o recibo contábil'
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método de Pagamento (Contábil)',
        required=True,
        domain="[('journal_id', '=', journal_id), ('payment_type', '=', 'inbound')]",
        help='Método de pagamento disponível no diário selecionado'
    )

    # Link para account.payment
    account_payment_id = fields.Many2one(
        'account.payment',
        string='Recibo Contábil',
        readonly=True,
        help='Pagamento contábil criado a partir deste pagamento proforma'
    )

    has_payment = fields.Boolean(
        string='Tem Pagamento',
        compute='_compute_has_payment',
        help='Indica se já foi criado um account.payment'
    )

    @api.depends('account_payment_id')
    def _compute_has_payment(self):
        """Verificar se já tem payment criado"""
        for payment in self:
            payment.has_payment = bool(payment.account_payment_id)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, **kwargs):
        """No picker de alocação (context proforma_picker) enriquece SÓ as opções
        do dropdown com saldo + data, para distinguir recibos do mesmo cliente.
        O valor selecionado/existente continua a mostrar o nome normal (display_name)."""
        res = super().name_search(name=name, args=args, operator=operator, limit=limit, **kwargs)
        if not self.env.context.get('proforma_picker'):
            return res
        enriched = []
        for pid, _label in res:
            rec = self.browse(pid)
            sym = rec.currency_id.symbol or ''
            data = rec.date.strftime('%d/%m/%Y') if rec.date else ''
            enriched.append((pid, '%s — saldo %s %s (%s)' % (
                rec.name, f'{rec.amount_remaining:,.2f}', sym, data)))
        return enriched

    @api.depends('allocation_ids')
    def _compute_allocation_count(self):
        """Calcular número de alocações"""
        for payment in self:
            payment.allocation_count = len(payment.allocation_ids)

    @api.depends('allocation_ids', 'allocation_ids.amount', 'allocation_ids.sale_order_id.is_proforma', 'amount')
    def _compute_allocation_stats(self):
        """Calcular estatísticas de alocação"""
        for payment in self:
            allocations = payment.allocation_ids
            total_allocated = sum(allocations.mapped('amount'))

            payment.amount_allocated = total_allocated
            payment.amount_remaining = payment.amount - total_allocated

            # Determinar tipo de alocação baseado nas encomendas alocadas
            if not allocations:
                payment.allocation_type = 'none'
            else:
                # Verificar se alguma alocação é para fatura pró-forma
                has_proforma = any(alloc.sale_order_id.is_proforma for alloc in allocations)
                payment.allocation_type = 'proforma' if has_proforma else 'normal'

    @api.model_create_multi
    def create(self, vals_list):
        """Definir nome como DRAFT ao criar"""
        for vals in vals_list:
            if vals.get('name', 'DRAFT') in ['New', 'DRAFT', False]:
                vals['name'] = 'DRAFT'
        return super().create(vals_list)

    @api.constrains('amount')
    def _check_amount(self):
        """Validar valor positivo"""
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError('O valor deve ser maior que zero.')

    @api.constrains('partner_id')
    def _check_partner_top_level(self):
        """O cliente do recibo tem de ser a entidade de topo (sem empresa-mãe).

        A alocação recibo↔ordem casa por igualdade exata de partner_id e as
        ordens são restringidas a entidades de topo (constraint na sale.order).
        Se o recibo ficasse num contacto-filho, nunca casaria com uma ordem
        desse cliente — ficaria órfão. Garante a mesma regra em todos os
        caminhos (o domínio da vista só filtra o dropdown).
        """
        for payment in self:
            partner = payment.partner_id
            if partner and partner.parent_id:
                raise ValidationError(_(
                    "O cliente do recibo tem de ser a entidade de topo, não um "
                    "contacto.\n\n«%(child)s» pertence a «%(parent)s».\n"
                    "Selecione «%(parent)s» como cliente."
                ) % {'child': partner.name, 'parent': partner.parent_id.name})

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Limpar e seleccionar método de pagamento ao trocar diário"""
        if self.journal_id:
            # Buscar primeiro método de pagamento disponível
            payment_methods = self.env['account.payment.method.line'].search([
                ('journal_id', '=', self.journal_id.id),
                ('payment_type', '=', 'inbound')
            ], limit=1)
            self.payment_method_line_id = payment_methods[0] if payment_methods else False
        else:
            self.payment_method_line_id = False

    def action_post(self):
        """Confirmar pagamento proforma"""
        for payment in self:
            if payment.state != 'draft':
                raise UserError('Apenas pagamentos em rascunho podem ser confirmados.')

            # Gerar número de sequência apenas na primeira confirmação (quando ainda é DRAFT)
            vals = {'state': 'posted'}
            if payment.name == 'DRAFT':
                vals['name'] = self.env['ir.sequence'].next_by_code('proforma.payment') or 'PROF/001'

            payment.write(vals)

            # Mensagem no chatter
            payment.message_post(
                body=Markup(
                    "✅ <b>Recibo Pró-forma Confirmado</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Confirmado por: <b>%s</b>"
                ) % (
                    f'{payment.amount:,.2f}',
                    payment.currency_id.symbol,
                    self.env.user.name
                ),
                subject='Recibo Confirmado',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return True

    def action_cancel(self):
        """Cancelar pagamento proforma"""
        if self.env.user.has_group('mh_sale.group_block_proforma_cancel'):
            raise UserError('Não tem permissão para cancelar pagamentos. Contacte o administrador.')
        for payment in self:
            if payment.state == 'cancelled':
                raise UserError('Este pagamento já está cancelado.')

            # Verificar se já tem payment contábil criado (mesmo em estado 'paid')
            if payment.has_payment:
                raise UserError(
                    f'Não é possível cancelar este pagamento proforma pois já foi transformado '
                    f'no pagamento contábil {payment.account_payment_id.name}.\n\n'
                    f'Para cancelar, é necessário primeiro cancelar ou deletar o pagamento contábil.'
                )

            # Verificar se tem alocações
            if payment.allocation_ids:
                allocation_info = '\n'.join([
                    f'- {alloc.sale_order_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                    for alloc in payment.allocation_ids
                ])
                raise UserError(
                    'Não é possível cancelar um pagamento com alocações ativas.\n\n'
                    f'Alocações existentes:\n{allocation_info}\n\n'
                    'Por favor, desaloque o pagamento das cotações antes de cancelar.'
                )

            payment.write({'state': 'cancelled'})

            # Mensagem no chatter
            payment.message_post(
                body=Markup(
                    "❌ <b>Recibo Pró-forma Cancelado</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Cancelado por: <b>%s</b>"
                ) % (
                    f'{payment.amount:,.2f}',
                    payment.currency_id.symbol,
                    self.env.user.name
                ),
                subject='Recibo Cancelado',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return True

    def action_draft(self):
        """Voltar para rascunho"""
        for payment in self:
            if payment.state == 'draft':
                raise UserError('Este pagamento já está em rascunho.')

            if self.env.user.has_group('mh_sale.group_block_proforma_cancel'):
                raise UserError('Não tem permissão para retornar para rascunho pagamentos. Contacte o administrador.')
        
            # Verificar se já tem payment contábil criado
            if payment.has_payment:
                raise UserError(
                    f'Não é possível retornar para rascunho este pagamento proforma pois já foi transformado '
                    f'no pagamento contábil {payment.account_payment_id.name}.\n\n'
                    f'Para retornar a rascunho, é necessário primeiro cancelar ou deletar o pagamento contábil.'
                )
            

            # Verificar se tem alocações
            if payment.allocation_ids:
                allocation_info = '\n'.join([
                    f'- {alloc.sale_order_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                    for alloc in payment.allocation_ids
                ])
                raise UserError(
                    'Não é possível retornar para rascunho um pagamento com alocações ativas.\n\n'
                    f'Alocações existentes:\n{allocation_info}\n\n'
                    'Por favor, desaloque o pagamento das cotações antes de retornar para rascunho.'
                )

            # Voltar para rascunho mantendo o nome/sequência existente
            payment.write({'state': 'draft'})

            payment.message_post(
                body=Markup(
                    "🔄 <b>Recibo Pró-forma Retornado a Rascunho</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Retornado por: <b>%s</b>"
                ) % (
                    f'{payment.amount:,.2f}',
                    payment.currency_id.symbol,
                    self.env.user.name
                ),
                subject='Retornado a Rascunho',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return True

    def action_view_allocations(self):
        """Ver alocações deste pagamento"""
        self.ensure_one()
        return {
            'name': f'Alocações do Recibo {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment.allocation',
            'view_mode': 'list,form',
            'domain': [('payment_id', '=', self.id)],
            'context': {
                'default_payment_id': self.id,
                'default_payment_partner_id': self.partner_id.id
            }
        }

    def action_create_allocation(self):
        """Abrir wizard para criar nova alocação"""
        self.ensure_one()
        return {
            'name': 'Nova Alocação',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment.allocation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
                'default_amount': self.amount_remaining,
            }
        }

    can_convert_to_payment = fields.Boolean(compute='_compute_can_convert_to_payment')

    @api.depends_context('uid')
    def _compute_can_convert_to_payment(self):
        has_access = self.env.user.has_group('mh_sale.group_proforma_to_payment')
        for rec in self:
            rec.can_convert_to_payment = has_access

    def action_create_payment_wizard(self):
        """Abrir wizard para transformar em account.payment"""
        self.ensure_one()

        if not self.env.user.has_group('mh_sale.group_proforma_to_payment'):
            raise UserError(_('Não tem permissão para transformar recibos pró-forma em recibos definitivos. Contacte o administrador.'))

        # Validações
        if self.state != 'posted':
            raise UserError('Apenas pagamentos proforma confirmados podem ser transformados em pagamentos.')

        if self.has_payment:
            raise UserError(
                f'Este pagamento proforma já foi transformado no pagamento {self.account_payment_id.name}.'
            )

        if self.allocation_type != 'normal':
            if self.allocation_type == 'proforma':
                raise UserError(
                    'Não é possível transformar em pagamento contábil.\n\n'
                    'Este recibo está alocado a uma Fatura Pró-Forma.\n'
                    'Apenas recibos alocados a Encomendas Normais podem ser transformados em pagamentos.'
                )
            else:
                raise UserError(
                    'Não é possível transformar em pagamento contábil.\n\n'
                    'Este recibo não está alocado a nenhuma encomenda.\n'
                    'Aloque o recibo a uma Encomenda Normal antes de transformar em pagamento.'
                )

        return {
            'name': 'Transformar em Recibo',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.to.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_proforma_payment_id': self.id}
        }

    def action_view_account_payment(self):
        """Ver pagamento contábil criado"""
        self.ensure_one()

        if not self.account_payment_id:
            raise UserError('Este pagamento proforma ainda não foi transformado em pagamento contábil.')

        return {
            'name': f'Pagamento {self.account_payment_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': self.account_payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def unlink(self):
        """Impedir exclusão de pagamentos proforma"""
        raise UserError(
            'Não é possível deletar pagamentos proforma.\n\n'
            'Para anular um pagamento, utilize o botão "Cancelar" em vez de deletar.'
        )

    @api.model
    def get_dashboard_data(self, date_from=False, date_to=False, partner_id=False):
        """Retorna dados para o dashboard"""
        from datetime import datetime, timedelta

        # Definir today no início para evitar UnboundLocalError
        today = datetime.today()

        # Validar e definir datas default se não fornecidas
        if not date_from or not date_to:
            first_day = today.replace(day=1)
            date_from = first_day.strftime('%Y-%m-%d')
            date_to = today.strftime('%Y-%m-%d')

        # Domínio base com datas
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to)
        ]

        # Adicionar filtro de cliente se fornecido
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        # Buscar todos os pagamentos do período
        payments = self.search(domain)

        # Contadores por estado
        count_draft = len(payments.filtered(lambda p: p.state == 'draft'))
        count_posted = len(payments.filtered(lambda p: p.state == 'posted'))
        count_paid = len(payments.filtered(lambda p: p.state == 'paid'))
        count_cancelled = len(payments.filtered(lambda p: p.state == 'cancelled'))
        count_ready = len(payments.filtered(lambda p: p.state == 'posted' and p.allocation_type == 'normal'))

        # Valores por estado
        amount_draft = sum(payments.filtered(lambda p: p.state == 'draft').mapped('amount'))
        amount_posted = sum(payments.filtered(lambda p: p.state == 'posted').mapped('amount'))
        amount_paid = sum(payments.filtered(lambda p: p.state == 'paid').mapped('amount'))
        amount_cancelled = sum(payments.filtered(lambda p: p.state == 'cancelled').mapped('amount'))
        amount_ready = sum(payments.filtered(lambda p: p.state == 'posted' and p.allocation_type == 'normal').mapped('amount'))

        # Recibos prontos para converter (primeiros 5)
        ready_payments = payments.filtered(lambda p: p.state == 'posted' and p.allocation_type == 'normal')
        ready_payments_list = []
        for payment in ready_payments[:5]:
            ready_payments_list.append({
                'id': payment.id,
                'name': payment.name,
                'partner_name': payment.partner_id.name,
                'amount': payment.amount,
                'date': payment.date.strftime('%d/%m/%Y'),
                'remaining_amount': payment.amount_remaining,
            })

        # Gráfico por método de pagamento
        method_data = {}
        for payment in payments.filtered(lambda p: p.state in ['posted', 'paid']):
            method = dict(self._fields['payment_method'].selection).get(payment.payment_method, payment.payment_method)
            method_data[method] = method_data.get(method, 0) + payment.amount

        # Gráfico evolução temporal (últimos 6 meses)
        six_months_ago = today - timedelta(days=180)
        timeline_data = {}
        for payment in payments.filtered(lambda p: p.state in ['posted', 'paid'] and p.date >= six_months_ago.date()):
            month_key = payment.date.strftime('%b/%y')
            timeline_data[month_key] = timeline_data.get(month_key, 0) + payment.amount

        # Ordenar timeline por data
        sorted_timeline = dict(sorted(timeline_data.items(), key=lambda x: datetime.strptime(x[0], '%b/%y')))

        # Gráfico por tipo de alocação
        allocation_data = {
            'Sem Alocações': sum(payments.filtered(lambda p: p.allocation_type == 'none').mapped('amount')),
            'Fatura Pró-Forma': sum(payments.filtered(lambda p: p.allocation_type == 'proforma').mapped('amount')),
            'Encomenda Normal': sum(payments.filtered(lambda p: p.allocation_type == 'normal').mapped('amount')),
        }

        # Totalizador geral
        total_count = len(payments)
        total_amount = sum(payments.mapped('amount'))
        average_ticket = total_amount / total_count if total_count > 0 else 0

        return {
            'count_draft': count_draft,
            'count_posted': count_posted,
            'count_paid': count_paid,
            'count_cancelled': count_cancelled,
            'count_ready': count_ready,
            'amount_draft': amount_draft,
            'amount_posted': amount_posted,
            'amount_paid': amount_paid,
            'amount_cancelled': amount_cancelled,
            'amount_ready': amount_ready,
            'ready_payments': ready_payments_list,
            'total_count': total_count,
            'total_amount': total_amount,
            'average_ticket': average_ticket,
            'currency': self.env.company.currency_id.symbol,
            'methodChart': {
                'labels': list(method_data.keys()),
                'values': list(method_data.values())
            },
            'timelineChart': {
                'labels': list(sorted_timeline.keys()),
                'values': list(sorted_timeline.values())
            },
            'allocationChart': {
                'labels': list(allocation_data.keys()),
                'values': list(allocation_data.values())
            }
        }