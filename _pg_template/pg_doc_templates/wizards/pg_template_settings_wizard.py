from odoo import api, fields, models


class PgTemplateSettingsWizard(models.TransientModel):
    _name = "pg.template.settings.wizard"
    _description = "PG Template Settings Wizard"

    article_id = fields.Many2one("knowledge.article", string="Article", required=True)
    pg_is_template = fields.Boolean(string="PG Is Template")
    pg_template_code = fields.Char(string="PG Template Code")
    pg_template_version = fields.Char(string="PG Template Version")
    pg_template_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("deprecated", "Deprecated"),
        ],
        string="PG Template State",
    )
    pg_template_body_md = fields.Text(
        string="PG Template Body (Markdown)",
        help=(
            "Campo de fallback (legado). "
            "O pull prioriza o conteudo nativo do artigo Knowledge; "
            "este campo so e usado se o corpo nativo estiver vazio."
        ),
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        article = self.env["knowledge.article"].browse(self.env.context.get("active_id"))
        if article.exists():
            values.update({
                "article_id": article.id,
                "pg_is_template": article.pg_is_template,
                "pg_template_code": article.pg_template_code,
                "pg_template_version": article.pg_template_version,
                "pg_template_state": article.pg_template_state,
                "pg_template_body_md": article.pg_template_body_md,
            })
        return values

    def action_apply(self):
        self.ensure_one()
        self.article_id.write({
            "pg_is_template": self.pg_is_template,
            "pg_template_code": self.pg_template_code,
            "pg_template_version": self.pg_template_version,
            "pg_template_state": self.pg_template_state,
            "pg_template_body_md": self.pg_template_body_md,
        })
        return {"type": "ir.actions.act_window_close"}
