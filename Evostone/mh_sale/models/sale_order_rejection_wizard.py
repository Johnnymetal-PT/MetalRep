from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from markupsafe import Markup

class SaleOrderRejectionWizard(models.TransientModel):
    _name = 'sale.order.rejection.wizard'
    _description = 'Wizard de Rejeição de Cotação'

    order_id = fields.Many2one(
        'sale.order',
        string='Cotação',
        required=True,
        readonly=True
    )

    rejection_reason = fields.Text(
        string='Motivo da Rejeição',
        required=True,
        help='Por favor, informe o motivo da rejeição da cotação'
    )

    @api.constrains('rejection_reason')
    def _check_rejection_reason(self):
        """Validar que o motivo foi preenchido"""
        for wizard in self:
            if not wizard.rejection_reason or len(wizard.rejection_reason.strip()) < 10:
                raise ValidationError('Por favor, forneça um motivo detalhado para a rejeição (mínimo 10 caracteres).')

    def action_confirm_rejection(self):
        """Confirmar rejeição da cotação"""
        self.ensure_one()

        # BLOQUEIO: não rejeitar se houver recibos pró-forma já convertidos
        # em pagamento definitivo (has_payment=True). Desalocá-los aqui
        # quebraria a ligação a um pagamento real já contabilizado.
        converted = self.order_id.payment_allocation_ids.filtered(
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
                "Não é possível rejeitar a cotação %(order)s.\n\n"
                "Os seguintes recibos pró-forma já foram transformados em "
                "pagamento definitivo e estão alocados a esta cotação:\n%(det)s\n\n"
                "Rejeitar agora desalocaria um pagamento real já contabilizado. "
                "Trate primeiro o pagamento definitivo (reverter/reconciliar) "
                "antes de rejeitar."
            ) % {'order': self.order_id.name, 'det': detalhe})

        # Desalocar todos os pagamentos existentes ANTES de rejeitar
        if self.order_id.payment_allocation_ids:
            # Registrar os pagamentos que serão desalocados
            allocation_info = '\n'.join([
                f'- {alloc.payment_id.name}: {alloc.amount:,.2f} {alloc.currency_id.symbol}'
                for alloc in self.order_id.payment_allocation_ids
            ])

            # Deletar todas as alocações usando contexto para permitir unlink
            self.order_id.payment_allocation_ids.with_context(allow_unlink=True).unlink()

            # Mensagem sobre desalocação
            self.order_id.message_post(
                body=Markup(
                    f'<p><b>Pagamentos automaticamente desalocados devido à rejeição:</b></p>'
                    f'<pre>{allocation_info}</pre>'
                ),
                subject='Pagamentos Desalocados'
            )

        # Atualizar a cotação com o motivo da rejeição
        self.order_id.write({
            'approval_state': 'rejected',
            'rejection_date': fields.Datetime.now(),
            'rejected_by': self.env.user.id,
            'rejection_reason': self.rejection_reason,
            'approval_date': False,
            'approved_by': False,
        })

        # Log de atividade
        self.order_id.message_post(
            body=Markup(
                f'<p><b>Cotação rejeitada por {self.env.user.name}</b></p>'
                f'<p><b>Motivo:</b> {self.rejection_reason}</p>'
            ),
            subject='Cotação Rejeitada'
        )

        return {'type': 'ir.actions.act_window_close'}