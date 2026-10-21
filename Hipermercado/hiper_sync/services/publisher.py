"""Coracao da fase ``publish`` do Hiper Sync.

``HiperPublisher.run(vendors)`` recebe uma colecao de fornecedores activos e
executa, em ordem: fetch (via adapter), traducao, merge (entre fornecedores),
escrita em ``product.template`` / ``supplierinfo`` / ``hiper.sync.run.line``.

Pontos de atencao para quem mexer aqui:

* O publisher mantem um conjunto de caches em memoria (brand, vendor, barcode,
  reference, fingerprint, ...) para evitar centenas de pesquisas SQL repetidas
  por passe; nao adicionar logica que ignore estas caches sem necessidade.
* O loop de publicacao respeita ``_max_invocation_seconds`` (480 s),
  ``_max_publish_records_per_pass`` (3000) e ``_publish_heartbeat_seconds``
  (60 s) -- estes limites coordenam-se com ``hiper.sync.run._stale_timeout_minutes``
  para nunca passar o threshold de stale do worker.
* Em runs muito longos, o publisher persiste um *snapshot* das linhas
  pendentes (``pg_publish_snapshot_*``) para conseguir retomar de onde ficou
  no proximo passe do worker, em vez de comecar do zero.
"""

import json
import logging
import time

from odoo import fields

from .merger import HiperMerger
from .utils import clean_html_text, fingerprint_for_payload, is_valid_ean13, normalize_text, parse_json, text_to_basic_html

_logger = logging.getLogger(__name__)


class HiperPublisher:
    """Orquestra fetch + merge + publicacao para um conjunto de fornecedores."""

    # Limite duro de tempo por invocacao do worker (480 s = 8 min).
    _max_invocation_seconds = 480
    # Numero maximo de produtos publicados por passe (evita transacoes gigantes).
    _max_publish_records_per_pass = 3000
    # Tamanho do batch usado para persistir snapshots de retoma.
    _snapshot_batch_size = 5000
    # De quantos em quantos registos se atualiza o progresso visivel na UI.
    _publish_progress_interval = 1000
    # Frequencia minima do heartbeat enviado ao ``hiper.sync.run``.
    _publish_heartbeat_seconds = 60

    def __init__(self, env, run):
        self.env = env
        self.sync_run = run
        self.merger = HiperMerger()
        self._brand_cache = {}
        self._vendor_cache = {}
        self._translator_cache = {}
        self._translation_warning_vendors = set()
        self._barcode_cache = {}
        self._reference_cache = {}
        self._fingerprint_cache = {}
        self._name_search_cache = {}
        self._category_target_cache = {}
        self._supplier_partner_cache = {}
        self._pending_image_updates = 0
        params = self.env["ir.config_parameter"].sudo()
        self._disable_out_of_stock = params.get_param("hiper_sync.disable_out_of_stock", "True") == "True"
        self._publish_zero_price = params.get_param("hiper_sync.publish_zero_price", "False") == "True"

    def run(self, vendors):
        supplier_warning_messages = []
        publish_error_messages = []
        deferred_vendor_ids = []
        start_time = time.time()
        total_vendors = len(vendors)
        resume_state = self._load_resume_state()
        resume_count = resume_state["processed_count"]
        checkpoint_percent = self._resume_percent(resume_count, self.sync_run.planned_records)
        pending_lines = self.env["hiper.sync.run.line"]
        total_publish = 0
        _logger.info(
            "HiperPublisher starting run id=%s vendors=%s total_vendors=%s resume_count=%s",
            self.sync_run.id,
            vendors.ids,
            total_vendors,
            resume_count,
        )
        if self.sync_run.pg_publish_snapshot_ready:
            total_publish, pending_lines = self._load_publish_snapshot_state()
            resume_count = max(total_publish - len(pending_lines), 0)
            _logger.info(
                "Run id=%s resuming from stored publish snapshot total_publish=%s pending_rows=%s resume_count=%s",
                self.sync_run.id,
                total_publish,
                len(pending_lines),
                resume_count,
            )
        else:
            all_rows = []
            self._prime_remote_crawler_jobs(vendors, supplier_warning_messages)
            if self._is_cancel_requested():
                return self._cancelled_result("Sync cancelled before fetching suppliers.")
            if self._is_pause_requested():
                return self._paused_result("Sync paused before fetching suppliers.")
            self.sync_run.set_progress(
                phase="fetch",
                state="running",
                percent=checkpoint_percent,
                note=(
                    "Refreshing supplier feeds before resuming publish."
                    if resume_count
                    else "Fetching supplier feeds."
                ),
                processed_vendors=0,
                total_vendors=total_vendors,
                planned_records=max(self.sync_run.planned_records, resume_count),
                processed_records=resume_count,
                eta_seconds=0,
                current_item=False,
            )
            for index, vendor in enumerate(vendors, start=1):
                if self._is_cancel_requested():
                    return self._cancelled_result("Sync cancelled while fetching suppliers.")
                if self._is_pause_requested():
                    return self._paused_result("Sync paused while fetching suppliers.")
                _logger.info(
                    "Run id=%s fetching vendor id=%s code=%s (%s/%s)",
                    self.sync_run.id,
                    vendor.id,
                    vendor.code,
                    index,
                    total_vendors,
                )
                try:
                    vendor.write({"last_sync_status": "running", "last_sync_message": False})
                    diagnostics = vendor._fetch_normalized_rows_with_diagnostics(allow_remote_crawler_defer=True)
                    if diagnostics.get("deferred"):
                        deferred_vendor_ids.append(vendor.id)
                        deferred_message = diagnostics.get("deferred_reason") or (
                            "remote crawler result not ready yet; supplier deferred to a follow-up run"
                        )
                        supplier_warning_messages.append("%s: %s" % (vendor.name, deferred_message))
                        vendor.write(
                            {
                                "last_sync_at": fields.Datetime.now(),
                                "last_sync_status": "running",
                                "last_sync_message": deferred_message,
                            }
                        )
                        _logger.info(
                            "Run id=%s vendor id=%s code=%s deferred awaiting remote crawler result",
                            self.sync_run.id,
                            vendor.id,
                            vendor.code,
                        )
                        continue
                    rows = diagnostics["rows"]
                    _logger.info(
                        "Run id=%s vendor id=%s fetched raw=%s normalized=%s dropped=%s",
                        self.sync_run.id,
                        vendor.id,
                        diagnostics.get("raw_count"),
                        diagnostics.get("normalized_count"),
                        diagnostics.get("dropped_count"),
                    )
                    for row in rows:
                        row["vendor_id"] = vendor.id
                        row["vendor_code"] = vendor.code
                        row["vendor_name"] = vendor.name
                    all_rows.extend(rows)
                    message = vendor._build_diagnostics_message(diagnostics)
                    vendor.write(
                        {
                            "last_sync_at": fields.Datetime.now(),
                            "last_sync_status": "done",
                            "last_sync_message": message,
                        }
                    )
                    fetch_percent = (index / max(total_vendors, 1)) * 45.0
                    eta_seconds = self._estimate_eta(
                        start_time,
                        completed_units=index,
                        total_units=max(total_vendors, 1),
                    )
                    self.sync_run.set_progress(
                        phase="fetch",
                        percent=max(fetch_percent, checkpoint_percent),
                        note=(
                            "Fetched %s of %s suppliers while preparing resume."
                            % (index, total_vendors)
                            if resume_count
                            else "Fetched %s of %s suppliers." % (index, total_vendors)
                        ),
                        current_vendor=vendor,
                        processed_vendors=index,
                        total_vendors=total_vendors,
                        planned_records=len(all_rows),
                        processed_records=resume_count,
                        eta_seconds=eta_seconds,
                        current_item=False,
                    )
                except Exception as exc:
                    _logger.exception(
                        "Run id=%s vendor id=%s code=%s failed during fetch/normalize: %s",
                        self.sync_run.id,
                        vendor.id,
                        vendor.code,
                        exc,
                    )
                    message = "%s: %s" % (vendor.name, exc)
                    supplier_warning_messages.append(message)
                    vendor.write(
                        {
                            "last_sync_at": fields.Datetime.now(),
                            "last_sync_status": "failed",
                            "last_sync_message": str(exc),
                        }
                    )

            if self._is_cancel_requested():
                return self._cancelled_result("Sync cancelled before merge.")
            if self._is_pause_requested():
                return self._paused_result("Sync paused before merge.")
            self.sync_run.set_progress(
                phase="merge",
                percent=max(50.0, checkpoint_percent),
                note=(
                    "Merging supplier offers by product identity before resuming publish."
                    if resume_count
                    else "Merging supplier offers by product identity."
                ),
                current_vendor=False,
                planned_records=len(all_rows),
                processed_records=resume_count,
                eta_seconds=self._estimate_eta(start_time, completed_units=1, total_units=2),
                current_item=False,
            )
            merged_rows = self.merger.merge(all_rows)
            _logger.info(
                "Run id=%s merge finished source_rows=%s merged_rows=%s",
                self.sync_run.id,
                len(all_rows),
                len(merged_rows),
            )
            all_rows = []
            total_publish = len(merged_rows)
            processed_group_keys = resume_state["processed_group_keys"]
            if processed_group_keys:
                merged_rows = [row for row in merged_rows if row["group_key"] not in processed_group_keys]
                skipped_count = total_publish - len(merged_rows)
                if skipped_count != resume_count:
                    _logger.warning(
                        "Run id=%s resume checkpoint mismatch stored=%s matched=%s total_publish=%s",
                        self.sync_run.id,
                        resume_count,
                        skipped_count,
                        total_publish,
                    )
                    resume_count = skipped_count
            if self._is_cancel_requested():
                return self._cancelled_result("Sync cancelled before publish.")
            if self._is_pause_requested():
                return self._paused_result("Sync paused before publish.")
            self.sync_run.set_progress(
                phase="publish",
                percent=self._resume_percent(resume_count, total_publish),
                note="Persisting merged publish snapshot for resumable processing.",
                current_vendor=False,
                planned_records=total_publish,
                processed_records=resume_count,
                eta_seconds=self._estimate_eta(start_time, completed_units=0, total_units=max(len(merged_rows), 1)),
                current_item=False,
            )
            self._store_publish_snapshot(merged_rows, total_publish)
            total_publish, pending_lines = self._load_publish_snapshot_state()

        pending_publish = len(pending_lines)
        if self._is_cancel_requested():
            return self._cancelled_result("Sync cancelled before publish.")
        if self._is_pause_requested():
            return self._paused_result("Sync paused before publish.")
        self.sync_run.set_progress(
            phase="publish",
            percent=self._resume_percent(resume_count, total_publish),
            note=(
                "Resuming publish from checkpoint (%s already processed)." % resume_count
                if resume_count
                else "Publishing merged products."
            ),
            current_vendor=False,
            planned_records=total_publish,
            processed_records=resume_count,
            eta_seconds=self._estimate_eta(start_time, completed_units=0, total_units=max(pending_publish, 1)),
            current_item=False,
        )
        pending_rows = [line.payload() for line in pending_lines]
        _logger.info(
            "Run id=%s preparing publish lookup indexes pending_rows=%s total_publish=%s resume_count=%s",
            self.sync_run.id,
            len(pending_rows),
            total_publish,
            resume_count,
        )
        self._prepare_lookup_indexes(pending_rows)
        _logger.info(
            "Run id=%s publish lookup indexes ready barcode=%s reference=%s fingerprint=%s",
            self.sync_run.id,
            len(self._barcode_cache),
            len(self._reference_cache),
            len(self._fingerprint_cache),
        )
        processed_total = resume_count
        dirty_since_checkpoint = 0
        last_heartbeat = time.time()
        _logger.info(
            "Run id=%s publish starting pending_rows=%s total_publish=%s resume_count=%s",
            self.sync_run.id,
            len(pending_lines),
            total_publish,
            resume_count,
        )
        for line in pending_lines:
            processed_in_attempt = processed_total - resume_count
            if processed_in_attempt and self._should_yield(start_time, processed_in_attempt):
                if dirty_since_checkpoint:
                    self.env.cr.commit()
                self.sync_run.set_progress(
                    phase="publish",
                    percent=self._resume_percent(processed_total, total_publish),
                    note=(
                        "Processed %s of %s merged products. Queued to continue in the next worker pass."
                        % (processed_total, total_publish)
                    ),
                    current_vendor=False,
                    planned_records=total_publish,
                    processed_records=processed_total,
                    eta_seconds=self._estimate_eta(
                        start_time,
                        completed_units=processed_in_attempt,
                        total_units=max(pending_publish, 1),
                    ),
                    current_item=False,
                )
                self._trigger_pending_image_worker()
                return {
                    "error_count": len(supplier_warning_messages) + len(publish_error_messages),
                    "supplier_warning_count": len(supplier_warning_messages),
                    "publish_error_count": len(publish_error_messages),
                    "deferred_vendor_ids": deferred_vendor_ids,
                    "notes": "\n".join(supplier_warning_messages + publish_error_messages)
                    if (supplier_warning_messages or publish_error_messages)
                    else False,
                    "requeue": True,
                }
            if self._is_cancel_requested():
                if dirty_since_checkpoint:
                    self.env.cr.commit()
                return self._cancelled_result("Sync cancelled during publish.")
            if self._is_pause_requested():
                if dirty_since_checkpoint:
                    self.env.cr.commit()
                return self._paused_result("Sync paused during publish.")
            row = line.payload()
            processed_total += 1
            if (
                processed_total == resume_count + 1
                or processed_total % self._publish_progress_interval == 0
                or processed_total == total_publish
            ):
                _logger.info(
                    "Run id=%s publishing row progress=%s/%s ref=%s ean=%s vendor_id=%s",
                    self.sync_run.id,
                    processed_total,
                    total_publish,
                    row.get("reference"),
                    row.get("ean13"),
                    row.get("vendor_id"),
                )
            try:
                self._translate_row_for_publish(row, supplier_warning_messages)
                template, method, state, state_note = self._publish_row(row)
                line_updates = {
                    "state": state,
                    "product_tmpl_id": template.id if template else False,
                    "match_method": method,
                    "publish_note": state_note,
                    "error_message": False,
                }
                payload_json = json.dumps(row)
                if line.payload_json != payload_json:
                    line_updates["payload_json"] = payload_json
                if (
                    line.state != line_updates["state"]
                    or line.product_tmpl_id.id != line_updates["product_tmpl_id"]
                    or line.match_method != line_updates["match_method"]
                    or line.publish_note != line_updates["publish_note"]
                    or bool(line.error_message) != bool(line_updates["error_message"])
                    or "payload_json" in line_updates
                ):
                    line.write(line_updates)
            except Exception as exc:
                publish_error_messages.append("Publish %s: %s" % (row.get("reference") or row.get("ean13"), exc))
                line_updates = {
                    "state": "error",
                    "publish_note": "Publishing failed.",
                    "error_message": str(exc),
                }
                payload_json = json.dumps(row)
                if line.payload_json != payload_json:
                    line_updates["payload_json"] = payload_json
                if (
                    line.state != line_updates["state"]
                    or line.publish_note != line_updates["publish_note"]
                    or line.error_message != line_updates["error_message"]
                    or "payload_json" in line_updates
                ):
                    line.write(line_updates)
                _logger.exception(
                    "Run id=%s failed publishing merged row ref=%s ean=%s vendor_id=%s: %s",
                    self.sync_run.id,
                    row.get("reference"),
                    row.get("ean13"),
                    row.get("vendor_id"),
                    exc,
                )
            dirty_since_checkpoint += 1
            heartbeat_due = (time.time() - last_heartbeat) >= self._publish_heartbeat_seconds
            if (
                processed_total == total_publish
                or processed_total % self._publish_progress_interval == 0
                or heartbeat_due
            ):
                publish_percent = self._resume_percent(processed_total, total_publish)
                attempt_processed = processed_total - resume_count
                eta_seconds = self._estimate_eta(
                    start_time,
                    completed_units=attempt_processed,
                    total_units=max(pending_publish, 1),
                )
                self.sync_run.set_progress(
                    phase="publish",
                    percent=publish_percent,
                    note="Processed %s of %s merged products." % (processed_total, total_publish),
                    current_vendor=self._vendor_from_row(row),
                    planned_records=total_publish,
                    processed_records=processed_total,
                    eta_seconds=eta_seconds,
                    current_item="%s | %s" % (
                        row.get("reference") or row.get("ean13") or "-",
                        row.get("name_pt") or row.get("name") or "-",
                    ),
                )
                dirty_since_checkpoint = 0
                last_heartbeat = time.time()
                _logger.info(
                    "Run id=%s publish progress %s/%s (%.2f%%)",
                    self.sync_run.id,
                    processed_total,
                    total_publish,
                    publish_percent,
                )
        if dirty_since_checkpoint:
            self.env.cr.commit()
        self._trigger_pending_image_worker()
        self.sync_run.set_progress(
            phase="finalize",
            percent=100.0,
            note="Finalizing sync run.",
            current_vendor=False,
            planned_records=total_publish,
            processed_records=total_publish,
            eta_seconds=0,
            current_item=False,
        )
        return {
            "error_count": len(supplier_warning_messages) + len(publish_error_messages),
            "supplier_warning_count": len(supplier_warning_messages),
            "publish_error_count": len(publish_error_messages),
            "deferred_vendor_ids": deferred_vendor_ids,
            "notes": "\n".join(supplier_warning_messages + publish_error_messages)
            if (supplier_warning_messages or publish_error_messages)
            else False,
        }

    def _prime_remote_crawler_jobs(self, vendors, supplier_warning_messages):
        if self.sync_run.pg_remote_crawler_prime_done:
            return
        remote_crawler_vendors = vendors.filtered(lambda vendor: vendor._is_remote_crawler_supplier())
        if not remote_crawler_vendors:
            self.sync_run.write({"pg_remote_crawler_prime_done": True})
            self.env.cr.commit()
            return
        _logger.info(
            "Run id=%s priming remote crawler jobs upfront for vendors=%s",
            self.sync_run.id,
            remote_crawler_vendors.ids,
        )
        for vendor in remote_crawler_vendors:
            try:
                payload = vendor._prime_remote_crawler_job_for_sync()
                _logger.info(
                    "Run id=%s remote crawler primed for vendor id=%s code=%s immediate_csv=%s job_id=%s status=%s",
                    self.sync_run.id,
                    vendor.id,
                    vendor.code,
                    bool(payload.get("csv_url") or vendor.feed_url),
                    vendor.remote_crawler_job_id,
                    vendor.remote_crawler_job_status,
                )
            except Exception as exc:
                supplier_warning_messages.append("%s: remote crawler prime failed: %s" % (vendor.name, exc))
                vendor.write(
                    {
                        "last_sync_at": fields.Datetime.now(),
                        "last_sync_status": "failed",
                        "last_sync_message": str(exc),
                    }
                )
                _logger.exception(
                    "Run id=%s failed priming remote crawler for vendor id=%s code=%s: %s",
                    self.sync_run.id,
                    vendor.id,
                    vendor.code,
                    exc,
                )
        self.sync_run.write({"pg_remote_crawler_prime_done": True})
        self.env.cr.commit()

    def _is_cancel_requested(self):
        run = self.env["hiper.sync.run"].sudo().browse(self.sync_run.id)
        return bool(run.cancel_requested or run.state == "cancelled")

    def _is_pause_requested(self):
        run = self.env["hiper.sync.run"].sudo().browse(self.sync_run.id)
        return bool(getattr(run, "pause_requested", False) or run.state == "paused")

    def _cancelled_result(self, note):
        _logger.warning("Run id=%s cancelled: %s", self.sync_run.id, note)
        self._trigger_pending_image_worker()
        self.sync_run.set_progress(
            phase="cancelled",
            percent=100.0,
            note=note,
            eta_seconds=0,
            current_vendor=False,
            state="cancelled",
            current_item=False,
        )
        return {"error_count": 0, "notes": note, "cancelled": True}

    def _paused_result(self, note):
        _logger.warning("Run id=%s paused: %s", self.sync_run.id, note)
        self._trigger_pending_image_worker()
        self.sync_run.set_progress(
            phase="paused",
            note=note,
            eta_seconds=0,
            current_vendor=False,
            state="paused",
            current_item=False,
        )
        return {"error_count": 0, "notes": note, "paused": True}

    def _load_resume_state(self):
        lines = self.env["hiper.sync.run.line"].sudo().search_read(
            [
                ("run_id", "=", self.sync_run.id),
                ("group_key", "!=", False),
                ("state", "in", ["published", "skipped", "error"]),
            ],
            ["group_key"],
            order="id asc",
        )
        processed_group_keys = []
        seen = set()
        for line in lines:
            group_key = line.get("group_key")
            if not group_key or group_key in seen:
                continue
            seen.add(group_key)
            processed_group_keys.append(group_key)
        return {
            "processed_count": len(processed_group_keys),
            "processed_group_keys": set(processed_group_keys),
        }

    def _load_publish_snapshot_state(self):
        line_model = self.env["hiper.sync.run.line"].sudo()
        pending_lines = line_model.search(
            [("run_id", "=", self.sync_run.id), ("state", "=", "pending")],
            order="id asc",
        )
        total_publish = self.sync_run.pg_publish_snapshot_total or line_model.search_count(
            [("run_id", "=", self.sync_run.id)]
        )
        return total_publish, pending_lines

    def _store_publish_snapshot(self, rows, total_publish):
        if self.sync_run.pg_publish_snapshot_ready:
            return
        line_model = self.env["hiper.sync.run.line"].sudo()
        stale_pending = line_model.search([("run_id", "=", self.sync_run.id), ("state", "=", "pending")])
        if stale_pending:
            for start in range(0, len(stale_pending), self._snapshot_batch_size):
                stale_pending[start : start + self._snapshot_batch_size].unlink()
        self.env.cr.commit()
        for start in range(0, len(rows), self._snapshot_batch_size):
            chunk = rows[start : start + self._snapshot_batch_size]
            line_model.create(
                [
                    self._prepare_run_line_vals(
                        row,
                        state="pending",
                        selected=True,
                    )
                    for row in chunk
                ]
            )
            self.env.cr.commit()
        self.sync_run.write(
            {
                "pg_publish_snapshot_ready": True,
                "pg_publish_snapshot_total": total_publish,
                "planned_records": total_publish,
            }
        )
        self.env.cr.commit()

    def _flush_run_lines(self, line_values):
        if not line_values:
            return []
        self.env["hiper.sync.run.line"].create(line_values)
        self.env.cr.commit()
        return []

    def _estimate_eta(self, start_time, completed_units, total_units):
        if not completed_units or completed_units >= total_units:
            return 0
        elapsed = max(time.time() - start_time, 0.0)
        rate = elapsed / completed_units
        remaining = max(total_units - completed_units, 0)
        return int(rate * remaining)

    def _should_yield(self, start_time, processed_in_attempt):
        elapsed = max(time.time() - start_time, 0.0)
        return bool(
            elapsed >= self._max_invocation_seconds
            or processed_in_attempt >= self._max_publish_records_per_pass
        )

    def _resume_percent(self, completed_units, total_units):
        if not total_units:
            return 0.0
        return min((completed_units / max(total_units, 1)) * 100.0, 100.0)

    def _vendor_from_row(self, row):
        vendor_id = row.get("vendor_id")
        if not vendor_id:
            return False
        if vendor_id not in self._vendor_cache:
            self._vendor_cache[vendor_id] = self.env["hiper.sync.vendor"].browse(vendor_id)
        return self._vendor_cache[vendor_id]

    def _get_translation_components(self, vendor):
        vendor_id = vendor.id
        if vendor_id not in self._translator_cache:
            self._translator_cache[vendor_id] = {
                "translator": vendor._get_translation_service(),
                "warning": vendor._get_translation_warning(),
            }
        return self._translator_cache[vendor_id]

    def _append_translation_warning_once(self, vendor, warning, supplier_warning_messages):
        if not warning:
            return
        if vendor.id in self._translation_warning_vendors:
            return
        self._translation_warning_vendors.add(vendor.id)
        supplier_warning_messages.append("%s: %s" % (vendor.name, warning))

    def _translate_row_for_publish(self, row, supplier_warning_messages):
        vendor = self._vendor_from_row(row)
        if not vendor or not vendor.translate_enabled:
            return
        can_publish, _state_note = self._compute_publish_decision(vendor, row)
        if not can_publish:
            _logger.debug(
                "Translation skipped vendor=%s ref=%s ean=%s reason=publish_decision",
                vendor.code,
                row.get("reference"),
                row.get("ean13"),
            )
            return
        components = self._get_translation_components(vendor)
        warning = components["warning"]
        translator = components["translator"]
        if warning:
            self._append_translation_warning_once(vendor, warning, supplier_warning_messages)
            return
        if not translator:
            _logger.warning(
                "Translation skipped vendor=%s ref=%s ean=%s reason=no_translator",
                vendor.code,
                row.get("reference"),
                row.get("ean13"),
            )
            return
        vendor._translate_row_text_fields([row], translator)
        runtime_warning = translator.get_warning()
        if runtime_warning:
            self._append_translation_warning_once(vendor, runtime_warning, supplier_warning_messages)

    def _prepare_run_line_vals(
        self,
        row,
        state,
        selected,
        product_tmpl_id=False,
        match_method=False,
        publish_note=False,
        error_message=False,
    ):
        return {
            "run_id": self.sync_run.id,
            "vendor_id": row["vendor_id"],
            "product_tmpl_id": product_tmpl_id,
            "state": state,
            "selected": selected,
            "match_method": match_method,
            "group_key": row["group_key"],
            "name": row.get("name_pt") or row.get("name"),
            "brand": row.get("brand"),
            "ean13": row.get("ean13"),
            "reference": row.get("reference"),
            "quantity": row.get("quantity"),
            "unit_price": row.get("unit_price"),
            "wholesale_price": row.get("wholesale_price"),
            "payload_json": json.dumps(row),
            "compare_data_json": json.dumps(row.get("compare_data", {})),
            "publish_note": publish_note,
            "error_message": error_message,
        }

    def _publish_row(self, row):
        product_tmpl, method = self._find_product_template(row)
        if product_tmpl and product_tmpl.hiper_skip_sync:
            return product_tmpl, method, "skipped", "Skipped because product is marked to be ignored by sync."

        if not product_tmpl:
            product_tmpl = self._create_product_template(row)
            method = "new"

        state, state_note = self._update_product_template(product_tmpl, row, method)
        return product_tmpl, method, state, state_note

    def _find_product_template(self, row):
        ProductProduct = self.env["product.product"].sudo()
        ProductTemplate = self.env["product.template"].sudo()

        barcode = row.get("ean13")
        if is_valid_ean13(barcode):
            product = self._barcode_cache.get(barcode)
            if product is None:
                product = ProductProduct.search([("barcode", "=", barcode)], limit=1)
                self._barcode_cache[barcode] = product or False
            if product:
                return product.product_tmpl_id, "barcode"

        reference = row.get("reference")
        if reference:
            product = self._reference_cache.get(reference)
            if product is None:
                product = ProductProduct.search([("default_code", "=", reference)], limit=1)
                self._reference_cache[reference] = product or False
            if product:
                return product.product_tmpl_id, "reference"

        fingerprint = fingerprint_for_payload(
            row.get("name_pt") or row.get("name") or "",
            row.get("description_short_pt") or row.get("description_short") or "",
            row.get("description_pt") or row.get("description") or "",
        )
        if fingerprint:
            product = self._fingerprint_cache.get(fingerprint)
            if product is None:
                product = ProductTemplate.search([("hiper_content_fingerprint", "=", fingerprint)], limit=1)
                self._fingerprint_cache[fingerprint] = product or False
            if product:
                return product, "fingerprint"

        normalized_name = normalize_text(row.get("name_pt") or row.get("name") or "")
        if normalized_name:
            search_name = row.get("name_pt") or row.get("name")
            candidates = self._name_search_cache.get(search_name)
            if candidates is None:
                candidates = ProductTemplate.search([("name", "ilike", search_name)], limit=25)
                self._name_search_cache[search_name] = candidates
            target_desc = normalize_text(row.get("description_pt") or row.get("description") or "")
            target_short = normalize_text(row.get("description_short_pt") or row.get("description_short") or "")
            for candidate in candidates:
                if normalize_text(candidate.name) != normalized_name:
                    continue
                candidate_desc = normalize_text(getattr(candidate, "website_description", False) or candidate.description or "")
                candidate_short = normalize_text(candidate.description_sale or "")
                if target_desc and candidate_desc == target_desc:
                    return candidate, "fingerprint"
                if target_short and candidate_short == target_short:
                    return candidate, "fingerprint"

        return False, False

    def _prepare_lookup_indexes(self, merged_rows):
        ProductProduct = self.env["product.product"].sudo()
        ProductTemplate = self.env["product.template"].sudo()

        barcodes = sorted({row.get("ean13") for row in merged_rows if is_valid_ean13(row.get("ean13"))})
        references = sorted({row.get("reference") for row in merged_rows if row.get("reference")})
        fingerprints = sorted(
            {
                fingerprint_for_payload(
                    row.get("name_pt") or row.get("name") or "",
                    row.get("description_short_pt") or row.get("description_short") or "",
                    row.get("description_pt") or row.get("description") or "",
                )
                for row in merged_rows
            }
        )
        fingerprints = [item for item in fingerprints if item]

        if barcodes or references:
            barcode_set = set(barcodes)
            reference_set = set(references)
            if barcodes and references:
                product_domain = ["|", ("barcode", "in", barcodes), ("default_code", "in", references)]
            elif barcodes:
                product_domain = [("barcode", "in", barcodes)]
            else:
                product_domain = [("default_code", "in", references)]
            for product in ProductProduct.search(product_domain):
                if product.barcode and product.barcode in barcode_set:
                    self._barcode_cache[product.barcode] = product
                if product.default_code and product.default_code in reference_set:
                    self._reference_cache[product.default_code] = product
            for barcode in barcodes:
                self._barcode_cache.setdefault(barcode, False)
            for reference in references:
                self._reference_cache.setdefault(reference, False)
        if fingerprints:
            for template in ProductTemplate.search([("hiper_content_fingerprint", "in", fingerprints)]):
                self._fingerprint_cache[template.hiper_content_fingerprint] = template
            for fingerprint in fingerprints:
                self._fingerprint_cache.setdefault(fingerprint, False)

    def _create_product_template(self, row):
        vendor = self.env["hiper.sync.vendor"].browse(row["vendor_id"])
        values = {
            "name": row.get("name_pt") or row.get("name") or row.get("reference") or row.get("ean13"),
            "sale_ok": True,
            "purchase_ok": True,
            "categ_id": self._get_fallback_internal_category(vendor).id,
            "product_brand_id": self._get_or_create_brand(row.get("brand")).id if row.get("brand") else False,
            "website_published": False,
            "active": True,
            "min_order_qty": row.get("qty_min") or 1,
            "hiper_tags_text": row.get("tags") or False,
            "hiper_manual_url": row.get("info_manual") or False,
        }
        if "is_storable" in self.env["product.template"]._fields:
            values["is_storable"] = True
        template = (
            self.env["product.template"]
            .sudo()
            .with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True)
            .create(values)
        )
        if vendor.default_public_categ_id:
            template.public_categ_ids = [(4, vendor.default_public_categ_id.id)]
        return template

    def _get_fallback_internal_category(self, vendor):
        if vendor.default_categ_id:
            return vendor.default_categ_id
        category = self.env.ref("product.product_category_all", raise_if_not_found=False)
        if category:
            return category
        ProductCategory = self.env["product.category"].sudo()
        category = ProductCategory.search([], order="id asc", limit=1)
        if category:
            return category
        return ProductCategory.create({"name": "Hiper Sync"})

    def _update_product_template(self, template, row, method):
        vendor = self.env["hiper.sync.vendor"].browse(row["vendor_id"])
        variant = template.product_variant_id or template.product_variant_ids[:1]
        supplier_qty = max(row.get("quantity") or 0.0, 0.0)
        template_values = {}
        variant_values = {}

        if not template.hiper_lock_name:
            new_name = row.get("name_pt") or row.get("name") or template.name
            if new_name and template.name != new_name:
                template_values["name"] = new_name

        if not template.hiper_lock_descriptions:
            short_description = clean_html_text(
                row.get("description_short_pt")
                or row.get("description_short")
                or row.get("description_pt")
                or row.get("description")
                or ""
            )
            if "description_sale" in template._fields and template.description_sale != short_description:
                template_values["description_sale"] = short_description
            full_description = (
                row.get("description_pt")
                or row.get("description")
                or row.get("description_short_pt")
                or row.get("description_short")
                or False
            )
            full_description = text_to_basic_html(full_description)
            if "website_description" in template._fields:
                if template.website_description != full_description:
                    template_values["website_description"] = full_description
            elif "description" in template._fields and template.description != full_description:
                template_values["description"] = full_description

        if not template.hiper_lock_categories:
            categ_id, public_categ_ids = self._get_cached_target_categories(vendor, row)
            if categ_id and template.categ_id.id != categ_id.id:
                template_values["categ_id"] = categ_id.id
            target_public_ids = False
            if public_categ_ids:
                target_public_ids = public_categ_ids.ids
            elif vendor.default_public_categ_id:
                target_public_ids = [vendor.default_public_categ_id.id]
            if target_public_ids is not False and template.public_categ_ids.ids != target_public_ids:
                template_values["public_categ_ids"] = [(6, 0, target_public_ids)]

        if row.get("brand"):
            brand = self._get_or_create_brand(row["brand"])
            if template.product_brand_id.id != brand.id:
                template_values["product_brand_id"] = brand.id

        if row.get("weight") and template.weight != row["weight"]:
            template_values["weight"] = row["weight"]
        if "volume" in template._fields and row.get("volume") and template.volume != row["volume"]:
            template_values["volume"] = row["volume"]
        if "website_meta_title" in template._fields and row.get("meta_title"):
            if template.website_meta_title != row["meta_title"]:
                template_values["website_meta_title"] = row["meta_title"]
        if "website_meta_description" in template._fields and row.get("meta_description"):
            if template.website_meta_description != row["meta_description"]:
                template_values["website_meta_description"] = row["meta_description"]

        payload_json = json.dumps(row)
        compare_data_json = json.dumps(row.get("compare_data", {}))
        fingerprint = fingerprint_for_payload(
            row.get("name_pt") or row.get("name") or "",
            row.get("description_short_pt") or row.get("description_short") or "",
            row.get("description_pt") or row.get("description") or "",
        )
        origin_category = row.get("_origin_category") or row.get("category")
        origin_sub_category = row.get("_origin_sub_category") or row.get("sub_category")
        template_meta_values = {
            "hiper_source_vendor_id": vendor.id,
            "hiper_source_module_code": vendor.code,
            "hiper_source_ean13": row.get("ean13"),
            "hiper_last_sync_at": fields.Datetime.now(),
            "hiper_sync_match_method": method,
            "hiper_last_feed_payload": payload_json,
            "hiper_last_compare_data": compare_data_json,
            "hiper_supplier_qty": supplier_qty,
            "hiper_supplier_price": row.get("unit_price") or 0.0,
            "hiper_supplier_wholesale_price": row.get("wholesale_price") or 0.0,
            "hiper_origin_category": origin_category,
            "hiper_origin_sub_category": origin_sub_category,
            "hiper_tags_text": row.get("tags") or template.hiper_tags_text,
            "hiper_manual_url": row.get("info_manual") or template.hiper_manual_url,
            "hiper_content_fingerprint": fingerprint,
        }
        for field_name, field_value in template_meta_values.items():
            current_value = template[field_name]
            if getattr(current_value, "id", current_value) != field_value:
                template_values[field_name] = field_value

        if variant:
            if row.get("reference") and variant.default_code != row["reference"]:
                variant_values["default_code"] = row["reference"]
            if is_valid_ean13(row.get("ean13")) and variant.barcode != row["ean13"]:
                variant_values["barcode"] = row["ean13"]

        if not template.hiper_lock_prices:
            list_price = row.get("unit_price") or 0.0
            if template.list_price != list_price:
                template_values["list_price"] = list_price
            if "standard_price" in template._fields:
                standard_price = row.get("wholesale_price") or list_price
                if template.standard_price != standard_price:
                    template_values["standard_price"] = standard_price

        if template_values:
            template.with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True).write(
                template_values
            )
        if variant and variant_values:
            variant.with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True).write(
                variant_values
            )

        self._update_supplierinfo(template, row, vendor)
        self._update_stock(template, row, supplier_qty=supplier_qty)
        self._update_images(template, row)
        if not template.hiper_lock_features:
            self._update_feature_lines(template, row)
        return self._apply_publish_flags(template, row, supplier_qty=supplier_qty)

    def _get_or_create_brand(self, name):
        if name in self._brand_cache:
            return self._brand_cache[name]
        Brand = self.env["product.brand"].sudo()
        brand = Brand.search([("name", "=", name)], limit=1)
        if not brand:
            brand = Brand.create({"name": name})
        self._brand_cache[name] = brand
        return brand

    def _get_cached_supplier_partner(self, vendor):
        if vendor.id not in self._supplier_partner_cache:
            self._supplier_partner_cache[vendor.id] = vendor._get_or_create_supplier_partner()
        return self._supplier_partner_cache[vendor.id]

    def _get_cached_target_categories(self, vendor, row):
        cache_key = (
            vendor.id,
            row.get("category"),
            row.get("sub_category"),
            row.get("_origin_category"),
            row.get("_origin_sub_category"),
        )
        if cache_key not in self._category_target_cache:
            categ_id, public_categ_ids = vendor._get_target_categories_for_row(row)
            self._category_target_cache[cache_key] = (
                categ_id.id if categ_id else False,
                public_categ_ids.ids if public_categ_ids else [],
            )
        categ_id, public_categ_ids = self._category_target_cache[cache_key]
        return (
            self.env["product.category"].browse(categ_id) if categ_id else False,
            self.env["product.public.category"].browse(public_categ_ids),
        )

    def _update_supplierinfo(self, template, row, vendor):
        partner = self._get_cached_supplier_partner(vendor)
        seller = template.seller_ids.filtered(lambda seller_id: seller_id.partner_id == partner)[:1]
        values = {
            "partner_id": partner.id,
            "price": row.get("unit_price") or 0.0,
            "min_qty": max(row.get("qty_min") or 1, 1),
            "product_code": row.get("reference") or False,
        }
        if seller:
            seller_updates = {}
            for field_name, field_value in values.items():
                current_value = seller[field_name]
                if getattr(current_value, "id", current_value) != field_value:
                    seller_updates[field_name] = field_value
            if seller_updates:
                seller.with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True).write(
                    seller_updates
                )
        else:
            values["product_tmpl_id"] = template.id
            (
                self.env["product.supplierinfo"]
                .sudo()
                .with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True)
                .create(values)
            )

    def _update_stock(self, template, row, supplier_qty=False):
        return None

    def _update_images(self, template, row):
        images = row.get("images") or []
        extra_media = row.get("extra_media") or []
        raw_extra_media = row.get("extra_media_json")
        if not extra_media and raw_extra_media:
            if isinstance(raw_extra_media, str):
                extra_media = parse_json(raw_extra_media, default=[])
            elif isinstance(raw_extra_media, list):
                extra_media = raw_extra_media
        queued = False
        if images:
            first_image = images[0]
            if template.queue_hiper_image_sync(first_image):
                queued = True
        if template.queue_pg_hiper_media_sync(extra_media):
            queued = True
        if queued:
            self._pending_image_updates += 1

    def _trigger_pending_image_worker(self):
        if not self._pending_image_updates:
            return
        self.env["product.template"]._trigger_hiper_image_worker()
        self._pending_image_updates = 0

    def _update_feature_lines(self, template, row):
        features = row.get("features") or []
        normalized_features = [
            (feature.get("name"), feature.get("value"))
            for feature in features
            if feature.get("name")
        ]
        current_features = [
            (line.name, line.value)
            for line in template.hiper_feature_line_ids.sorted(key=lambda feature_line: feature_line.sequence)
        ]
        if current_features == normalized_features:
            return
        template.hiper_feature_line_ids.with_context(
            tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True
        ).unlink()
        if normalized_features:
            (
                self.env["hiper.product.feature.line"]
                .sudo()
                .with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True)
                .create(
                [
                    {
                        "product_tmpl_id": template.id,
                        "sequence": index,
                        "name": feature_name,
                        "value": feature_value,
                    }
                    for index, (feature_name, feature_value) in enumerate(normalized_features, start=1)
                ]
            )
            )

    def _get_internal_sellable_qty(self, template):
        product = template.product_variant_id
        if not product:
            return 0.0
        company = self.env.company
        helper = getattr(company, "_pg_get_total_internal_sale_available_qty", None)
        if callable(helper):
            return max(helper(product), 0.0)
        return max(product.free_qty, 0.0)

    def _compute_publish_decision(self, template, vendor, row, supplier_qty=False):
        raw_qty = row.get("quantity") or 0.0
        qty = supplier_qty if supplier_qty is not False else max(raw_qty, 0.0)
        price = row.get("unit_price") or 0.0
        total_sellable_qty = self._get_internal_sellable_qty(template) + max(qty, 0.0)
        can_publish = True
        state_note = "Published on website."
        if raw_qty < 0:
            can_publish = False
            state_note = "Skipped because supplier quantity is negative."
        elif (self._disable_out_of_stock or vendor.ignore_out_of_stock_products) and total_sellable_qty <= 0:
            can_publish = False
            state_note = "Skipped because total sellable quantity is zero or negative."
        if not self._publish_zero_price and price <= 0:
            can_publish = False
            state_note = "Skipped because supplier price is zero or negative."

        can_publish = can_publish and vendor.product_default_active
        if not vendor.product_default_active:
            state_note = "Skipped because supplier default active is disabled."
        return can_publish, state_note

    def _apply_publish_flags(self, template, row, supplier_qty=False):
        vendor = self.env["hiper.sync.vendor"].browse(row["vendor_id"])
        can_publish, state_note = self._compute_publish_decision(template, vendor, row, supplier_qty=supplier_qty)
        publish_values = {}
        if template.active != can_publish:
            publish_values["active"] = can_publish
        if template.sale_ok != can_publish:
            publish_values["sale_ok"] = can_publish
        if "website_published" in template._fields:
            website_published = can_publish and vendor.publish_to_website
            if template.website_published != website_published:
                publish_values["website_published"] = website_published
        if can_publish and not vendor.publish_to_website:
            state_note = "Updated product, but website publishing is disabled for this supplier."
        if publish_values:
            template.with_context(tracking_disable=True, mail_notrack=True, mail_create_nosubscribe=True).write(
                publish_values
            )
        return ("published" if can_publish else "skipped"), state_note
