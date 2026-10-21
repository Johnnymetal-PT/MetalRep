# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _pg_default_workorder_definitions(self):
        """Definições de centros de trabalho por defeito aplicáveis a esta OF.

        Inclui as definições da empresa da OF e as globais (sem empresa).
        """
        self.ensure_one()
        return self.env['pg.mrp.default.workorder'].search([
            ('company_id', 'in', [self.company_id.id, False]),
        ], order='sequence, id')

    def _pg_needs_default_workorders(self):
        """True quando a OF não tem qualquer Ordem de Trabalho com centro de trabalho."""
        self.ensure_one()
        return not self.workorder_ids.filtered('workcenter_id')

    def _pg_default_workorder_vals(self):
        """Valores para criar as Ordens de Trabalho por defeito desta OF."""
        self.ensure_one()
        vals_list = []
        for definition in self._pg_default_workorder_definitions():
            vals_list.append({
                'name': definition.name,
                'workcenter_id': definition.workcenter_id.id,
                'production_id': self.id,
                'product_uom_id': self.product_uom_id.id,
                'duration_expected': definition.duration_expected,
                'state': 'pending',
            })
        return vals_list

    def _pg_seed_default_workorders(self):
        """Semeia as Ordens de Trabalho por defeito nas OFs elegíveis.

        Só atua em OFs em estado draft/confirmed que não tenham qualquer centro de
        trabalho definido. Devolve o conjunto de OFs efetivamente semeadas.
        """
        seeded = self.env['mrp.production']
        workorder_vals = []
        for production in self:
            if production.state not in ('draft', 'confirmed'):
                continue
            if not production._pg_needs_default_workorders():
                continue
            vals_list = production._pg_default_workorder_vals()
            if not vals_list:
                continue
            workorder_vals += vals_list
            seeded |= production
        if workorder_vals:
            self.env['mrp.workorder'].create(workorder_vals)
        return seeded

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        productions._pg_seed_default_workorders()
        return productions

    def action_pg_apply_default_workorders(self):
        """Aplica os centros de trabalho por defeito às OFs selecionadas.

        Usado pelo botão do formulário e pela ação em lote na lista. Só toca em OFs
        sem qualquer centro de trabalho definido (em draft/confirmed). Devolve uma
        notificação detalhada com o que foi feito e porque é que o resto foi ignorado.
        """
        if not self.env['pg.mrp.default.workorder'].search_count([]):
            raise UserError(_(
                "Não há centros de trabalho por defeito configurados.\n"
                "Configure em Fabrico → Configuração → Centros de Trabalho por Defeito."))

        editable = self.filtered(lambda p: p.state in ('draft', 'confirmed'))
        without_wc = editable.filtered(lambda p: p._pg_needs_default_workorders())
        seeded = without_wc._pg_seed_default_workorders()

        skipped_state = self - editable
        skipped_has_wc = editable - without_wc
        # Sem defeitos aplicáveis: tipicamente OFs cuja empresa não tem linhas de
        # configuração (ou só existem defaults de outra empresa).
        skipped_no_defaults = without_wc - seeded

        lines = []
        if seeded:
            lines.append(_("✓ %s atualizada(s) com os centros de trabalho por defeito.") % len(seeded))
        if skipped_has_wc:
            lines.append(_("• %s ignorada(s): já têm centros de trabalho.") % len(skipped_has_wc))
        if skipped_state:
            lines.append(_("• %s ignorada(s): não estão em rascunho/confirmada.") % len(skipped_state))
        if skipped_no_defaults:
            companies = ", ".join(sorted(skipped_no_defaults.mapped('company_id.name')))
            lines.append(_("• %s ignorada(s): sem centros de trabalho por defeito "
                           "configurados para a(s) empresa(s): %s. Configure-os (ou "
                           "deixe a empresa em branco para aplicar a todas) em Fabrico → "
                           "Configuração → Centros de Trabalho por Defeito.")
                         % (len(skipped_no_defaults), companies))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Centros de trabalho por defeito"),
                'message': "\n".join(lines),
                'type': 'success' if seeded else 'warning',
                'sticky': bool(skipped_no_defaults),
            },
        }
