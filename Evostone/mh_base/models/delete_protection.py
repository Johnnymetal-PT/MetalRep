# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Campos que podem ser alterados mesmo em documentos reconciliados
# state é permitido porque as transições de estado são controladas pelos métodos do Odoo (action_post, action_cancel, etc.)
ALLOWED_FIELDS_PAYMENT = {'message_main_attachment_id', 'message_ids', 'activity_ids', 'state'}
ALLOWED_FIELDS_MOVE = {'message_main_attachment_id', 'message_ids', 'activity_ids', 'state'}


class SaleOrderDeleteProtection(models.Model):
    _inherit = 'sale.order'

    def unlink(self):
        # Permitir eliminar em rascunho ou anulado, como já se faz para os
        # pagamentos abaixo e para os lançamentos. Um orçamento em rascunho
        # nunca produziu
        # efeito fiscal: não tem número de série, não tem lançamento, não tem
        # movimento de stock.
        #
        # O `super()` mantém-se a decidir por cima: o Odoo 18 tem
        # `_unlink_except_draft_or_cancel` em `sale.order`, com a mesma
        # condição. Esta guarda deixou de ser mais restritiva do que o núcleo,
        # e passou a dizer o mesmo em português.
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('Não é permitido eliminar Ordens de Venda confirmadas. Cancele o documento em vez de eliminar.'))
        return super().unlink()


class AccountPaymentDeleteProtection(models.Model):
    _inherit = 'account.payment'

    can_cancel = fields.Boolean(compute='_compute_can_cancel')

    @api.depends_context('uid')
    def _compute_can_cancel(self):
        is_blocked = self.env.user.has_group('mh_base.group_block_payment_cancel')
        for rec in self:
            rec.can_cancel = not is_blocked

    def action_cancel(self):
        if self.env.user.has_group('mh_base.group_block_payment_cancel'):
            raise UserError(_('Não tem permissão para cancelar pagamentos. Contacte o administrador.'))
        return super().action_cancel()

    def action_draft(self):
        if self.env.user.has_group('mh_base.group_block_payment_cancel'):
            raise UserError(_('Não tem permissão para reverter pagamentos para rascunho. Contacte o administrador.'))
        return super().action_draft()

    def unlink(self):
        # Permitir eliminar pagamentos em draft (necessário para workflow Odoo)
        for payment in self:
            if payment.state not in ('draft',):
                raise UserError(_('Não é permitido eliminar Pagamentos validados. Cancele o documento em vez de eliminar.'))
        return super().unlink()

    # def write(self, vals):
    #     # Permitir alterações em campos de sistema (mensagens, anexos, etc)
    #     if set(vals.keys()) <= ALLOWED_FIELDS_PAYMENT:
    #         return super().write(vals)

    #     for payment in self:
    #         if payment.is_reconciled or payment.is_matched:
    #             raise UserError(_(
    #                 'Não é permitido alterar o pagamento "%s" porque já está reconciliado com o banco.\n\n'
    #                 'Para fazer alterações, primeiro remova a reconciliação.'
    #             ) % payment.name)
    #     return super().write(vals)


class AccountMoveDeleteProtection(models.Model):
    _inherit = 'account.move'

    can_cancel = fields.Boolean(compute='_compute_can_cancel')

    @api.depends_context('uid')
    def _compute_can_cancel(self):
        is_blocked = self.env.user.has_group('mh_base.group_block_account_cancel')
        for rec in self:
            rec.can_cancel = not is_blocked

    def button_cancel(self):
        if self.env.user.has_group('mh_base.group_block_account_cancel'):
            raise UserError(_('Não tem permissão para cancelar lançamentos contabilísticos. Contacte o administrador.'))
        return super().button_cancel()

    def button_draft(self):
        if self.env.user.has_group('mh_base.group_block_account_cancel'):
            raise UserError(_('Não tem permissão para reverter lançamentos contabilísticos para rascunho. Contacte o administrador.'))
        return super().button_draft()

    # def write(self, vals):
    #     # Permitir alterações em campos de sistema
    #     if set(vals.keys()) <= ALLOWED_FIELDS_MOVE:
    #         return super().write(vals)

    #     for move in self:
    #         # Verificar se alguma linha do movimento está reconciliada
    #         if move.line_ids.filtered(lambda l: l.reconciled):
    #             raise UserError(_(
    #                 'Não é permitido alterar o lançamento "%s" porque possui linhas reconciliadas.\n\n'
    #                 'Para fazer alterações, primeiro remova a reconciliação.'
    #             ) % move.name)
    #     return super().write(vals)

class StockPickingDeleteProtection(models.Model):
    _inherit = 'stock.picking'

    def unlink(self):
        # Rascunho ou anulado pode sair. O que protege o histórico de stock
        # não é esta guarda: é a do `stock.move` no `mh_stock_at_date`, que
        # bloqueia movimentos com camada de valorização, e o `unlink` do
        # próprio Odoo, que apaga os movimentos da operação e recusa os que
        # estejam concluídos.
        for picking in self:
            if picking.state not in ('draft', 'cancel'):
                raise UserError(_('Não é permitido eliminar Transferências de Stock em curso ou concluídas. Cancele o documento em vez de eliminar.'))
        return super().unlink()


class PurchaseOrderDeleteProtection(models.Model):
    _inherit = 'purchase.order'

    def unlink(self):
        # Mesma condição das ordens de venda. O núcleo do Odoo 18 é ainda mais
        # restritivo — o `_unlink_if_cancelled` exige `cancel` — e continua a
        # decidir depois desta guarda: uma ordem de compra em rascunho tem de
        # ser anulada antes de poder ser eliminada.
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(_('Não é permitido eliminar Ordens de Compra confirmadas. Cancele o documento em vez de eliminar.'))
        return super().unlink()
