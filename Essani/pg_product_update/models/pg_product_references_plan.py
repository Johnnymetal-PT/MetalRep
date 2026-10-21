"""Persistent plan model for Drive references-only sync.

The transient wizard works for small batches but Odoo workers kill long
HTTP requests (limit_time_real ~120s on Odoo.sh). This persistent plan
model exists so large batches can be built incrementally by a cron and
survive worker restarts.

See pg_product_references_plan_cron.py / cron_advance_references_plans
for the chunk processor.
"""
import logging
import time

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


_STATE_SELECTION = [
    ("building", "A construir"),
    ("built", "Plano pronto"),
    ("applying", "A aplicar"),
    ("applied", "Aplicado"),
    ("failed", "Falhou"),
]


# Mirror of wizard line status values so the persistent plan can be
# materialised back into the wizard view without surprises.
_LINE_STATUS_SELECTION = [
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


class PgProductReferencesPlan(models.Model):
    _name = "pg.product.references.plan"
    _description = "PG Drive references - persistent plan"
    _order = "id desc"

    name = fields.Char(string="Nome", required=True, default=lambda self: self._default_name())
    state = fields.Selection(_STATE_SELECTION, string="Estado", required=True, default="building", index=True)
    mode = fields.Selection(
        [("only_empty", "So preencher vazias"), ("force", "Sobrescrever existentes")],
        string="Modo",
        default="only_empty",
        required=True,
    )

    # input
    template_ids = fields.Many2many(
        "product.template",
        relation="pg_refs_plan_template_rel",
        column1="plan_id",
        column2="template_id",
        string="Produtos",
        required=True,
    )
    variant_filter_ids = fields.Many2many(
        "product.product",
        relation="pg_refs_plan_variant_filter_rel",
        column1="plan_id",
        column2="variant_id",
        string="Filtro de variantes",
    )

    # work tracking
    pending_template_ids = fields.Many2many(
        "product.template",
        relation="pg_refs_plan_pending_template_rel",
        column1="plan_id",
        column2="template_id",
        string="Pendentes",
    )
    processed_template_ids = fields.Many2many(
        "product.template",
        relation="pg_refs_plan_processed_template_rel",
        column1="plan_id",
        column2="template_id",
        string="Processados",
    )

    line_ids = fields.One2many(
        "pg.product.references.plan.line", "plan_id", string="Linhas",
    )

    # progress / dashboards
    total_count = fields.Integer(compute="_compute_progress", string="Total")
    pending_count = fields.Integer(compute="_compute_progress", string="Pendentes")
    processed_count = fields.Integer(compute="_compute_progress", string="Processados")
    progress_percent = fields.Float(compute="_compute_progress", string="Progresso (%)")
    line_count = fields.Integer(compute="_compute_progress", string="Linhas no plano")

    summary = fields.Text(string="Resumo", readonly=True)
    error_count = fields.Integer(default=0)
    last_error = fields.Text()
    started_at = fields.Datetime(default=fields.Datetime.now, readonly=True)
    finished_at = fields.Datetime(readonly=True)
    applied_at = fields.Datetime(readonly=True)

    @api.model
    def _default_name(self):
        return f"References plan {fields.Datetime.now().strftime('%Y-%m-%d %H:%M')}"

    @api.depends("template_ids", "pending_template_ids", "processed_template_ids", "line_ids")
    def _compute_progress(self):
        for plan in self:
            total = len(plan.template_ids)
            pending = len(plan.pending_template_ids)
            processed = len(plan.processed_template_ids)
            plan.total_count = total
            plan.pending_count = pending
            plan.processed_count = processed
            plan.progress_percent = (processed * 100.0 / total) if total else 0.0
            plan.line_count = len(plan.line_ids)

    def action_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    # ------------------------------------------------------------------
    # Lifecycle: pending = template_ids on create
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.template_ids and not record.pending_template_ids:
                record.write({"pending_template_ids": [(6, 0, record.template_ids.ids)]})
        return records

    # ------------------------------------------------------------------
    # Chunked build (cron-driven)
    # ------------------------------------------------------------------
    def _advance_chunk(self, max_templates=10):
        """Process the next chunk of pending templates and persist plan
        lines. Each call commits at the end so progress survives worker
        restarts. Returns True if more work remains, False if done.
        """
        self.ensure_one()
        if self.state != "building":
            return False
        if not self.pending_template_ids:
            self.write({
                "state": "built",
                "finished_at": fields.Datetime.now(),
            })
            self.env.cr.commit()
            return False

        templates_to_process = self.pending_template_ids[:max_templates]
        template_ids_done = templates_to_process.ids
        variant_filter_ids = self.variant_filter_ids.ids if self.variant_filter_ids else None

        try:
            plan_rows = self.env["product.update"].pg_fetch_references_plan(
                templates_to_process,
                variant_filter_ids=variant_filter_ids,
            )
        except Exception as exc:
            _logger.exception(
                "References plan chunk failed for plan=%s templates=%s",
                self.id, template_ids_done,
            )
            # Move the failing chunk to processed anyway so the plan does
            # not get stuck on the same templates forever; record error
            # context for the user.
            self.write({
                "error_count": (self.error_count or 0) + 1,
                "last_error": (str(exc)[:1500] or "")[:1500],
                "pending_template_ids": [(3, tid) for tid in template_ids_done],
                "processed_template_ids": [(4, tid) for tid in template_ids_done],
            })
            self.env.cr.commit()
            return bool(self.pending_template_ids)

        if plan_rows:
            line_vals = [{
                "plan_id": self.id,
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
            } for row in plan_rows]
            self.env["pg.product.references.plan.line"].create(line_vals)

        self.write({
            "pending_template_ids": [(3, tid) for tid in template_ids_done],
            "processed_template_ids": [(4, tid) for tid in template_ids_done],
        })

        # Mark built if pending is empty now
        if not self.pending_template_ids:
            self.write({
                "state": "built",
                "finished_at": fields.Datetime.now(),
                "summary": self._build_summary_text(),
            })

        self.env.cr.commit()
        return bool(self.pending_template_ids)

    # ------------------------------------------------------------------
    # Apply (synchronous for now, light enough for typical batches)
    # ------------------------------------------------------------------
    def action_refresh(self):
        """Manual refresh; useful while the cron is processing."""
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def _build_summary_text(self, counters=None):
        self.ensure_one()
        from collections import Counter
        c = Counter(line.status for line in self.line_ids)
        status_label = dict(_LINE_STATUS_SELECTION)
        lines = []
        for code, _label in _LINE_STATUS_SELECTION:
            n = c.get(code, 0)
            if n:
                lines.append(f"  {status_label.get(code, code)}: {n}")
        if counters:
            lines.append("")
            lines.append("Aplicacao:")
            lines.append(f"  Escritas: {counters.get('applied', 0)}")
            lines.append(f"  Saltadas (ja correto): {counters.get('skipped_already', 0)}")
            lines.append(f"  Saltadas (modo so-vazias): {counters.get('skipped_mode', 0)}")
            lines.append(f"  Conflitos: {counters.get('conflicts', 0)}")
            lines.append(f"  Erros: {counters.get('errors', 0)}")
        return "\n".join(lines) or "Plano vazio."

    def action_compute_summary(self):
        """Recompute summary text from current line_ids state."""
        for plan in self:
            plan.summary = plan._build_summary_text()

    def action_apply(self):
        """Apply the plan's lines to the variants' default_code.
        Reuses the same logic as the transient wizard via product.update.
        Restricts writes to fill/overwrite rows according to plan.mode.
        """
        self.ensure_one()
        if self.state != "built":
            raise UserError(
                f"So e possivel aplicar planos no estado 'built'. Estado actual: {self.state}."
            )

        self.write({"state": "applying"})
        self.env.cr.commit()

        # Materialise plan dicts from persistent lines so we can reuse
        # product.update.pg_apply_references_plan unchanged.
        plan_rows = [{
            "template_id": line.template_id.id if line.template_id else False,
            "template_name": line.template_name,
            "variant_id": line.variant_id.id if line.variant_id else False,
            "variant_display": line.variant_display,
            "attributes_display": line.attributes_display,
            "current_code": line.current_code or "",
            "proposed_code": line.proposed_code or "",
            "drive_folder_id": line.drive_folder_id or "",
            "status": line.status,
            "message": line.message or "",
        } for line in self.line_ids]

        try:
            counters = self.env["product.update"].pg_apply_references_plan(plan_rows, mode=self.mode)
        except Exception as exc:
            _logger.exception("Plan %s apply failed", self.id)
            self.write({
                "state": "failed",
                "last_error": str(exc)[:2000],
                "finished_at": fields.Datetime.now(),
            })
            return self.action_open()

        # Push line statuses back from the (mutated) plan_rows.
        row_by_variant = {row["variant_id"]: row for row in plan_rows if row.get("variant_id")}
        for line in self.line_ids:
            if not line.variant_id:
                continue
            row = row_by_variant.get(line.variant_id.id)
            if not row:
                continue
            if row.get("status") and row["status"] != line.status:
                line.status = row["status"]
            if row.get("message") and row["message"] != line.message:
                line.message = row["message"]

        self.write({
            "state": "applied",
            "applied_at": fields.Datetime.now(),
            "summary": self._build_summary_text(counters),
        })
        return self.action_open()

    # ------------------------------------------------------------------
    # Cron entrypoint - process all building plans within a time budget
    # ------------------------------------------------------------------
    @api.model
    def cron_advance_references_plans(self, time_budget_s=8 * 60, chunk_size=10):
        """Find plans in 'building' state and advance them in chunks until
        the time budget is consumed. Designed to be scheduled at ~1 minute
        intervals.
        """
        start_ts = time.time()
        plans = self.search([("state", "=", "building")], order="id asc", limit=20)
        if not plans:
            return
        for plan in plans:
            if (time.time() - start_ts) > time_budget_s:
                return
            try:
                # Advance chunks until this plan is done or budget runs out
                while True:
                    if (time.time() - start_ts) > time_budget_s:
                        break
                    has_more = plan._advance_chunk(max_templates=chunk_size)
                    if not has_more:
                        break
                    # Refresh to reload pending_template_ids after the chunk commit
                    plan = self.browse(plan.id)
                    if plan.state != "building":
                        break
            except Exception as exc:
                _logger.exception("Plan %s failed catastrophically", plan.id)
                plan.write({
                    "state": "failed",
                    "last_error": str(exc)[:2000],
                    "finished_at": fields.Datetime.now(),
                })
                self.env.cr.commit()


class PgProductReferencesPlanLine(models.Model):
    _name = "pg.product.references.plan.line"
    _description = "PG Drive references plan line (persistent)"
    _order = "template_id, attributes_display, id"

    plan_id = fields.Many2one(
        "pg.product.references.plan", required=True, ondelete="cascade", index=True,
    )
    template_id = fields.Many2one("product.template", string="Produto", ondelete="set null", index=True)
    template_name = fields.Char(string="Produto (nome)")
    variant_id = fields.Many2one("product.product", string="Variante", ondelete="set null", index=True)
    variant_display = fields.Char(string="Variante (descricao)")
    attributes_display = fields.Char(string="Atributos")
    current_code = fields.Char(string="default_code atual")
    proposed_code = fields.Char(string="default_code Drive")
    drive_folder_id = fields.Char(string="Drive folder ID")
    drive_folder_url = fields.Char(string="Abrir no Drive", compute="_compute_drive_folder_url")
    status = fields.Selection(_LINE_STATUS_SELECTION, string="Estado", index=True)
    message = fields.Char(string="Mensagem")

    @api.depends("drive_folder_id")
    def _compute_drive_folder_url(self):
        for line in self:
            line.drive_folder_url = (
                f"https://drive.google.com/drive/folders/{line.drive_folder_id}"
                if line.drive_folder_id else ""
            )
