import json

from odoo import _, fields, models
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval


class ProjectProject(models.Model):
    _inherit = "project.project"

    pg_crm_opportunity_count = fields.Integer(
        string="CRM Opportunities",
        compute="_compute_pg_crm_opportunity_count",
        compute_sudo=True,
        readonly=True,
    )

    def _pg_get_opportunity_ids_per_project(self):
        opportunity_ids_per_project = {project.id: set() for project in self}
        if not self:
            return opportunity_ids_per_project

        # 1) Direct link from CRM opportunity to project (manual user association).
        direct_opportunities = self.env["crm.lead"].sudo().search(
            [("pg_project_id", "in", self.ids), ("type", "=", "opportunity")]
        )
        for opportunity in direct_opportunities:
            if opportunity.pg_project_id:
                opportunity_ids_per_project[opportunity.pg_project_id.id].add(opportunity.id)

        # 2) Fallback link through Sales Orders / Sale Order Lines.
        sale_lines_per_project = self.sudo()._fetch_sale_order_items_per_project_id()
        for project in self:
            sale_lines = sale_lines_per_project.get(project.id, self.env["sale.order.line"]).sudo()
            opportunity_ids = set(sale_lines.order_id.mapped("opportunity_id").ids)
            opportunity_ids_per_project[project.id].update(opportunity_ids)
        return opportunity_ids_per_project

    def _compute_pg_crm_opportunity_count(self):
        if not self.env.user.has_group("sales_team.group_sale_salesman"):
            for project in self:
                project.pg_crm_opportunity_count = 0
            return

        opportunity_ids_per_project = self._pg_get_opportunity_ids_per_project()
        for project in self:
            project.pg_crm_opportunity_count = len(opportunity_ids_per_project.get(project.id, set()))

    def action_pg_view_crm_opportunities(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_opportunities")
        action_context = action.get("context", {})
        if isinstance(action_context, str):
            action_context = safe_eval(
                action_context,
                {
                    "uid": self.env.uid,
                    "active_id": self.id,
                    "active_ids": self.ids,
                    "active_model": self._name,
                },
            )
        action_context = dict(action_context or {})
        action_context["default_type"] = "opportunity"
        action["context"] = action_context

        action_domain = action.get("domain", [])
        if isinstance(action_domain, str):
            action_domain = safe_eval(
                action_domain,
                {
                    "uid": self.env.uid,
                    "active_id": self.id,
                    "active_ids": self.ids,
                    "active_model": self._name,
                },
            )
        if not isinstance(action_domain, (list, tuple)):
            action_domain = []

        opportunity_ids = sorted(self._pg_get_opportunity_ids_per_project().get(self.id, set()))
        if opportunity_ids:
            action["domain"] = expression.AND([list(action_domain), [("id", "in", opportunity_ids)]])
        else:
            action["domain"] = [("id", "=", False)]
        action["name"] = _("CRM Opportunities")

        if len(opportunity_ids) == 1:
            action["views"] = [(self.env.ref("crm.crm_lead_view_form").id, "form")]
            action["res_id"] = opportunity_ids[0]
        return action

    def _get_stat_buttons(self):
        buttons = super()._get_stat_buttons()
        if self.env.user.has_group("sales_team.group_sale_salesman"):
            self_sudo = self.sudo()
            buttons.append(
                {
                    "icon": "briefcase",
                    "text": self.env._("CRM Opportunities"),
                    "number": self_sudo.pg_crm_opportunity_count,
                    "action_type": "object",
                    "action": "action_pg_view_crm_opportunities",
                    "show": True,
                    "sequence": 29,
                    "additional_context": json.dumps({"active_id": self.id}),
                }
            )
        return buttons

