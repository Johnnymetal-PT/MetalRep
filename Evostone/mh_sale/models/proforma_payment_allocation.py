from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from markupsafe import Markup

class ProformaPaymentAllocation(models.Model):
    _name = 'proforma.payment.allocation'
    _description = 'Alocação de Recibo Pró-forma'
    _rec_name = 'display_name'
    _order = 'allocation_date desc'

    display_name = fields.Char(
        string='Nome',
        compute='_compute_display_name'
    )

    payment_id = fields.Many2one(
        'proforma.payment',
        string='Recibo Pró-forma',
        required=True,
        ondelete='cascade',
    )

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Cotação/Venda',
        required=True,
        ondelete='cascade',
        readonly=True
    )

    amount = fields.Monetary(
        string='Valor Alocado',
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        related='payment_id.currency_id',
        readonly=True
    )

    allocation_date = fields.Datetime(
        string='Data de Alocação',
        default=fields.Datetime.now,
        required=True,
        readonly=True
    )

    notes = fields.Text(
        string='Observações'
    )

    # Campos relacionados para facilitar consultas
    payment_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente do Pagamento',
        related='payment_id.partner_id',
        store=True,
        readonly=True
    )

    order_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente da Cotação',
        related='sale_order_id.partner_id',
        store=True,
        readonly=True
    )

    payment_amount = fields.Monetary(
        string='Valor Total do Pagamento',
        related='payment_id.amount',
        readonly=True
    )

    order_amount = fields.Monetary(
        string='Valor Total da Cotação',
        related='sale_order_id.amount_total',
        readonly=True
    )

    payment_state = fields.Selection(
        related='payment_id.state',
        string='Estado do Pagamento',
        readonly=True
    )

    order_state = fields.Selection(
        related='sale_order_id.state',
        string='Estado da Cotação',
        readonly=True
    )

    # Campos computados para validação
    payment_remaining = fields.Monetary(
        string='Restante no Pagamento',
        compute='_compute_payment_remaining',
        help='Valor disponível no pagamento após esta alocação'
    )

    order_remaining = fields.Monetary(
        string='Restante na Cotação',
        compute='_compute_order_remaining',
        help='Valor pendente na cotação após esta alocação'
    )

    available_payment_domain = fields.Char(
        compute='_compute_available_payment_domain',
        help='Domínio dinâmico para o campo payment_id: só recibos do mesmo '
             'cliente, com saldo e do tipo compatível com a ordem (proforma/normal).'
    )

    @api.depends('sale_order_id', 'sale_order_id.partner_id', 'sale_order_id.is_proforma')
    def _compute_available_payment_domain(self):
        """Restringe o picker do recibo aos que NÃO vão falhar a consistência:
        mesmo cliente, confirmado com saldo, e tipo compatível com a ordem."""
        for alloc in self:
            order = alloc.sale_order_id
            partner = order.partner_id
            compatible = ['none', 'proforma'] if order.is_proforma else ['none', 'normal']
            domain = [
                ('partner_id', '=', partner.id if partner else False),
                ('state', '=', 'posted'),
                ('amount_remaining', '>', 0),
                ('allocation_type', 'in', compatible),
            ]
            alloc.available_payment_domain = repr(domain)

    @api.depends('payment_id', 'sale_order_id', 'amount')
    def _compute_display_name(self):
        for allocation in self:
            allocation.display_name = f"{allocation.payment_id.name} → {allocation.sale_order_id.name}: {allocation.amount:.2f}"

    @api.depends('payment_id', 'amount')
    def _compute_payment_remaining(self):
        """Calcular valor restante no pagamento após esta alocação"""
        for allocation in self:
            if allocation.payment_id and allocation.amount:
                # Buscar outras alocações deste pagamento (excluindo a atual)
                domain = [('payment_id', '=', allocation.payment_id.id)]
                if allocation.id:
                    domain.append(('id', '!=', allocation.id))

                other_allocations = self.search(domain)
                total_other = sum(other_allocations.mapped('amount'))

                # Restante = Total do pagamento - outras alocações - esta alocação
                remaining = allocation.payment_id.amount - total_other - allocation.amount
                allocation.payment_remaining = max(0, remaining)
            else:
                allocation.payment_remaining = 0

    @api.depends('sale_order_id', 'sale_order_id.is_proforma',
                 'sale_order_id.amount_total', 'sale_order_id.amount_untaxed', 'amount')
    def _compute_order_remaining(self):
        """Calcular valor restante na cotação após esta alocação

        IMPORTANTE: Se is_proforma=True, valida contra amount_untaxed (SEM impostos)
                    Se is_proforma=False, valida contra amount_total (COM impostos)
        """
        for allocation in self:
            if allocation.sale_order_id and allocation.amount:
                # Buscar outras alocações desta cotação (excluindo a atual)
                domain = [('sale_order_id', '=', allocation.sale_order_id.id)]
                if allocation.id:
                    domain.append(('id', '!=', allocation.id))

                other_allocations = self.search(domain)
                total_other = sum(other_allocations.mapped('amount'))

                # Determinar valor de referência baseado em tipo
                reference_amount = (allocation.sale_order_id.amount_untaxed
                                  if allocation.sale_order_id.is_proforma
                                  else allocation.sale_order_id.amount_total)

                # Restante = Valor referência - outras alocações - esta alocação
                remaining = reference_amount - total_other - allocation.amount
                allocation.order_remaining = max(0, remaining)
            else:
                allocation.order_remaining = 0

    @api.onchange('payment_id', 'sale_order_id')
    def _onchange_payment_order(self):
        """Sugerir valor de alocação baseado no menor valor entre disponível e pendente"""
        if self.payment_id and self.sale_order_id:
            # Valor disponível no pagamento
            payment_available = self.payment_id.amount_remaining

            # Valor pendente na cotação
            order_pending = self.sale_order_id.amount_pending

            # Sugerir o menor valor entre os dois
            if payment_available > 0 and order_pending > 0:
                self.amount = min(payment_available, order_pending)
            else:
                self.amount = 0

    @api.constrains('amount')
    def _check_amount(self):
        """Validar valor alocado"""
        for allocation in self:
            if allocation.amount <= 0:
                raise ValidationError('O valor alocado deve ser maior que zero.')

            # Buscar outras alocações para cálculo correto
            payment_others = self.search([
                ('payment_id', '=', allocation.payment_id.id),
                ('id', '!=', allocation.id if allocation.id else 0)
            ])
            payment_already_allocated = sum(payment_others.mapped('amount'))
            payment_available = allocation.payment_id.amount - payment_already_allocated

            # Usar float_compare para evitar erros de precisão de ponto flutuante
            if float_compare(allocation.amount, payment_available, precision_digits=2) > 0:
                raise ValidationError(
                    f'O valor alocado ({allocation.amount:,.2f}) excede o valor disponível '
                    f'no pagamento ({payment_available:,.2f}).'
                )

            order_others = self.search([
                ('sale_order_id', '=', allocation.sale_order_id.id),
                ('id', '!=', allocation.id if allocation.id else 0)
            ])
            order_already_allocated = sum(order_others.mapped('amount'))

            # Determinar valor de referência baseado em tipo
            reference_amount = (allocation.sale_order_id.amount_untaxed
                              if allocation.sale_order_id.is_proforma
                              else allocation.sale_order_id.amount_total)

            order_pending = reference_amount - order_already_allocated

            amount_type = "SEM impostos" if allocation.sale_order_id.is_proforma else "Total"

            # Usar float_compare para evitar erros de precisão de ponto flutuante
            if float_compare(allocation.amount, order_pending, precision_digits=2) > 0:
                raise ValidationError(
                    f'O valor alocado ({allocation.amount:,.2f}) excede o valor pendente '
                    f'na cotação ({order_pending:,.2f} - {amount_type}).\n\n'
                    f'Tipo de encomenda: {"Fatura Proforma" if allocation.sale_order_id.is_proforma else "Normal"}'
                )

    @api.constrains('payment_id', 'sale_order_id')
    def _check_partners(self):
        """Verificar se pagamento e cotação são do mesmo cliente"""
        for allocation in self:
            if allocation.payment_partner_id != allocation.order_partner_id:
                raise ValidationError(
                    f'O pagamento e a cotação devem ser do mesmo cliente. '
                    f'Pagamento: {allocation.payment_partner_id.name}, '
                    f'Cotação: {allocation.order_partner_id.name}'
                )

    @api.constrains('payment_id')
    def _check_payment_state(self):
        """Verificar se o pagamento está confirmado"""
        for allocation in self:
            if allocation.payment_id.state != 'posted':
                raise ValidationError('Só é possível alocar pagamentos confirmados.')

    @api.constrains('sale_order_id')
    def _check_order_state(self):
        """Verificar se a cotação pode receber alocações"""
        for allocation in self:
            if allocation.sale_order_id.state in ['cancel']:
                raise ValidationError('Não é possível alocar pagamentos em cotações canceladas.')
            
            if allocation.sale_order_id.invoice_status == 'invoiced':
                raise ValidationError('Não é possível alocar pagamentos em ordens de vendas faturadas')

            if allocation.sale_order_id.approval_state == 'rejected':
                raise ValidationError(
                    'Não é possível alocar pagamentos em cotações rejeitadas.\n'
                    'É necessário resetar a aprovação primeiro.'
                )

    @api.constrains('payment_id', 'sale_order_id')
    def _check_proforma_consistency(self):
        """Verificar consistência de tipo entre pagamento e cotação

        Recibos alocados a Fatura Pró-Forma só podem alocar remanescente a outras Faturas Pró-Forma.
        Recibos alocados a Encomenda Normal só podem alocar a outras Encomendas Normais.
        """
        for allocation in self:
            payment = allocation.payment_id
            order = allocation.sale_order_id

            # Buscar outras alocações do mesmo pagamento (excluindo a atual)
            other_allocations = self.search([
                ('payment_id', '=', payment.id),
                ('id', '!=', allocation.id if allocation.id else 0)
            ])

            if not other_allocations:
                # Primeira alocação - pode ser qualquer tipo
                continue

            # Verificar tipo das alocações existentes
            existing_is_proforma = any(alloc.sale_order_id.is_proforma for alloc in other_allocations)
            new_is_proforma = order.is_proforma

            if existing_is_proforma and not new_is_proforma:
                raise ValidationError(
                    'Este pagamento já está alocado a uma Fatura Pró-Forma.\n\n'
                    'Não é possível alocar o remanescente a uma Encomenda Normal.\n'
                    'O remanescente só pode ser alocado a outras Faturas Pró-Forma.'
                )

            if not existing_is_proforma and new_is_proforma:
                raise ValidationError(
                    'Este pagamento já está alocado a uma Encomenda Normal.\n\n'
                    'Não é possível alocar o remanescente a uma Fatura Pró-Forma.\n'
                    'O remanescente só pode ser alocado a outras Encomendas Normais.'
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Registrar criação no chatter"""
        allocations = super().create(vals_list)

        # Mensagem para cada alocação criada
        for allocation in allocations:
            # Mensagem no pagamento
            allocation.payment_id.message_post(
                body=Markup(
                    "💰 <b>Recibo Alocado</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Cotação: <b>%s</b>"
                ) % (
                    f'{allocation.amount:,.2f}',
                    allocation.currency_id.symbol,
                    allocation.sale_order_id.name
                ),
                subject='Alocação de Recibo',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

            # Mensagem na cotação
            allocation.sale_order_id.message_post(
                body=Markup(
                    "💰 <b>Recibo Recebido</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Recibo: <b>%s</b>"
                ) % (
                    f'{allocation.amount:,.2f}',
                    allocation.currency_id.symbol,
                    allocation.payment_id.name
                ),
                subject='Recibo Alocado',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

        return allocations

    def action_deallocate(self):
        """Desalocar este pagamento específico"""
        self.ensure_one()

        if self.sale_order_id.invoice_status == 'invoiced' and not self.env.user.has_group('base.group_erp_manager'):
            raise ValidationError('Não é possível desalocar pagamentos em ordens de vendas faturadas.\n\nContacte um administrador.')

        if self.payment_id.has_payment:
            raise ValidationError(
                f'Não é possível desalocar o recibo "{self.payment_id.name}".\n\n'
                'Este recibo já foi transformado em pagamento definitivo.'
            )

        # Deletar a alocação usando contexto para permitir unlink
        self.with_context(allow_unlink=True).unlink()

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def unlink(self):
        """Registrar remoção no chatter apenas quando permitido via método específico"""
        # Permitir exclusão apenas quando chamado via action_deallocate
        if not self.env.context.get('allow_unlink'):
            raise UserError(
                'Não é possível deletar alocações diretamente.\n\n'
                'Use o botão "Desalocar" para remover alocações adequadamente.'
            )

        # Registrar remoção no chatter
        for allocation in self:
            allocation.payment_id.message_post(
                body=Markup(
                    "🔄 <b>Alocação Removida</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Cotação: <b>%s</b>"
                ) % (
                    f'{allocation.amount:,.2f}',
                    allocation.currency_id.symbol,
                    allocation.sale_order_id.name
                ),
                subject='Alocação Removida',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
            allocation.sale_order_id.message_post(
                body=Markup(
                    "🔄 <b>Alocação Removida</b><br/><br/>"
                    "Valor: <b>%s %s</b><br/>"
                    "Recibo: <b>%s</b>"
                ) % (
                    f'{allocation.amount:,.2f}',
                    allocation.currency_id.symbol,
                    allocation.payment_id.name
                ),
                subject='Alocação Removida',
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
        return super().unlink()