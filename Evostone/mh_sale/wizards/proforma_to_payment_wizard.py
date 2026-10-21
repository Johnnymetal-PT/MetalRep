from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup


class ProformaToPaymentWizard(models.TransientModel):
    _name = 'proforma.to.payment.wizard'
    _description = 'Wizard para Transformar Recibo Pró-forma em account.payment'

    proforma_payment_id = fields.Many2one(
        'proforma.payment',
        string='Recibo Pró-forma',
        required=True,
        readonly=True
    )

    # Preview fields (readonly)
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='proforma_payment_id.partner_id',
        readonly=True
    )

    amount = fields.Monetary(
        string='Valor',
        related='proforma_payment_id.amount',
        readonly=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='proforma_payment_id.currency_id',
        readonly=True
    )

    proforma_date = fields.Date(
        string='Data Proforma',
        related='proforma_payment_id.date',
        readonly=True
    )

    # User input fields
    journal_id = fields.Many2one(
        'account.journal',
        string='Diário',
        required=True,
        domain="[('type', 'in', ['bank', 'cash'])]",
        help='Selecione o diário de banco ou caixa'
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método de Pagamento',
        required=True,
        domain="[('journal_id', '=', journal_id), ('payment_type', '=', 'inbound')]",
        help='Método de pagamento disponível no diário selecionado'
    )

    payment_date = fields.Date(
        string='Data do Recibo',
        required=True,
        default=fields.Date.context_today,
        help='Data em que o pagamento será registado'
    )

    memo = fields.Text(
        string='Memorando',
        help='Descrição do pagamento. Se vazio, será preenchido automaticamente.'
    )

    # Allocation info
    allocation_info = fields.Html(
        string='Informações de Alocação',
        compute='_compute_allocation_info',
        readonly=True
    )

    @api.depends('proforma_payment_id', 'proforma_payment_id.allocation_ids')
    def _compute_allocation_info(self):
        """Mostrar informações de alocação do proforma"""
        for wizard in self:
            if wizard.proforma_payment_id and wizard.proforma_payment_id.allocation_ids:
                allocations = wizard.proforma_payment_id.allocation_ids
                html = '<ul>'
                for alloc in allocations:
                    html += f'<li><b>{alloc.sale_order_id.name}</b>: {alloc.amount:,.2f} {alloc.currency_id.symbol}</li>'
                html += '</ul>'
                wizard.allocation_info = html
            else:
                wizard.allocation_info = '<p><i>Sem alocações associadas</i></p>'

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Preencher o método de pagamento ao trocar de diário, SEM sobrepor
        um método já válido (ex.: o que vem pré-preenchido do recibo
        pró-forma). Só auto-escolhe o 1.º método quando está vazio ou quando
        o método actual não pertence ao diário seleccionado."""
        if not self.journal_id:
            self.payment_method_line_id = False
            return
        if (not self.payment_method_line_id
                or self.payment_method_line_id.journal_id != self.journal_id):
            payment_methods = self.env['account.payment.method.line'].search([
                ('journal_id', '=', self.journal_id.id),
                ('payment_type', '=', 'inbound')
            ], limit=1)
            self.payment_method_line_id = payment_methods[:1] or False

    @api.model
    def default_get(self, fields_list):
        """Preencher valores default baseado no contexto"""
        res = super().default_get(fields_list)

        # Obter proforma_payment_id do contexto
        proforma_id = self.env.context.get('active_id') or self.env.context.get('default_proforma_payment_id')
        if proforma_id:
            proforma = self.env['proforma.payment'].browse(proforma_id)
            res['proforma_payment_id'] = proforma.id

            # Preencher journal_id e payment_method_line_id do proforma
            if 'journal_id' in fields_list and proforma.journal_id:
                res['journal_id'] = proforma.journal_id.id

            if 'payment_method_line_id' in fields_list and proforma.payment_method_line_id:
                res['payment_method_line_id'] = proforma.payment_method_line_id.id

            # Preencher payment_date com a data do proforma
            if 'payment_date' in fields_list and proforma.date:
                res['payment_date'] = proforma.date
                
            # Usar memo do proforma se existir, senão gerar default
            if 'memo' in fields_list and not res.get('memo'):
                if proforma.memo:
                    res['memo'] = proforma.memo
                else:
                    # Gerar memo default
                    memo = f"Pagamento proforma {proforma.name} do cliente {proforma.partner_id.name}"

                    # Adicionar informações de alocação
                    if proforma.allocation_ids:
                        sales = ', '.join(proforma.allocation_ids.mapped('sale_order_id.name'))
                        memo += f" referente às vendas: {sales}"

                    res['memo'] = memo

        return res

    def action_create_payment(self):
        """Criar account.payment a partir do pagamento proforma"""
        self.ensure_one()

        # Validações
        if self.proforma_payment_id.state != 'posted':
            raise UserError('Apenas pagamentos proforma confirmados podem ser transformados em pagamentos.')

        if self.proforma_payment_id.account_payment_id:
            raise UserError(
                f'Este pagamento proforma já foi transformado no pagamento {self.proforma_payment_id.account_payment_id.name}.'
            )

        # Preparar valores do payment
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.proforma_payment_id.partner_id.id,
            'amount': self.proforma_payment_id.amount,
            'currency_id': self.proforma_payment_id.currency_id.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'memo': self.memo or f"Pagamento proforma {self.proforma_payment_id.name}",
        }

        # Criar payment
        payment = self.env['account.payment'].create(payment_vals)

        # Postar (confirmar) o pagamento automaticamente
        payment.action_post()

        # Linkar payment ao proforma e mudar estado para 'paid'
        self.proforma_payment_id.write({
            'account_payment_id': payment.id,
            'state': 'paid'
        })

        # Mensagem no chatter do proforma
        self.proforma_payment_id.message_post(
            body=Markup(
                "💳 <b>Recibo Contábil Criado</b><br/><br/>"
                "Pagamento: <b>%s</b><br/>"
                "Valor: <b>%s %s</b><br/>"
                "Criado por: <b>%s</b>"
            ) % (
                payment.name,
                f'{payment.amount:,.2f}',
                payment.currency_id.symbol,
                self.env.user.name
            ),
            subject='Pagamento Criado',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        # Mensagem no chatter do payment
        payment.message_post(
            body=Markup(
                "📋 <b>Origem: Pagamento Pró-forma</b><br/><br/>"
                "Criado a partir do recibo pró-forma <b>%s</b><br/>"
                "Cliente: <b>%s</b>"
            ) % (
                self.proforma_payment_id.name,
                self.proforma_payment_id.partner_id.name
            ),
            subject='Origem: Pagamento Proforma',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        # Retornar ação para abrir o payment criado
        return {
            'name': 'Pagamento Criado',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }
