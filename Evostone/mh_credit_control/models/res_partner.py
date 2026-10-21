from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campos computed para verificar estado de facturas
    has_overdue_invoices = fields.Boolean(
        string='Tem Facturas Vencidas',
        compute='_compute_invoice_status',
        help='Indica se o cliente tem facturas vencidas (passaram da data de vencimento)',
    )
    has_pending_invoices = fields.Boolean(
        string='Tem Facturas Pendentes',
        compute='_compute_invoice_status',
        help='Indica se o cliente tem facturas pendentes (não pagas)',
    )
    overdue_invoice_amount = fields.Monetary(
        string='Total Facturas Vencidas',
        compute='_compute_invoice_status',
        currency_field='currency_id',
        help='Valor total das facturas vencidas',
    )
    pending_invoice_amount = fields.Monetary(
        string='Total Facturas Pendentes',
        compute='_compute_invoice_status',
        currency_field='currency_id',
        help='Valor total das facturas pendentes',
    )
    overdue_invoice_count = fields.Integer(
        string='Nº Facturas Vencidas',
        compute='_compute_invoice_status',
    )
    pending_invoice_count = fields.Integer(
        string='Nº Facturas Pendentes',
        compute='_compute_invoice_status',
    )

    # Campo para indicar se bloqueio de crédito está activo
    credit_block_enabled = fields.Boolean(
        string='Controle de Crédito Activo',
        default=True,
        help='Se activo, vendas serão bloqueadas quando limite excedido ou facturas vencidas/pendentes',
    )

    @api.depends('invoice_ids.state', 'invoice_ids.amount_residual', 'invoice_ids.invoice_date_due')
    def _compute_invoice_status(self):
        today = fields.Date.context_today(self)

        # Estes campos estao nas vistas de lista e de formulario do contacto, e
        # sao calculados em cada leitura. Um utilizador sem acesso a
        # contabilidade — por exemplo quem so consulta contactos — nao pode
        # pesquisar account.move, e sem esta guarda a app Contactos fica
        # inutilizavel para ele: a lista e a ficha rebentam com AccessError.
        # Sem visibilidade sobre facturas, a leitura correcta e' «nada a
        # assinalar», e nao expor valores que o utilizador nao pode consultar.
        if not self.env['account.move'].has_access('read'):
            for partner in self:
                partner.has_overdue_invoices = False
                partner.has_pending_invoices = False
                partner.overdue_invoice_amount = 0.0
                partner.pending_invoice_amount = 0.0
                partner.overdue_invoice_count = 0
                partner.pending_invoice_count = 0
            return

        for partner in self:
            # Buscar facturas do cliente (incluindo contactos filhos)
            domain = [
                ('partner_id', 'child_of', partner.commercial_partner_id.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'in_payment', 'reversed']),
            ]

            invoices = self.env['account.move'].search(domain)

            # Facturas vencidas (data de vencimento < hoje)
            overdue_invoices = invoices.filtered(
                lambda inv: inv.invoice_date_due and inv.invoice_date_due < today
            )

            # Facturas pendentes (não pagas, independente da data)
            pending_invoices = invoices.filtered(
                lambda inv: inv.amount_residual > 0
            )

            partner.has_overdue_invoices = bool(overdue_invoices)
            partner.has_pending_invoices = bool(pending_invoices)
            partner.overdue_invoice_amount = sum(overdue_invoices.mapped('amount_residual'))
            partner.pending_invoice_amount = sum(pending_invoices.mapped('amount_residual'))
            partner.overdue_invoice_count = len(overdue_invoices)
            partner.pending_invoice_count = len(pending_invoices)

    def _check_credit_limit_exceeded(self, order_amount=0.0):
        """
        Verifica se o limite de crédito seria excedido com uma nova ordem

        Args:
            order_amount: Valor da nova ordem a ser confirmada

        Returns:
            tuple: (exceeded: bool, credit_limit: float, current_credit: float)
        """
        self.ensure_one()
        partner = self.commercial_partner_id

        # Se não tem limite definido, não bloqueia
        credit_limit = partner.credit_limit
        if not credit_limit:
            return False, 0.0, 0.0

        # Verificar limite mínimo global
        # Só bloqueia se o limite do cliente >= limite mínimo configurado
        credit_limit_minimum = float(self.env['ir.config_parameter'].sudo().get_param(
            'mh_credit_control.credit_limit_minimum', '0'
        ))

        if credit_limit_minimum > 0 and credit_limit < credit_limit_minimum:
            # Limite do cliente está abaixo do mínimo global, não bloquear
            return False, credit_limit, partner.credit

        # Crédito actual (campo nativo do Odoo - total a receber)
        current_credit = partner.credit

        # Verificar se novo pedido excederia o limite
        total_with_order = current_credit + order_amount
        exceeded = total_with_order > credit_limit

        return exceeded, credit_limit, current_credit

    def action_view_overdue_invoices(self):
        """Abrir lista de facturas vencidas"""
        self.ensure_one()
        today = fields.Date.context_today(self)
        return {
            'name': f'Facturas Vencidas - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'child_of', self.commercial_partner_id.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'in_payment', 'reversed']),
                ('invoice_date_due', '<', today),
            ],
            'context': {'create': False},
        }

    def action_view_pending_invoices(self):
        """Abrir lista de facturas pendentes"""
        self.ensure_one()
        return {
            'name': f'Facturas Pendentes - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', 'child_of', self.commercial_partner_id.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'in_payment', 'reversed']),
                ('amount_residual', '>', 0),
            ],
            'context': {'create': False},
        }

    def _recompute_sale_order_credit_blocks(self):
        """
        Recalcula os campos de bloqueio de crédito nas ordens de venda em rascunho.
        Chamado quando o estado das facturas muda (ex: pagamento).
        """
        if not self:
            return

        # Buscar ordens de venda em rascunho para os partners afectados
        partner_ids = self.mapped('commercial_partner_id').ids
        if not partner_ids:
            return

        orders = self.env['sale.order'].search([
            ('partner_invoice_id.commercial_partner_id', 'in', partner_ids),
            ('state', 'in', ['draft', 'sent']),
        ])

        if orders:
            # Forçar recálculo dos campos computados armazenados
            orders._compute_credit_blocks()
