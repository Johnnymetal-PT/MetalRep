from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _pg_obras_get_obras_receipt_type(self):
        return self.env.ref('pg_obras.picking_type_obras_in', raise_if_not_found=False) or self.env['stock.picking.type']

    def _pg_obras_get_project_distribution(self):
        self.ensure_one()
        if 'project_id' not in self._fields:
            return {}
        project = self.project_id
        if not project or not getattr(project, 'account_id', False):
            return {}
        return {project.account_id.id: 100}

    def _pg_obras_apply_project_defaults(self, force=False):
        """
        force=False:
          - só aplica defaults quando faz sentido e sem pisar manual edits
        """
        for order in self:
            if 'project_id' not in order._fields or not order.project_id:
                continue

            # Só mexer em picking_type se estiver em draft/sent
            if order.state in ('draft', 'sent'):
                picking_type = order._pg_obras_get_obras_receipt_type()
                if picking_type and (force or not order.picking_type_id or order.picking_type_id != picking_type):
                    order.picking_type_id = picking_type

            dist = order._pg_obras_get_project_distribution()
            if not dist:
                continue

            # Header analytic_distribution (se existir) — não pisar se já estiver preenchido
            if 'analytic_distribution' in order._fields:
                if force or not order.analytic_distribution:
                    order.analytic_distribution = dist

            # Linhas (se existir) — não pisar se já estiver preenchido
            if 'analytic_distribution' in order.order_line._fields:
                for line in order.order_line:
                    if force or not line.analytic_distribution:
                        line.analytic_distribution = dist

    @api.onchange('project_id')
    def _onchange_pg_obras_project(self):
        self._pg_obras_apply_project_defaults(force=False)

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._pg_obras_apply_project_defaults(force=True)
        return orders

    def write(self, vals):
        res = super().write(vals)
        if 'project_id' in vals:
            self._pg_obras_apply_project_defaults(force=False)
        return res
