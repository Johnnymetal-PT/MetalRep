from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from markupsafe import Markup

class SaleOrderCancelWizard(models.TransientModel):
    _name = 'sale.order.cancel.wizard'
    _description = 'Wizard de Cancelamento de Cotação'

    order_id = fields.Many2one(
        'sale.order',
        string='Cotação',
        required=True,
        readonly=True
    )

    confirmation_message = fields.Text(
        string='Ações que serão executadas',
        readonly=True,
        help='Lista das ações que serão executadas automaticamente'
    )

    def action_confirm_cancel(self):
        """Confirmar cancelamento com limpeza automática"""
        self.ensure_one()

        order = self.order_id

        # 0. BLOQUEIO: não cancelar se houver recibos pró-forma já convertidos
        #    em pagamento definitivo (has_payment=True). Desalocá-los aqui
        #    quebraria a ligação a um pagamento real já contabilizado.
        converted = order.payment_allocation_ids.filtered(
            lambda a: a.payment_id.has_payment
        )
        if converted:
            detalhe = '\n'.join(
                '- %s: %s %s (Cliente: %s)' % (
                    a.payment_id.name,
                    '%.2f' % a.amount,
                    a.currency_id.symbol,
                    a.payment_partner_id.name or '',
                )
                for a in converted
            )
            raise UserError(_(
                "Não é possível cancelar a cotação %(order)s.\n\n"
                "Os seguintes recibos pró-forma já foram transformados em "
                "pagamento definitivo e estão alocados a esta cotação:\n%(det)s\n\n"
                "Cancelar agora desalocaria um pagamento real já contabilizado. "
                "Trate primeiro o pagamento definitivo (reverter/reconciliar) "
                "antes de cancelar."
            ) % {'order': order.name, 'det': detalhe})

        # 1. Desalocar pagamentos se houver
        if order.payment_allocation_ids:
            # Registrar os pagamentos que serão desalocados
            allocation_info = '\n'.join([
                f'- {alloc.payment_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                for alloc in order.payment_allocation_ids
            ])

            # Deletar todas as alocações
            order.payment_allocation_ids.with_context(allow_unlink=True).unlink()

            # Mensagem sobre desalocação
            order.message_post(
                body=Markup(
                    f'<p><b>Pagamentos automaticamente desalocados devido ao cancelamento:</b></p>'
                    f'<pre>{allocation_info}</pre>'
                ),
                subject='Pagamentos Desalocados'
            )

        # 2. Resetar aprovação se estiver aprovada
        if order.approval_state == 'approved':
            order.write({
                'approval_state': 'pending',
                'approval_date': False,
                'approved_by': False,
            })

            order.message_post(
                body=f'Aprovação automaticamente resetada devido ao cancelamento por {self.env.user.name}',
                subject='Aprovação Resetada'
            )

        # 3. Cancelar a cotação
        order.with_context(skip_cancel_wizard=True).action_cancel()

        # Log final
        order.message_post(
            body=Markup(
                f'<p><b>Cotação cancelada por {self.env.user.name}</b></p>'
                f'<p>Cancelamento executado com limpeza automática.</p>'
            ),
            subject='Cotação Cancelada'
        )

        return {'type': 'ir.actions.act_window_close'}