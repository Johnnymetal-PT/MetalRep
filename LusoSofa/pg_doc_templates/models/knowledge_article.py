from odoo import fields, models


class KnowledgeArticle(models.Model):
    _inherit = "knowledge.article"

    pg_is_template = fields.Boolean(
        string="PG Is Template",
        help="Ative para preencher metadados de template PG neste artigo.",
        default=False,
        copy=False,
    )

    pg_template_code = fields.Char(
        string="PG Template Code",
        help="Codigo unico do template (ex. TPL_EMAIL_CLIENTE). Vazio se o article nao e um template PG.",
        copy=False,
        index=True,
    )
    pg_template_version = fields.Char(
        string="PG Template Version",
        help="Semver MAJOR.MINOR.PATCH (ex. 1.0.0).",
        copy=False,
    )
    pg_template_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("deprecated", "Deprecated"),
        ],
        string="PG Template State",
        copy=False,
        index=True,
    )
    pg_template_body_md = fields.Text(
        string="PG Template Body (Markdown)",
        help=(
            "Campo de fallback (legado). "
            "O pull prioriza o conteudo nativo do artigo Knowledge; "
            "este campo so e usado se o corpo nativo estiver vazio."
        ),
        copy=False,
    )

    _sql_constraints = [
        (
            "pg_template_code_unique",
            "UNIQUE(pg_template_code)",
            "Ja existe um article PG template com este codigo.",
        ),
    ]

    def action_open_pg_template_settings(self):
        self.ensure_one()
        return {
            "name": "PG Template Settings",
            "type": "ir.actions.act_window",
            "res_model": "pg.template.settings.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
                "active_model": "knowledge.article",
            },
        }
