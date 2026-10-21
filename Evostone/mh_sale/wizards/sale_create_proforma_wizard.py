from odoo import models, fields, api
from odoo.exceptions import UserError
from markupsafe import Markup


class SaleCreateProformaWizard(models.TransientModel):
    _name = 'sale.create.proforma.wizard'
    _description = 'Wizard para Criar Recibo Pró-forma'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Encomenda',
        required=True,
        readonly=True
    )

    # Dados da encomenda (readonly)
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='sale_order_id.partner_id',
        readonly=True
    )

    order_amount_total = fields.Monetary(
        string='Valor Total',
        related='sale_order_id.amount_total',
        readonly=True
    )

    order_amount_pending = fields.Monetary(
        string='Valor Pendente',
        related='sale_order_id.amount_pending',
        readonly=True
    )

    order_amount_covered = fields.Monetary(
        string='Valor Coberto',
        related='sale_order_id.amount_covered',
        readonly=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moeda',
        related='sale_order_id.currency_id',
        readonly=True
    )

    # Campos configuráveis
    amount = fields.Monetary(
        string='Valor do Pagamento',
        required=True
    )

    date = fields.Date(
        string='Data',
        required=True,
        default=fields.Date.context_today
    )

    memo = fields.Text(
        string='Memo/Descrição'
    )

    # Campos para transformação futura em account.payment
    journal_id = fields.Many2one(
        'account.journal',
        string='Diário',
        required=True,
        domain="[('type', 'in', ['bank', 'cash'])]",
        help='Diário de banco ou caixa para o recibo contábil'
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método de Pagamento (Contábil)',
        required=True,
        domain="[('journal_id', '=', journal_id), ('payment_type', '=', 'inbound')]",
        help='Método de pagamento disponível no diário selecionado'
    )

    @api.model
    def default_get(self, fields_list):
        """Definir valores padrão baseado na encomenda"""
        res = super().default_get(fields_list)

        if 'sale_order_id' in res:
            order = self.env['sale.order'].browse(res['sale_order_id'])
            if order:
                res['amount'] = order.amount_pending

        return res

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

    @api.constrains('amount')
    def _check_amount(self):
        """Validar valor positivo"""
        for wizard in self:
            if wizard.amount <= 0:
                raise UserError('O valor deve ser maior que zero.')

    def action_create_proforma(self):
        """Criar recibo pró-forma e confirmar"""
        self.ensure_one()

        # Validações
        if self.sale_order_id.is_fully_covered:
            raise UserError('Esta encomenda já está totalmente coberta por pagamentos.')

        if self.sale_order_id.state == 'cancel':
            raise UserError('Não é possível criar pagamentos para encomendas canceladas.')

        # Criar proforma.payment
        proforma_vals = {
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'memo': self.memo or f'Pagamento para {self.sale_order_id.name}',
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
        }

        proforma = self.env['proforma.payment'].create(proforma_vals)

        # Confirmar automaticamente
        proforma.action_post()

        # Criar alocação automática para esta encomenda
        allocation_amount = min(self.amount, self.sale_order_id.amount_pending)
        if allocation_amount > 0:
            self.env['proforma.payment.allocation'].create({
                'payment_id': proforma.id,
                'sale_order_id': self.sale_order_id.id,
                'amount': allocation_amount,
            })

        # Mensagem no chatter da encomenda
        self.sale_order_id.message_post(
            body=Markup(
                "💰 <b>Recibo Pró-forma Criado e Alocado</b><br/><br/>"
                "Recibo: <b>%s</b><br/>"
                "Valor alocado: <b>%s %s</b><br/>"
                "Diário: <b>%s</b>"
            ) % (
                proforma.name,
                f'{allocation_amount:,.2f}',
                self.currency_id.symbol,
                self.journal_id.name
            ),
            subject='Recibo Pró-forma Criado e Alocado',
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

        # Retornar para o recibo criado
        return {
            'name': 'Recibo Pró-forma',
            'type': 'ir.actions.act_window',
            'res_model': 'proforma.payment',
            'res_id': proforma.id,
            'view_mode': 'form',
            'target': 'current',
        }
