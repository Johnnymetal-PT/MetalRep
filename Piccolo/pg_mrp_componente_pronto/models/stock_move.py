# -*- coding: utf-8 -*-
"""Marcar 'Pronto' num componente preenche a Quantidade em falta.

Quando o operador marca um componente da MO como pronto
(``x_studio_pronto`` = True) e ainda ha quantidade por consumir nesse
componente, preenche-se a Quantidade consumida (``quantity``):
- se a WO esta em progresso, com o "Para Consumir" (``should_consume_qty``);
- se a WO ainda esta confirmada (``should_consume_qty`` = 0), com a
  Procura/Demand (``product_uom_qty``), para acertar tambem nesse estado.

Feito por override de ``write`` (server-side) para funcionar em qualquer
contexto: Shop Floor, formulario da MO ou edicao em lista.
"""
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def write(self, vals):
        res = super().write(vals)
        # Só reage quando este write MARCA como pronto (True). O write que
        # fazemos a seguir mexe apenas em `quantity`, logo não re-entra aqui.
        if vals.get('x_studio_pronto'):
            for move in self:
                # Apenas componentes (matéria-prima) de uma MO.
                if not move.raw_material_production_id:
                    continue
                # "Para Consumir" (should_consume_qty) só tem valor com a
                # WO em progresso. Se a WO ainda está confirmada, esse valor
                # é 0, por isso cai-se na Procura/Demand (product_uom_qty)
                # para acertar também nesse estado.
                to_consume = move.should_consume_qty or move.product_uom_qty
                # Só preenche quando há falta; nunca reduz o já consumido.
                if to_consume and to_consume > move.quantity:
                    move.quantity = to_consume
        return res
