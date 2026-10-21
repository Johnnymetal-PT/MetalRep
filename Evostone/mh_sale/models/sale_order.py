from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    can_edit_pricelist = fields.Boolean(
        string='Pode Editar Pricelist',
        compute='_compute_can_edit_pricelist',
        store=False,
        help='Indica se o utilizador pode alterar a pricelist da ordem'
    )

    @api.depends_context('uid')
    def _compute_can_edit_pricelist(self):
        has_permission = self.env.user.has_group('mh_sale.group_sale_price_edit')
        for order in self:
            order.can_edit_pricelist = has_permission

    @api.constrains('partner_id')
    def _check_partner_top_level(self):
        """O cliente da encomenda tem de ser a entidade de topo (sem empresa-mãe).

        Complementa o domínio da vista (que só filtra o dropdown): garante a regra
        também nos caminhos que saltam esse domínio — conversão de oportunidade
        CRM, default_partner_id do contexto, importação, duplicação, etc.
        """
        for order in self:
            # Fluxo Stone Trading (MZ): nas empresas em standard e' normal
            # vender a um contacto de uma empresa.
            if not order._mh_stone_gates_apply():
                continue

            partner = order.partner_id
            if partner and partner.parent_id:
                raise ValidationError(_(
                    "O cliente da encomenda tem de ser a entidade de topo, não um "
                    "contacto.\n\n«%(child)s» pertence a «%(parent)s».\n"
                    "Selecione «%(parent)s» como cliente."
                ) % {'child': partner.name, 'parent': partner.parent_id.name})

    approval_state = fields.Selection([
        ('pending', 'Pendente'),
        ('approved', 'Aprovada'),
        ('rejected', 'Rejeitada')
    ], string='Estado de Aprovação', default='pending', tracking=True, copy=False)

    approval_date = fields.Datetime(
        string='Data de Aprovação',
        readonly=True,
        copy=False
    )

    approved_by = fields.Many2one(
        'res.users',
        string='Aprovado por',
        readonly=True,
        copy=False
    )

    rejection_date = fields.Datetime(
        string='Data de Rejeição',
        readonly=True,
        copy=False
    )

    rejected_by = fields.Many2one(
        'res.users',
        string='Rejeitado por',
        readonly=True,
        copy=False
    )

    rejection_reason = fields.Text(
        string='Motivo da Rejeição',
        readonly=True,
        copy=False
    )

    # Campos de alocação de pagamentos
    payment_allocation_ids = fields.One2many(
        'proforma.payment.allocation',
        'sale_order_id',
        string='Alocações de Pagamento'
    )

    has_proforma_receipt = fields.Boolean(
        string='Tem Pró-forma',
        compute='_compute_payment_stats',
        compute_sudo=True,
        store=True
    )

    allocation_count = fields.Integer(
        string='Nº de Pagamentos',
        compute='_compute_payment_stats',
        compute_sudo=True,
        store=True
    )

    amount_covered = fields.Monetary(
        string='Valor Coberto',
        compute='_compute_payment_stats',
        store=True,
        compute_sudo=True,
        help='Total coberto por pagamentos proforma'
    )

    amount_pending = fields.Monetary(
        string='Valor Pendente',
        compute='_compute_payment_stats',
        store=True,
        compute_sudo=True,
        help='Valor ainda não coberto por pagamentos'
    )

    coverage_percentage = fields.Float(
        string='% Coberto',
        compute='_compute_payment_stats',
        store=True,
        compute_sudo=True
    )

    is_fully_covered = fields.Boolean(
        string='Totalmente Coberto',
        compute='_compute_payment_stats',
        store=True,
        compute_sudo=True
    )

    suggested_payment_count = fields.Integer(
        string='Qtd Pagamentos Disponíveis',
        compute='_compute_suggested_payments'
    )

    is_locked = fields.Boolean(
        string='Bloqueado',
        compute='_compute_is_locked',
        store=False,
        help='Indica se a ordem está bloqueada para edição (aprovada ou totalmente coberta)'
    )

    is_proforma = fields.Boolean(
        string='Factura Pró-forma',
        default=False,
        tracking=True,
        copy=False,
        help='Quando ativo, pagamentos proforma validam contra valor SEM impostos e faturação fica bloqueada'
    )

    can_create_invoice = fields.Boolean(
        string='Pode Criar Factura',
        compute='_compute_can_create_invoice',
        store=False,
        help='Controla se a encomenda pode gerar faturas'
    )

    location_id = fields.Many2one(
        'stock.location',
        string='Localização Interna',
        domain="[('usage', '=', 'internal'), ('warehouse_id', '=', warehouse_id)]",
        check_company=True,
        help='Localização de origem para retirada de stock no picking'
    )

    sale_status = fields.Selection([
        ('action_required', 'Necessário Ação'),
        ('ready_to_sell', 'Pronta para Venda'),
        ('invoiced', 'Faturada'),
        ('blocked', 'Bloqueada'),
    ], string='Estado de Venda',
       compute='_compute_sale_status',
       store=True,
       help='Status geral da cotação baseado na aprovação e cobertura de pagamentos')

    # Campos de margem de lucro total
    amount_margin = fields.Monetary(
        string='Margem Total',
        compute='_compute_margin_total',
        store=True,
        currency_field='currency_id',
        help='Margem de lucro total em valor monetário'
    )

    margin_percent = fields.Float(
        string='Margem Total (%)',
        compute='_compute_margin_total',
        store=True,
        digits='Product Price',
        help='Margem de lucro média ponderada em percentual'
    )

    # Campos de cubicagem
    total_area = fields.Float(
        string='Área Total (m²)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 3),
        help='Soma das áreas de todas as linhas (placas, bandas, ladrilhos)'
    )

    total_volume = fields.Float(
        string='Volume Total (m³)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 3),
        help='Soma dos volumes de todas as linhas (blocos)'
    )

    total_weight = fields.Float(
        string='Peso Total (KG)',
        compute='_compute_cubage',
        store=True,
        digits=(16, 2),
        help='Peso total de todos os produtos'
    )

    @api.depends('order_line.area', 'order_line.volume', 'order_line.peso')
    def _compute_cubage(self):
        """Soma área, volume e peso das linhas.

        order_line.peso é compute com state guard próprio (preserva snapshot
        quando state in sale/done), portanto o header só precisa somar.
        """
        for order in self:
            order.total_area = sum(order.order_line.mapped('area'))
            order.total_volume = sum(order.order_line.mapped('volume'))
            order.total_weight = sum(order.order_line.mapped('peso'))

    @api.depends('order_line.margin_amount', 'amount_untaxed')
    def _compute_margin_total(self):
        """Calcular margem total da ordem"""
        for order in self:
            # Soma das margens em valor de todas as linhas
            amount_margin = sum(order.order_line.mapped('margin_amount'))
            order.amount_margin = amount_margin

            # Margem % média ponderada: (margem total / custo total) - decimal para widget percentage
            if order.amount_untaxed > 0:
                # Custo total = amount_untaxed - margem
                cost_total = order.amount_untaxed - amount_margin
                if cost_total > 0:
                    order.margin_percent = amount_margin / cost_total
                else:
                    order.margin_percent = 0.0
            else:
                order.margin_percent = 0.0

    @api.depends('payment_allocation_ids', 'payment_allocation_ids.amount',
                 'amount_total', 'amount_untaxed', 'is_proforma')
    def _compute_payment_stats(self):
        """Calcular todas as estatísticas de pagamentos alocados

        IMPORTANTE: Se is_proforma=True, valida contra amount_untaxed (SEM impostos)
                    Se is_proforma=False, valida contra amount_total (COM impostos)
        """
        for order in self:
            allocations = order.payment_allocation_ids
            total_covered = sum(allocations.mapped('amount'))

            # Determinar valor de referência baseado em tipo de proforma
            reference_amount = order.amount_untaxed if order.is_proforma else order.amount_total

            # Campos básicos
            order.allocation_count = len(allocations)
            order.has_proforma_receipt = len(allocations) > 0
            order.amount_covered = total_covered
            order.amount_pending = reference_amount - total_covered

            # Percentual de cobertura
            if reference_amount > 0:
                order.coverage_percentage = (total_covered / reference_amount) * 100
            else:
                order.coverage_percentage = 0

            # Verificação se está totalmente coberto
            # Só considera coberto se tem valor total > 0 e está totalmente pago
            order.is_fully_covered = reference_amount > 0 and order.amount_pending <= 0

    @api.depends('partner_id', 'amount_pending', 'is_proforma')
    def _compute_suggested_payments(self):
        """Buscar pagamentos disponíveis que ainda têm saldo e são compatíveis com o tipo"""
        # A sugestao de pagamentos so faz sentido para quem trata de recibos.
        # Para os restantes perfis nao ha nada a sugerir, e sem esta guarda a
        # pesquisa a proforma.payment rebenta a ficha da ordem de venda.
        if not self.env['proforma.payment'].has_access('read'):
            for order in self:
                order.suggested_payment_count = 0
            return
        for order in self:
            if not order.partner_id or order.amount_pending <= 0:
                order.suggested_payment_count = 0
                continue

            # Determinar tipos compatíveis baseado em is_proforma
            if order.is_proforma:
                compatible_types = ['none', 'proforma']
            else:
                compatible_types = ['none', 'normal']

            # Buscar pagamentos do cliente com saldo disponível e tipo compatível
            payments = self.env['proforma.payment'].search([
                ('partner_id', '=', order.partner_id.id),
                ('state', '=', 'posted'),
                ('amount_remaining', '>', 0),
                ('allocation_type', 'in', compatible_types)
            ])

            order.suggested_payment_count = len(payments)

    @api.depends('approval_state', 'is_fully_covered', 'invoice_status')
    def _compute_sale_status(self):
        """Calcular status de venda baseado na aprovação e cobertura de pagamentos"""
        for order in self:
            # Totalmente faturada = Faturada (prioridade máxima)
            if order.invoice_status == 'invoiced':
                order.sale_status = 'invoiced'
            # Rejeitada = Bloqueada (sem ação possível)
            elif order.approval_state == 'rejected':
                order.sale_status = 'blocked'
            # Aprovada OU totalmente coberta = Pronta
            elif order.approval_state == 'approved' or order.is_fully_covered:
                order.sale_status = 'ready_to_sell'
            # Pendente e não coberta = Precisa ação
            else:
                order.sale_status = 'action_required'

    @api.depends('approval_state', 'is_fully_covered', 'state', 'amount_total')
    def _compute_is_locked(self):
        """Determinar se a ordem está bloqueada para edição"""
        for order in self:
            # Não bloquear se a cotação ainda está vazia (sem valor)
            if order.amount_total == 0:
                order.is_locked = order.approval_state == 'rejected' or order.state not in ['draft', 'sent']
            else:
                order.is_locked = (
                    order.approval_state in ['approved', 'rejected'] or
                    order.is_fully_covered or
                    order.state not in ['draft', 'sent']
                )

    @api.depends('is_proforma', 'state')
    def _compute_can_create_invoice(self):
        """Determinar se pode criar faturas

        Faturas Proforma (is_proforma=True) NÃO podem gerar faturas
        Encomendas normais podem gerar faturas normalmente
        """
        for order in self:
            order.can_create_invoice = not order.is_proforma

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """Limpar localização quando warehouse mudar"""
        if self.warehouse_id and self.location_id:
            # Verificar se a location ainda pertence ao warehouse selecionado
            if self.location_id.warehouse_id != self.warehouse_id:
                self.location_id = False

    @api.onchange('is_proforma')
    def _onchange_is_proforma(self):
        """Alertar sobre mudança de tipo com pagamentos alocados"""
        if self.payment_allocation_ids:
            old_reference = self.amount_total if not self.is_proforma else self.amount_untaxed
            new_reference = self.amount_untaxed if self.is_proforma else self.amount_total

            if abs(old_reference - new_reference) > 0.01:  # Diferença significativa
                return {
                    'warning': {
                        'title': 'Alteração de Tipo de Fatura',
                        'message': (
                            f'Esta encomenda já possui {len(self.payment_allocation_ids)} pagamento(s) alocado(s).\n\n'
                            f'Valor anterior de validação: {old_reference:,.2f} {self.currency_id.symbol}\n'
                            f'Novo valor de validação: {new_reference:,.2f} {self.currency_id.symbol}\n\n'
                            f'Verifique se os pagamentos alocados continuam corretos.'
                        )
                    }
                }

    def action_approve_quotation(self):
        """Aprovar cotação"""
        self.ensure_one()

        if not self.env.user.has_group('mh_sale.group_sale_approver'):
            raise UserError('Não tem permissão para aprovar cotações.')

        if self.amount_total == 0:
            raise UserError('Não é possível aprovar uma cotação sem produtos.')

        if self.state not in ['draft', 'sent']:
            raise UserError('Só é possível aprovar cotações em rascunho ou enviadas.')

        if self.approval_state != 'pending':
            raise UserError('Esta cotação já foi processada.')

        self.write({
            'approval_state': 'approved',
            'approval_date': fields.Datetime.now(),
            'approved_by': self.env.user.id,
            'rejection_reason': False,
            'rejected_by': False,
            'rejection_date': False,
        })

        # Log de atividade
        self.message_post(
            body=f'Cotação aprovada por {self.env.user.name}',
            subject='Cotação Aprovada'
        )

        return True

    def action_reject_quotation(self):
        """Rejeitar cotação - Abre wizard para informar motivo"""
        self.ensure_one()

        if not self.env.user.has_group('mh_sale.group_sale_approver'):
            raise UserError('Não tem permissão para rejeitar cotações.')

        if self.amount_total == 0:
            raise UserError('Não é possível rejeitar uma cotação sem produtos.')

        if self.state not in ['draft', 'sent']:
            raise UserError('Só é possível rejeitar cotações em rascunho ou enviadas.')

        if self.approval_state != 'pending':
            raise UserError('Esta cotação já foi processada.')

        # Abrir wizard para informar motivo da rejeição
        return {
            'name': 'Rejeitar Cotação',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }

    def action_reset_approval(self):
        """Resetar aprovação para pendente"""
        self.ensure_one()

        if not self.env.user.has_group('mh_sale.group_sale_approver'):
            raise UserError('Não tem permissão para resetar aprovações.')

        if self.state not in ['draft', 'sent']:
            raise UserError('Não é possível resetar aprovação de ordens já confirmadas.')

        self.write({
            'approval_state': 'pending',
            'approval_date': False,
            'approved_by': False,
            'rejection_reason': False,
            'rejected_by': False,
            'rejection_date': False,
        })

        self.message_post(
            body=f'Aprovação resetada por {self.env.user.name}',
            subject='Aprovação Resetada'
        )

        return True

    def action_view_payment_allocations(self):
        """Abrir lista de alocações de pagamento"""
        self.ensure_one()
        return {
            'name': f'Alocações de Pagamento - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment.allocation',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id,
                'default_order_partner_id': self.partner_id.id
            }
        }

    def action_view_suggested_payments(self):
        """Ver pagamentos disponíveis para alocar"""
        self.ensure_one()

        # Determinar tipos compatíveis baseado em is_proforma
        if self.is_proforma:
            compatible_types = ['none', 'proforma']
        else:
            compatible_types = ['none', 'normal']

        return {
            'name': f'Pagamentos Disponíveis - {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'view_mode': 'list,kanban,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('amount_remaining', '>', 0),
                ('allocation_type', 'in', compatible_types)
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_create_allocation(self):
        """Abrir wizard para criar nova alocação"""
        self.ensure_one()

        # Verificar se não está confirmada
        if self.state in ['cancel']:
            raise UserError('Não é possível alocar pagamentos em ordens cancelada.')

        if self.invoice_status == 'invoiced':
            raise UserError('Não é possível alocar pagamentos em ordens de vendas faturadas.')

        # Verificar se não está rejeitada
        if self.approval_state == 'rejected':
            raise UserError(
                'Não é possível alocar pagamentos em cotações rejeitadas.\n\n'
                'É necessário resetar a aprovação antes de alocar pagamentos.'
            )

        # Determinar tipos compatíveis baseado em is_proforma
        if self.is_proforma:
            compatible_types = ['none', 'proforma']
        else:
            compatible_types = ['none', 'normal']

        # Buscar pagamentos disponíveis e compatíveis
        available_payments = self.env['proforma.payment'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'posted'),
            ('amount_remaining', '>', 0),
            ('allocation_type', 'in', compatible_types)
        ])

        if not available_payments:
            type_name = "Fatura Pró-Forma" if self.is_proforma else "Encomenda Normal"
            raise UserError(
                f'Não há pagamentos proforma disponíveis para este cliente.\n\n'
                f'Tipo de encomenda: {type_name}\n'
                f'Apenas recibos sem alocações ou já alocados ao mesmo tipo são permitidos.'
            )

        # Se há apenas um pagamento disponível, usá-lo diretamente
        default_payment = available_payments[0] if len(available_payments) == 1 else False

        return {
            'name': 'Alocar Recibo',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment.allocation',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_payment_id': default_payment.id if default_payment else False,
                'default_amount': min(
                    default_payment.amount_remaining if default_payment else self.amount_pending,
                    self.amount_pending
                ),
            }
        }

    def action_deallocate_payments(self):
        """Desalocar todos os pagamentos desta ordem"""
        self.ensure_one()

        if not self.payment_allocation_ids:
            raise UserError('Esta cotação não possui pagamentos alocados.')

        # Verificar se a ordem já foi faturada
        if self.invoice_status == 'invoiced':
            raise UserError(
                'Não é possível desalocar pagamentos em ordens de vendas faturadas.\n\n'
                f'Estado atual: {dict(self._fields["invoice_status"].selection)[self.state]}'
            )

        # Verificar se algum recibo já foi transformado em pagamento definitivo
        paid_allocations = self.payment_allocation_ids.filtered(lambda a: a.payment_id.has_payment)
        if paid_allocations:
            payment_names = ', '.join(paid_allocations.mapped('payment_id.name'))
            raise UserError(
                f'Não é possível desalocar. Os seguintes recibos já foram transformados em pagamento definitivo:\n\n'
                f'{payment_names}'
            )

        # Registrar no log
        allocation_info = '\n'.join([
            f'- {alloc.payment_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
            for alloc in self.payment_allocation_ids
        ])

        # Deletar todas as alocações usando contexto para permitir unlink
        self.payment_allocation_ids.with_context(allow_unlink=True).unlink()

        # Mensagem no chatter
        self.message_post(
            body=f'Pagamentos desalocados por {self.env.user.name}:\n{allocation_info}',
            subject='Pagamentos Desalocados'
        )

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Override para bloquear criação de faturas em Faturas Proforma

        Faturas Proforma (is_proforma=True) NÃO podem gerar faturas.
        Este bloqueio funciona independente de onde a criação é invocada
        (UI, API, XML-RPC, scheduled actions, etc.)
        """
        # Verificar se alguma ordem é proforma
        proforma_orders = self.filtered(lambda o: o.is_proforma)

        if proforma_orders:
            order_names = ', '.join(proforma_orders.mapped('name'))
            raise UserError(
                f'Não é possível criar faturas para Faturas Proforma.\n\n'
                f'Encomendas afetadas: {order_names}\n\n'
                f'Este tipo de encomenda não permite faturação. '
                f'Se necessário, desmarque a opção "Fatura Proforma" primeiro.'
            )

        # Permitir criação de faturas para encomendas normais
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    def _mh_stone_gates_apply(self):
        """As regras de negócio do fluxo Stone Trading (MZ) aplicam-se a esta ordem?

        Ponto de extensão. Por omissão devolve True, para manter intacto o
        comportamento histórico da base (empresa STONE TRADING, MZ): margem,
        dimensões, lotes, validade, workflow de aprovação, recibos proforma e
        verificação de stock na confirmação.

        As empresas onde o fluxo é o standard do Odoo — a EVOSTONE Portugal —
        desligam-nas em `pg_evostone_pt_sale`. Em Portugal a disponibilidade de
        stock e os lotes são tratados na entrega (stock.picking), como no
        standard, e não na confirmação da ordem de venda.
        """
        self.ensure_one()
        return True

    def action_confirm(self):
        """Override do método de confirmação para validar aprovação"""
        # GATE: avisar se houver linhas com margem <= 0 (venda abaixo do
        # custo, ou custo por apurar). Só um aprovador pode forçar.
        if not self.env.context.get('skip_margin_check'):
            for order in self:
                if not order._mh_stone_gates_apply():
                    continue
                neg_lines = order.order_line.filtered(
                    lambda l: not l.display_type and l.product_id
                    and l.margin_amount <= 0 and l.margin_percent <= 0
                )
                if neg_lines:
                    message = _(
                        'As seguintes linhas têm margem ≤ 0 (venda abaixo do '
                        'custo, ou custo por apurar).\n\n'
                        'Reveja a tabela abaixo. Verifique preços e custos; '
                        'ao confirmar, assume vender com margem ≤ 0.'
                    )
                    return {
                        'name': _('Margem não positiva'),
                        'type': 'ir.actions.act_window',
                        'res_model': 'sale.order.margin.wizard',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_order_id': order.id,
                            'default_line_ids': [(6, 0, neg_lines.ids)],
                            'default_confirmation_message': message,
                        },
                    }

        for order in self:
            # Fluxo Stone Trading (MZ). Nas empresas em standard — Portugal —
            # nada disto se aplica: sem conta corrente por parceiro, sem
            # validação de dimensões/lotes, sem workflow de aprovação, sem
            # recibos proforma e sem verificação de stock na confirmação.
            if not order._mh_stone_gates_apply():
                continue

            # CRIAR CONTA DE CLIENTE (se não existir)
            if order.partner_id and hasattr(order.partner_id, 'ensure_partner_account'):
                order.partner_id.ensure_partner_account('customer')

            # VALIDAÇÕES DAS LINHAS (ignoradas em draft, executadas ao confirmar)
            order.order_line._validate_quantity_positive()
            order.order_line._validate_dimensions()
            order.order_line._validate_lot_required()
            order.order_line._validate_price_unit_positive()
            order.order_line._validate_discount_limit()
            
            # 1ª VALIDAÇÃO: Verificar se está expirada
            if order.is_expired:
                raise UserError(
                    _('Não é possível confirmar uma cotação expirada!\n\n'
                      'Cotação: %s\n'
                      'Data de Validade: %s\n'
                      'Dias desde expiração: %s\n\n'
                      'Por favor, renove a validade antes de confirmar.') % (
                          order.name,
                          order.validity_date.strftime('%d/%m/%Y') if order.validity_date else 'N/A',
                          abs(order.days_until_expiry)
                      )
                )

            # 2ª VALIDAÇÃO: Verificar se a cotação tem itens com valor
            if order.amount_total <= 0:
                raise UserError(
                    f"Não é possível confirmar a cotação '{order.name}'.\n\n"
                    f"O valor total da cotação é {order.amount_total:.2f}.\n"
                    f"Adicione produtos com valor antes de confirmar."
                )

            # Verificar se não está rejeitada
            if order.approval_state == 'rejected':
                raise UserError(
                    'Não é possível confirmar uma cotação rejeitada.\n\n'
                    f'Motivo da Rejeição: {order.rejection_reason or "Não especificado"}\n'
                    f'Rejeitado por: {order.rejected_by.name if order.rejected_by else "N/A"}\n\n'
                    'Para prosseguir, é necessário resetar a aprovação.'
                )

            # Verificar se tem aprovação OU está totalmente coberta por pagamentos
            if order.approval_state != 'approved' and not order.is_fully_covered:
                # Determinar valor de referência e label baseado em tipo
                reference_amount = order.amount_untaxed if order.is_proforma else order.amount_total
                amount_label = "SEM impostos" if order.is_proforma else "Total"

                raise UserError(
                    'Para confirmar a ordem de venda, a cotação deve estar aprovada '
                    'OU estar totalmente coberta por pagamentos proforma.\n\n'
                    f'Estado de Aprovação: {dict(self._fields["approval_state"].selection)[order.approval_state]}\n'
                    f'Tipo: {"Fatura Proforma (valida s/ impostos)" if order.is_proforma else "Normal"}\n'
                    f'Valor {amount_label}: {reference_amount:,.2f} {order.currency_id.symbol}\n'
                    f'Valor Coberto: {order.amount_covered:,.2f} {order.currency_id.symbol}\n'
                    f'Valor Pendente: {order.amount_pending:,.2f} {order.currency_id.symbol}'
                )

            # Verificar disponibilidade de stock para cada linha
            # Só verificar se o armazém tem verificação de disponibilidade ativa
            check_availability = order.warehouse_id and not self.env.context.get('skip_stock_check', False)

            lines_without_stock = []
            if check_availability:
                # Agrupar linhas por produto e lote para verificar quantidade total
                product_lot_quantities = {}

                for line in order.order_line:
                    # Só processar produtos armazenáveis com quantidade > 0
                    if (line.product_id
                        and line.product_id.type == 'consu'
                        and line.product_uom_qty > 0):

                        # Criar chave única para produto/lote
                        if line.lot_id:
                            key = ('lot', line.product_id.id, line.lot_id.id)
                        else:
                            key = ('product', line.product_id.id, None)

                        # Acumular quantidades
                        if key not in product_lot_quantities:
                            product_lot_quantities[key] = {
                                'product': line.product_id,
                                'lot': line.lot_id,
                                'total_qty': 0,
                                'uom': line.product_uom,
                                'lines': []
                            }

                        product_lot_quantities[key]['total_qty'] += line.product_uom_qty
                        product_lot_quantities[key]['lines'].append(line)

                # Agora verificar disponibilidade para cada grupo produto/lote
                for key, data in product_lot_quantities.items():
                    available_qty = 0

                    if data['lot']:
                        # Verificar disponibilidade do lote específico
                        domain = [
                            ('lot_id', '=', data['lot'].id),
                            ('location_id.usage', '=', 'internal'),
                        ]
                        if order.warehouse_id:
                            domain.append(('location_id.warehouse_id', '=', order.warehouse_id.id))

                        quants = self.env['stock.quant'].search(domain)
                        available_qty = sum(quants.mapped(lambda q: q.quantity - q.reserved_quantity))

                        if available_qty < data['total_qty']:
                            # Mostrar detalhes das linhas se houver múltiplas
                            if len(data['lines']) > 1:
                                line_numbers = []
                                for line in data['lines']:
                                    # Encontrar o número real da linha na ordem
                                    line_num = order.order_line.ids.index(line.id) + 1
                                    line_numbers.append(f"Linha {line_num}: {line.product_uom_qty:.2f}")
                                line_details = " (" + " + ".join(line_numbers) + ")"
                            else:
                                line_details = ""

                            lines_without_stock.append(
                                _("- %s (Lote %s): Pedido Total %.2f %s%s | Disponível: %.2f %s") % (
                                    data['product'].display_name,
                                    data['lot'].name,
                                    data['total_qty'],
                                    data['uom'].name,
                                    line_details,
                                    available_qty,
                                    data['uom'].name
                                )
                            )
                    else:
                        # Verificar disponibilidade geral do produto
                        product = data['product'].with_context(
                            warehouse=order.warehouse_id.id if order.warehouse_id else False
                        )
                        available_qty = product.virtual_available

                        if available_qty < data['total_qty']:
                            # Mostrar detalhes das linhas se houver múltiplas
                            if len(data['lines']) > 1:
                                line_numbers = []
                                for line in data['lines']:
                                    # Encontrar o número real da linha na ordem
                                    line_num = order.order_line.ids.index(line.id) + 1
                                    line_numbers.append(f"Linha {line_num}: {line.product_uom_qty:.2f}")
                                line_details = " (" + " + ".join(line_numbers) + ")"
                            else:
                                line_details = ""

                            lines_without_stock.append(
                                _("- %s: Pedido Total %.2f %s%s | Disponível: %.2f %s") % (
                                    data['product'].display_name,
                                    data['total_qty'],
                                    data['uom'].name,
                                    line_details,
                                    available_qty,
                                    data['uom'].name
                                )
                            )

            if lines_without_stock:
                raise ValidationError(
                    _("Não é possível confirmar a venda devido à falta de stock:\n\n%s\n\n"
                      "Por favor, ajuste as quantidades ou aguarde reposição de stock.") % (
                        "\n".join(lines_without_stock)
                    )
                )

        # Congelar custo nas linhas no momento da confirmação.
        # Peso é compute store com state guard — congela automaticamente quando
        # state passa para 'sale', sem necessidade de setting explícito.
        for order in self:
            for line in order.order_line:
                if line.product_id:
                    line.cost_at_confirmation = line.purchase_price

        # Chamar super para criar pickings
        result = super().action_confirm()

        # Aplicar location customizada aos pickings criados
        for order in self:
            if order.location_id and order.picking_ids:
                # Filtrar pickings outgoing (delivery) que ainda não foram validados
                delivery_pickings = order.picking_ids.filtered(
                    lambda p: p.picking_type_id.code == 'outgoing' and p.state in ['draft', 'waiting', 'confirmed', 'assigned']
                )

                for picking in delivery_pickings:
                    # Atualizar location no picking
                    picking.location_id = order.location_id

                    # Atualizar location nos moves
                    for move in picking.move_ids:
                        move.location_id = order.location_id

        return result

    can_cancel = fields.Boolean(compute='_compute_can_cancel')
    is_erp_manager = fields.Boolean(compute='_compute_is_erp_manager')

    @api.depends_context('uid')
    def _compute_can_cancel(self):
        is_blocked = self.env.user.has_group('mh_base.group_block_sale_cancel')
        for rec in self:
            rec.can_cancel = not is_blocked

    @api.depends_context('uid')
    def _compute_is_erp_manager(self):
        is_manager = self.env.user.has_group('base.group_erp_manager')
        for rec in self:
            rec.is_erp_manager = is_manager

    def action_cancel(self):
        """Cancelamento inteligente com limpeza automática"""
        if self.env.user.has_group('mh_base.group_block_sale_cancel'):
            raise UserError(_('Não tem permissão para cancelar vendas. Contacte o administrador.'))

        # Se já faturada, só admin pode cancelar
        for order in self:
            if order.invoice_status == 'invoiced' and not self.env.user.has_group('base.group_erp_manager'):
                raise UserError(_('Não é possível cancelar vendas já faturadas. Contacte um administrador.'))
        # Se chamado pelo wizard, pular verificações e ir direto ao cancelamento
        if self.env.context.get('skip_cancel_wizard'):
            return super().action_cancel()

        for order in self:
            actions_needed = []

            # Verificar se tem alocações que precisam ser removidas
            if order.payment_allocation_ids:
                allocation_info = '\n'.join([
                    f'- {alloc.payment_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                    for alloc in order.payment_allocation_ids
                ])
                actions_needed.append(f'Desalocar pagamentos:\n{allocation_info}')

            # Verificar se está aprovada e precisa resetar
            if order.approval_state == 'approved':
                actions_needed.append('Resetar aprovação')

            # Se há ações necessárias, mostrar confirmação
            if actions_needed:
                message = (
                    'Para cancelar esta cotação, as seguintes ações serão executadas automaticamente:\n\n'
                    + '\n\n'.join([f'• {action}' for action in actions_needed]) +
                    '\n\nDeseja continuar com o cancelamento?'
                )

                # Retornar wizard de confirmação
                return {
                    'name': 'Confirmar Cancelamento',
                    'type': 'ir.actions.act_window',
                    'res_model': 'sale.order.cancel.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_order_id': order.id,
                        'default_confirmation_message': message
                    }
                }

        return super().action_cancel()

    def _action_cancel(self):
        """Override do método interno de cancelamento"""
        for order in self:
            # Verificar se tem fatura (exceto canceladas)
            active_invoices = order.invoice_ids.filtered(lambda i: i.state != 'cancel')
            if active_invoices:
                invoice_names = ', '.join(active_invoices.mapped('name'))
                raise UserError(
                    f"Não é possível cancelar a venda '{order.name}'.\n\n"
                    f"Existem faturas associadas:\n{invoice_names}\n\n"
                    f"Não é permitido cancelar vendas com faturas."
                )

            # Verificar se tem picking validado sem devolução
            done_outgoing = order.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_code == 'outgoing'
            )
            done_returns = order.picking_ids.filtered(
                lambda p: p.state == 'done' and p.picking_type_code == 'incoming'
            )
            if done_outgoing and not done_returns:
                picking_names = ', '.join(done_outgoing.mapped('name'))
                raise UserError(
                    f"Não é possível cancelar a venda '{order.name}'.\n\n"
                    f"Existem entregas já validadas:\n{picking_names}\n\n"
                    f"Não é permitido cancelar vendas com entregas concluídas sem devolução."
                )

            # Verificar se tem alocações de pagamento
            if order.payment_allocation_ids:
                allocation_info = '\n'.join([
                    f'- {alloc.payment_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                    for alloc in order.payment_allocation_ids
                ])
                raise UserError(
                    'Não é possível cancelar uma cotação com pagamentos alocados.\n\n'
                    f'Pagamentos alocados:\n{allocation_info}\n\n'
                    'Por favor, desaloque todos os pagamentos antes de cancelar.'
                )

            # Verificar se está aprovada
            if order.approval_state == 'approved':
                raise UserError(
                    'Não é possível cancelar uma cotação aprovada.\n\n'
                    'Por favor, resete a aprovação antes de cancelar.'
                )

        return super()._action_cancel()

    @api.model_create_multi
    def create(self, vals_list):
        """Definir estado de aprovação como pendente ao criar"""
        for vals in vals_list:
            if 'approval_state' not in vals:
                vals['approval_state'] = 'pending'

        # Criar os registos
        orders = super().create(vals_list)

        # Verificar se alguma ordem foi criada como proforma e registar no chatter
        proforma_orders = orders.filtered(lambda o: o.is_proforma)

        for order in proforma_orders:
            order.message_post(
                body=Markup(
                    "🔔 <b>Fatura Proforma Criada</b><br/><br/>"
                    "Esta encomenda foi criada como Fatura Proforma:<br/>"
                    "• Pagamentos validam contra valor <b>SEM impostos</b><br/>"
                    "• <b>NÃO</b> permite criação de faturas<br/>"
                    "• Valor de referência: <b>%s %s</b>"
                ) % (f'{order.amount_untaxed:,.2f}', order.currency_id.symbol),
                subject='Fatura Proforma Criada',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return orders

    def write(self, vals):
        """Override para notificar quando mudar para Fatura Proforma"""
        # Verificar se está a ativar is_proforma e registar ordens afetadas antes do write
        orders_to_notify = self.env['sale.order']
        if vals.get('is_proforma') is True:
            # Filtrar apenas ordens que não eram proforma antes
            orders_to_notify = self.filtered(lambda o: not o.is_proforma)

        # Executar o write
        result = super().write(vals)

        # Registar no chatter após o write (para ter valores atualizados)
        for order in orders_to_notify:
            order.message_post(
                body=Markup(
                    "🔔 <b>Fatura Proforma Ativada</b><br/><br/>"
                    "Esta encomenda foi convertida para Fatura Proforma:<br/>"
                    "• Pagamentos validam contra valor <b>SEM impostos</b><br/>"
                    "• <b>NÃO</b> permite criação de faturas<br/>"
                    "• Valor de referência: <b>%s %s</b>"
                ) % (f'{order.amount_untaxed:,.2f}', order.currency_id.symbol),
                subject='Fatura Proforma Ativada',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return result

    def unlink(self):
        """Impedir exclusão de ordens de venda confirmadas

        Alterado em 07/09/2026, com a guarda equivalente do `mh_base`: rascunho
        ou anulado pode sair, o resto não. Um orçamento em rascunho nunca
        produziu efeito fiscal — sem número de série, sem lançamento, sem
        movimento de stock.

        Esta guarda vem **antes** da do `mh_base` na ordem de resolução de
        métodos, portanto era esta que decidia. Corrigir só a outra não mudava
        nada, e foi o que o ensaio no staging mostrou.

        O `super()` continua a decidir por cima: o Odoo 18 tem
        `_unlink_except_draft_or_cancel` com a mesma condição.
        """
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    'Não é possível eliminar ordens de venda confirmadas.\n\n'
                    'Para anular uma venda, utilize o botão "Cancelar".'
                )
        return super().unlink()

    def action_draft(self):
        """Voltar ordem para rascunho e limpar campos congelados

        Quando a ordem volta para rascunho, os campos congelados na confirmação
        (weight_at_confirmation, cost_at_confirmation) são zerados para permitir
        recálculo na próxima confirmação.
        """
        # Limpar campos congelados para permitir recálculo
        for order in self:
            order.order_line.write({
                'weight_at_confirmation': 0.0,
                'cost_at_confirmation': 0.0,
            })
        return super().action_draft()

    def action_open_stock_wizard(self):
        """Abrir wizard de seleção de estoque disponível

        Este método é chamado por sale.order.line.action_open_stock_wizard()
        """
        self.ensure_one()

        # Criar wizard
        wizard = self.env['stock.available.wizard'].create({
            'sale_order_id': self.id,
            'warehouse_id': self.warehouse_id.id if self.warehouse_id else False,
        })

        # Computar estoque disponível
        wizard._compute_available_stock()

        # Retornar action que abre a lista de linhas com search view
        return {
            'name': 'Selecionar Estoque Disponível',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.available.wizard.line',
            'view_mode': 'list,form',
            'target': 'new',
            'domain': [('wizard_id', '=', wizard.id)],
            'context': {
                'default_wizard_id': wizard.id,
                'search_default_available': 1,
                'search_default_group_lot': 1,
            }
        }

    def action_create_proforma_payment(self):
        """Abrir wizard para criar recibo pró-forma"""
        self.ensure_one()

        if self.is_fully_covered:
            raise UserError('Esta encomenda já está totalmente coberta por pagamentos.')

        if self.state == 'cancel':
            raise UserError('Não é possível criar pagamentos para encomendas canceladas.')

        return {
            'name': 'Criar Recibo Pró-forma',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.create.proforma.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_amount': self.amount_pending,
            }
        }