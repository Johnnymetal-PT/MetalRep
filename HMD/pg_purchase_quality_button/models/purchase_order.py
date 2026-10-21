# -*- coding: utf-8 -*-

from odoo import _, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    quality_check_count = fields.Integer(
        string='Verificacoes de Qualidade',
        compute='_compute_quality_check_count',
        compute_sudo=True,
        readonly=True,
    )

    def _compute_quality_check_count(self):
        # Defensivo: se o quality_control nao estiver disponivel, contagem 0.
        if 'quality.check' not in self.env:
            for order in self:
                order.quality_check_count = 0
            return
        QualityCheck = self.env['quality.check']
        for order in self:
            picking_ids = order.picking_ids.ids
            order.quality_check_count = (
                QualityCheck.search_count([('picking_id', 'in', picking_ids)])
                if picking_ids else 0
            )

    def action_view_quality_checks(self):
        self.ensure_one()
        picking_ids = self.picking_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Verificacoes de Qualidade'),
            'res_model': 'quality.check',
            'view_mode': 'list,form',
            'domain': [('picking_id', 'in', picking_ids)],
            # Sem criacao a partir deste contexto: as QC nascem dos pontos de controlo.
            'context': {'create': False},
        }
