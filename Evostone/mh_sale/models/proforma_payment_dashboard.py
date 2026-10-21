from odoo import models, fields, api
from odoo.exceptions import UserError


class ProformaPaymentDashboard(models.TransientModel):
    _name = 'proforma.payment.dashboard'
    _description = 'Dashboard de Recibos Pró-forma'

    # Filtros
    date_from = fields.Date(
        string='Data Inicial',
        default=lambda self: fields.Date.today().replace(day=1),
        required=True
    )

    date_to = fields.Date(
        string='Data Final',
        default=fields.Date.today,
        required=True
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente (Opcional)',
        help='Deixe vazio para ver todos os clientes'
    )

    payment_method = fields.Selection([
        ('all', 'Todos'),
        ('cash', 'Dinheiro'),
        ('bank_transfer', 'Transferência Bancária'),
        ('check', 'Cheque'),
        ('mpesa', 'M-Pesa'),
        ('mkesh', 'Mkesh'),
        ('emola', 'E-Mola'),
        ('deposit_slip', 'Talão de Depósito'),
        ('pos', 'POS/Cartão'),
        ('other', 'Outro')
    ], string='Método de Pagamento', default='all')

    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # KPIs - Contadores
    count_draft = fields.Integer(string='Qtd Rascunho', compute='_compute_kpis')
    count_posted = fields.Integer(string='Qtd Confirmados', compute='_compute_kpis')
    count_paid = fields.Integer(string='Qtd Pagos', compute='_compute_kpis')
    count_cancelled = fields.Integer(string='Qtd Cancelados', compute='_compute_kpis')
    count_ready_convert = fields.Integer(
        string='Prontos para Converter',
        compute='_compute_kpis',
        help='Recibos confirmados com allocation_type = normal'
    )

    # KPIs - Valores
    amount_draft = fields.Monetary(string='Total Rascunho', compute='_compute_kpis')
    amount_posted = fields.Monetary(string='Total Confirmados', compute='_compute_kpis')
    amount_paid = fields.Monetary(string='Total Pagos', compute='_compute_kpis')
    amount_cancelled = fields.Monetary(string='Total Cancelados', compute='_compute_kpis')
    amount_ready_convert = fields.Monetary(
        string='Valor Pronto p/ Converter',
        compute='_compute_kpis'
    )

    # Análise por método
    amount_cash = fields.Monetary(string='Dinheiro', compute='_compute_by_method')
    amount_bank = fields.Monetary(string='Transfer. Bancária', compute='_compute_by_method')
    amount_mpesa = fields.Monetary(string='M-Pesa', compute='_compute_by_method')
    amount_mkesh = fields.Monetary(string='Mkesh', compute='_compute_by_method')
    amount_emola = fields.Monetary(string='E-Mola', compute='_compute_by_method')
    amount_other = fields.Monetary(string='Outros', compute='_compute_by_method')

    @api.depends('date_from', 'date_to', 'partner_id', 'payment_method')
    def _compute_kpis(self):
        """Calcular KPIs principais"""
        for dash in self:
            domain = [
                ('date', '>=', dash.date_from),
                ('date', '<=', dash.date_to),
            ]

            if dash.partner_id:
                domain.append(('partner_id', '=', dash.partner_id.id))

            if dash.payment_method != 'all':
                domain.append(('payment_method', '=', dash.payment_method))

            payments = self.env['proforma.payment'].search(domain)

            # Contadores
            dash.count_draft = len(payments.filtered(lambda p: p.state == 'draft'))
            dash.count_posted = len(payments.filtered(lambda p: p.state == 'posted'))
            dash.count_paid = len(payments.filtered(lambda p: p.state == 'paid'))
            dash.count_cancelled = len(payments.filtered(lambda p: p.state == 'cancelled'))
            dash.count_ready_convert = len(payments.filtered(
                lambda p: p.state == 'posted' and p.allocation_type == 'normal'
            ))

            # Valores
            draft = payments.filtered(lambda p: p.state == 'draft')
            posted = payments.filtered(lambda p: p.state == 'posted')
            paid = payments.filtered(lambda p: p.state == 'paid')
            cancelled = payments.filtered(lambda p: p.state == 'cancelled')
            ready = payments.filtered(lambda p: p.state == 'posted' and p.allocation_type == 'normal')

            dash.amount_draft = sum(draft.mapped('amount'))
            dash.amount_posted = sum(posted.mapped('amount'))
            dash.amount_paid = sum(paid.mapped('amount'))
            dash.amount_cancelled = sum(cancelled.mapped('amount'))
            dash.amount_ready_convert = sum(ready.mapped('amount'))

    @api.depends('date_from', 'date_to', 'partner_id', 'payment_method')
    def _compute_by_method(self):
        """Calcular valores por método de pagamento"""
        for dash in self:
            domain = [
                ('date', '>=', dash.date_from),
                ('date', '<=', dash.date_to),
                ('state', 'in', ['posted', 'paid'])  # Apenas confirmados e pagos
            ]

            if dash.partner_id:
                domain.append(('partner_id', '=', dash.partner_id.id))

            payments = self.env['proforma.payment'].search(domain)

            dash.amount_cash = sum(payments.filtered(lambda p: p.payment_method == 'cash').mapped('amount'))
            dash.amount_bank = sum(payments.filtered(lambda p: p.payment_method == 'bank_transfer').mapped('amount'))
            dash.amount_mpesa = sum(payments.filtered(lambda p: p.payment_method == 'mpesa').mapped('amount'))
            dash.amount_mkesh = sum(payments.filtered(lambda p: p.payment_method == 'mkesh').mapped('amount'))
            dash.amount_emola = sum(payments.filtered(lambda p: p.payment_method == 'emola').mapped('amount'))

            other_methods = ['check', 'deposit_slip', 'pos', 'other']
            dash.amount_other = sum(payments.filtered(lambda p: p.payment_method in other_methods).mapped('amount'))

    def action_view_ready_convert(self):
        """Ver recibos prontos para converter em pagamento"""
        self.ensure_one()

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('allocation_type', '=', 'normal'),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        if self.payment_method != 'all':
            domain.append(('payment_method', '=', self.payment_method))

        return {
            'name': 'Recibos Prontos para Pagamento',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
        }

    def action_view_posted(self):
        """Ver todos recibos confirmados"""
        self.ensure_one()

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'posted'),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        if self.payment_method != 'all':
            domain.append(('payment_method', '=', self.payment_method))

        return {
            'name': 'Recibos Confirmados',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
        }

    def action_view_paid(self):
        """Ver todos recibos pagos"""
        self.ensure_one()

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'paid'),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        if self.payment_method != 'all':
            domain.append(('payment_method', '=', self.payment_method))

        return {
            'name': 'Recibos Pagos',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
        }

    def action_view_analysis(self):
        """Abrir análise pivot/graph"""
        self.ensure_one()

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        if self.payment_method != 'all':
            domain.append(('payment_method', '=', self.payment_method))

        return {
            'name': 'Análise de Recibos',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'view_mode': 'pivot,graph,list',
            'domain': domain,
            'context': {'create': False, 'group_by': ['date', 'payment_method']},
        }
