"""Atalho para abrir o wizard de cubicagem a partir do stock.move.

O botao que invoca este metodo e adicionado em Studio na vista do
``stock.move``; aqui apenas se expoe o ``ir.actions.act_window``.

Persistência por Entrega: o wizard já não grava os inputs de packing
no produto (pedido Piccolo). Para que a calculadora reabra com o que o
operador introduziu **para aquela Entrega**, os inputs ficam guardados
neste ``stock.move``, no campo ``pg_cubicagem_inputs`` (JSON).
"""
from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    pg_cubicagem_inputs = fields.Json(
        string="Cubicagem — inputs do wizard",
        help="Dimensões e volumes introduzidos no wizard de cubicagem, "
             "guardados por Entrega (stock.move). São usados para reabrir a "
             "calculadora já preenchida e NÃO são propagados ao produto.",
    )

    def open_cubicagem_wizard(self):
        self.ensure_one()
        return {
            'name': 'Cubicagem Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.cubicagem.wizard',
            'view_mode': 'form',
            'target': 'new',  # modal
            'context': {
                # O wizard precisa de saber qual o move de origem para
                # escrever depois nos campos Studio - passa via default.
                'default_move_id': self.id,
            }
        }
