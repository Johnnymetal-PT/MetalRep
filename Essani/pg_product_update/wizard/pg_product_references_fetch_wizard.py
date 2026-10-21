"""Wizard transiente para rever e aplicar referencias de variantes lidas do Google Drive."""
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


_STATUS_SELECTION = [
    ("fill", "A preencher (vazio)"),
    ("overwrite", "A sobrescrever"),
    ("already_correct", "Ja correto"),
    ("conflict_other_variant", "Conflito: ja usado"),
    ("duplicated_drive_code", "Drive: codigo duplicado"),
    ("no_variant_match", "Drive sem default_code"),
    ("drive_extra_variant", "Drive sem variante Odoo"),
    ("odoo_extra_variant", "Odoo sem variante Drive"),
    ("resolve_error", "Erro a resolver Drive"),
    ("applied", "Aplicado"),
    ("error", "Erro ao escrever"),
]


class PgProductReferencesFetchWizard(models.TransientModel):
    _name = "pg.product.references.fetch.wizard"
    _description = "Pescar referencias de variantes do Google Drive"

    template_ids = fields.Many2many(
        "product.template",
        string="Produtos",
        required=True,
    )
    variant_ids = fields.Many2many(
        "product.product",
        string="Variantes (filtro)",
        help="Quando preenchido, o plano so mostra linhas para estas variantes. "
             "Caso contrario, mostra todas as variantes dos produtos selecionados.",
    )
    mode = fields.Selection(
        [
            ("only_empty", "So preencher vazias"),
            ("force", "Sobrescrever existentes"),
        ],
        string="Modo",
        default="only_empty",
        required=True,
    )
    line_ids = fields.One2many(
        "pg.product.references.fetch.wizard.line",
        "wizard_id",
        string="Plano",
    )
    summary = fields.Text(string="Resumo", readonly=True)
    has_plan = fields.Boolean(string="Plano gerado", default=False)
    has_applied = fields.Boolean(string="Aplicado", default=False)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids") or []
        active_id = self.env.context.get("active_id")
        template_ids = []
        variant_ids = []
        if active_model == "product.template":
            template_ids = active_ids or ([active_id] if active_id else [])
        elif active_model == "product.product":
            variant_ids = active_ids or ([active_id] if active_id else [])
            if variant_ids:
                variants = self.env["product.product"].browse(variant_ids)
                template_ids = variants.mapped("product_tmpl_id").ids
        if template_ids:
            vals["template_ids"] = [(6, 0, template_ids)]
        if variant_ids:
            vals["variant_ids"] = [(6, 0, variant_ids)]
        return vals

    def _set_lines_from_plan(self, plan):
        self.line_ids.unlink()
        line_vals = []
        for row in plan:
            line_vals.append((0, 0, {
                "template_id": row.get("template_id") or False,
                "template_name": row.get("template_name") or "",
                "variant_id": row.get("variant_id") or False,
                "variant_display": row.get("variant_display") or "",
                "attributes_display": row.get("attributes_display") or "",
                "current_code": row.get("current_code") or "",
                "proposed_code": row.get("proposed_code") or "",
                "drive_folder_id": row.get("drive_folder_id") or "",
                "status": row.get("status") or "",
                "message": row.get("message") or "",
            }))
        if line_vals:
            self.write({"line_ids": line_vals})

    def _build_summary(self, plan, counters=None):
        from collections import Counter
        c = Counter(row.get("status") for row in plan or [])
        lines = []
        for code, _label in _STATUS_SELECTION:
            n = c.get(code, 0)
            if n:
                label = dict(_STATUS_SELECTION).get(code, code)
                lines.append(f"  {label}: {n}")
        if counters:
            lines.append("")
            lines.append("Aplicacao:")
            lines.append(f"  Escritas: {counters.get('applied', 0)}")
            lines.append(f"  Saltadas (ja correto): {counters.get('skipped_already', 0)}")
            lines.append(f"  Saltadas (modo so-vazias): {counters.get('skipped_mode', 0)}")
            lines.append(f"  Conflitos: {counters.get('conflicts', 0)}")
            lines.append(f"  Erros: {counters.get('errors', 0)}")
        return "\n".join(lines) or "Plano vazio."

    def action_generate_plan(self):
        self.ensure_one()
        if not self.template_ids:
            raise UserError("Selecionar pelo menos um produto.")
        variant_filter_ids = self.variant_ids.ids if self.variant_ids else None
        plan = self.env["product.update"].pg_fetch_references_plan(
            self.template_ids, variant_filter_ids=variant_filter_ids,
        )
        # Cache plan as lines (for the user to inspect and to be reused by apply)
        self._set_lines_from_plan(plan)
        self.write({
            "summary": self._build_summary(plan),
            "has_plan": True,
            "has_applied": False,
        })
        return self._reopen()

    def action_run_in_background(self):
        """Create a persistent plan record and let the cron build it
        asynchronously. Returns an action that opens the new plan form,
        from where the user can watch progress and apply when ready."""
        self.ensure_one()
        if not self.template_ids:
            raise UserError("Selecionar pelo menos um produto.")
        Plan = self.env["pg.product.references.plan"].sudo()
        plan = Plan.create({
            "name": f"Refs plan {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')} "
                    f"({len(self.template_ids)} produto(s))",
            "mode": self.mode,
            "template_ids": [(6, 0, self.template_ids.ids)],
            "variant_filter_ids": [(6, 0, self.variant_ids.ids)] if self.variant_ids else [(6, 0, [])],
        })
        return {
            "type": "ir.actions.act_window",
            "name": "Plano de references (em background)",
            "res_model": "pg.product.references.plan",
            "res_id": plan.id,
            "view_mode": "form",
            "target": "current",
        }

    def _plan_from_lines(self):
        plan = []
        for line in self.line_ids:
            plan.append({
                "template_id": line.template_id.id if line.template_id else False,
                "template_name": line.template_name,
                "variant_id": line.variant_id.id if line.variant_id else False,
                "variant_display": line.variant_display,
                "attributes_display": line.attributes_display,
                "current_code": line.current_code,
                "proposed_code": line.proposed_code,
                "drive_folder_id": line.drive_folder_id,
                "status": line.status,
                "message": line.message,
            })
        return plan

    def action_apply(self):
        self.ensure_one()
        if not self.has_plan:
            # Generate the plan first, then apply.
            self.action_generate_plan()
        plan = self._plan_from_lines()
        counters = self.env["product.update"].pg_apply_references_plan(plan, mode=self.mode)
        # Persist final statuses back to the lines
        self._set_lines_from_plan(plan)
        self.write({
            "summary": self._build_summary(plan, counters=counters),
            "has_applied": True,
        })
        return self._reopen()

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class PgProductReferencesFetchWizardLine(models.TransientModel):
    _name = "pg.product.references.fetch.wizard.line"
    _description = "Linha do plano de referencias do Drive"
    _order = "template_name, attributes_display, id"

    wizard_id = fields.Many2one(
        "pg.product.references.fetch.wizard",
        required=True,
        ondelete="cascade",
    )
    template_id = fields.Many2one("product.template", string="Produto", ondelete="set null")
    template_name = fields.Char(string="Produto (nome)")
    variant_id = fields.Many2one("product.product", string="Variante", ondelete="set null")
    variant_display = fields.Char(string="Variante (descricao)")
    attributes_display = fields.Char(string="Atributos")
    current_code = fields.Char(string="default_code atual")
    proposed_code = fields.Char(string="default_code Drive")
    drive_folder_id = fields.Char(string="Drive folder ID")
    drive_folder_url = fields.Char(string="Abrir no Drive", compute="_compute_drive_folder_url")
    status = fields.Selection(_STATUS_SELECTION, string="Estado")
    message = fields.Char(string="Mensagem")

    @api.depends("drive_folder_id")
    def _compute_drive_folder_url(self):
        for line in self:
            line.drive_folder_url = (
                f"https://drive.google.com/drive/folders/{line.drive_folder_id}"
                if line.drive_folder_id else ""
            )
