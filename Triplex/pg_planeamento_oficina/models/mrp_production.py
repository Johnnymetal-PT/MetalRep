# -*- coding: utf-8 -*-
"""Mantém o painel de planeamento sincronizado quando as ordens de produção mudam.

O campo `mo_ids` da linha de planeamento é calculado e ARMAZENADO (para ser
pesquisável e propagar tempos/estados). Como uma ordem de produção liga-se à linha
por correspondência de `origin` + `product_id` (e não por relação direta), é preciso
recalcular `mo_ids` das linhas afetadas quando se criam/alteram/eliminam ordens.
Ver o __manifest__.py.
"""
from odoo import api, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _pg_affected_planeamento_lines(self):
        Line = self.env['pg.planeamento.line'].sudo()
        lines = Line.browse()
        for mo in self:
            if mo.origin and mo.product_id:
                lines |= Line.search([
                    ('sale_line_id.order_id.name', '=', mo.origin),
                    ('sale_line_id.product_id', '=', mo.product_id.id),
                ])
        return lines

    def _pg_resync_planeamento(self, extra_lines=None):
        lines = self._pg_affected_planeamento_lines()
        if extra_lines:
            lines |= extra_lines
        if lines:
            # Marca mo_ids para recálculo; ao mudar, propaga aos campos dependentes.
            self.env.add_to_compute(lines._fields['mo_ids'], lines)

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        productions._pg_resync_planeamento()
        return productions

    def write(self, vals):
        # Se a origem/produto mudar, as linhas antigas também têm de ser recalculadas.
        before = None
        if {'origin', 'product_id'} & set(vals):
            before = self._pg_affected_planeamento_lines()
        res = super().write(vals)
        if {'origin', 'product_id'} & set(vals):
            self._pg_resync_planeamento(extra_lines=before)
        return res

    def unlink(self):
        lines = self._pg_affected_planeamento_lines()
        res = super().unlink()
        if lines:
            self.env.add_to_compute(lines._fields['mo_ids'], lines)
        return res
