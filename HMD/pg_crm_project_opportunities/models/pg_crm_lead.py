from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pg_project_id = fields.Many2one(
        "project.project",
        string="Project",
        help="Project linked to this lead/opportunity.",
    )

