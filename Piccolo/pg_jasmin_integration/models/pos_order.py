"""Acrescenta payment_method_id na pos.order.

Razao: a logica de selecao do documento JASMIN (FS vs FR) precisa de
distinguir numerario vs cartao no POS. O campo standard
``pos.payment.method`` esta nas pos.payment, mas e mais conveniente
para a UI da fatura ter o metodo agregado na propria pos.order.

NOTA: ``create_from_ui`` neste ficheiro NAO esta indentado dentro de
``PosOrder`` (esta como funcao module-level). Resultado: o override
**nao** aplica - o codigo abaixo nao corre. Mantido literal para
nao quebrar import. Para corrigir, mover a funcao para dentro da
classe.
"""
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')


# NOTA: este metodo nao esta dentro da classe PosOrder - definido como
# funcao module-level por engano. Nao tem efeito sobre ``pos.order``.
# Manter ate decidir se queremos efetivamente preencher
# ``payment_method_id`` automaticamente no checkout do POS.
def create_from_ui(self, orders, draft=False):
    for order in orders:
        pos_order_data = order['data']
        payment_method_id = pos_order_data.get('payment_method_id')

        pos_order = self.create({
            **pos_order_data,
            'payment_method_id': payment_method_id,
        })

    return super(PosOrder, self).create_from_ui(orders, draft)
