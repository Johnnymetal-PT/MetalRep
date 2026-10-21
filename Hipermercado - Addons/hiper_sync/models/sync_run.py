"""Modelo de execucao de sincronizacao ``hiper.sync.run``.

Representa uma corrida (manual ou agendada) que processa um conjunto de
fornecedores. O ciclo de vida tipico e
``queued -> running -> {done | done_warning | failed | cancelled}``, com
suporte para ``paused`` e re-fila quando o crawler remoto ainda nao tem CSV
pronto.

A robustez desta classe assenta em dois mecanismos importantes:

* **Checkpoints com commit manual** -- cada atualizacao significativa de estado
  e gravada em DB com ``self.env.cr.commit()`` para que, em caso de queda do
  worker, o run seja recuperado coerentemente em vez de ficar preso em
  ``running``.
* **Stale recovery** (``_recover_stale_runs``) -- runs em ``running`` sem
  heartbeat ha mais que ``_stale_timeout_minutes`` (ou
  ``_publish_stale_timeout_minutes`` na fase de publicacao) sao
  re-enfileirados ate ``_stale_retry_limit`` vezes antes de serem marcados
  como ``failed``.
"""

import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..services.publisher import HiperPublisher

_logger = logging.getLogger(__name__)


class HiperSyncRun(models.Model):
    """Uma corrida de sincronizacao com fila, progresso e recuperacao automatica."""

    _name = "hiper.sync.run"
    _description = "Hiper Sync Run"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    # Tolerancia de heartbeat antes de considerar o worker preso.
    _stale_timeout_minutes = 30
    # Tolerancia menor na fase de publicacao (escritas mais rapidas).
    _publish_stale_timeout_minutes = 18
    # Numero maximo de re-tentativas antes de marcar o run como ``failed``.
    _stale_retry_limit = 3

    name = fields.Char(required=True)
    state = fields.Selection(
        [
            ("queued", "Queued"),
            ("draft", "Draft"),
            ("running", "Running"),
            ("paused", "Paused"),
            ("done", "Done"),
            ("done_warning", "Done With Warnings"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    started_at = fields.Datetime()
    finished_at = fields.Datetime()
    vendor_ids = fields.Many2many("hiper.sync.vendor", string="Suppliers")
    current_vendor_id = fields.Many2one("hiper.sync.vendor", string="Current Supplier", readonly=True)
    current_item_label = fields.Char(readonly=True)
    current_phase = fields.Selection(
        [
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("fetch", "Fetching"),
            ("merge", "Merging"),
            ("publish", "Publishing"),
            ("paused", "Paused"),
            ("finalize", "Finalizing"),
            ("done", "Done"),
            ("done_warning", "Done With Warnings"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        readonly=True,
    )
    cancel_requested = fields.Boolean(readonly=True)
    pause_requested = fields.Boolean(readonly=True)
    progress_percent = fields.Float(readonly=True)
    progress_note = fields.Char(readonly=True)
    total_vendors = fields.Integer(readonly=True)
    processed_vendors = fields.Integer(readonly=True)
    planned_records = fields.Integer(readonly=True)
    processed_records = fields.Integer(readonly=True)
    duration_seconds = fields.Integer(readonly=True)
    eta_seconds = fields.Integer(readonly=True)
    progress_updated_at = fields.Datetime(readonly=True)
    retry_count = fields.Integer(readonly=True, default=0)
    pg_not_before_at = fields.Datetime(readonly=True, copy=False)
    pg_publish_snapshot_ready = fields.Boolean(readonly=True, copy=False)
    pg_publish_snapshot_total = fields.Integer(readonly=True, copy=False)
    pg_remote_crawler_prime_done = fields.Boolean(readonly=True, copy=False)
    line_ids = fields.One2many("hiper.sync.run.line", "run_id")
    total_records = fields.Integer(compute="_compute_totals", readonly=True)
    selected_records = fields.Integer(compute="_compute_totals", readonly=True)
    published_records = fields.Integer(compute="_compute_totals", readonly=True)
    skipped_records = fields.Integer(compute="_compute_totals", readonly=True)
    error_records = fields.Integer(compute="_compute_totals", readonly=True)
    notes = fields.Text()

    @api.depends("line_ids.state", "line_ids.selected")
    def _compute_totals(self):
        for run in self:
            run.total_records = 0
            run.selected_records = 0
            run.published_records = 0
            run.skipped_records = 0
            run.error_records = 0
        if not self:
            return
        line_model = self.env["hiper.sync.run.line"].sudo()
        state_rows = line_model.read_group(
            domain=[("run_id", "in", self.ids)],
            fields=["run_id"],
            groupby=["run_id", "state"],
            lazy=False,
        )
        selected_rows = line_model.read_group(
            domain=[("run_id", "in", self.ids), ("selected", "=", True)],
            fields=["run_id"],
            groupby=["run_id"],
        )
        totals_by_run: dict[int, int] = {}
        state_by_run: dict[int, dict[str, int]] = {}
        for row in state_rows:
            raw = row.get("run_id")
            run_id = raw[0] if isinstance(raw, (tuple, list)) else raw
            if not run_id:
                continue
            count = row.get("__count", 0) or 0
            totals_by_run[run_id] = totals_by_run.get(run_id, 0) + count
            state_by_run.setdefault(run_id, {})[row.get("state") or ""] = count
        selected_by_run: dict[int, int] = {}
        for row in selected_rows:
            raw = row.get("run_id")
            run_id = raw[0] if isinstance(raw, (tuple, list)) else raw
            if not run_id:
                continue
            selected_by_run[run_id] = row.get("run_id_count", 0) or 0
        for run in self:
            run.total_records = totals_by_run.get(run.id, 0)
            run.selected_records = selected_by_run.get(run.id, 0)
            buckets = state_by_run.get(run.id, {})
            run.published_records = buckets.get("published", 0)
            run.skipped_records = buckets.get("skipped", 0)
            run.error_records = buckets.get("error", 0)

    def set_progress(
        self,
        *,
        phase=False,
        percent=False,
        note=False,
        current_vendor=False,
        processed_vendors=False,
        total_vendors=False,
        planned_records=False,
        processed_records=False,
        eta_seconds=False,
        state=False,
        current_item=False,
    ):
        """Checkpoint atomico de progresso usado pelo publisher.

        Faz ``write`` + ``commit`` para que o front-end (auto-refresh via JS)
        veja sempre o estado mais recente e para que ``_recover_stale_runs``
        possa distinguir entre worker activo (heartbeat fresco) e worker
        bloqueado. Usa ``tracking_disable`` / ``mail_notrack`` para evitar
        encher o chatter com mensagens automatizadas durante o sync.
        """
        for run in self:
            values = {}
            now = fields.Datetime.now()
            if phase is not False:
                values["current_phase"] = phase
            if percent is not False:
                values["progress_percent"] = percent
            if note is not False:
                values["progress_note"] = note
            if current_vendor is not False:
                values["current_vendor_id"] = current_vendor.id if current_vendor else False
            if processed_vendors is not False:
                values["processed_vendors"] = processed_vendors
            if total_vendors is not False:
                values["total_vendors"] = total_vendors
            if planned_records is not False:
                values["planned_records"] = planned_records
            if processed_records is not False:
                values["processed_records"] = processed_records
            if eta_seconds is not False:
                values["eta_seconds"] = eta_seconds
            if state is not False:
                values["state"] = state
            if current_item is not False:
                values["current_item_label"] = current_item or False
            if values:
                values["progress_updated_at"] = now
                if run.started_at:
                    values["duration_seconds"] = max(int((now - run.started_at).total_seconds()), 0)
                run.with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True).write(values)
                run.env.cr.commit()

    @api.model
    def cron_process_queued_runs(self):
        """Cron worker invocado por ``hiper_sync.ir_cron_hiper_sync_queue``.

        Antes de pegar trabalho novo, varre runs em ``running`` sem heartbeat e
        re-enfileira-os ou marca-os como falhados (ver ``_recover_stale_runs``).
        Depois processa apenas UM run da fila por chamada (limit=1) para
        garantir que cada worker pega um lote pequeno e o cron volta a libertar
        a transacao rapidamente. Runs com ``pg_not_before_at`` no futuro sao
        ignorados (uso tipico: re-tentar mais tarde apos crawler remoto).
        """
        self._recover_stale_runs()
        now = fields.Datetime.now()
        queued_runs = self.search(
            [
                ("state", "=", "queued"),
                "|",
                ("pg_not_before_at", "=", False),
                ("pg_not_before_at", "<=", now),
            ],
            order="pg_not_before_at asc, create_date asc, id asc",
            limit=1,
        )
        if queued_runs:
            _logger.info(
                "Hiper queue cron picked %s queued run(s): %s",
                len(queued_runs),
                ", ".join(str(run.id) for run in queued_runs),
            )
        else:
            _logger.info("Hiper queue cron found no queued runs.")
        for run in queued_runs:
            run._process_queued_run()
        return True

    @api.model
    def _trigger_queue_worker(self):
        """Reativa o cron de fila imediatamente (``nextcall = now`` + ``_trigger``).

        Usado depois de enfileirar um run novo, para nao depender do proximo
        ciclo do cron. Tolera o caso em que o cron ja esta em execucao
        (UserError com "currently being executed") porque nesse caso o run
        ficara para o proximo passe -- nao e erro a propagar.
        """
        cron = self.env.ref("hiper_sync.ir_cron_hiper_sync_queue", raise_if_not_found=False)
        if not cron:
            _logger.error("Queue cron record hiper_sync.ir_cron_hiper_sync_queue was not found.")
            return
        try:
            cron.sudo().write(
                {
                    "active": True,
                    "nextcall": fields.Datetime.now(),
                }
            )
            self.env.cr.commit()
        except UserError as exc:
            if "currently being executed" in str(exc):
                _logger.info(
                    "Queue cron id=%s is already executing; leaving queued sync for the next scheduled pass.",
                    cron.id,
                )
                return
            raise
        if hasattr(cron, "_trigger"):
            try:
                cron._trigger()
            except Exception:
                _logger.exception("Failed to trigger queue cron id=%s", cron.id)

    def _enqueue_followup_run(
        self,
        vendors,
        *,
        note=False,
        not_before_at=False,
        remote_crawler_prime_done=True,
    ):
        vendors = vendors.filtered(lambda vendor: vendor.active and vendor.sync_active)
        if not vendors:
            return False
        run = self.create(
            {
                "name": fields.Datetime.now().strftime("SYNC %Y-%m-%d %H:%M:%S"),
                "state": "queued",
                "current_phase": "queued",
                "started_at": fields.Datetime.now(),
                "vendor_ids": [(6, 0, vendors.ids)],
                "total_vendors": len(vendors),
                "progress_percent": 0.0,
                "progress_note": note or "Queued. Waiting for background worker.",
                "notes": note or False,
                "pg_not_before_at": not_before_at,
                "pg_remote_crawler_prime_done": remote_crawler_prime_done,
            }
        )
        self.env.cr.commit()
        self._trigger_queue_worker()
        return run

    @api.model
    def _recover_stale_runs(self):
        """Recupera runs cujo worker bloqueou ou caiu sem heartbeat.

        Politica:
            * ``cancel_requested`` -> marca como ``cancelled``;
            * ``pause_requested``  -> marca como ``paused``;
            * caso contrario, se nao houver outro run em curso para os mesmos
              fornecedores e ainda restarem retries (``< _stale_retry_limit``),
              re-enfileira (incrementando ``retry_count``);
            * sem condicoes para re-tentar -> marca como ``failed`` com a
              razao explicita em ``notes``.
        """
        now = fields.Datetime.now()
        stale_runs = self.search([("state", "=", "running")], order="id asc")
        for run in stale_runs:
            heartbeat = run.progress_updated_at or run.started_at or run.create_date
            timeout_minutes = (
                self._publish_stale_timeout_minutes
                if run.current_phase == "publish"
                else self._stale_timeout_minutes
            )
            stale_cutoff = now - timedelta(minutes=timeout_minutes)
            if not heartbeat or heartbeat >= stale_cutoff:
                continue
            _logger.warning(
                "Recovering stale sync run id=%s retry_count=%s last_heartbeat=%s current_phase=%s timeout_minutes=%s current_item=%s",
                run.id,
                run.retry_count,
                heartbeat,
                run.current_phase,
                timeout_minutes,
                run.current_item_label,
            )
            if run.cancel_requested:
                finished_at = fields.Datetime.now()
                run.write(
                    {
                        "state": "cancelled",
                        "current_phase": "cancelled",
                        "finished_at": finished_at,
                        "progress_percent": 100.0,
                        "progress_note": "Sync cancelled after stale worker timeout.",
                        "notes": (
                            (run.notes or "")
                            + "\nCancelled after stale worker timeout while waiting for a safe checkpoint."
                        ).strip(),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                        "cancel_requested": False,
                        "pause_requested": False,
                        "duration_seconds": max(
                            int((finished_at - run.started_at).total_seconds()),
                            0,
                        )
                        if run.started_at
                        else 0,
                        "progress_updated_at": finished_at,
                    }
                )
                self.env.cr.commit()
                continue
            if run.pause_requested:
                paused_at = fields.Datetime.now()
                run.write(
                    {
                        "state": "paused",
                        "current_phase": "paused",
                        "finished_at": False,
                        "progress_note": "Sync paused after stale worker timeout.",
                        "notes": (
                            (run.notes or "")
                            + "\nPaused after stale worker timeout while waiting for a safe checkpoint."
                        ).strip(),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                        "cancel_requested": False,
                        "pause_requested": False,
                        "duration_seconds": max(
                            int((paused_at - run.started_at).total_seconds()),
                            0,
                        )
                        if run.started_at
                        else 0,
                        "progress_updated_at": paused_at,
                    }
                )
                self.env.cr.commit()
                continue
            overlapping = self.search_count(
                [
                    ("id", "!=", run.id),
                    ("state", "in", ["queued", "running"]),
                    ("vendor_ids", "in", run.vendor_ids.ids),
                ]
            )
            can_resume = bool(not overlapping and run.retry_count < self._stale_retry_limit and run.vendor_ids)
            recovered_at = fields.Datetime.now()
            if can_resume:
                run.write(
                    {
                        "state": "queued",
                        "current_phase": "queued",
                        "finished_at": False,
                        "progress_note": "Recovered after worker timeout. Queued to resume from the last checkpoint.",
                        "notes": (
                            (run.notes or "")
                            + "\nQueued to resume after stale worker timeout (retry %s/%s)."
                            % (run.retry_count + 1, self._stale_retry_limit)
                        ).strip(),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                        "retry_count": run.retry_count + 1,
                        "progress_updated_at": recovered_at,
                    }
                )
            else:
                reason = (
                    "another queued/running sync already exists for the same supplier set"
                    if overlapping
                    else "the stale retry limit was reached"
                )
                run.write(
                    {
                        "state": "failed",
                        "current_phase": "failed",
                        "finished_at": recovered_at,
                        "progress_note": "Recovered as stale run after worker timeout.",
                        "notes": (
                            (run.notes or "")
                            + "\nMarked failed after stale worker timeout because %s."
                            % reason
                        ).strip(),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                        "duration_seconds": max(
                            int((recovered_at - run.started_at).total_seconds()),
                            0,
                        )
                        if run.started_at
                        else 0,
                        "progress_updated_at": recovered_at,
                    }
                )
            self.env.cr.commit()
            if can_resume:
                self._trigger_queue_worker()

    def _process_queued_run(self):
        for run in self:
            run_id = run.id
            started_at = run.started_at
            _logger.info(
                "Starting queued sync run id=%s name=%s state=%s vendors=%s cancel_requested=%s",
                run_id,
                run.name,
                run.state,
                run.vendor_ids.ids,
                run.cancel_requested,
            )
            if run.state == "cancelled" or run.cancel_requested:
                _logger.warning(
                    "Queued sync run id=%s cancelled before start. state=%s cancel_requested=%s",
                    run.id,
                    run.state,
                    run.cancel_requested,
                )
                run.write(
                    {
                        "state": "cancelled",
                        "current_phase": "cancelled",
                        "finished_at": fields.Datetime.now(),
                        "progress_percent": 100.0,
                        "progress_note": run.progress_note or "Sync cancelled before start.",
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                    }
                )
                continue
            if run.state == "paused" or run.pause_requested:
                _logger.warning(
                    "Queued sync run id=%s paused before start. state=%s pause_requested=%s",
                    run.id,
                    run.state,
                    run.pause_requested,
                )
                run.write(
                    {
                        "state": "paused",
                        "current_phase": "paused",
                        "finished_at": False,
                        "progress_note": run.progress_note or "Sync paused before start.",
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                    }
                )
                continue
            try:
                vendors = run.vendor_ids.filtered(lambda vendor: vendor.active and vendor.sync_active)
                _logger.info(
                    "Queued sync run id=%s resolved active vendors=%s",
                    run.id,
                    vendors.ids,
                )
                if not vendors:
                    _logger.error("Queued sync run id=%s has no active suppliers to process.", run.id)
                    run.write(
                        {
                            "state": "failed",
                            "current_phase": "failed",
                            "finished_at": fields.Datetime.now(),
                            "progress_percent": 100.0,
                            "progress_note": "No active suppliers available for this queued run.",
                            "current_item_label": False,
                        }
                    )
                    continue
                run.write(
                    {
                        "state": "running",
                        "current_phase": "draft",
                        "started_at": run.started_at or fields.Datetime.now(),
                        "finished_at": False,
                        "cancel_requested": False,
                        "pause_requested": False,
                        "total_vendors": len(vendors),
                        "progress_percent": run.progress_percent if run.line_ids else 0.0,
                        "progress_note": (
                            "Queued sync resumed from the last checkpoint."
                            if run.line_ids
                            else "Queued sync started."
                        ),
                        "pg_not_before_at": False,
                        "planned_records": run.planned_records if run.line_ids else 0,
                        "processed_records": max(
                            run.processed_records,
                            self.env["hiper.sync.run.line"].search_count(
                                [
                                    ("run_id", "=", run.id),
                                    ("state", "in", ["published", "skipped", "error"]),
                                ]
                            ),
                        ),
                    }
                )
                run.env.cr.commit()
                publisher = HiperPublisher(self.env, run)
                stats = publisher.run(vendors)
                _logger.info(
                    "Queued sync run id=%s publisher finished cancelled=%s paused=%s requeue=%s error_count=%s",
                    run_id,
                    stats.get("cancelled"),
                    stats.get("paused"),
                    stats.get("requeue"),
                    stats.get("error_count"),
                )
                if stats.get("cancelled"):
                    finished_at = fields.Datetime.now()
                    run.write(
                        {
                            "finished_at": finished_at,
                            "notes": stats.get("notes"),
                            "state": "cancelled",
                            "current_phase": "cancelled",
                            "cancel_requested": False,
                            "pause_requested": False,
                            "progress_percent": 100.0,
                            "progress_note": stats.get("notes") or "Sync cancelled.",
                            "eta_seconds": 0,
                            "current_vendor_id": False,
                            "current_item_label": False,
                            "duration_seconds": max(
                                int((finished_at - run.started_at).total_seconds()),
                                0,
                            )
                            if run.started_at
                            else 0,
                            "progress_updated_at": finished_at,
                        }
                    )
                    run.env.cr.commit()
                    continue
                if stats.get("paused"):
                    note_parts = [run.notes or ""]
                    if stats.get("notes"):
                        note_parts.append(stats.get("notes"))
                    paused_at = fields.Datetime.now()
                    run.write(
                        {
                            "notes": "\n".join(part for part in note_parts if part).strip() or False,
                            "state": "paused",
                            "current_phase": "paused",
                            "cancel_requested": False,
                            "pause_requested": False,
                            "finished_at": False,
                            "progress_note": stats.get("notes") or "Sync paused.",
                            "eta_seconds": 0,
                            "current_vendor_id": False,
                            "current_item_label": False,
                            "duration_seconds": max(
                                int((paused_at - run.started_at).total_seconds()),
                                0,
                            )
                            if run.started_at
                            else 0,
                            "progress_updated_at": paused_at,
                        }
                    )
                    run.env.cr.commit()
                    continue
                if stats.get("requeue"):
                    note_parts = [run.notes or ""]
                    if stats.get("notes"):
                        note_parts.append(stats.get("notes"))
                    deferred_vendor_ids = stats.get("deferred_vendor_ids") or []
                    if deferred_vendor_ids:
                        deferred_vendors = self.env["hiper.sync.vendor"].browse(deferred_vendor_ids).filtered(
                            lambda vendor: vendor.active and vendor.sync_active
                        )
                        if deferred_vendors:
                            followup_note = (
                                "Deferred crawler suppliers queued for retry after their CSV feed becomes ready."
                            )
                            followup_run = self._enqueue_followup_run(
                                deferred_vendors,
                                note=followup_note,
                                not_before_at=fields.Datetime.now() + timedelta(minutes=10),
                                remote_crawler_prime_done=True,
                            )
                            _logger.info(
                                "Queued follow-up crawler sync run id=%s from requeued run id=%s deferred_vendors=%s",
                                followup_run.id if followup_run else False,
                                run.id,
                                deferred_vendors.ids,
                            )
                    run.write(
                        {
                            "notes": "\n".join(part for part in note_parts if part).strip() or False,
                            "state": "queued",
                            "current_phase": "queued",
                            "cancel_requested": False,
                            "pause_requested": False,
                            "finished_at": False,
                            "progress_note": run.progress_note
                            or "Queued to continue sync processing in the next worker pass.",
                            "eta_seconds": run.eta_seconds or 0,
                            "current_vendor_id": False,
                            "current_item_label": False,
                            "progress_updated_at": fields.Datetime.now(),
                        }
                    )
                    run.env.cr.commit()
                    self._trigger_queue_worker()
                    continue
                deferred_vendor_ids = stats.get("deferred_vendor_ids") or []
                if deferred_vendor_ids:
                    deferred_vendors = self.env["hiper.sync.vendor"].browse(deferred_vendor_ids).filtered(
                        lambda vendor: vendor.active and vendor.sync_active
                    )
                    if deferred_vendors:
                        followup_note = (
                            "Deferred crawler suppliers queued for retry after their CSV feed becomes ready."
                        )
                        followup_run = self._enqueue_followup_run(
                            deferred_vendors,
                            note=followup_note,
                            not_before_at=fields.Datetime.now() + timedelta(minutes=10),
                            remote_crawler_prime_done=True,
                        )
                        _logger.info(
                            "Queued follow-up crawler sync run id=%s from completed run id=%s deferred_vendors=%s",
                            followup_run.id if followup_run else False,
                            run.id,
                            deferred_vendors.ids,
                        )
                has_publish_errors = bool(stats.get("publish_error_count") or run.error_records)
                has_supplier_warnings = bool(stats.get("supplier_warning_count"))
                run.write(
                    {
                        "finished_at": fields.Datetime.now(),
                        "notes": stats.get("notes"),
                        "state": (
                            "failed"
                            if has_publish_errors
                            else "done_warning" if has_supplier_warnings else "done"
                        ),
                        "current_phase": (
                            "failed"
                            if has_publish_errors
                            else "done_warning" if has_supplier_warnings else "done"
                        ),
                        "progress_percent": 100.0,
                        "cancel_requested": False,
                        "pause_requested": False,
                        "progress_note": (
                            "Sync finished with warnings."
                            if has_supplier_warnings and not has_publish_errors
                            else "Sync finished."
                        ),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                        "duration_seconds": max(
                            int((fields.Datetime.now() - run.started_at).total_seconds()),
                            0,
                        )
                        if run.started_at
                        else 0,
                        "progress_updated_at": fields.Datetime.now(),
                    }
                )
                run.env.cr.commit()
                _logger.info(
                    "Queued sync run id=%s completed with state=%s total_records=%s published=%s errors=%s",
                    run_id,
                    run.state,
                    run.total_records,
                    run.published_records,
                    run.error_records,
                )
            except Exception as exc:
                _logger.exception("Queued sync run id=%s crashed: %s", run_id, exc)
                try:
                    failed_at = fields.Datetime.now()
                    run.write(
                        {
                            "finished_at": failed_at,
                            "notes": str(exc),
                            "state": "failed",
                            "current_phase": "failed",
                            "cancel_requested": False,
                            "pause_requested": False,
                            "progress_percent": 100.0,
                            "progress_note": "Queued sync crashed.",
                            "eta_seconds": 0,
                            "current_vendor_id": False,
                            "current_item_label": False,
                            "duration_seconds": max(
                                int((failed_at - started_at).total_seconds()),
                                0,
                            )
                            if started_at
                            else 0,
                            "progress_updated_at": failed_at,
                        }
                    )
                    run.env.cr.commit()
                except Exception:
                    _logger.exception(
                        "Queued sync run id=%s crashed and failure state could not be persisted.",
                        run_id,
                    )

    def action_process_now(self):
        self.ensure_one()
        if self.state in ("queued", "paused"):
            self.write(
                {
                    "state": "queued",
                    "current_phase": "queued",
                    "pause_requested": False,
                    "cancel_requested": False,
                    "progress_note": (
                        "Paused sync queued to resume in the background."
                        if self.state == "paused"
                        else "Queued. Background worker requested."
                    ),
                    "finished_at": False,
                }
            )
            self.env.cr.commit()
            self._trigger_queue_worker()
        return {
            "type": "ir.actions.act_window",
            "name": "Sync Run",
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_pause_run(self):
        for run in self:
            if run.state not in ("queued", "running"):
                continue
            values = {
                "pause_requested": True,
                "cancel_requested": False,
                "progress_note": "Pause requested. Waiting for a safe checkpoint.",
            }
            if run.state == "queued":
                values.update(
                    {
                        "state": "paused",
                        "current_phase": "paused",
                        "finished_at": False,
                        "progress_note": "Sync paused before start.",
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                    }
                )
            run.write(values)
            run.env.cr.commit()
        return {
            "type": "ir.actions.act_window",
            "name": "Sync Run",
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_cancel_run(self):
        for run in self:
            if run.state in ("done", "done_warning", "failed", "cancelled"):
                continue
            values = {
                "cancel_requested": True,
                "pause_requested": False,
                "progress_note": "Cancellation requested. Waiting for a safe checkpoint.",
            }
            if run.state in ("queued", "paused", "draft"):
                values.update(
                    {
                        "state": "cancelled",
                        "current_phase": "cancelled",
                        "finished_at": fields.Datetime.now(),
                        "progress_percent": 100.0,
                        "progress_note": "Sync cancelled before processing.",
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                    }
                )
            run.write(values)
            run.env.cr.commit()
        return {
            "type": "ir.actions.act_window",
            "name": "Sync Run",
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_force_cancel_run(self):
        for run in self:
            if run.state in ("done", "done_warning", "failed", "cancelled"):
                continue
            finished_at = fields.Datetime.now()
            run.write(
                {
                    "state": "cancelled",
                    "current_phase": "cancelled",
                    "finished_at": finished_at,
                    "progress_percent": 100.0,
                    "progress_note": "Sync force-cancelled by user.",
                    "eta_seconds": 0,
                    "current_vendor_id": False,
                    "current_item_label": False,
                    "cancel_requested": False,
                    "pause_requested": False,
                    "duration_seconds": max(
                        int((finished_at - run.started_at).total_seconds()),
                        0,
                    )
                    if run.started_at
                    else 0,
                    "progress_updated_at": finished_at,
                    "notes": (
                        ((run.notes or "").strip() + "\n") if run.notes else ""
                    )
                    + "Force-cancelled by user from the sync run form.",
                }
            )
            run.env.cr.commit()
        return {
            "type": "ir.actions.act_window",
            "name": "Sync Run",
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }
