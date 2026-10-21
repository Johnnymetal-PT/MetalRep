# -*- coding: utf-8 -*-
from odoo import _, api, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _mh_tem_valorizacao(self):
        """O movimento gerou camada de valorização?

        É isto que lhe dá peso fiscal: a SVL é o que entra na valorização de
        inventário e no SAF-T. Um movimento sem SVL não deixou rasto contabilístico.

        O campo vem do `stock_account`, que pode não estar instalado — daí a
        verificação em `_fields` em vez de acesso directo. Sem `stock_account`
        não há valorização nenhuma, e a resposta é não.
        """
        self.ensure_one()
        if 'stock_valuation_layer_ids' not in self._fields:
            return False
        return bool(self.stock_valuation_layer_ids)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_or_cancel(self):
        """Bloqueia eliminação de stock.move em done/cancel (gap do Odoo nativo).

        Em Odoo 18, stock.move.line já tem protecção semelhante, mas
        stock.move não — qualquer movimento done/cancel podia ser apagado,
        comprometendo rastreio fiscal e reconstrução histórica de inventário.

        Excepção: moves de scrap em 'cancel' (scrap_id definido) podem ser
        eliminados — o Odoo cria/descarta moves cancelados nos fluxos de scrap
        (ex.: "libertar reserva"), e esses não têm impacto fiscal (sem SVL,
        fora do relatório que usa apenas state='done').

        Excepção alargada em 07/09/2026: qualquer move em 'cancel' **sem camada
        de valorização** pode ser eliminado. Não é uma porta nova — é a mesma
        razão que a excepção de scrap já invocava, escrita como condição em vez
        de como caso particular. O que dá impacto fiscal a um movimento é a
        camada de valorização (SVL) que ele gerou; um movimento anulado que
        nunca gerou nenhuma não aparece no relatório de stock à data, que só lê
        `state='done'`, nem em SAF-T.

        Motivo concreto: a migração de Moçambique para Portugal deixou uma
        entrada de armazém anulada, sem valorização, que o cliente pediu para
        eliminar. Sem esta condição, a única alternativa era despir a guarda —
        que é precisamente o que não se faz a um mecanismo de integridade.
        """
        for move in self:
            if move.state == 'cancel' and move.scrap_id:
                continue
            if move.state == 'cancel' and not move._mh_tem_valorizacao():
                continue
            if move.state in ('done', 'cancel'):
                raise UserError(_(
                    'Não pode eliminar o movimento de stock %(name)s '
                    '(estado: %(state)s).\n\n'
                    'O movimento está congelado para rastreio fiscal e '
                    'reconstrução histórica de inventário.'
                ) % {
                    'name': move.reference or move.name or move.id,
                    'state': move.state,
                })
