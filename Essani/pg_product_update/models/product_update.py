"""Motor de importacao Google Drive para catalogo, imagens, documentos e referencias."""
import os
import gc
import re
import json
import time
import base64
import logging
import hashlib
import unicodedata
from io import BytesIO
from contextlib import contextmanager
from datetime import datetime

from PIL import Image, UnidentifiedImageError
from psycopg2.errors import SerializationFailure

from odoo import models, api, fields
from odoo.exceptions import UserError

try:
    import psutil
except ImportError:
    psutil = None

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    try:
        from googleapiclient.errors import HttpError
    except Exception:
        HttpError = Exception
except ImportError:
    service_account = None
    build = None
    MediaIoBaseDownload = None
    HttpError = Exception

_logger = logging.getLogger(__name__)

DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT = 50_000_000
DRIVE_DOCUMENT_DOWNLOAD_HARD_LIMIT = 100_000_000
DRIVE_METADATA_FOLDERS_DEFAULT = frozenset({
    "IMAGENS",
    "3D",
    "FICHA TECNICA",
    "CERTIFICADO CONFORMIDADE",
    "OPCIONAIS",
    "ALTERNATIVOS",
    "ACESSORIOS",
})
DRIVE_METADATA_FOLDERS_PARAM = "pg_product_update.drive_metadata_folders"


def normalize_folder_name_match(folder_name):
    name = re.sub(r"^\d+\.", "", (folder_name or "")).strip()
    name = unicodedata.normalize("NFD", name)
    name = "".join(ch for ch in name if not unicodedata.combining(ch))
    name = re.sub(r"\s+", " ", name).strip()
    return name.upper()


# ---------------------------------------------------------------------------
# Google Drive helper (readonly)
# ---------------------------------------------------------------------------
class _GDriveHelper:
    def __init__(self, env):
        self.env = env
        self._service = None
        self._get_cache = {}
        self._children_cache = {}

    def service(self):
        if self._service:
            return self._service

        if not service_account or not build:
            raise RuntimeError(
                "Google API libraries not installed. Ensure requirements.txt contains "
                "google-api-python-client, google-auth, google-auth-httplib2."
            )

        ICP = self.env["ir.config_parameter"].sudo()
        sa_b64 = ICP.get_param("product_update.gdrive_sa_json_b64")
        if not sa_b64:
            raise RuntimeError("Missing system parameter: product_update.gdrive_sa_json_b64")

        try:
            sa_json = base64.b64decode(sa_b64).decode("utf-8")
            info = json.loads(sa_json)
        except Exception as e:
            raise RuntimeError(f"Invalid base64/json in product_update.gdrive_sa_json_b64: {e}")

        creds = service_account.Credentials.from_service_account_info(info, scopes=DRIVE_SCOPES)
        self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    # ---------- low-level retry wrapper ----------
    def _execute(self, call, retries=5, base_sleep=1.0):
        last_exc = None
        for attempt in range(retries):
            try:
                return call.execute()
            except (SerializationFailure,) as e:
                last_exc = e
                sleep_s = min(20.0, base_sleep * (2 ** attempt))
                _logger.warning("DB SerializationFailure (attempt %s/%s): %s", attempt + 1, retries, e)
                time.sleep(sleep_s)
            except Exception as e:
                last_exc = e
                # Network errors / transient google errors -> retry
                sleep_s = min(20.0, base_sleep * (2 ** attempt))
                _logger.warning("Drive API transient error (attempt %s/%s): %s", attempt + 1, retries, e)
                time.sleep(sleep_s)
        raise last_exc

    def get(self, file_id, fields="id,name,mimeType,parents,modifiedTime,md5Checksum,size"):
        cache_key = (file_id, fields)
        if cache_key in self._get_cache:
            return self._get_cache[cache_key]
        call = self.service().files().get(
            fileId=file_id,
            fields=fields,
            supportsAllDrives=True,
        )
        res = self._execute(call)
        self._get_cache[cache_key] = res
        return res

    def list_children(self, folder_id, folders_only=False):
        cache_key = (folder_id, folders_only)
        if cache_key in self._children_cache:
            return self._children_cache[cache_key]
        mime_filter = f"and mimeType = '{DRIVE_FOLDER_MIME}'" if folders_only else ""
        q = f"'{folder_id}' in parents and trashed = false {mime_filter}"
        fields_ = "files(id,name,mimeType,modifiedTime,md5Checksum,size,parents)"
        call = self.service().files().list(
            q=q,
            fields=fields_,
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        res = self._execute(call)
        files = res.get("files", [])
        self._children_cache[cache_key] = files
        return files

    def find_child_folder(self, parent_id, normalized_name_upper):
        """Find direct child folder whose normalized name matches (case-insensitive)."""
        for item in self.list_children(parent_id, folders_only=True):
            name_norm = normalize_folder_name_match(item.get("name", ""))
            if name_norm == normalized_name_upper:
                return item
        return None

    def download_bytes(self, file_id):
        request = self.service().files().get_media(fileId=file_id, supportsAllDrives=True)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        # downloader.next_chunk() can throw transient errors too
        retries = 5
        for attempt in range(retries):
            try:
                while not done:
                    _, done = downloader.next_chunk()
                return fh.getvalue()
            except Exception as e:
                if attempt >= retries - 1:
                    raise
                sleep_s = min(20.0, 1.0 * (2 ** attempt))
                _logger.warning("Drive download transient error (attempt %s/%s): %s", attempt + 1, retries, e)
                time.sleep(sleep_s)

    def walk_tree(self, root_folder_id):
        """
        Walk entire tree returning tuples:
          (folder_id, folder_path_names_list, child_item_dict)
        where child_item_dict can be file or folder.
        """
        stack = [(root_folder_id, [])]
        while stack:
            folder_id, path_parts = stack.pop()
            children = self.list_children(folder_id, folders_only=False)
            for child in children:
                yield folder_id, path_parts, child
                if child.get("mimeType") == DRIVE_FOLDER_MIME:
                    stack.append((child["id"], path_parts + [child.get("name", "")]))


# ---------------------------------------------------------------------------
# Job model (persists progress across worker restarts)
# ---------------------------------------------------------------------------
class ProductUpdateDriveJob(models.Model):
    _name = "product.update.drive.job"
    _description = "Product Update Drive Job"
    _order = "id desc"

    state = fields.Selection(
        [("running", "Running"), ("done", "Done"), ("failed", "Failed")],
        default="running",
        required=True,
        index=True,
    )
    name = fields.Char(compute="_compute_dashboard_metrics")
    root_folder_id = fields.Char(required=True, index=True)

    # discovery (incremental tree scan)
    discovery_done = fields.Boolean(default=False)
    scan_stack_json = fields.Text(default="[]")        # stack of folder IDs to scan for IMAGENS
    pending_imagens_json = fields.Text(default="[]")   # queue of IMAGENS folder IDs found

    # fixed ids created at start (so the run stays consistent)
    all_category_id = fields.Many2one("product.category")
    all_web_category_id = fields.Many2one("product.public.category")

    # counters / logging
    discovered_count = fields.Integer(default=0)
    discovered_items_json = fields.Text(default="[]")
    processed_count = fields.Integer(default=0)
    processed_items_json = fields.Text(default="[]")
    skipped_count = fields.Integer(default=0)
    skipped_items_json = fields.Text(default="[]")
    skipped_items_preview = fields.Text(compute="_compute_skipped_items_preview")
    trace_events_json = fields.Text(default="[]")
    trace_events_preview = fields.Text(compute="_compute_trace_events_preview")
    unaccounted_count = fields.Integer(compute="_compute_unaccounted_items_preview")
    unaccounted_items_preview = fields.Text(compute="_compute_unaccounted_items_preview")
    error_count = fields.Integer(default=0)
    last_error = fields.Text()
    started_at = fields.Datetime(default=fields.Datetime.now)
    finished_at = fields.Datetime()

    # current retry bookkeeping (per IMAGENS item)
    current_item_id = fields.Char()
    current_item_attempts = fields.Integer(default=0)

    phase = fields.Selection(
        [
            ("discovery", "Discovery"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        compute="_compute_dashboard_metrics",
    )
    pending_count = fields.Integer(compute="_compute_dashboard_metrics")
    scan_remaining_count = fields.Integer(compute="_compute_dashboard_metrics")
    total_count = fields.Integer(compute="_compute_dashboard_metrics")
    progress_percent = fields.Float(compute="_compute_dashboard_metrics")
    duration_seconds = fields.Integer(compute="_compute_dashboard_metrics")
    current_item_display = fields.Char(compute="_compute_dashboard_metrics")

    @api.depends("skipped_items_json")
    def _compute_skipped_items_preview(self):
        for job in self:
            entries = self._safe_json_load(job.skipped_items_json)
            lines = []
            for entry in entries[-10:]:
                label = entry.get("product_name") or entry.get("imagens_id") or "Unknown item"
                hierarchy = entry.get("hierarchy")
                reason = entry.get("reason") or "No reason recorded"
                source = entry.get("source") or "runtime"
                if hierarchy:
                    lines.append(f"{label} [{hierarchy}] - {reason} ({source})")
                else:
                    lines.append(f"{label} - {reason} ({source})")
            job.skipped_items_preview = "\n".join(lines)

    @api.depends("trace_events_json")
    def _compute_trace_events_preview(self):
        for job in self:
            entries = self._safe_json_load(job.trace_events_json)
            lines = []
            for entry in entries[-200:]:
                timestamp = entry.get("timestamp") or ""
                stage = entry.get("stage") or "trace"
                label = entry.get("product_name") or entry.get("imagens_id") or "Unknown item"
                hierarchy = entry.get("hierarchy")
                message = entry.get("message") or ""
                if hierarchy:
                    lines.append(f"{timestamp} | {stage} | {label} [{hierarchy}] | {message}")
                else:
                    lines.append(f"{timestamp} | {stage} | {label} | {message}")
            job.trace_events_preview = "\n".join(lines)

    @api.depends("discovered_items_json", "processed_items_json", "skipped_items_json", "pending_imagens_json", "current_item_id")
    def _compute_unaccounted_items_preview(self):
        for job in self:
            discovered_entries = self._safe_json_load(job.discovered_items_json)
            processed_entries = self._safe_json_load(job.processed_items_json)
            skipped_entries = self._safe_json_load(job.skipped_items_json)
            trace_entries = self._safe_json_load(job.trace_events_json)
            pending_ids = set(self._safe_json_load(job.pending_imagens_json))
            current_item_id = job.current_item_id

            processed_ids = {entry.get("imagens_id") for entry in processed_entries if entry.get("imagens_id")}
            skipped_ids = {entry.get("imagens_id") for entry in skipped_entries if entry.get("imagens_id")}
            last_trace_by_item = {}
            for trace in trace_entries:
                trace_imagens_id = trace.get("imagens_id")
                if trace_imagens_id:
                    last_trace_by_item[trace_imagens_id] = trace

            unaccounted_entries = [
                entry for entry in discovered_entries
                if (
                    entry.get("imagens_id")
                    and entry.get("imagens_id") not in processed_ids
                    and entry.get("imagens_id") not in skipped_ids
                    and entry.get("imagens_id") not in pending_ids
                    and entry.get("imagens_id") != current_item_id
                )
            ]

            lines = []
            for entry in unaccounted_entries[-10:]:
                label = entry.get("product_name") or entry.get("imagens_id") or "Unknown item"
                hierarchy = entry.get("hierarchy")
                message = "discovered but never marked processed/skipped"
                trace = last_trace_by_item.get(entry.get("imagens_id"))
                if trace:
                    last_stage = trace.get("stage") or "trace"
                    last_message = trace.get("message") or "No trace message recorded"
                    message = f"{message} | last={last_stage}: {last_message}"
                if hierarchy:
                    lines.append(f"{label} [{hierarchy}] - {message}")
                else:
                    lines.append(f"{label} - {message}")

            job.unaccounted_count = len(unaccounted_entries)
            job.unaccounted_items_preview = "\n".join(lines)

    @api.depends(
        "state",
        "root_folder_id",
        "discovery_done",
        "scan_stack_json",
        "pending_imagens_json",
        "discovered_count",
        "processed_count",
        "current_item_id",
        "started_at",
        "finished_at",
    )
    def _compute_dashboard_metrics(self):
        now_dt = fields.Datetime.now()
        for job in self:
            pending = len(self._safe_json_load(job.pending_imagens_json))
            scan_remaining = len(self._safe_json_load(job.scan_stack_json))
            current_item = 1 if job.current_item_id else 0
            known_total = job.processed_count + pending + current_item
            discovered_total = max(job.discovered_count, known_total)
            historical_total = self._get_historical_total_estimate(job)
            total = max(discovered_total, historical_total if not job.discovery_done else 0)
            if total == 0 and job.state in ("done", "failed"):
                total = job.processed_count

            if job.state == "failed":
                phase = "failed"
                progress = 100.0 if total == 0 else min(100.0, (job.processed_count / max(total, 1)) * 100.0)
            elif job.state == "done":
                phase = "done"
                progress = 100.0
            elif pending or current_item or job.processed_count:
                phase = "processing"
                progress = 0.0 if total == 0 else min(99.0, (job.processed_count / max(total, 1)) * 100.0)
            elif not job.discovery_done:
                phase = "discovery"
                progress = 0.0 if total == 0 else min(99.0, (job.processed_count / max(total, 1)) * 100.0)
            else:
                phase = "processing"
                progress = 0.0 if total == 0 else min(99.0, (job.processed_count / max(total, 1)) * 100.0)

            end_dt = job.finished_at or now_dt
            duration = 0
            if job.started_at:
                started_dt = fields.Datetime.to_datetime(job.started_at)
                ended_dt = fields.Datetime.to_datetime(end_dt)
                duration = max(0, int((ended_dt - started_dt).total_seconds()))

            phase_labels = dict(self._fields["phase"].selection)
            job.name = "Import #%s - %s" % (job.id or 0, phase_labels.get(phase, "Running"))
            job.phase = phase
            job.pending_count = pending
            job.scan_remaining_count = scan_remaining
            job.total_count = total
            job.progress_percent = round(progress, 2)
            job.duration_seconds = duration
            job.current_item_display = job.current_item_id or ""

    def _get_historical_total_estimate(self, job):
        if not job.root_folder_id:
            return 0
        previous_jobs = self.search(
            [
                ("root_folder_id", "=", job.root_folder_id),
                ("state", "=", "done"),
                ("processed_count", ">", 0),
                ("id", "!=", job.id),
            ],
            order="finished_at desc, id desc",
            limit=5,
        )
        if not previous_jobs:
            return 0
        return max(previous_jobs.mapped("processed_count"))

    @api.model
    def _safe_json_load(self, payload):
        try:
            return json.loads(payload or "[]")
        except Exception:
            return []

    def action_refresh_view(self):
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_open_live_dashboard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "pg_product_update.drive_job_dashboard",
            "target": "current",
            "params": {"job_id": self.id},
        }

    def action_force_start_processing(self):
        self.ensure_one()
        if self.state != "running":
            return self.action_open_live_dashboard()

        product_update = self.env["product.update"]
        product_update._advance_job_discovery(self, scan_limit=2000, time_budget_s=120.0)
        product_update.cron_run_drive_jobs()
        return self.action_open_live_dashboard()


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------
class ProductUpdate(models.Model):
    _name = "product.update"
    _description = "Product Update"
    _gdrive_helper_cache = {}
    _attribute_cache = {}
    _attribute_value_cache = {}
    _product_imagens_cache = {}
    _drive_metadata_folders_cache = {}

    # ----------------------------
    # Helpers
    # ----------------------------
    def _gdrive(self):
        cache = getattr(type(self), "_gdrive_helper_cache", None)
        if cache is None:
            cache = {}
            setattr(type(self), "_gdrive_helper_cache", cache)
        dbname = self.env.cr.dbname
        helper = cache.get(dbname)
        if helper is None:
            helper = _GDriveHelper(self.env)
            cache[dbname] = helper
        else:
            helper.env = self.env
        return helper

    def _cache_bucket(self, name):
        cache = getattr(type(self), name, None)
        if cache is None:
            cache = {}
            setattr(type(self), name, cache)
        dbname = self.env.cr.dbname
        return cache.setdefault(dbname, {})

    def _clear_runtime_caches(self):
        dbname = self.env.cr.dbname
        type(self)._gdrive_helper_cache.pop(dbname, None)
        type(self)._attribute_cache.pop(dbname, None)
        type(self)._attribute_value_cache.pop(dbname, None)
        type(self)._product_imagens_cache.pop(dbname, None)
        type(self)._drive_metadata_folders_cache.pop(dbname, None)

    def _normalize_match_key(self, value):
        return normalize_folder_name_match(value or "")

    def _get_drive_metadata_folders(self):
        cache = self._cache_bucket("_drive_metadata_folders_cache")
        if "value" in cache:
            return cache["value"]
        raw = self.env["ir.config_parameter"].sudo().get_param(DRIVE_METADATA_FOLDERS_PARAM, "")
        names = {normalize_folder_name_match(part) for part in (raw or "").split(",") if part.strip()}
        names |= set(DRIVE_METADATA_FOLDERS_DEFAULT)
        names.discard("")
        result = frozenset(names)
        cache["value"] = result
        return result

    def _advisory_xact_lock(self, key):
        self.env.cr.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [key])

    def _pos_available(self):
        """True if POS is installed/loaded (pos.category model exists)."""
        return "pos.category" in self.env

    def _variant_image_related_to_template(self):
        field = self.env["product.product"]._fields.get("image_1920")
        return bool(getattr(field, "related", False))

    def _variant_image_field_name(self):
        if "image_variant_1920" in self.env["product.product"]._fields:
            return "image_variant_1920"
        return "image_1920"

    def _json_load(self, txt, default):
        try:
            if not txt:
                return default
            return json.loads(txt)
        except Exception:
            return default

    def _json_dump(self, obj):
        return json.dumps(obj, ensure_ascii=False)

    def _action_open_drive_job_dashboard(self, job):
        return job.action_open_live_dashboard()

    def _drive_file_size_bytes(self, file_info):
        size = (file_info or {}).get("size")
        try:
            return int(size) if size is not None else None
        except Exception:
            return None

    def _format_bytes(self, size_bytes):
        if size_bytes in (None, False):
            return "unknown"
        units = ["B", "KB", "MB", "GB"]
        value = float(size_bytes)
        for unit in units:
            if value < 1024.0 or unit == units[-1]:
                return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
            value /= 1024.0

    def _format_exception_message(self, exc):
        exc_name = exc.__class__.__name__
        exc_message = str(exc) or exc_name
        return f"{exc_name}: {exc_message}" if exc_message != exc_name else exc_name

    def _trace_drive_file_event(self, stage, file_info, extra_message="", imagens_id=None):
        file_name = (file_info or {}).get("name") or "unknown"
        file_id = (file_info or {}).get("id") or "no-id"
        file_md5 = (file_info or {}).get("md5Checksum") or (file_info or {}).get("md5") or "no-md5"
        file_size = self._format_bytes(self._drive_file_size_bytes(file_info))
        message = f"{file_name} | id={file_id} | md5={file_md5} | size={file_size}"
        if extra_message:
            message = f"{message} | {extra_message}"
        self._append_context_job_trace(stage, message, imagens_id=imagens_id)

    def _should_skip_drive_file(self, file_info, hard_limit_bytes):
        file_size = self._drive_file_size_bytes(file_info)
        if file_size and hard_limit_bytes and file_size > hard_limit_bytes:
            return True, f"Skipped oversized file ({self._format_bytes(file_size)} > {self._format_bytes(hard_limit_bytes)})"
        return False, ""

    def _build_job_skip_entry(self, imagens_id, reason, source):
        return self._build_job_item_entry(imagens_id, source, reason)

    def _build_job_item_entry(self, imagens_id, source, reason=None):
        product_name = None
        hierarchy = []
        product_folder_id = None
        try:
            product_name, hierarchy, product_folder_id = self.find_product_info_from_imagens(imagens_id)
        except Exception:
            product_name = None
            hierarchy = []
            product_folder_id = None

        return {
            "timestamp": fields.Datetime.now().isoformat(),
            "source": source,
            "imagens_id": imagens_id,
            "product_name": product_name,
            "hierarchy": " / ".join(hierarchy) if hierarchy else "",
            "product_folder_id": product_folder_id,
            "reason": reason or "",
        }

    def _append_job_item_entries(self, job, field_name, item_entries, max_entries=2000):
        if not item_entries:
            return

        existing_entries = self._json_load(getattr(job, field_name), [])
        all_entries, new_entries = self._merge_job_item_entries(existing_entries, item_entries, max_entries=max_entries)
        if not new_entries:
            return

        job.write({field_name: self._json_dump(all_entries)})
        self.env.cr.commit()

    def _append_job_skips(self, job, skip_entries):
        if not skip_entries:
            return

        existing_entries = self._json_load(job.skipped_items_json, [])
        all_entries, new_entries = self._merge_job_item_entries(existing_entries, skip_entries, max_entries=100)
        if not new_entries:
            return
        vals = {
            "skipped_count": (job.skipped_count or 0) + len(new_entries),
            "skipped_items_json": self._json_dump(all_entries),
        }
        job.write(vals)
        self.env.cr.commit()

        for entry in new_entries:
            _logger.warning(
                "Drive job %s skipped IMAGENS %s (%s): %s",
                job.id,
                entry.get("imagens_id"),
                entry.get("product_name") or "unknown product",
                entry.get("reason"),
            )

    def _merge_job_item_entries(self, existing_entries, new_entries, max_entries=2000):
        existing_entries = list(existing_entries or [])
        new_entries = list(new_entries or [])
        known_ids = {entry.get("imagens_id") for entry in existing_entries if entry.get("imagens_id")}
        appended_entries = [
            entry for entry in new_entries
            if entry.get("imagens_id") and entry.get("imagens_id") not in known_ids
        ]
        return (existing_entries + appended_entries)[-max_entries:], appended_entries

    def _append_job_trace(self, job, stage, message, imagens_id=None, max_entries=5000):
        existing_entries = self._json_load(job.trace_events_json, [])
        entry = self._build_job_item_entry(imagens_id, stage, reason=message)
        entry["stage"] = stage
        entry["message"] = message
        all_entries = (existing_entries + [entry])[-max_entries:]
        job.write({"trace_events_json": self._json_dump(all_entries)})
        self.env.cr.commit()

    def _append_context_job_trace(self, stage, message, imagens_id=None):
        job_id = self.env.context.get("pg_drive_job_trace_job_id")
        if not job_id:
            return
        job = self.env["product.update.drive.job"].browse(job_id).exists()
        if not job:
            return
        self._append_job_trace(
            job,
            stage,
            message,
            imagens_id=imagens_id or self.env.context.get("pg_drive_job_trace_imagens_id"),
        )

    def _recover_interrupted_job_item(self, job, max_item_retries):
        imagens_id = job.current_item_id
        if not imagens_id:
            return False

        processed_entries = self._json_load(job.processed_items_json, [])
        skipped_entries = self._json_load(job.skipped_items_json, [])
        processed_ids = {entry.get("imagens_id") for entry in processed_entries if entry.get("imagens_id")}
        skipped_ids = {entry.get("imagens_id") for entry in skipped_entries if entry.get("imagens_id")}

        if imagens_id in processed_ids or imagens_id in skipped_ids:
            job.write({"current_item_id": False, "current_item_attempts": 0})
            self.env.cr.commit()
            self._append_job_trace(job, "processing_cleanup", "Cleared stale current item already accounted", imagens_id=imagens_id)
            return True

        pending = self._json_load(job.pending_imagens_json, [])
        if imagens_id not in pending:
            pending.insert(0, imagens_id)

        attempts = min((job.current_item_attempts or 0) + 1, max_item_retries)
        job.write(
            {
                "current_item_id": False,
                "current_item_attempts": attempts if attempts < max_item_retries else 0,
                "pending_imagens_json": self._json_dump(pending) if attempts < max_item_retries else self._json_dump([pid for pid in pending if pid != imagens_id]),
            }
        )
        self.env.cr.commit()

        if attempts < max_item_retries:
            self._append_job_trace(
                job,
                "processing_recovered",
                f"Recovered interrupted item and requeued it (attempt {attempts}/{max_item_retries}, pending={len(pending)})",
                imagens_id=imagens_id,
            )
        else:
            reason = f"Recovered interrupted item exceeded max retries ({attempts}/{max_item_retries})"
            self._append_job_trace(job, "processing_drop", reason, imagens_id=imagens_id)
            self._append_job_skips(
                job,
                [self._build_job_skip_entry(imagens_id, reason, "interrupted_recovery_drop")],
            )
        return True

    def _explain_product_level_imagens(self, imagens_folder_id):
        gd = self._gdrive()
        imagens_info = gd.get(imagens_folder_id, fields="id,parents")
        if not imagens_info.get("parents"):
            return False, "IMAGENS folder has no parent"

        parent_id = imagens_info["parents"][0]
        _, custom_folders = self._split_drive_folders(parent_id)
        if not custom_folders:
            return False, "Parent folder has no custom attribute folders"

        _, variant_specs, _ = self._collect_variant_specs_from_attributes(parent_id)
        if not variant_specs:
            return False, "Parent folder has custom children but no valid reference-folder variant structure"

        return True, None

    def _advance_job_discovery(self, job, scan_limit=30, time_budget_s=None):
        start_ts = time.time()
        stack = self._json_load(job.scan_stack_json, [])
        pending = self._json_load(job.pending_imagens_json, [])
        discovered_count = max(job.discovered_count or 0, job.processed_count + len(pending) + (1 if job.current_item_id else 0))
        pending_ids = set(pending)
        gd = self._gdrive()
        queued_before = len(pending)
        scanned = 0

        while stack and scanned < scan_limit:
            folder_id = stack.pop()
            scanned += 1

            children = gd.list_children(folder_id, folders_only=True)
            for ch in children:
                child_id = ch.get("id")
                ch_name = self.normalize_folder_name(ch.get("name") or "").upper()
                if ch_name == "IMAGENS":
                    if (
                        child_id
                        and self._is_product_level_imagens(child_id)
                        and child_id not in pending_ids
                        and child_id != job.current_item_id
                    ):
                        pending.append(child_id)
                        pending_ids.add(child_id)
                        discovered_count += 1
                        self._append_job_item_entries(
                            job,
                            "discovered_items_json",
                            [self._build_job_item_entry(child_id, "discovery")],
                        )
                        self._append_job_trace(
                            job,
                            "discovery_queue",
                            f"Queued discovered IMAGENS item (pending={len(pending)}, scanned={scanned})",
                            imagens_id=child_id,
                        )
                else:
                    if child_id:
                        stack.append(child_id)

            if time_budget_s and (time.time() - start_ts) > time_budget_s:
                break

        discovery_done = not stack
        job.write(
            {
                "discovery_done": discovery_done,
                "scan_stack_json": self._json_dump(stack),
                "pending_imagens_json": self._json_dump(pending),
                "discovered_count": discovered_count,
            }
        )
        self.env.cr.commit()
        return {
            "scanned": scanned,
            "queued": len(pending) - queued_before,
            "discovery_done": discovery_done,
            "pending_count": len(pending),
            "scan_remaining_count": len(stack),
        }

    def _process_next_job_pending_item(self, job, all_category, max_item_retries):
        if job.current_item_id:
            self._recover_interrupted_job_item(job, max_item_retries)

        pending = self._json_load(job.pending_imagens_json, [])
        if pending:
            filtered = []
            skip_entries = []
            for pid in pending:
                is_valid, reason = self._explain_product_level_imagens(pid)
                if is_valid:
                    filtered.append(pid)
                else:
                    self._append_job_trace(
                        job,
                        "pending_revalidation_skip",
                        f"Removed from pending after revalidation: {reason}",
                        imagens_id=pid,
                    )
                    skip_entries.append(
                        self._build_job_skip_entry(
                            pid,
                            reason,
                            "pending_revalidation",
                        )
                    )
            if len(filtered) != len(pending):
                pending = filtered
                job.write({"pending_imagens_json": self._json_dump(pending)})
                self.env.cr.commit()
                self._append_job_skips(job, skip_entries)

        if not pending:
            return False

        imagens_id = pending.pop(0)
        job.write(
            {
                "current_item_id": imagens_id,
                "pending_imagens_json": self._json_dump(pending),
            }
        )
        self.env.cr.commit()
        self._append_job_trace(
            job,
            "processing_claimed",
            f"Claimed IMAGENS item from queue (pending_remaining={len(pending)})",
            imagens_id=imagens_id,
        )
        self._append_job_trace(job, "processing_start", "Started processing IMAGENS item", imagens_id=imagens_id)

        try:
            outcome = self.with_context(
                pg_drive_job_trace_job_id=job.id,
                pg_drive_job_trace_imagens_id=imagens_id,
            )._process_one_imagens_folder(imagens_id, all_category)
            outcome = outcome or {"status": "processed"}
            outcome_status = outcome.get("status") or "processed"
            outcome_reason = outcome.get("reason") or ""

            if outcome_status == "skipped":
                job.write(
                    {
                        "current_item_attempts": 0,
                        "current_item_id": False,
                    }
                )
                self.env.cr.commit()
                self._append_job_trace(
                    job,
                    "processing_skip",
                    f"Processing ended without import: {outcome_reason}",
                    imagens_id=imagens_id,
                )
                self._append_job_skips(
                    job,
                    [
                        self._build_job_skip_entry(
                            imagens_id,
                            outcome_reason or "Processing ended without import",
                            "processing_outcome_skip",
                        )
                    ],
                )
                self._clear_runtime_caches()
                gc.collect()
                return True

            processed_entry = self._build_job_item_entry(imagens_id, "processed")
            processed_entries, appended_entries = self._merge_job_item_entries(
                self._json_load(job.processed_items_json, []),
                [processed_entry],
            )

            job.write(
                {
                    "processed_count": job.processed_count + 1,
                    "current_item_attempts": 0,
                    "current_item_id": False,
                    "processed_items_json": self._json_dump(processed_entries),
                }
            )
            self.env.cr.commit()
            if appended_entries:
                _logger.info(
                    "Drive job %s processed IMAGENS %s (%s)",
                    job.id,
                    imagens_id,
                    processed_entry.get("product_name") or "unknown product",
                )
            success_message = "Finished processing IMAGENS item"
            if outcome_reason:
                success_message = f"{success_message}: {outcome_reason}"
            self._append_job_trace(job, "processing_success", success_message, imagens_id=imagens_id)
            self._clear_runtime_caches()
            gc.collect()
            return True

        except Exception as e:
            self.env.cr.rollback()

            attempts = (job.current_item_attempts or 0) + 1
            formatted_error = self._format_exception_message(e)

            _logger.error(
                "Job %s error on IMAGENS %s (attempt %s/%s): %s",
                job.id,
                imagens_id,
                attempts,
                max_item_retries,
                e,
            )
            self._append_job_trace(
                job,
                "processing_exception",
                f"Processing raised {formatted_error} (attempt {attempts}/{max_item_retries})",
                imagens_id=imagens_id,
            )

            if attempts < max_item_retries:
                pending2 = self._json_load(job.pending_imagens_json, [])
                pending2.insert(0, imagens_id)
                vals = {
                    "current_item_id": False,
                    "current_item_attempts": attempts,
                    "last_error": formatted_error,
                    "error_count": job.error_count + 1,
                    "pending_imagens_json": self._json_dump(pending2),
                }
                self._append_job_trace(
                    job,
                    "processing_retry",
                    f"Attempt {attempts}/{max_item_retries} failed and item was requeued: {formatted_error}",
                    imagens_id=imagens_id,
                )
            else:
                _logger.error("Dropping IMAGENS %s after %s attempts.", imagens_id, attempts)
                vals = {
                    "current_item_attempts": 0,
                    "current_item_id": False,
                    "last_error": formatted_error,
                    "error_count": job.error_count + 1,
                }
                self._append_job_trace(
                    job,
                    "processing_drop",
                    f"Max retries exhausted after {attempts} attempts: {formatted_error}",
                    imagens_id=imagens_id,
                )

            job.write(vals)
            self.env.cr.commit()
            if attempts >= max_item_retries:
                self._append_job_skips(
                    job,
                    [
                        self._build_job_skip_entry(
                            imagens_id,
                            f"Max retries exhausted after {attempts} attempts: {formatted_error}",
                            "max_retries_exhausted",
                        )
                    ],
                )
            self._clear_runtime_caches()
            gc.collect()
            return True

    def _get_cached(self, cache, key, compute):
        if key in cache:
            return cache[key]
        value = compute()
        cache[key] = value
        return value

    def _find_template_by_reference(self, reference):
        template_model = self.env["product.template"]
        if "default_code" in template_model._fields:
            tmpl = template_model.search([("default_code", "=", reference)], limit=1)
            if tmpl:
                return tmpl
        return template_model.search([("name", "=", reference)], limit=1)

    def _find_variant_by_reference(self, reference):
        variant_model = self.env["product.product"]
        variant = variant_model.search([("default_code", "=", reference)], limit=1)
        if variant:
            return variant
        tmpl = self._find_template_by_reference(reference)
        if tmpl:
            return tmpl.product_variant_id or tmpl.product_variant_ids[:1]
        return None

    def _apply_related_products_from_drive(self, product, product_path):
        gd = self._gdrive()

        folder_map = {
            "OPCIONAIS": "optional_product_ids",
            "ALTERNATIVOS": "alternative_product_ids",
            "ACESSORIOS": "accessory_product_ids",
        }

        variant_model = self.env["product.product"]
        template_model = self.env["product.template"]

        for folder_name, field_name in folder_map.items():
            field = product._fields.get(field_name)
            if not field:
                continue
            target_model = getattr(field, "comodel_name", None)
            if target_model not in ("product.template", "product.product"):
                continue

            related_folder = gd.find_child_folder(product_path, folder_name)
            if not related_folder:
                continue

            ref_names = []
            for folder in gd.list_children(related_folder["id"], folders_only=True):
                ref_name = self.normalize_folder_name(folder.get("name") or "")
                if ref_name:
                    ref_names.append(ref_name)

            if not ref_names:
                product.write({field_name: [(6, 0, [])]})
                continue

            unique_refs = list(dict.fromkeys(ref_names))

            variants_by_code = {}
            variants = variant_model.search([("default_code", "in", unique_refs)])
            for v in variants:
                variants_by_code.setdefault(v.default_code, v)

            templates_by_code = {}
            if "default_code" in template_model._fields:
                templates = template_model.search([("default_code", "in", unique_refs)])
                for t in templates:
                    templates_by_code.setdefault(t.default_code, t)

            templates_by_name = {}
            missing_name_refs = [ref for ref in unique_refs if ref not in templates_by_code]
            if missing_name_refs:
                templates = template_model.search([("name", "in", missing_name_refs)])
                for t in templates:
                    templates_by_name.setdefault(t.name, t)

            related_ids = []
            missing_refs = []
            for ref_name in unique_refs:
                if target_model == "product.product":
                    variant = variants_by_code.get(ref_name)
                    if not variant:
                        template = templates_by_code.get(ref_name) or templates_by_name.get(ref_name)
                        if template:
                            variant = template.product_variant_id or template.product_variant_ids[:1]
                    if variant:
                        related_ids.append(variant.id)
                    else:
                        missing_refs.append(ref_name)
                    continue

                template = templates_by_code.get(ref_name) or templates_by_name.get(ref_name)
                if not template:
                    variant = variants_by_code.get(ref_name)
                    if variant:
                        template = variant.product_tmpl_id
                if template:
                    related_ids.append(template.id)
                else:
                    missing_refs.append(ref_name)

            product.write({field_name: [(6, 0, sorted(set(related_ids)))]})

            if missing_refs:
                _logger.info(
                    "Related products not found for %s (%s): %s",
                    product.name,
                    folder_name,
                    ", ".join(sorted(set(missing_refs))),
                )

    # ----------------------------
    # String helpers
    # ----------------------------
    def normalize_folder_name(self, folder_name):
        return re.sub(r"^\d+\.", "", (folder_name or "")).strip()

    def extract_default_code(self, folder_name):
        """Return folder name preserving numeric prefixes before a dot."""
        folder_name = (folder_name or "").strip()
        match = re.match(r"^(\d+\.)\s*(.*)$", folder_name)
        if match:
            prefix, rest = match.groups()
            return f"{prefix}{rest.strip()}"
        return folder_name

    # ----------------------------
    # Drive folder resolution for a given product.template
    # ----------------------------
    def _pg_drive_root_id(self):
        root_id = self.env["ir.config_parameter"].sudo().get_param(
            "product_update.gdrive_root_folder_id"
        )
        if not root_id:
            raise UserError(
                "Parametro de sistema 'product_update.gdrive_root_folder_id' "
                "nao definido. Configurar antes de continuar."
            )
        return root_id

    def _pg_folder_is_under_root(self, folder_id, root_id, max_depth=12):
        """Walk parents up; True if any ancestor matches root_id."""
        gd = self._gdrive()
        current = folder_id
        for _ in range(max_depth):
            try:
                info = gd.get(current, fields="id,parents")
            except Exception:
                return False
            parents = info.get("parents") or []
            if not parents:
                return False
            parent = parents[0]
            if parent == root_id:
                return True
            current = parent
        return False

    def _pg_folder_looks_like_product(self, folder_id):
        """A product folder is the parent of a product-level IMAGENS folder,
        or has attribute folders whose leaves contain reference folders with IMAGENS."""
        gd = self._gdrive()
        children = gd.list_children(folder_id, folders_only=True)
        for ch in children:
            if normalize_folder_name_match(ch.get("name") or "") == "IMAGENS":
                if self._is_product_level_imagens(ch["id"]):
                    return True
        try:
            _, variant_specs, _ = self._collect_variant_specs_from_attributes(folder_id)
        except Exception:
            return False
        return bool(variant_specs)

    def _pg_search_drive_folder_candidates_by_name(self, product_name):
        """Drive API name-based search across the SA-accessible drives.
        Returns a list of {id, name, parents}."""
        gd = self._gdrive()
        # Escape single quotes for Drive's q-language.
        safe_name = (product_name or "").replace("'", r"\'")
        q = (
            f"name = '{safe_name}' "
            f"and mimeType = '{DRIVE_FOLDER_MIME}' "
            f"and trashed = false"
        )
        call = gd.service().files().list(
            q=q,
            fields="files(id,name,parents)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        res = gd._execute(call)
        return res.get("files", []) or []

    def _pg_collect_template_name_translations(self, template):
        """Return the set of all unique name translations for a template
        (product.template.name is translate=True). Empty/None values are
        excluded. Languages tried: all active installed languages in
        res.lang. If only one language is active, returns a singleton set.
        """
        names = set()
        # Always include the current-context name (covers the no-multilang case)
        if template.name:
            names.add(template.name.strip())

        active_langs = self.env["res.lang"].with_context(active_test=False).search([
            ("active", "=", True),
        ])
        for lang in active_langs:
            code = lang.code
            if not code:
                continue
            try:
                translated = template.with_context(lang=code).name
            except Exception:
                continue
            if translated and translated.strip():
                names.add(translated.strip())
        names.discard("")
        return names

    def _pg_collect_known_gdrive_file_ids(self, template):
        """Return the set of Drive file IDs known to belong to this template
        (gathered from past Drive sync writes on template/variant/image/document)."""
        ids = set()
        if template.gdrive_main_image_file_id:
            ids.add(template.gdrive_main_image_file_id)
        for variant in template.with_context(active_test=False).product_variant_ids:
            if variant.gdrive_main_image_file_id:
                ids.add(variant.gdrive_main_image_file_id)
        variant_ids = template.product_variant_ids.ids
        images = self.env["product.image"].with_context(active_test=False).search([
            "|",
            ("product_tmpl_id", "=", template.id),
            ("product_variant_id", "in", variant_ids or [0]),
        ])
        for img in images:
            if img.gdrive_file_id:
                ids.add(img.gdrive_file_id)
        doc_domain = [
            "|",
            "&", ("res_model", "=", "product.template"), ("res_id", "=", template.id),
            "&", ("res_model", "=", "product.product"), ("res_id", "in", variant_ids or [0]),
        ]
        docs = self.env["product.document"].with_context(active_test=False).search(doc_domain)
        for doc in docs:
            if doc.gdrive_file_id:
                ids.add(doc.gdrive_file_id)
        ids.discard(False)
        ids.discard("")
        return ids

    def _pg_reverse_lookup_template_drive_folder(self, template, max_ancestor_depth=4):
        """Follow stored Drive file IDs (from past imports) up to their
        parent folders to find the product folder. Voting-based: the most
        common product-like ancestor wins, provided it has a clear majority.
        Returns folder id or None.
        """
        file_ids = self._pg_collect_known_gdrive_file_ids(template)
        if not file_ids:
            return None

        gd = self._gdrive()
        from collections import Counter
        candidates = Counter()
        files_with_any_match = 0

        for file_id in file_ids:
            try:
                info = gd.get(file_id, fields="id,parents")
            except Exception:
                continue
            parents = info.get("parents") or []
            if not parents:
                continue
            current = parents[0]
            for _depth in range(max_ancestor_depth):
                try:
                    if self._pg_folder_looks_like_product(current):
                        candidates[current] += 1
                        files_with_any_match += 1
                        break
                except Exception:
                    break
                try:
                    parent_info = gd.get(current, fields="id,parents")
                except Exception:
                    break
                up = parent_info.get("parents") or []
                if not up:
                    break
                current = up[0]

        if not candidates:
            return None

        best, vote_count = candidates.most_common(1)[0]
        # Require a clear majority among files we managed to trace
        if files_with_any_match == 0:
            return None
        majority_ratio = vote_count / files_with_any_match
        if majority_ratio < 0.6:
            _logger.info(
                "Reverse lookup for template %s (%s) inconclusive: top candidate %s "
                "has only %s/%s votes (%.0f%%). Falling back to name search.",
                template.id, template.name, best, vote_count, files_with_any_match,
                majority_ratio * 100,
            )
            return None

        _logger.info(
            "Reverse lookup matched template %s (%s) to Drive folder %s "
            "via %s/%s known file IDs (%.0f%%).",
            template.id, template.name, best, vote_count, files_with_any_match,
            majority_ratio * 100,
        )
        return best

    def _pg_resolve_template_drive_folder(self, template, persist=True):
        """Return Drive folder id for a product.template, resolving via the
        following chain (each step deterministic, no fuzzy matching):
          1) Cached pg_gdrive_folder_id on the template
          2) Reverse lookup via known gdrive_file_id from past imports
          3) Drive search by literal name under the configured root

        Raises UserError on missing root, no candidates, or empty name.
        """
        # 1) Cache hit
        if template.pg_gdrive_folder_id:
            gd = self._gdrive()
            try:
                info = gd.get(template.pg_gdrive_folder_id, fields="id,name,parents")
                if info and info.get("id"):
                    return info["id"]
            except Exception:
                _logger.warning(
                    "Cached pg_gdrive_folder_id %s for template %s is stale, re-resolving",
                    template.pg_gdrive_folder_id,
                    template.id,
                )

        # 2) Reverse lookup via known gdrive_file_id (data trail from past imports)
        root_id = self._pg_drive_root_id()
        reverse_found = self._pg_reverse_lookup_template_drive_folder(template)
        if reverse_found:
            if self._pg_folder_is_under_root(reverse_found, root_id):
                if persist:
                    template.sudo().write({"pg_gdrive_folder_id": reverse_found})
                return reverse_found
            else:
                _logger.info(
                    "Reverse lookup for template %s returned folder %s but it is "
                    "not under the configured root; ignoring.",
                    template.id, reverse_found,
                )

        # 3) Resolve by name - try ALL translations (PT, EN, etc.) because
        #    product.template.name is translate=True and the Drive folder name
        #    may correspond to any one of them.
        name_variants = self._pg_collect_template_name_translations(template)
        if not name_variants:
            raise UserError(
                f"Produto id={template.id} sem nome em nenhuma lingua; "
                f"nao da para resolver pasta Drive."
            )

        candidates = []
        seen_candidate_ids = set()
        for variant_name in name_variants:
            for c in self._pg_search_drive_folder_candidates_by_name(variant_name):
                cid = c.get("id")
                if cid and cid not in seen_candidate_ids:
                    seen_candidate_ids.add(cid)
                    candidates.append(c)
        if not candidates:
            tried = ", ".join(sorted(name_variants))
            raise UserError(
                f"Nenhuma pasta Drive encontrada para '{template.name}' "
                f"(tentadas as traducoes: {tried})."
            )

        # 4) Filter to candidates under the configured root
        under_root = [c for c in candidates if self._pg_folder_is_under_root(c["id"], root_id)]
        if not under_root:
            tried = ", ".join(sorted(name_variants))
            raise UserError(
                f"Encontradas {len(candidates)} pasta(s) Drive a bater em alguma "
                f"traducao de '{template.name}' (tentadas: {tried}) mas nenhuma "
                f"esta debaixo da raiz Drive configurada."
            )

        # 5) Filter to candidates that look like product folders
        product_like = [c for c in under_root if self._pg_folder_looks_like_product(c["id"])]
        if not product_like:
            tried = ", ".join(sorted(name_variants))
            raise UserError(
                f"Encontradas {len(under_root)} pasta(s) com nome a bater em "
                f"traducoes de '{template.name}' (tentadas: {tried}) debaixo "
                f"da raiz, mas nenhuma tem estrutura de produto (IMAGENS ou "
                f"atributos+refs)."
            )

        if len(product_like) > 1:
            # Multiple Drive folders share this product name with valid product
            # structure - the assumption is the same product is listed under
            # multiple categories with identical content. Pick the first, log
            # for visibility, and cache the choice so future runs are
            # deterministic; the user can manually override via
            # template.pg_gdrive_folder_id if a different folder is preferred.
            ids = ", ".join(c["id"] for c in product_like)
            _logger.info(
                "Drive name '%s' matched %s product-like folders; picking %s. Others: %s",
                name,
                len(product_like),
                product_like[0]["id"],
                ids,
            )

        resolved = product_like[0]["id"]
        if persist:
            template.sudo().write({"pg_gdrive_folder_id": resolved})
        return resolved

    # ----------------------------
    # References-only sync (default_code per variant, from Drive)
    # ----------------------------
    def _pg_match_variant_by_attribute_pairs(self, template, attribute_pairs):
        """Lookup-only match of a variant of `template` whose set of
        (attribute_name, value_name) equals `attribute_pairs`. No side effects.
        Returns a product.product or empty recordset.
        """
        if not attribute_pairs:
            return self.env["product.product"]
        target = {
            (self._normalize_match_key(a), self._normalize_match_key(v))
            for a, v in attribute_pairs
        }
        Variant = self.env["product.product"].with_context(active_test=False)
        for variant in template.with_context(active_test=False).product_variant_ids:
            pairs = {
                (
                    self._normalize_match_key(ptav.attribute_id.name),
                    self._normalize_match_key(ptav.product_attribute_value_id.name),
                )
                for ptav in variant.product_template_attribute_value_ids
            }
            if pairs == target:
                return variant
        return Variant

    def pg_fetch_references_plan(self, templates, variant_filter_ids=None):
        """Build a plan (no writes) for references-only sync of the given
        product.template recordset.

        When `variant_filter_ids` is provided, the returned plan is filtered
        to rows that concern those product.product ids: rows for matched
        variants in the filter set, plus resolve_error rows for the template
        (so the user still sees Drive-level failures that affect them).

        Returns a list of dicts, one per row, with keys:
          template_id, template_name, variant_id, variant_display,
          attributes_display, current_code, proposed_code, drive_folder_id,
          status, message
        """
        variant_filter = set(variant_filter_ids or [])
        plan = []
        Template = self.env["product.template"].with_context(active_test=False)
        for template in templates:
            template = Template.browse(template.id).exists()
            if not template:
                continue

            try:
                folder_id = self._pg_resolve_template_drive_folder(template, persist=True)
            except UserError as exc:
                plan.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "variant_id": False,
                    "variant_display": "",
                    "attributes_display": "",
                    "current_code": "",
                    "proposed_code": "",
                    "status": "resolve_error",
                    "message": str(exc),
                })
                continue
            except Exception as exc:
                _logger.exception("Unexpected error resolving Drive folder for %s", template.name)
                plan.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "variant_id": False,
                    "variant_display": "",
                    "attributes_display": "",
                    "current_code": "",
                    "proposed_code": "",
                    "status": "resolve_error",
                    "message": f"Erro inesperado: {exc}",
                })
                continue

            try:
                _, variant_specs, _ = self._collect_variant_specs_from_attributes(folder_id)
            except Exception as exc:
                _logger.exception("Failed to collect specs for %s (%s)", template.name, folder_id)
                plan.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "variant_id": False,
                    "variant_display": "",
                    "attributes_display": "",
                    "current_code": "",
                    "proposed_code": "",
                    "status": "resolve_error",
                    "message": f"Erro a ler estrutura no Drive: {exc}",
                })
                continue

            matched_variant_ids = set()
            template_rows = []
            for spec in variant_specs:
                proposed = (spec.get("default_code") or "").strip()
                attrs = spec.get("attributes") or []
                spec_folder_id = spec.get("folder_id") or ""
                attrs_display = " / ".join(f"{a}={v}" for a, v in attrs) or "(sem atributos)"
                variant = self._pg_match_variant_by_attribute_pairs(template, attrs)
                if not variant:
                    template_rows.append({
                        "template_id": template.id,
                        "template_name": template.name,
                        "variant_id": False,
                        "variant_display": "",
                        "attributes_display": attrs_display,
                        "current_code": "",
                        "proposed_code": proposed,
                        "drive_folder_id": spec_folder_id,
                        "status": "drive_extra_variant",
                        "message": "Spec do Drive nao tem variante correspondente em Odoo",
                    })
                    continue

                matched_variant_ids.add(variant.id)
                current = (variant.default_code or "").strip()
                if not proposed:
                    template_rows.append({
                        "template_id": template.id,
                        "template_name": template.name,
                        "variant_id": variant.id,
                        "variant_display": variant.display_name,
                        "attributes_display": attrs_display,
                        "current_code": current,
                        "proposed_code": "",
                        "drive_folder_id": spec_folder_id,
                        "status": "no_variant_match",
                        "message": "Drive nao tem default_code para esta variante",
                    })
                    continue

                if current == proposed:
                    status = "already_correct"
                    message = ""
                elif not current:
                    status = "fill"
                    message = ""
                else:
                    status = "overwrite"
                    message = f"Atual='{current}' -> Drive='{proposed}'"

                template_rows.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "variant_id": variant.id,
                    "variant_display": variant.display_name,
                    "attributes_display": attrs_display,
                    "current_code": current,
                    "proposed_code": proposed,
                    "drive_folder_id": spec_folder_id,
                    "status": status,
                    "message": message,
                })

            # Detect proposed-code duplication within the same template - strong
            # signal that the Drive folder structure has misnamed reference
            # folders (same code under different attribute paths).
            from collections import Counter
            code_counts = Counter(
                row["proposed_code"]
                for row in template_rows
                if row.get("proposed_code")
                and row.get("status") in ("fill", "overwrite", "already_correct")
            )
            duplicated_codes = {code for code, n in code_counts.items() if n > 1}
            if duplicated_codes:
                for row in template_rows:
                    if (
                        row.get("proposed_code") in duplicated_codes
                        and row.get("status") in ("fill", "overwrite", "already_correct")
                    ):
                        row["status"] = "duplicated_drive_code"
                        prev = (row.get("message") or "")
                        row["message"] = (
                            f"default_code '{row['proposed_code']}' aparece em multiplas "
                            f"pastas Drive deste produto - verificar estrutura do Drive."
                            + (f" ({prev})" if prev else "")
                        )

            plan.extend(template_rows)

            for variant in template.with_context(active_test=False).product_variant_ids:
                if variant.id in matched_variant_ids:
                    continue
                attrs_display = " / ".join(
                    f"{ptav.attribute_id.name}={ptav.product_attribute_value_id.name}"
                    for ptav in variant.product_template_attribute_value_ids
                ) or "(sem atributos)"
                plan.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "variant_id": variant.id,
                    "variant_display": variant.display_name,
                    "attributes_display": attrs_display,
                    "current_code": (variant.default_code or "").strip(),
                    "proposed_code": "",
                    "drive_folder_id": "",
                    "status": "odoo_extra_variant",
                    "message": "Variante em Odoo sem correspondencia no Drive",
                })

        if variant_filter:
            # Keep rows that target a variant in the filter set, plus
            # resolve_error rows (template-level Drive failures that affect
            # whatever the user selected).
            plan = [
                row for row in plan
                if (row.get("variant_id") in variant_filter)
                or row.get("status") == "resolve_error"
            ]

        return plan

    def pg_apply_references_plan(self, plan, mode="only_empty"):
        """Apply a plan returned by pg_fetch_references_plan.

        mode:
          - 'only_empty': only writes default_code where current is empty
          - 'force': also overwrites non-empty default_code (logged)

        Returns a dict with counters: applied, skipped_already, skipped_mode,
        conflicts, errors. Conflicts (proposed code already used by another
        product.product) are never written.
        """
        if mode not in ("only_empty", "force"):
            raise UserError(f"Modo invalido: {mode!r}. Esperado 'only_empty' ou 'force'.")

        Variant = self.env["product.product"].with_context(active_test=False)
        applied = 0
        skipped_already = 0
        skipped_mode = 0
        conflicts = 0
        errors = 0

        rows_to_apply = [
            row for row in (plan or [])
            if row.get("status") in ("fill", "overwrite")
            and row.get("variant_id")
            and row.get("proposed_code")
        ]
        if not rows_to_apply:
            for row in (plan or []):
                if row.get("status") == "already_correct":
                    skipped_already += 1
            return {
                "applied": applied,
                "skipped_already": skipped_already,
                "skipped_mode": skipped_mode,
                "conflicts": conflicts,
                "errors": errors,
            }

        proposed_codes = sorted({row["proposed_code"] for row in rows_to_apply})
        existing_users = Variant.search([("default_code", "in", proposed_codes)])
        existing_by_code = {}
        for variant in existing_users:
            existing_by_code.setdefault(variant.default_code, []).append(variant.id)

        for row in (plan or []):
            status = row.get("status")
            if status == "already_correct":
                skipped_already += 1
                continue
            if status not in ("fill", "overwrite"):
                continue
            variant_id = row.get("variant_id")
            proposed = row.get("proposed_code")
            if not (variant_id and proposed):
                continue

            if status == "overwrite" and mode == "only_empty":
                skipped_mode += 1
                continue

            other_users = [
                vid for vid in existing_by_code.get(proposed, [])
                if vid != variant_id
            ]
            if other_users:
                conflicts += 1
                row["status"] = "conflict_other_variant"
                row["message"] = (
                    f"default_code '{proposed}' ja usado por variant id(s) {other_users}; "
                    f"nao foi escrito"
                )
                continue

            try:
                Variant.browse(variant_id).write({"default_code": proposed})
                existing_by_code.setdefault(proposed, []).append(variant_id)
                applied += 1
                row["status"] = "applied"
            except Exception as exc:
                errors += 1
                row["status"] = "error"
                row["message"] = f"Erro ao escrever default_code: {exc}"
                _logger.exception(
                    "pg_fetch_references: error writing default_code on variant %s", variant_id
                )

        return {
            "applied": applied,
            "skipped_already": skipped_already,
            "skipped_mode": skipped_mode,
            "conflicts": conflicts,
            "errors": errors,
        }

    # ----------------------------
    # Attribute helpers
    # ----------------------------
    def _get_or_create_attribute(self, name):
        normalized_name = self._normalize_match_key(name)
        cache = self._cache_bucket("_attribute_cache")
        if normalized_name in cache:
            cached = cache[normalized_name]
            cached_id = cached.id if hasattr(cached, "id") else cached
            attr = self.env["product.attribute"].with_context(active_test=False).browse(cached_id).exists()
            if attr:
                cache[normalized_name] = attr.id
                return attr
            cache.pop(normalized_name, None)

        self._advisory_xact_lock(f"pg_product_update:attribute:{normalized_name}")
        attribute_model = self.env["product.attribute"].with_context(active_test=False)
        candidates = attribute_model.search([("name", "=ilike", (name or "").strip())], order="active desc, id asc")
        matching = candidates.filtered(lambda record: self._normalize_match_key(record.name) == normalized_name)
        attr = (matching.filtered("active")[:1] or matching[:1])
        if not attr:
            attr = self.env["product.attribute"].create({"name": name, "create_variant": "always"})
        elif len(matching) > 1:
            _logger.warning(
                "Duplicate product attributes detected for %s: ids=%s; using id=%s",
                name,
                matching.ids,
                attr.id,
            )
        cache[normalized_name] = attr.id
        return attr

    def _get_or_create_attribute_value(self, attribute, value_name):
        normalized_name = self._normalize_match_key(value_name)
        cache = self._cache_bucket("_attribute_value_cache")
        cache_key = (attribute.id, normalized_name)
        if cache_key in cache:
            cached = cache[cache_key]
            cached_id = cached.id if hasattr(cached, "id") else cached
            value = self.env["product.attribute.value"].with_context(active_test=False).browse(cached_id).exists()
            if value:
                cache[cache_key] = value.id
                return value
            cache.pop(cache_key, None)

        self._advisory_xact_lock(f"pg_product_update:attribute_value:{attribute.id}:{normalized_name}")
        value_model = self.env["product.attribute.value"].with_context(active_test=False)
        candidates = value_model.search(
            [("attribute_id", "=", attribute.id), ("name", "=ilike", (value_name or "").strip())],
            order="active desc, id asc",
        )
        matching = candidates.filtered(lambda record: self._normalize_match_key(record.name) == normalized_name)
        value = (matching.filtered("active")[:1] or matching[:1])
        if not value:
            value = self.env["product.attribute.value"].create(
                {"name": value_name, "attribute_id": attribute.id}
            )
        elif len(matching) > 1:
            _logger.warning(
                "Duplicate product attribute values detected for attribute=%s value=%s: ids=%s; using id=%s",
                attribute.id,
                value_name,
                matching.ids,
                value.id,
            )
        cache[cache_key] = value.id
        return value

    def _canonicalize_attribute_value_ids(self, attribute, values):
        canonical_ids = set()
        for value in values:
            canonical = self._get_or_create_attribute_value(attribute, value.name)
            canonical_ids.add(canonical.id)
        return sorted(canonical_ids)

    def _find_matching_attribute_lines(self, product, attribute):
        normalized_name = self._normalize_match_key(attribute.name)
        line_model = self.env["product.template.attribute.line"].with_context(active_test=False)
        lines = line_model.search(
            [("product_tmpl_id", "=", product.id)],
            order="active desc, id asc",
        )
        return lines.filtered(
            lambda line: self._normalize_match_key(line.attribute_id.name) == normalized_name
        )

    @contextmanager
    def _preservar_documentos_de_variante(self, product):
        """Mantem os documentos ligados as variantes ao longo de uma operacao que as recria.

        Apagar uma `product.template.attribute.line` faz o Odoo destruir e recriar as
        variantes do artigo, com ids novos. Os `product.document` continuam a apontar
        para o id antigo e ficam presos a um registo que ja nao existe: deixam de ser
        alcancaveis pelo produto, pelo site e pelo orcamento, e o proprio Odoo recusa
        le-los por API porque nao consegue validar acesso ao registo-alvo.

        Foi assim que se acumularam 5697 documentos orfaos, espalhados por 1790
        variantes mortas, ao longo de varias importacoes.

        A ponte entre a variante antiga e a nova e a **referencia interna**, que
        sobrevive a recriacao. O que nao tiver referencia — ou cuja combinacao
        desapareca de vez — passa para o artigo-pai em vez de ficar orfao: perde-se
        a especificidade da variante, mas o ficheiro continua alcancavel, que e
        infinitamente melhor do que ficar ilegivel.
        """
        doc_model = self.env["product.document"].with_context(active_test=False)
        variantes = product.product_variant_ids.with_context(active_test=False)
        ref_por_variante = {v.id: v.default_code for v in variantes}
        docs = doc_model.search(
            [("res_model", "=", "product.product"), ("res_id", "in", variantes.ids)]
        ) if variantes else doc_model.browse()
        antes = {doc.id: ref_por_variante.get(doc.res_id) for doc in docs}

        yield

        if not antes:
            return
        product.invalidate_recordset(["product_variant_ids"])
        novas = product.product_variant_ids.with_context(active_test=False)
        variante_por_ref = {v.default_code: v.id for v in novas if v.default_code}
        vivas = set(novas.ids)
        religados = para_o_artigo = 0
        for doc_id, referencia in antes.items():
            doc = doc_model.browse(doc_id)
            if not doc.exists() or doc.res_id in vivas:
                continue
            destino = variante_por_ref.get(referencia)
            if destino:
                doc.write({"res_id": destino})
                religados += 1
            else:
                doc.write({"res_model": "product.template", "res_id": product.id})
                para_o_artigo += 1
        if religados or para_o_artigo:
            _logger.info(
                "pg_product_update: variantes recriadas em product=%s; "
                "%s documentos religados pela referencia, %s passados para o artigo.",
                product.id, religados, para_o_artigo,
            )

    def _ensure_attribute_line(self, product, attribute, value_ids, prune_stale=False):
        """Garante a linha de atributo sem deixar documentos orfaos pelo caminho.

        Envolve-se a funcao inteira, e nao apenas os dois `unlink()`: escrever
        `value_ids` numa linha existente tambem altera as combinacoes e leva o Odoo
        a recriar variantes. Qualquer dos caminhos desta funcao pode destruir ids.
        """
        with self._preservar_documentos_de_variante(product):
            return self._ensure_attribute_line_bruto(
                product, attribute, value_ids, prune_stale=prune_stale
            )

    def _ensure_attribute_line_bruto(self, product, attribute, value_ids, prune_stale=False):
        normalized_name = self._normalize_match_key(attribute.name)
        self._advisory_xact_lock(f"pg_product_update:attribute_line:{product.id}:{normalized_name}")
        lines = self._find_matching_attribute_lines(product, attribute)
        requested_values = self.env["product.attribute.value"].browse(sorted(set(value_ids)))
        # When prune_stale is False, union in whatever values the existing lines
        # already carried (defensive merge). When True, the caller is asserting
        # that `value_ids` is the authoritative set and stale values should be
        # dropped — this prevents values renamed/removed in Drive from piling up
        # across imports.
        if prune_stale:
            merged_values = requested_values
        else:
            merged_values = requested_values
            for line in lines:
                for line_value in line.value_ids:
                    merged_values |= self._get_or_create_attribute_value(attribute, line_value.name)
        canonical_value_ids = self._canonicalize_attribute_value_ids(attribute, merged_values)
        canonical_lines = lines.filtered(lambda line: line.attribute_id.id == attribute.id)

        if canonical_lines:
            line = canonical_lines.filtered("active")[:1] or canonical_lines[:1]
            vals = {}
            if not line.active:
                vals["active"] = True
            if set(line.value_ids.ids) != set(canonical_value_ids):
                vals["value_ids"] = [(6, 0, canonical_value_ids)]
            if vals:
                line.write(vals)
            duplicate_lines = lines - line
            if duplicate_lines:
                _logger.warning(
                    "Merging duplicate logical attribute lines for product=%s attribute=%s duplicate_ids=%s duplicate_attribute_ids=%s canonical_id=%s",
                    product.id,
                    attribute.name,
                    duplicate_lines.ids,
                    duplicate_lines.mapped("attribute_id").ids,
                    line.id,
                )
                duplicate_lines.unlink()
            return line

        if lines:
            product.write(
                {
                    "attribute_line_ids": [
                        (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, canonical_value_ids)]})
                    ]
                }
            )
            line = self.env["product.template.attribute.line"].search(
                [("product_tmpl_id", "=", product.id), ("attribute_id", "=", attribute.id)],
                order="id desc",
                limit=1,
            )
            _logger.warning(
                "Replaced duplicate logical attribute lines for product=%s attribute=%s old_line_ids=%s old_attribute_ids=%s new_line_id=%s",
                product.id,
                attribute.name,
                lines.ids,
                lines.mapped("attribute_id").ids,
                line.id,
            )
            lines.unlink()
            return line

        product.write(
            {
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, canonical_value_ids)]})
                ]
            }
        )
        return self.env["product.template.attribute.line"].search(
            [("product_tmpl_id", "=", product.id), ("attribute_id", "=", attribute.id)],
            order="id desc",
            limit=1,
        )

    def _find_variant_by_value_ids(self, product, value_ids):
        desired = set(value_ids)
        for variant in product.product_variant_ids:
            variant_value_ids = set(
                variant.product_template_attribute_value_ids.mapped(
                    "product_attribute_value_id"
                ).ids
            )
            if variant_value_ids == desired:
                return variant
        return None

    def _pg_estimated_combination_count(self, attribute_values):
        estimated = 1
        for values in attribute_values.values():
            estimated *= max(1, len(values))
        return estimated

    def _pg_ensure_attributes_dynamic(self, attributes, product, estimated_count, variant_limit):
        # Switching create_variant to "dynamic" lets us avoid the cartesian
        # explosion that triggers Odoo's MAX_NUMBER_OF_VARIANTS UserError.
        # Existing variants on other templates keep working; we materialize
        # only the specific combinations Drive describes via
        # _pg_get_or_create_variant_for_combination.
        to_switch = attributes.filtered(lambda a: a.create_variant != "dynamic")
        if not to_switch:
            return
        _logger.warning(
            "Switching attributes %s to dynamic create_variant for product=%s estimated_combinations=%s exceeds limit=%s",
            to_switch.mapped("name"),
            product.id or "(new)",
            estimated_count,
            variant_limit,
        )
        to_switch.write({"create_variant": "dynamic"})

    def _pg_resolve_ptav_combination(self, product, value_map, spec_attributes):
        ptav_model = self.env["product.template.attribute.value"].with_context(active_test=False)
        ptavs = []
        for attr_name, value_name in spec_attributes:
            value = value_map.get((attr_name, value_name))
            if not value:
                return ptav_model
            ptav = ptav_model.search(
                [
                    ("product_tmpl_id", "=", product.id),
                    ("product_attribute_value_id", "=", value.id),
                ],
                limit=1,
            )
            if not ptav:
                return ptav_model
            ptavs.append(ptav.id)
        return ptav_model.browse(ptavs)

    def _pg_get_or_create_variant_for_combination(self, product, combination):
        if not combination:
            return self.env["product.product"]
        variant = product._get_variant_for_combination(combination)
        if variant:
            return variant
        return product._create_product_variant(combination)

    # ----------------------------
    # Category creation + images (Drive-aware)
    # ----------------------------
    def create_or_get_category(self, name, parent_id=None, img_path=None, gdrive_folder_id=None):
        category = self.env["product.category"].search(
            [("name", "=", name), ("parent_id", "=", parent_id)], limit=1
        )
        if not category:
            category = self.env["product.category"].create({"name": name, "parent_id": parent_id})

        if gdrive_folder_id:
            try:
                gd = self._gdrive()
                children = gd.list_children(gdrive_folder_id, folders_only=False)
                image_files = [
                    f for f in children
                    if f.get("mimeType") != DRIVE_FOLDER_MIME
                    and (f.get("name") or "").lower().endswith((".jpg", ".jpeg", ".png"))
                ]
                image_files.sort(key=lambda x: (x.get("name") or "").lower())

                vals = {}
                if len(image_files) > 0:
                    vals["cat_image_1"] = base64.b64encode(gd.download_bytes(image_files[0]["id"]))
                if len(image_files) > 1:
                    vals["cat_image_2"] = base64.b64encode(gd.download_bytes(image_files[1]["id"]))

                if vals:
                    category.write(vals)
                    _logger.info("Uploaded category images for: %s", name)
            except Exception as e:
                _logger.warning("Category image upload failed for %s: %s", name, e)

        return category

    # ----------------------------
    # Image resize
    # ----------------------------
    def resize_image(self, image_data, max_width=1920, max_height=1920):
        image = Image.open(BytesIO(image_data))
        try:
            resample = Image.Resampling.LANCZOS  # Pillow >=10
        except Exception:
            resample = Image.ANTIALIAS
        image.thumbnail((max_width, max_height), resample)
        output = BytesIO()
        if image.mode == "RGBA":
            image = image.convert("RGB")
        image.save(output, format="JPEG")
        return output.getvalue()

    # ----------------------------
    # Upload images (Drive)
    # folder_path param is a Drive folder ID
    # ----------------------------
    def upload_images(
        self,
        folder_path,
        product,
        is_main_product=True,
        variant_names=None,
        variant=None,
        force_refresh=True,
    ):
        variant_names = variant_names or []
        gd = self._gdrive()

        processed_images = set()
        main_image_uploaded = False
        any_image_found = False
        seen_file_ids = set()
        first_image_info = None
        variant_image_related = self._variant_image_related_to_template() if variant else False
        variant_image_field = self._variant_image_field_name() if variant else "image_1920"
        image_domain = [("product_tmpl_id", "=", product.id)]
        if variant:
            image_domain.append(("product_variant_id", "=", variant.id))
        existing_images = self.env["product.image"].search(image_domain)
        images_by_file_id = {
            img.gdrive_file_id: img for img in existing_images if img.gdrive_file_id
        }
        images_by_name = {
            img.name: img for img in existing_images if not img.gdrive_file_id and img.name
        }

        _logger.info(
            "Uploading images from Drive folder ID: %s for %s",
            folder_path,
            "main product" if is_main_product else "variant",
        )
        if variant:
            _logger.info(
                "Variant image field related to template: %s (variant=%s code=%s)",
                variant_image_related,
                variant.id,
                variant.default_code,
            )
            _logger.info(
                "Variant image state pre-sync: variant=%s code=%s %s=%s gdrive_id=%s gdrive_md5=%s",
                variant.id,
                variant.default_code,
                variant_image_field,
                bool(getattr(variant, variant_image_field)),
                variant.gdrive_main_image_file_id,
                variant.gdrive_main_image_md5,
            )

        stack = [folder_path]
        while stack:
            current_folder_id = stack.pop()
            children = gd.list_children(current_folder_id, folders_only=False)

            for ch in children:
                if ch.get("mimeType") == DRIVE_FOLDER_MIME:
                    stack.append(ch["id"])

            files = [
                ch for ch in children
                if ch.get("mimeType") != DRIVE_FOLDER_MIME
                and (ch.get("name") or "").lower() != "thumbs.db"
            ]
            files.sort(key=lambda x: (x.get("name") or "").lower())

            for f in files:
                name = f.get("name") or ""
                if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue

                try:
                    any_image_found = True
                    if not first_image_info:
                        first_image_info = {
                            "id": f.get("id"),
                            "md5": f.get("md5Checksum"),
                            "size": f.get("size"),
                            "name": name,
                        }
                    _logger.info(
                        "Variant image candidate: variant=%s file=%s id=%s md5=%s",
                        variant.id if variant else None,
                        name,
                        f.get("id"),
                        f.get("md5Checksum"),
                    )
                    self._trace_drive_file_event("image_candidate", f, imagens_id=folder_path)
                    # IMPORTANT: Use Drive md5Checksum if available. If not, hash bytes.
                    image_hash = f.get("md5Checksum")
                    image_id = f.get("id")
                    if image_id:
                        seen_file_ids.add(image_id)
                    if image_hash and image_hash in processed_images:
                        _logger.info("Skipping duplicate image: %s", name)
                        self._trace_drive_file_event("image_skip", f, "Duplicate image hash already processed", imagens_id=folder_path)
                        continue
                    if image_hash:
                        processed_images.add(image_hash)

                    existing = images_by_file_id.get(image_id) or images_by_name.get(name)
                    if not force_refresh and existing and existing.gdrive_md5 == image_hash:
                        _logger.info("Skipping unchanged image: %s", name)
                        self._trace_drive_file_event("image_skip", f, "Unchanged image md5", imagens_id=folder_path)
                        continue

                    should_skip, skip_reason = self._should_skip_drive_file(f, DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT)
                    if should_skip:
                        _logger.warning("Skipping oversized image %s: %s", name, skip_reason)
                        self._trace_drive_file_event("image_skip", f, skip_reason, imagens_id=folder_path)
                        continue

                    if image_hash and image_id and not main_image_uploaded:
                        if variant:
                            if (
                                variant.gdrive_main_image_file_id == image_id
                                and variant.gdrive_main_image_md5 == image_hash
                            ):
                                if not force_refresh:
                                    main_image_uploaded = True
                                    if not variant_image_related and not getattr(variant, variant_image_field):
                                        self._trace_drive_file_event("image_download", f, "Restoring unchanged variant thumbnail from Drive", imagens_id=folder_path)
                                        image_data = gd.download_bytes(f["id"])
                                        if len(image_data) > DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT:
                                            image_data = self.resize_image(image_data)
                                        variant.write(
                                            {variant_image_field: base64.b64encode(image_data)}
                                        )
                                        _logger.info(
                                            "Restored variant thumbnail from Drive: %s",
                                            name,
                                        )
                                    else:
                                        _logger.info("Skipping unchanged variant thumbnail: %s", name)
                                    continue
                        elif is_main_product and not variant_names:
                            if (
                                product.gdrive_main_image_file_id == image_id
                                and product.gdrive_main_image_md5 == image_hash
                            ):
                                if not force_refresh:
                                    main_image_uploaded = True
                                    if not product.image_1920:
                                        self._trace_drive_file_event("image_download", f, "Restoring unchanged product thumbnail from Drive", imagens_id=folder_path)
                                        image_data = gd.download_bytes(f["id"])
                                        if len(image_data) > DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT:
                                            image_data = self.resize_image(image_data)
                                        product.write({"image_1920": base64.b64encode(image_data)})
                                        _logger.info(
                                            "Restored product thumbnail from Drive: %s",
                                            name,
                                        )
                                    else:
                                        _logger.info("Skipping unchanged product thumbnail: %s", name)
                                    continue

                    self._trace_drive_file_event("image_download", f, "Downloading image payload", imagens_id=folder_path)
                    image_data = gd.download_bytes(f["id"])
                    if len(image_data) > DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT:
                        image_data = self.resize_image(image_data)
                        self._trace_drive_file_event("image_resize", f, "Resized downloaded image after payload threshold", imagens_id=folder_path)

                    if not image_hash:
                        image_hash = hashlib.sha256(image_data).hexdigest()
                        if image_hash in processed_images:
                            _logger.info("Skipping duplicate image: %s", name)
                            continue
                        processed_images.add(image_hash)

                    image_encoded = base64.b64encode(image_data)

                    if variant:
                        if not main_image_uploaded:
                            if (
                                variant.gdrive_main_image_file_id == image_id
                                and variant.gdrive_main_image_md5 == image_hash
                            ):
                                main_image_uploaded = True
                                continue
                            if variant_image_related:
                                if existing:
                                    existing.write(
                                        {
                                            "name": name,
                                            "image_1920": image_encoded,
                                            "gdrive_file_id": image_id,
                                            "gdrive_md5": image_hash,
                                            "sequence": 0,
                                        }
                                    )
                                else:
                                    self.env["product.image"].create(
                                        {
                                            "product_tmpl_id": product.id,
                                            "product_variant_id": variant.id,
                                            "name": name,
                                            "image_1920": image_encoded,
                                            "sequence": 0,
                                            "gdrive_file_id": image_id,
                                            "gdrive_md5": image_hash,
                                        }
                                    )
                                variant.write(
                                    {
                                        "gdrive_main_image_file_id": image_id,
                                        "gdrive_main_image_md5": image_hash,
                                    }
                                )
                                _logger.info(
                                    "Set first variant image as main media record: %s",
                                    name,
                                )
                            else:
                                variant.write(
                                    {
                                        variant_image_field: image_encoded,
                                        "gdrive_main_image_file_id": image_id,
                                        "gdrive_main_image_md5": image_hash,
                                    }
                                )
                                _logger.info("Set first variant image as thumbnail: %s", name)
                            main_image_uploaded = True
                        else:
                            if existing:
                                existing.write(
                                    {
                                        "name": name,
                                        "image_1920": image_encoded,
                                        "gdrive_file_id": image_id,
                                        "gdrive_md5": image_hash,
                                    }
                                )
                            else:
                                self.env["product.image"].create(
                                    {
                                        "product_tmpl_id": product.id,
                                        "product_variant_id": variant.id,
                                        "name": name,
                                        "image_1920": image_encoded,
                                        "sequence": 10,
                                        "gdrive_file_id": image_id,
                                        "gdrive_md5": image_hash,
                                    }
                                )
                            _logger.info("Added extra variant media: %s", name)
                    elif is_main_product and not variant_names:
                        if not main_image_uploaded:
                            if (
                                product.gdrive_main_image_file_id == image_id
                                and product.gdrive_main_image_md5 == image_hash
                            ):
                                main_image_uploaded = True
                                continue
                            product.write(
                                {
                                    "image_1920": image_encoded,
                                    "gdrive_main_image_file_id": image_id,
                                    "gdrive_main_image_md5": image_hash,
                                }
                            )
                            main_image_uploaded = True
                            _logger.info("Set first image as thumbnail: %s", name)
                        else:
                            if existing:
                                existing.write(
                                    {
                                        "name": name,
                                        "image_1920": image_encoded,
                                        "gdrive_file_id": image_id,
                                        "gdrive_md5": image_hash,
                                    }
                                )
                            else:
                                self.env["product.image"].create(
                                    {
                                        "product_tmpl_id": product.id,
                                        "name": name,
                                        "image_1920": image_encoded,
                                        "sequence": 10,
                                        "gdrive_file_id": image_id,
                                        "gdrive_md5": image_hash,
                                    }
                                )
                            _logger.info("Added extra media: %s", name)

                except UnidentifiedImageError as e:
                    _logger.warning("UnidentifiedImageError for file %s: %s", name, e)
                    self._trace_drive_file_event("image_error", f, f"UnidentifiedImageError: {e}", imagens_id=folder_path)
                except Exception as e:
                    _logger.error("Error processing image %s: %s", name, e)
                    self._trace_drive_file_event("image_error", f, str(e), imagens_id=folder_path)

        if seen_file_ids:
            stale_images = existing_images.filtered(
                lambda img: img.gdrive_file_id and img.gdrive_file_id not in seen_file_ids
            )
            stale_images.unlink()
        elif not any_image_found and existing_images:
            existing_images.unlink()
            _logger.info(
                "Cleared %s images for %s due to empty folder: %s",
                len(existing_images),
                "variant" if variant else "product",
                folder_path,
            )
        if variant and not any_image_found:
            _logger.info(
                "No images found for variant folder: %s (variant=%s)",
                folder_path,
                variant.id,
            )
        if (
            variant
            and any_image_found
            and not getattr(variant, variant_image_field)
            and first_image_info
            and first_image_info.get("id")
        ):
            should_skip, skip_reason = self._should_skip_drive_file(first_image_info, DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT)
            if should_skip:
                self._trace_drive_file_event("image_skip", first_image_info, skip_reason, imagens_id=folder_path)
                first_image_info = None
            else:
                self._trace_drive_file_event("image_download", first_image_info, "Restoring thumbnail from first image fallback", imagens_id=folder_path)
                image_data = gd.download_bytes(first_image_info["id"])
                if len(image_data) > DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT:
                    image_data = self.resize_image(image_data)
                variant.write(
                    {
                        variant_image_field: base64.b64encode(image_data),
                        "gdrive_main_image_file_id": first_image_info["id"],
                        "gdrive_main_image_md5": first_image_info.get("md5"),
                    }
                )
                _logger.info(
                    "Restored variant thumbnail from first image: %s (variant=%s)",
                    first_image_info.get("name"),
                    variant.id,
                )
        if variant and not main_image_uploaded:
            if variant_image_related:
                variant.write(
                    {
                        "gdrive_main_image_file_id": False,
                        "gdrive_main_image_md5": False,
                    }
                )
            else:
                variant.write(
                    {
                        variant_image_field: False,
                        "gdrive_main_image_file_id": False,
                        "gdrive_main_image_md5": False,
                    }
                )
            _logger.info(
                "Cleared variant thumbnail due to no main image: variant=%s",
                variant.id,
            )
        if variant:
            _logger.info(
                "Variant image state post-sync: variant=%s code=%s %s=%s gdrive_id=%s gdrive_md5=%s",
                variant.id,
                variant.default_code,
                variant_image_field,
                bool(getattr(variant, variant_image_field)),
                variant.gdrive_main_image_file_id,
                variant.gdrive_main_image_md5,
            )
        if is_main_product and not variant and not main_image_uploaded:
            product.write(
                {
                    "image_1920": False,
                    "gdrive_main_image_file_id": False,
                    "gdrive_main_image_md5": False,
                }
            )
            _logger.info("Cleared product thumbnail for folder: %s", folder_path)

    # ----------------------------
    # Product processing (Drive)
    # ----------------------------
    def _clear_product_media(self, product):
        self.env["ir.attachment"].search(
            [("res_model", "=", "product.template"), ("res_id", "=", product.id)]
        ).unlink()
        self.env["product.image"].search([("product_tmpl_id", "=", product.id)]).unlink()
        product.write({"image_1920": False})

    def _clear_variant_media(self, variant):
        self.env["product.image"].search([("product_variant_id", "=", variant.id)]).unlink()
        variant.write({"image_1920": False})

    def _get_specific_or_shared_folder(self, variant_folder, folder_name, shared_folders):
        gd = self._gdrive()
        normalized = normalize_folder_name_match(folder_name)
        specific = gd.find_child_folder(variant_folder, normalized)
        _logger.info(
            "Doc folder lookup: variant_folder=%s name=%s normalized=%s specific=%s shared=%s",
            variant_folder,
            folder_name,
            normalized,
            specific["id"] if specific else None,
            shared_folders.get(normalized),
        )
        return specific["id"] if specific else shared_folders.get(normalized)

    def _process_additional_docs(
        self,
        product,
        variant_path,
        shared_folders,
        base_path,
        res_model="product.template",
        res_id=None,
        product_variant=None,
        force_refresh=True,
    ):
        gd = self._gdrive()
        doc_model = self.env["product.document"]
        res_id = res_id or product.id

        for doc_type in ["3D", "FICHA TECNICA", "CERTIFICADO CONFORMIDADE"]:
            folder_id = self._get_specific_or_shared_folder(variant_path, doc_type, shared_folders)
            if not folder_id:
                _logger.info(
                    "Docs folder missing: type=%s variant_path=%s",
                    doc_type,
                    variant_path,
                )
                continue

            files = [
                f for f in gd.list_children(folder_id, folders_only=False)
                if f.get("mimeType") != DRIVE_FOLDER_MIME
                and (f.get("name") or "").lower() != "thumbs.db"
            ]
            files.sort(key=lambda x: (x.get("name") or "").lower())
            if files:
                sample_names = [f.get("name") for f in files[:10]]
                _logger.info(
                    "Docs folder contents: type=%s folder_id=%s count=%s sample=%s",
                    doc_type,
                    folder_id,
                    len(files),
                    sample_names,
                )
            else:
                _logger.info(
                    "Docs folder empty: type=%s folder_id=%s",
                    doc_type,
                    folder_id,
                )

            if "tipo_documento" in doc_model._fields:
                existing_docs = doc_model.search(
                    [
                        ("res_model", "=", res_model),
                        ("res_id", "=", res_id),
                        ("tipo_documento", "=", doc_type),
                    ]
                )
            else:
                existing_docs = doc_model.search(
                    [
                        ("res_model", "=", res_model),
                        ("res_id", "=", res_id),
                        ("name", "ilike", f"{doc_type} - "),
                    ]
                )
            docs_by_file_id = {
                doc.gdrive_file_id: doc for doc in existing_docs if doc.gdrive_file_id
            }
            docs_by_name = {
                doc.name: doc for doc in existing_docs if not doc.gdrive_file_id and doc.name
            }
            seen_file_ids = set()
            created = 0
            updated = 0
            skipped = 0

            for f in files:
                try:
                    file_id = f.get("id")
                    file_md5 = f.get("md5Checksum")
                    if file_id:
                        seen_file_ids.add(file_id)
                    self._trace_drive_file_event("document_candidate", f, f"type={doc_type}", imagens_id=variant_path)
                    existing = docs_by_file_id.get(file_id) or docs_by_name.get(
                        f"{doc_type} - {f.get('name')}"
                    )
                    desired_shown_on_product_page = res_model == "product.template" and not product_variant
                    desired_variant_id = (
                        product_variant.id
                        if product_variant and "product_variant_id" in doc_model._fields
                        else False
                    )
                    metadata_requires_update = bool(
                        existing and (
                            ("shown_on_product_page" in doc_model._fields and existing.shown_on_product_page != desired_shown_on_product_page)
                            or ("product_variant_id" in doc_model._fields and (existing.product_variant_id.id if existing.product_variant_id else False) != desired_variant_id)
                        )
                    )
                    if not force_refresh and existing and existing.gdrive_md5 == file_md5 and not metadata_requires_update:
                        skipped += 1
                        self._trace_drive_file_event("document_skip", f, "Unchanged document md5", imagens_id=variant_path)
                        continue

                    should_skip, skip_reason = self._should_skip_drive_file(f, DRIVE_DOCUMENT_DOWNLOAD_HARD_LIMIT)
                    if should_skip:
                        skipped += 1
                        _logger.warning("Skipping oversized document %s: %s", f.get("name"), skip_reason)
                        self._trace_drive_file_event("document_skip", f, f"{doc_type} | {skip_reason}", imagens_id=variant_path)
                        continue

                    attachment_name = f"{doc_type} - {f.get('name')}"
                    self._trace_drive_file_event("document_download", f, f"type={doc_type}", imagens_id=variant_path)
                    file_data = base64.b64encode(gd.download_bytes(f["id"]))

                    vals = {
                        "name": attachment_name,
                        "datas": file_data,
                        "res_id": res_id,
                        "res_model": res_model,
                        "active": True,
                        "shown_on_product_page": desired_shown_on_product_page,
                    }
                    if "product_tmpl_id" in doc_model._fields:
                        vals["product_tmpl_id"] = product.id
                    if product_variant and "product_variant_id" in doc_model._fields:
                        vals["product_variant_id"] = product_variant.id
                    if "tipo_documento" in doc_model._fields:
                        vals["tipo_documento"] = doc_type

                    if existing:
                        vals["gdrive_file_id"] = file_id
                        vals["gdrive_md5"] = file_md5
                        existing.write(vals)
                        updated += 1
                        _logger.info(
                            "Doc updated: type=%s res_model=%s res_id=%s name=%s file_id=%s",
                            doc_type,
                            res_model,
                            res_id,
                            attachment_name,
                            file_id,
                        )
                    else:
                        vals["gdrive_file_id"] = file_id
                        vals["gdrive_md5"] = file_md5
                        doc_model.create(vals)
                        created += 1
                        _logger.info(
                            "Doc created: type=%s res_model=%s res_id=%s name=%s file_id=%s",
                            doc_type,
                            res_model,
                            res_id,
                            attachment_name,
                            file_id,
                        )
                except Exception as e:
                    _logger.error(
                        "Error attaching document %s for product %s: %s",
                        f.get("name"),
                        product.name,
                        e,
                    )
                    self._append_context_job_trace(
                        "document_error",
                        f"{doc_type} / {f.get('name')} | size={self._format_bytes(self._drive_file_size_bytes(f))}: {e}",
                    )

            if seen_file_ids:
                stale_docs = existing_docs.filtered(
                    lambda doc: doc.gdrive_file_id and doc.gdrive_file_id not in seen_file_ids
                )
                stale_docs.unlink()
            _logger.info(
                "Docs sync summary: type=%s res_model=%s res_id=%s existing=%s created=%s updated=%s skipped=%s stale_deleted=%s",
                doc_type,
                res_model,
                res_id,
                len(existing_docs),
                created,
                updated,
                skipped,
                len(stale_docs) if seen_file_ids else 0,
            )

    def _drive_folder_has_imagens(self, folder_id):
        gd = self._gdrive()
        for ch in gd.list_children(folder_id, folders_only=True):
            if self.normalize_folder_name(ch.get("name") or "").upper() == "IMAGENS":
                return True
        return False

    def _split_drive_folders(self, folder_id):
        gd = self._gdrive()
        shared_folders = {}
        custom_folders = []
        metadata_folders = self._get_drive_metadata_folders()

        for entry in gd.list_children(folder_id, folders_only=True):
            upper = normalize_folder_name_match(entry.get("name") or "")
            if upper in metadata_folders:
                shared_folders[upper] = entry["id"]
            else:
                custom_folders.append(entry)

        return shared_folders, custom_folders

    def _is_product_level_imagens(self, imagens_folder_id):
        cache = self._cache_bucket("_product_imagens_cache")
        if imagens_folder_id in cache:
            return cache[imagens_folder_id]

        is_product_level, reason = self._explain_product_level_imagens(imagens_folder_id)
        if not is_product_level:
            _logger.info(
                "Skipping IMAGENS %s: %s",
                imagens_folder_id,
                reason,
            )
        cache[imagens_folder_id] = is_product_level
        return is_product_level

    def _get_first_image_base64(self, folder_id):
        gd = self._gdrive()
        children = gd.list_children(folder_id, folders_only=False)
        files = [
            ch for ch in children
            if ch.get("mimeType") != DRIVE_FOLDER_MIME
            and (ch.get("name") or "").lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ]
        files.sort(key=lambda x: (x.get("name") or "").lower())
        if not files:
            return None
        should_skip, _skip_reason = self._should_skip_drive_file(files[0], DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT)
        if should_skip:
            return None
        image_data = gd.download_bytes(files[0]["id"])
        if len(image_data) > DRIVE_IMAGE_DOWNLOAD_HARD_LIMIT:
            image_data = self.resize_image(image_data)
        return base64.b64encode(image_data)

    def _collect_variant_specs_from_attributes(self, product_path):
        gd = self._gdrive()
        shared_folders, attribute_roots = self._split_drive_folders(product_path)
        attribute_values = {}
        specs = []

        def add_value(attr_name, value_name):
            attribute_values.setdefault(attr_name, set()).add(value_name)

        def walk_attr_folder(attr_folder_id, attr_name, current_attrs):
            for value_folder in gd.list_children(attr_folder_id, folders_only=True):
                value_name = self.normalize_folder_name(value_folder.get("name") or "")
                add_value(attr_name, value_name)
                walk_value_folder(value_folder["id"], current_attrs + [(attr_name, value_name)])

        def walk_value_folder(value_folder_id, current_attrs):
            children = gd.list_children(value_folder_id, folders_only=True)
            if not children:
                return

            ref_folders = []
            attr_folders = []
            metadata_folders = self._get_drive_metadata_folders()
            for ch in children:
                ch_name = normalize_folder_name_match(ch.get("name") or "")
                if ch_name in metadata_folders:
                    continue
                if self._drive_folder_has_imagens(ch["id"]):
                    ref_folders.append(ch)
                else:
                    attr_folders.append(ch)

            for ref in ref_folders:
                ref_name = self.normalize_folder_name(ref.get("name") or "")
                specs.append(
                    {
                        "default_code": self.extract_default_code(ref_name),
                        "folder_id": ref["id"],
                        "attributes": list(current_attrs),
                    }
                )

            for attr_folder in attr_folders:
                attr_name = self.normalize_folder_name(attr_folder.get("name") or "")
                walk_attr_folder(attr_folder["id"], attr_name, current_attrs)

        for attr_folder in attribute_roots:
            attr_name = self.normalize_folder_name(attr_folder.get("name") or "")
            walk_attr_folder(attr_folder["id"], attr_name, [])

        return shared_folders, specs, attribute_values

    def _find_existing_product_template_for_drive_product(self, product_name, variant_specs):
        template_model = self.env["product.template"].with_context(active_test=False)

        product = template_model.search([("name", "=", product_name)], limit=1)
        if product:
            return product, "name"

        variant_codes = sorted(
            {
                spec.get("default_code")
                for spec in (variant_specs or [])
                if spec.get("default_code")
            }
        )
        if not variant_codes:
            return template_model, None

        variant_matches = self.env["product.product"].with_context(active_test=False).search(
            [("default_code", "in", variant_codes)]
        )
        if not variant_matches:
            return template_model, None

        matched_templates = variant_matches.mapped("product_tmpl_id")
        if len(matched_templates) != 1:
            _logger.warning(
                "Drive product %s matched multiple templates by default_code overlap: %s",
                product_name,
                matched_templates.ids,
            )
            return template_model, None

        overlap = sorted(
            set(variant_codes).intersection(
                set(matched_templates.product_variant_ids.with_context(active_test=False).mapped("default_code"))
            )
        )
        if not overlap:
            return template_model, None

        _logger.info(
            "Matched Drive product %s to archived/renamed template %s (%s) by variant codes: %s",
            product_name,
            matched_templates.id,
            matched_templates.name,
            ", ".join(overlap[:10]),
        )
        return matched_templates, "default_code"

    def process_multi_variant_product(self, category_id, pos_category_id, product_path):
        gd = self._gdrive()

        shared_folders, variant_specs, attribute_values = self._collect_variant_specs_from_attributes(
            product_path
        )
        _, custom_folders = self._split_drive_folders(product_path)
        product_name = self.normalize_folder_name(gd.get(product_path, fields="name")["name"])
        normalized_product_name = self._normalize_match_key(product_name)

        self._advisory_xact_lock(f"pg_product_update:product:{normalized_product_name}")

        if not variant_specs and custom_folders:
            _logger.warning(
                "Skipping product template creation for %s: folder %s has attribute-like folders but no reference folders",
                product_name,
                product_path,
            )
            return

        product, match_reason = self._find_existing_product_template_for_drive_product(
            product_name,
            variant_specs,
        )
        if not product:
            vals = {
                "name": product_name,
                "categ_id": category_id,
                "active": True,
                "is_published": True,
            }

            # POS (optional)
            if (
                pos_category_id
                and self._pos_available()
                and "pos_categ_ids" in self.env["product.template"]._fields
            ):
                vals["pos_categ_ids"] = [(4, pos_category_id)]

            product = self.env["product.template"].create(vals)
        else:
            was_archived = not product.active
            vals = {
                "name": product_name,
                "categ_id": category_id,
                "active": True,
                "is_published": True,
            }
            if (
                pos_category_id
                and self._pos_available()
                and "pos_categ_ids" in self.env["product.template"]._fields
            ):
                vals["pos_categ_ids"] = [(4, pos_category_id)]
            product.write(vals)
            if was_archived:
                _logger.info(
                    "Reactivated archived product template %s (%s) for Drive product %s via %s match",
                    product.id,
                    product.name,
                    product_path,
                    match_reason or "unknown",
                )

        imagens_folder = None
        try:
            self._apply_related_products_from_drive(product, product_path)
            imagens_folder = self._get_specific_or_shared_folder(product_path, "IMAGENS", shared_folders)
            if imagens_folder:
                self.upload_images(imagens_folder, product, is_main_product=True, force_refresh=False)

            self._process_additional_docs(
                product,
                product_path,
                shared_folders,
                product_path,
                force_refresh=False,
            )
        except Exception as e:
            _logger.error("Error processing product images for %s: %s", product_name, e)

        try:
            tmpl_main_id = product.gdrive_main_image_file_id if "gdrive_main_image_file_id" in product._fields else None
            tmpl_main_md5 = product.gdrive_main_image_md5 if "gdrive_main_image_md5" in product._fields else None
            _logger.info(
                "Template pre-variant: product=%s image_1920=%s gdrive_id=%s gdrive_md5=%s",
                product.id,
                bool(product.image_1920),
                tmpl_main_id,
                tmpl_main_md5,
            )

            if not variant_specs:
                _logger.info("No attribute-based variants found for %s", product_name)
                return

            attr_map = {}
            value_map = {}
            attribute_lines_changed = False

            for attr_name in attribute_values:
                attr_map[attr_name] = self._get_or_create_attribute(attr_name)

            estimated_count = self._pg_estimated_combination_count(attribute_values)
            variant_limit = product._pg_dynamic_variant_limit()
            use_dynamic_mode = estimated_count > variant_limit
            if use_dynamic_mode:
                attributes_recordset = self.env["product.attribute"]
                for attribute in attr_map.values():
                    attributes_recordset |= attribute
                self._pg_ensure_attributes_dynamic(
                    attributes_recordset, product, estimated_count, variant_limit
                )

            for attr_name, values in attribute_values.items():
                attribute = attr_map[attr_name]

                value_ids = []
                for value_name in sorted(values):
                    value = self._get_or_create_attribute_value(attribute, value_name)
                    value_map[(attr_name, value_name)] = value
                    value_ids.append(value.id)

                if value_ids:
                    existing_line = product.attribute_line_ids.filtered(lambda l: l.attribute_id.id == attribute.id)[:1]
                    if not existing_line or set(existing_line.value_ids.ids) != set(value_ids):
                        attribute_lines_changed = True
                    self._ensure_attribute_line(product, attribute, value_ids, prune_stale=True)

            if (
                not use_dynamic_mode
                and hasattr(product, "_create_variant_ids")
                and (attribute_lines_changed or len(product.product_variant_ids) <= 1)
            ):
                product._create_variant_ids()

            desired_sets = set()
            all_variants = product.with_context(active_test=False).product_variant_ids
            # Sort active-first so that when multiple variants share a default_code
            # or PTAV combination, the active one wins and we never route writes to
            # an archived ghost variant.
            ordered_variants = all_variants.sorted(key=lambda v: (0 if v.active else 1, v.id))
            variant_cache = {}
            for v in ordered_variants:
                if v.default_code and v.default_code not in variant_cache:
                    variant_cache[v.default_code] = v
            variant_by_combination = {}
            for variant in ordered_variants:
                combination = frozenset(
                    variant.product_template_attribute_value_ids.mapped("product_attribute_value_id").ids
                )
                variant_by_combination.setdefault(combination, variant)

            seen_spec_codes = {}
            deduped_specs = []
            for spec in variant_specs:
                code = spec.get("default_code")
                if code and code in seen_spec_codes:
                    _logger.warning(
                        "Duplicate default_code in Drive specs for product=%s code=%s: keeping first folder=%s, ignoring folder=%s",
                        product.id,
                        code,
                        seen_spec_codes[code],
                        spec.get("folder_id"),
                    )
                    continue
                if code:
                    seen_spec_codes[code] = spec.get("folder_id")
                deduped_specs.append(spec)
            variant_specs = deduped_specs
            variant_image_related = self._variant_image_related_to_template()
            for spec in variant_specs:
                value_ids = [
                    value_map[(attr_name, value_name)].id
                    for attr_name, value_name in spec["attributes"]
                ]
                desired_sets.add(frozenset(value_ids))

                variant = variant_cache.get(spec["default_code"])
                if variant and variant.product_tmpl_id.id != product.id:
                    variant = None
                if not variant:
                    variant = variant_by_combination.get(frozenset(value_ids))
                if not variant:
                    combination = self._pg_resolve_ptav_combination(
                        product, value_map, spec["attributes"]
                    )
                    if combination:
                        variant = self._pg_get_or_create_variant_for_combination(product, combination)
                        if variant:
                            variant_by_combination[frozenset(value_ids)] = variant
                            if variant.default_code:
                                variant_cache.setdefault(variant.default_code, variant)
                if variant:
                    if variant.default_code != spec["default_code"]:
                        variant.write({"default_code": spec["default_code"]})
                    variant_cache[spec["default_code"]] = variant

                    imagens_variant = gd.find_child_folder(spec["folder_id"], "IMAGENS")
                    if imagens_variant:
                        _logger.info(
                            "Variant image sync: default_code=%s folder_id=%s imagens_id=%s",
                            spec["default_code"],
                            spec["folder_id"],
                            imagens_variant["id"],
                        )
                        self.upload_images(
                            imagens_variant["id"],
                            product,
                            is_main_product=False,
                            variant=variant,
                            force_refresh=False,
                        )
                    else:
                        _logger.info(
                            "Variant has no IMAGENS folder: default_code=%s folder_id=%s",
                            spec["default_code"],
                            spec["folder_id"],
                        )
                        self.env["product.image"].search(
                            [("product_variant_id", "=", variant.id)]
                        ).unlink()
                        vals = {
                            "gdrive_main_image_file_id": False,
                            "gdrive_main_image_md5": False,
                        }
                        if not variant_image_related:
                            vals["image_1920"] = False
                        variant.write(vals)
                        _logger.info(
                            "Cleared variant media due to missing IMAGENS: variant=%s",
                            variant.id,
                        )
                    self._process_additional_docs(
                        product,
                        spec["folder_id"],
                        {},
                        spec["folder_id"],
                        res_model="product.product",
                        res_id=variant.id,
                        product_variant=variant,
                        force_refresh=False,
                    )

            all_template_variants = product.with_context(active_test=False).product_variant_ids
            for variant in all_template_variants:
                variant_value_ids = set(
                    variant.product_template_attribute_value_ids.mapped(
                        "product_attribute_value_id"
                    ).ids
                )
                is_desired = frozenset(variant_value_ids) in desired_sets
                if variant.active != is_desired:
                    variant.write({"active": is_desired})

            image_count_data = self.env["product.image"].read_group(
                [("product_variant_id", "in", all_template_variants.ids)],
                ["product_variant_id"],
                ["product_variant_id"],
            )
            image_counts = {
                row["product_variant_id"][0]: row["product_variant_id_count"]
                for row in image_count_data
                if row.get("product_variant_id")
            }
            variant_image_field = self._variant_image_field_name()
            for variant in all_template_variants:
                if variant.gdrive_main_image_file_id:
                    continue
                if image_counts.get(variant.id, 0) == 0 and getattr(variant, variant_image_field):
                    variant.write({variant_image_field: False})
                    _logger.info(
                        "Force-cleared variant image_1920 (empty IMAGENS): variant=%s",
                        variant.id,
                    )
            variant_summaries = []
            for variant in all_template_variants:
                v_main_id = (
                    variant.gdrive_main_image_file_id
                    if "gdrive_main_image_file_id" in variant._fields
                    else None
                )
                v_main_md5 = (
                    variant.gdrive_main_image_md5
                    if "gdrive_main_image_md5" in variant._fields
                    else None
                )
                variant_summaries.append(
                    "id=%s code=%s active=%s image_1920=%s images=%s gdrive_id=%s gdrive_md5=%s"
                    % (
                        variant.id,
                        variant.default_code,
                        variant.active,
                        bool(variant.image_1920),
                        image_counts.get(variant.id, 0),
                        v_main_id,
                        v_main_md5,
                    )
                )
            _logger.info(
                "Variant media summary: product=%s variants=%s",
                product.id,
                variant_summaries,
            )

            tmpl_docs = self.env["product.document"].search(
                [("res_model", "=", "product.template"), ("res_id", "=", product.id)]
            )
            tmpl_doc_types = [
                d.tipo_documento if "tipo_documento" in d._fields else None
                for d in tmpl_docs
            ]
            _logger.info(
                "Template docs detail: product=%s docs=%s types=%s",
                product.id,
                [d.name for d in tmpl_docs],
                tmpl_doc_types,
            )

            _logger.info(
                "Post-variant sync: product=%s variants_total=%s variants_active=%s",
                product.id,
                len(product.product_variant_ids),
                len(product.product_variant_ids.filtered(lambda v: v.active)),
            )
            _logger.info(
                "Template images/docs: product=%s images=%s docs=%s",
                product.id,
                len(self.env['product.image'].search([('product_tmpl_id', '=', product.id)])),
                len(self.env['product.document'].search([('res_model', '=', 'product.template'), ('res_id', '=', product.id)])),
            )
            _logger.info(
                "Template thumbnail: product=%s image_1920=%s",
                product.id,
                bool(product.image_1920),
            )

            if imagens_folder:
                template_image = self._get_first_image_base64(imagens_folder)
                if template_image:
                    product.write({"image_1920": template_image})
                    _logger.info(
                        "Re-applied template thumbnail from IMAGENS: product=%s",
                        product.id,
                    )

        except Exception as e:
            _logger.error("Error processing variants for %s: %s", product_name, e)

    # ----------------------------
    # COMPLEMENTOS (Drive)
    # ----------------------------
    def find_complementos_folder(self, folder_path):
        gd = self._gdrive()
        folder = gd.find_child_folder(folder_path, "COMPLEMENTOS")
        return folder["id"] if folder else None

    def process_complementos_images(self, product_template, product_path):
        gd = self._gdrive()
        try:
            for folder in gd.list_children(product_path, folders_only=True):
                normalized_folder_name = self.normalize_folder_name(folder.get("name") or "")
                if normalized_folder_name.upper() == "IMAGENS":
                    images_folder_id = folder["id"]
                    self.upload_images(
                        images_folder_id,
                        product_template,
                        is_main_product=True,
                        force_refresh=False,
                    )
        except Exception as e:
            _logger.error("Error processing COMPLEMENTOS images: %s", e)
            self.env.cr.rollback()

    def process_complementos_folder(self, complementos_folder, category_id):
        gd = self._gdrive()

        try:
            complementos_info = gd.get(complementos_folder, fields="id,name,parents")
            if not complementos_info.get("parents"):
                _logger.info("COMPLEMENTOS folder has no parent; skipping")
                return

            main_product_folder_id = complementos_info["parents"][0]
            main_product_folder = gd.get(main_product_folder_id, fields="id,name")
            main_product_name = self.normalize_folder_name(main_product_folder["name"])

            main_product = self.env["product.template"].search([("name", "=", main_product_name)], limit=1)
            if not main_product:
                _logger.info("Main product not found for COMPLEMENTOS folder ID: %s", complementos_folder)
                return

            for folder in gd.list_children(complementos_folder, folders_only=True):
                product_name = self.normalize_folder_name(folder.get("name") or "")
                _logger.info("Processing COMPLEMENTOS product: %s", product_name.upper())

                product_template = self.env["product.template"].search([("name", "=", product_name)], limit=1)
                if not product_template:
                    _logger.info("COMPLEMENTOS product not found: %s", product_name)
                    continue

                attachments = self.env["ir.attachment"].search(
                    [("res_model", "=", "product.template"), ("res_id", "=", product_template.id)]
                )
                attachments.unlink()

                product_images = self.env["product.image"].search([("product_tmpl_id", "=", product_template.id)])
                product_images.unlink()

                for variant in product_template.product_variant_ids:
                    variant_images = self.env["product.image"].search([("product_variant_id", "=", variant.id)])
                    variant_images.unlink()

                self.process_complementos_images(product_template, folder["id"])

                for variant in product_template.product_variant_ids:
                    main_product.write({"accessory_product_ids": [(4, variant.id)]})

        except Exception as e:
            _logger.error("Error processing COMPLEMENTOS folder: %s", e)
            self.env.cr.rollback()

    # ----------------------------
    # Top-level category images
    # ----------------------------
    def upload_top_level_category_images(self, root_folder, parent_category):
        gd = self._gdrive()

        for folder in gd.list_children(root_folder, folders_only=True):
            normalized_name = self.normalize_folder_name(folder.get("name") or "")
            children = gd.list_children(folder["id"], folders_only=False)
            image_files = [
                f for f in children
                if f.get("mimeType") != DRIVE_FOLDER_MIME
                and (f.get("name") or "").lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            if image_files:
                self.create_or_get_category(
                    normalized_name, parent_category.id, img_path=None, gdrive_folder_id=folder["id"]
                )
                _logger.info("Top-level category image(s) uploaded for: %s", normalized_name)

    # ----------------------------
    # Hierarchy reconstruction from IMAGENS (Drive)
    # ----------------------------
    def find_product_info_from_imagens(self, start_path):
        ICP = self.env["ir.config_parameter"].sudo()
        root_id = ICP.get_param("product_update.gdrive_root_folder_id")
        if not root_id:
            raise RuntimeError("Missing system parameter: product_update.gdrive_root_folder_id")

        gd = self._gdrive()
        imagens = gd.get(start_path, fields="id,name,parents")

        if not imagens.get("parents"):
            return None, [], None

        components = []
        folder_ids = []

        current_id = imagens["parents"][0]
        while current_id:
            folder = gd.get(current_id, fields="id,name,parents")
            if folder["id"] == root_id:
                break

            normalized_name = self.normalize_folder_name(folder["name"])
            components.insert(0, normalized_name)
            folder_ids.insert(0, folder["id"])

            if not folder.get("parents"):
                break
            current_id = folder["parents"][0]

        if not components:
            return None, [], None

        product_name = components[-1]
        subcategories = components[:-1]
        product_folder_id = folder_ids[-1]
        return product_name, subcategories, product_folder_id

    # ----------------------------
    # Process a SINGLE IMAGENS folder (one unit of work)
    # ----------------------------
    def _process_one_imagens_folder(self, imagens_folder_id, all_category):
        gd = self._gdrive()

        if not self._is_product_level_imagens(imagens_folder_id):
            _logger.info("Skipping variant-level IMAGENS folder id: %s", imagens_folder_id)
            return {"status": "skipped", "reason": "IMAGENS folder classified as variant-level, not product-level"}

        product_name, hierarchy, base_folder_id = self.find_product_info_from_imagens(imagens_folder_id)
        if not product_name or not base_folder_id:
            reason = "Could not derive product name or base folder from IMAGENS folder"
            self._append_context_job_trace("processing_derive_failed", reason, imagens_id=imagens_folder_id)
            return {"status": "skipped", "reason": reason}

        _logger.info("Derived product name: %s from IMAGENS folder id: %s", product_name, imagens_folder_id)
        self._append_context_job_trace(
            "processing_derived",
            f"Derived product folder successfully: product={product_name} base_folder={base_folder_id}",
            imagens_id=imagens_folder_id,
        )

        current_parent_id = all_category.id

        # Walk down from ROOT following hierarchy folder names to upload category images
        ICP = self.env["ir.config_parameter"].sudo()
        root_folder_id = ICP.get_param("product_update.gdrive_root_folder_id")
        current_drive_parent = root_folder_id

        for level_name in hierarchy:
            level_folder = gd.find_child_folder(current_drive_parent, level_name.upper())
            level_folder_id = level_folder["id"] if level_folder else None

            current_parent = self.create_or_get_category(
                level_name, current_parent_id, img_path=None, gdrive_folder_id=level_folder_id
            )

            current_parent_id = current_parent.id

            if level_folder_id:
                current_drive_parent = level_folder_id

        # POS category OPTIONAL
        pos_category = None
        if self._pos_available():
            pos_category = self.env["pos.category"].search([("name", "=", product_name)], limit=1)
            if not pos_category:
                pos_category = self.env["pos.category"].create({"name": product_name})

        # Process products inside product folder (variants by default_code)
        self.process_multi_variant_product(
            current_parent_id,
            pos_category.id if pos_category else None,
            base_folder_id,
        )
        self._append_context_job_trace(
            "processing_product_updated",
            f"Processed product folder into categories product={product_name}",
            imagens_id=imagens_folder_id,
        )

        # COMPLEMENTOS if exists
        complementos_folder = self.find_complementos_folder(base_folder_id)
        if complementos_folder:
            _logger.info("Processing COMPLEMENTOS folder id: %s", complementos_folder)
            self.process_complementos_folder(complementos_folder, current_parent_id)
            self._append_context_job_trace(
                "processing_complementos",
                f"Processed COMPLEMENTOS folder {complementos_folder}",
                imagens_id=imagens_folder_id,
            )
        else:
            self._append_context_job_trace(
                "processing_complementos",
                "No COMPLEMENTOS folder found",
                imagens_id=imagens_folder_id,
            )
        return {"status": "processed", "reason": f"Imported product {product_name}"}

    # -----------------------------------------------------------------------
    # OPTION A: Job-based background execution
    # -----------------------------------------------------------------------
    @api.model
    def start_drive_update_job(self):
        """
        Called by the button. Creates (or resumes) a job and returns quickly.
        The actual heavy work is done by cron_run_drive_jobs().
        """
        self._clear_runtime_caches()
        cron = self.env.ref("pg_product_update.ir_cron_pg_product_update_drive_job_runner", raise_if_not_found=False)
        if cron and not cron.active:
            cron.sudo().write({"active": True})
        ICP = self.env["ir.config_parameter"].sudo()
        root_folder_id = ICP.get_param("product_update.gdrive_root_folder_id")
        if not root_folder_id:
            _logger.error("Missing system parameter: product_update.gdrive_root_folder_id")
            return False

        # If a job is already running for this root, close it and start fresh
        job = self.env["product.update.drive.job"].search(
            [("state", "=", "running"), ("root_folder_id", "=", root_folder_id)],
            limit=1,
        )
        if job:
            job.write({"state": "done", "finished_at": fields.Datetime.now()})
            self.env.cr.commit()

        all_category = self.create_or_get_category("All", None)
        # Upload top-level category images once per run (safe to repeat across runs)
        try:
            self.upload_top_level_category_images(root_folder_id, all_category)
        except Exception as e:
            _logger.warning("Top-level category image upload failed (will continue job): %s", e)

        # Initialize incremental scan stack with the root
        job = self.env["product.update.drive.job"].create(
            {
                "state": "running",
                "root_folder_id": root_folder_id,
                "discovery_done": False,
                "discovered_count": 0,
                "scan_stack_json": self._json_dump([root_folder_id]),
                "pending_imagens_json": self._json_dump([]),
                "all_category_id": all_category.id,
            }
        )
        self.env.cr.commit()
        _logger.info("Started Drive update job id=%s", job.id)
        return self._action_open_drive_job_dashboard(job)

    @api.model
    def cron_run_drive_jobs(self):
        """
        Scheduled Action (cron) should call this every 1 minute.
        It will:
          1) incrementally discover IMAGENS folders
          2) process them one-by-one with retries

        IMPORTANT Odoo 17 fix:
          - DO NOT call job.flush() (recordsets don't have it)
          - Use write() + self.env.cr.commit() to persist progress per step
        """
        # Tune these if needed
        SOFT_TIME_BUDGET_S = 8 * 60        # try to do < 8 minutes each tick
        DISCOVERY_BATCH_FOLDERS = 120      # how many folders to scan per tick at most
        MAX_ITEMS_PER_JOB_RUN = 5          # allow each cron tick to process several products per job
        MAX_ITEM_RETRIES = 5

        start_ts = time.time()

        jobs = self.env["product.update.drive.job"].search([("state", "=", "running")], order="id asc", limit=5)
        if not jobs:
            cron = self.env.ref(
                "pg_product_update.ir_cron_pg_product_update_drive_job_runner",
                raise_if_not_found=False,
            )
            if cron and cron.active:
                _logger.info(
                    "Drive job runner: no running jobs; leaving cron active to avoid write during execution."
                )
            return

        for job in jobs:
            # Stop if we used our time budget for this cron tick
            if (time.time() - start_ts) > SOFT_TIME_BUDGET_S:
                return

            try:
                all_category = job.all_category_id
                if not all_category:
                    # Repair if missing
                    all_category = self.create_or_get_category("All", None)
                    job.write({"all_category_id": all_category.id})
                    self.env.cr.commit()

                processed_this_run = 0
                while (
                    processed_this_run < MAX_ITEMS_PER_JOB_RUN
                    and (time.time() - start_ts) <= SOFT_TIME_BUDGET_S
                ):
                    # 1) PROCESS pending items first, so discovery cannot starve imports.
                    if self._process_next_job_pending_item(job, all_category, MAX_ITEM_RETRIES):
                        processed_this_run += 1
                        continue

                    # 2) DISCOVERY PHASE (incremental)
                    if not job.discovery_done:
                        discovery_stats = self._advance_job_discovery(
                            job,
                            scan_limit=DISCOVERY_BATCH_FOLDERS,
                            time_budget_s=max(1.0, SOFT_TIME_BUDGET_S - (time.time() - start_ts)),
                        )
                        if discovery_stats.get("queued") or discovery_stats.get("scanned"):
                            continue

                    pending = self._json_load(job.pending_imagens_json, [])
                    if not pending and not job.current_item_id and job.discovery_done:
                        discovered_entries = self._json_load(job.discovered_items_json, [])
                        processed_entries = self._json_load(job.processed_items_json, [])
                        skipped_entries = self._json_load(job.skipped_items_json, [])
                        processed_ids = {entry.get("imagens_id") for entry in processed_entries if entry.get("imagens_id")}
                        skipped_ids = {entry.get("imagens_id") for entry in skipped_entries if entry.get("imagens_id")}
                        unaccounted_entries = [
                            entry for entry in discovered_entries
                            if entry.get("imagens_id") and entry.get("imagens_id") not in processed_ids and entry.get("imagens_id") not in skipped_ids
                        ]
                        job.write({"state": "done", "finished_at": fields.Datetime.now()})
                        _logger.info(
                            "Drive update job id=%s DONE. discovered=%s processed=%s skipped=%s unaccounted=%s errors=%s",
                            job.id,
                            job.discovered_count,
                            job.processed_count,
                            job.skipped_count,
                            len(unaccounted_entries),
                            job.error_count,
                        )
                        if unaccounted_entries:
                            sample = ", ".join(
                                entry.get("product_name") or entry.get("imagens_id")
                                for entry in unaccounted_entries[:10]
                            )
                            self._append_job_trace(
                                job,
                                "job_done_unaccounted",
                                f"Job finished with {len(unaccounted_entries)} unaccounted items: {sample}",
                            )
                            _logger.warning(
                                "Drive update job id=%s finished with unaccounted IMAGENS items: %s",
                                job.id,
                                sample,
                            )
                        self.env.cr.commit()
                        if not self.env["product.update.drive.job"].search_count([("state", "=", "running")]):
                            _logger.info(
                                "Drive job runner: no running jobs; leaving cron active to avoid write during execution."
                            )
                        break

                    # No pending items ready right now, and discovery did not advance enough to queue more.
                    break

            except Exception as e:
                # If the job itself is broken, mark failed but do not crash cron loop
                self.env.cr.rollback()
                job.write({"state": "failed", "last_error": str(e), "finished_at": fields.Datetime.now()})
                _logger.exception("Job %s FAILED: %s", job.id, e)
                self.env.cr.commit()

    @api.model
    def cron_stop_drive_job_runner(self):
        """
        Separate cron: disables the runner when no jobs are running.
        This avoids writing to the running cron record itself.
        """
        jobs = self.env["product.update.drive.job"].search_count([("state", "=", "running")])
        if jobs:
            return
        cron = self.env.ref(
            "pg_product_update.ir_cron_pg_product_update_drive_job_runner",
            raise_if_not_found=False,
        )
        if cron and cron.active:
            cron.sudo().write({"active": False})
            _logger.info("Drive job runner disabled (no running jobs).")

    # ----------------------------
    # Memory logging
    # ----------------------------
    def log_memory_usage(self, message=""):
        if psutil:
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / (1024**2)
            _logger.info("[Memory Usage] %s: %.2f MB", message, memory_usage)
        else:
            _logger.warning("psutil is not installed; skipping memory logging.")


class ProductTemplate(models.Model):
    _inherit = "product.template"
    gdrive_main_image_file_id = fields.Char(index=True)
    gdrive_main_image_md5 = fields.Char()
    # Cache of the Drive folder that represents this product (parent of IMAGENS
    # at product level). Populated on first successful resolve and reused after.
    pg_gdrive_folder_id = fields.Char(string="Drive Folder ID", index=True)
    pg_import_job_count = fields.Integer(compute="_compute_pg_import_job_count")
    pg_running_import_job_count = fields.Integer(compute="_compute_pg_import_job_count")
    pg_duplicate_variant_count = fields.Integer(compute="_compute_pg_duplicate_variant_count")

    def _compute_pg_import_job_count(self):
        job_model = self.env["product.update.drive.job"].sudo()
        total_count = job_model.search_count([])
        running_count = job_model.search_count([("state", "=", "running")])
        for product in self:
            product.pg_import_job_count = total_count
            product.pg_running_import_job_count = running_count

    def _compute_pg_duplicate_variant_count(self):
        for product in self:
            groups = {}
            for variant in product.with_context(active_test=False).product_variant_ids:
                key = product._pg_duplicate_variant_key(variant)
                groups.setdefault(key, []).append(variant.id)
            product.pg_duplicate_variant_count = sum(max(0, len(ids) - 1) for ids in groups.values())

    def _pg_normalize_duplicate_key(self, value):
        updater = self.env["product.update"]
        return updater._normalize_match_key(value or "")

    def _pg_duplicate_variant_key(self, variant):
        ptavs = variant.product_template_attribute_value_ids.sorted(
            key=lambda ptav: (
                self._pg_normalize_duplicate_key(ptav.attribute_id.name),
                self._pg_normalize_duplicate_key(ptav.product_attribute_value_id.name),
                ptav.id,
            )
        )
        return tuple(
            (
                self._pg_normalize_duplicate_key(ptav.attribute_id.name),
                self._pg_normalize_duplicate_key(ptav.product_attribute_value_id.name),
            )
            for ptav in ptavs
        )

    def _pg_variant_has_references(self, variant):
        checks = [
            ("sale.order.line", "product_id"),
            ("purchase.order.line", "product_id"),
            ("stock.move", "product_id"),
            ("account.move.line", "product_id"),
            ("stock.quant", "product_id"),
        ]
        for model, field in checks:
            try:
                if self.env[model].search_count([(field, "=", variant.id)], limit=1):
                    return True
            except Exception:
                pass
        return False

    def _pg_select_canonical_variant(self, variants):
        return sorted(
            variants,
            key=lambda v: (
                0 if self._pg_variant_has_references(v) else 1,
                0 if v.active else 1,
                0 if v.default_code else 1,
                v.id,
            ),
        )[0]

    def _pg_dynamic_variant_limit(self):
        limit = self.env["ir.config_parameter"].sudo().get_param("product.dynamic_variant_limit", 1000)
        try:
            return int(limit)
        except Exception:
            return 1000

    def _pg_is_variant_limit_error(self, error):
        message = str(error or "")
        normalized = self._pg_normalize_duplicate_key(message)
        return any(
            self._pg_normalize_duplicate_key(fragment) in normalized
            for fragment in (
                "number of variants to generate is above allowed limit",
                "numero de variantes a serem geradas esta acima do limite permitido",
            )
        )

    def _pg_estimated_logical_variant_count(self, product_id):
        lines = self.env["product.template.attribute.line"].with_context(active_test=False).search(
            [("product_tmpl_id", "=", product_id), ("active", "=", True)],
            order="id asc",
        )
        groups = {}
        for line in lines:
            key = self._pg_normalize_duplicate_key(line.attribute_id.name)
            groups.setdefault(key, set())
            for value in line.value_ids:
                groups[key].add(self._pg_normalize_duplicate_key(value.name))

        estimated = 1
        for values in groups.values():
            value_count = max(1, len(values))
            estimated *= value_count
        return estimated

    def _pg_cleanup_duplicate_attribute_lines(self):
        updater = self.env["product.update"]
        cleaned = 0
        skipped_products = 0
        skipped_runtime_products = 0
        template_ids = list(self.ids)
        line_model = self.env["product.template.attribute.line"].with_context(active_test=False)
        template_model = self.env["product.template"].with_context(active_test=False)
        variant_limit = self._pg_dynamic_variant_limit()
        for product_id in template_ids:
            updater._advisory_xact_lock(f"pg_product_update:cleanup_product:{product_id}")
            product = template_model.browse(product_id).exists()
            if not product:
                continue
            estimated_variant_count = self._pg_estimated_logical_variant_count(product_id)
            _logger.info(
                "Starting duplicate attribute-line cleanup for product=%s name=%s estimated_logical_variants=%s variant_limit=%s",
                product_id,
                product.display_name,
                estimated_variant_count,
                variant_limit,
            )
            if estimated_variant_count > variant_limit:
                skipped_products += 1
                _logger.warning(
                    "Skipping duplicate attribute-line cleanup for product=%s name=%s because estimated logical variant count %s exceeds limit %s",
                    product_id,
                    product.display_name,
                    estimated_variant_count,
                    variant_limit,
                )
                continue
            lines = line_model.search(
                [("product_tmpl_id", "=", product_id)],
                order="active desc, id asc",
            )
            groups = {}
            for line in lines:
                attribute_name = line.attribute_id.name or ""
                key = self._pg_normalize_duplicate_key(attribute_name)
                groups.setdefault(key, [])
                groups[key].append(
                    {
                        "line_id": line.id,
                        "attribute_name": attribute_name,
                        "value_names": [value.name for value in line.value_ids],
                    }
                )

            for group_lines in groups.values():
                if len(group_lines) <= 1:
                    continue
                requested_attribute = updater._get_or_create_attribute(group_lines[0]["attribute_name"])
                _logger.info(
                    "Attempting duplicate attribute-line normalization for product=%s name=%s attribute=%s line_ids=%s value_names=%s",
                    product_id,
                    product.display_name,
                    requested_attribute.name,
                    [line["line_id"] for line in group_lines],
                    sorted({value_name for line in group_lines for value_name in line["value_names"]}),
                )
                value_ids = []
                for line in group_lines:
                    for value_name in line["value_names"]:
                        canonical_value = updater._get_or_create_attribute_value(requested_attribute, value_name)
                        value_ids.append(canonical_value.id)
                try:
                    updater._ensure_attribute_line(product, requested_attribute, value_ids)
                except UserError as err:
                    if not self._pg_is_variant_limit_error(err):
                        _logger.exception(
                            "Duplicate attribute-line cleanup failed for product=%s name=%s attribute=%s with non-limit UserError",
                            product_id,
                            product.display_name,
                            requested_attribute.name,
                        )
                        raise
                    skipped_runtime_products += 1
                    _logger.warning(
                        "Skipping duplicate attribute-line cleanup during runtime for product=%s name=%s attribute=%s because core variant limit was triggered: %s",
                        product_id,
                        product.display_name,
                        requested_attribute.name,
                        err,
                    )
                    break
                except Exception:
                    _logger.exception(
                        "Duplicate attribute-line cleanup crashed for product=%s name=%s attribute=%s",
                        product_id,
                        product.display_name,
                        requested_attribute.name,
                    )
                    raise
                _logger.info(
                    "Finished duplicate attribute-line normalization for product=%s name=%s attribute=%s merged_line_count=%s",
                    product_id,
                    product.display_name,
                    requested_attribute.name,
                    len(group_lines),
                )
                cleaned += max(0, len(group_lines) - 1)
            _logger.info(
                "Finished duplicate attribute-line cleanup for product=%s name=%s cumulative_cleaned_lines=%s cumulative_skipped_products=%s",
                product_id,
                product.display_name,
                cleaned,
                skipped_products + skipped_runtime_products,
            )
        return {
            "cleaned_line_count": cleaned,
            "skipped_products": skipped_products + skipped_runtime_products,
        }

    def _pg_archive_duplicate_variant_group(self, variants):
        canonical = self._pg_select_canonical_variant(variants)
        duplicates = variants - canonical
        if not duplicates:
            return canonical, self.env["product.product"]

        if not canonical.default_code:
            default_code_source = duplicates.filtered(lambda variant: variant.default_code)[:1]
            if default_code_source:
                canonical.write({"default_code": default_code_source.default_code})

        safe_to_archive = self.env["product.product"]
        for dup in duplicates:
            if self._pg_variant_has_references(dup):
                _logger.warning(
                    "Skipping archival of duplicate variant=%s (product=%s) because it has document references",
                    dup.id,
                    dup.product_tmpl_id.id,
                )
            else:
                safe_to_archive |= dup

        if safe_to_archive:
            safe_to_archive.write({"active": False})
        return canonical, safe_to_archive

    def _pg_cleanup_duplicate_variants(self):
        templates = self.with_context(active_test=False)
        template_ids = list(templates.ids)
        _logger.info(
            "Starting duplicate variant cleanup for template_ids=%s product_count=%s",
            template_ids,
            len(template_ids),
        )
        line_cleanup_summary = templates._pg_cleanup_duplicate_attribute_lines()
        archived_variants = self.env["product.product"]
        duplicate_groups = 0

        template_model = self.env["product.template"].with_context(active_test=False)
        updater = self.env["product.update"]
        for product_id in template_ids:
            updater._advisory_xact_lock(f"pg_product_update:cleanup_product:{product_id}")
            product = template_model.browse(product_id).exists()
            if not product:
                continue
            _logger.info(
                "Scanning duplicate variants for product=%s name=%s existing_variant_ids=%s",
                product_id,
                product.display_name,
                product.with_context(active_test=False).product_variant_ids.ids,
            )
            groups = {}
            for variant in product.with_context(active_test=False).product_variant_ids:
                key = product._pg_duplicate_variant_key(variant)
                groups.setdefault(key, self.env["product.product"])
                groups[key] |= variant

            for key, variants in groups.items():
                if len(variants) <= 1:
                    continue
                _logger.info(
                    "Attempting duplicate variant archival for product=%s name=%s key=%s variant_ids=%s",
                    product_id,
                    product.display_name,
                    key,
                    variants.ids,
                )
                canonical, duplicates = product._pg_archive_duplicate_variant_group(variants)
                if duplicates:
                    duplicate_groups += 1
                    archived_variants |= duplicates
                    _logger.warning(
                        "Archived duplicate logical variants for product=%s key=%s canonical_variant=%s duplicate_variant_ids=%s",
                        product.id,
                        key,
                        canonical.id,
                        duplicates.ids,
                    )
            _logger.info(
                "Finished duplicate variant scan for product=%s name=%s duplicate_groups_so_far=%s archived_variants_so_far=%s",
                product_id,
                product.display_name,
                duplicate_groups,
                len(archived_variants),
            )

        summary = {
            "products": len(template_ids),
            "duplicate_line_count": line_cleanup_summary["cleaned_line_count"],
            "skipped_line_cleanup_products": line_cleanup_summary["skipped_products"],
            "duplicate_variant_count": len(archived_variants),
            "duplicate_group_count": duplicate_groups,
        }
        _logger.info("Finished duplicate variant cleanup summary=%s", summary)
        return summary

    def action_pg_cleanup_duplicate_variants(self):
        self.ensure_one()
        summary = self._pg_cleanup_duplicate_variants()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Duplicate variants cleaned",
                "message": (
                    "Product: %s | Archived duplicate variants: %s | "
                    "Duplicate attribute lines cleaned: %s | "
                    "Line cleanup skipped on products above variant limit: %s"
                ) % (
                    self.display_name,
                    summary["duplicate_variant_count"],
                    summary["duplicate_line_count"],
                    summary["skipped_line_cleanup_products"],
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_pg_cleanup_duplicate_variants_all(self):
        templates = self.env["product.template"].with_context(active_test=False).search([])
        summary = templates._pg_cleanup_duplicate_variants()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Duplicate variants cleaned",
                "message": (
                    "Products scanned: %s | Duplicate variant groups: %s | "
                    "Archived duplicate variants: %s | Duplicate attribute lines cleaned: %s | "
                    "Line cleanup skipped on products above variant limit: %s"
                ) % (
                    summary["products"],
                    summary["duplicate_group_count"],
                    summary["duplicate_variant_count"],
                    summary["duplicate_line_count"],
                    summary["skipped_line_cleanup_products"],
                ),
                "type": "success",
                "sticky": True,
            },
        }

    def action_open_pg_import_jobs(self):
        job_model = self.env["product.update.drive.job"].sudo()
        running_job = job_model.search([("state", "=", "running")], order="id desc", limit=1)
        latest_job = running_job or job_model.search([], order="id desc", limit=1)

        action = {
            "type": "ir.actions.act_window",
            "name": "Import Jobs",
            "res_model": "product.update.drive.job",
            "view_mode": "list,form",
            "target": "current",
            "domain": [],
            "context": {"search_default_running_jobs": 1} if running_job else {},
        }
        if latest_job:
            action.update({"res_id": latest_job.id, "view_mode": "form,list", "views": [[False, "form"], [False, "list"]]})
        return action

    def action_open_pg_import_dashboard(self):
        job_model = self.env["product.update.drive.job"].sudo()
        running_job = job_model.search([("state", "=", "running")], order="id desc", limit=1)
        latest_job = running_job or job_model.search([], order="id desc", limit=1)
        if latest_job:
            return latest_job.action_open_live_dashboard()
        return self.action_open_pg_import_jobs()

    def update_product_data(self):
        """
        Button action:
        - Starts a Drive job
        - The cron continues until it finishes
        """
        return self.env["product.update"].start_drive_update_job()

    def action_pg_fetch_references_from_drive(self):
        """Open the references-only wizard pre-loaded with self templates."""
        templates = self
        if not templates:
            raise UserError("Selecionar pelo menos um produto.")
        action = self.env.ref(
            "pg_product_update.action_pg_product_references_fetch_wizard"
        ).sudo().read()[0]
        action["context"] = {
            "default_template_ids": [(6, 0, templates.ids)],
            "active_model": "product.template",
            "active_ids": templates.ids,
            "active_id": templates[:1].id,
        }
        return action


class ProductUpdateAction(models.Model):
    _inherit = "product.update"

    def update_products(self):
        return self.start_drive_update_job()


class ProductAttribute(models.Model):
    _inherit = "product.attribute"


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"


class ProductProduct(models.Model):
    _inherit = "product.product"
    gdrive_main_image_file_id = fields.Char(index=True)
    gdrive_main_image_md5 = fields.Char()

    def action_pg_fetch_references_from_drive(self):
        """Open the references-only wizard pre-loaded with self variants
        (filters the plan to those specific variants)."""
        variants = self
        if not variants:
            raise UserError("Selecionar pelo menos uma variante.")
        action = self.env.ref(
            "pg_product_update.action_pg_product_references_fetch_wizard"
        ).sudo().read()[0]
        action["context"] = {
            "active_model": "product.product",
            "active_ids": variants.ids,
            "active_id": variants[:1].id,
        }
        return action


class ProductImage(models.Model):
    _inherit = "product.image"

    gdrive_file_id = fields.Char(index=True)
    gdrive_md5 = fields.Char()


class ProductDocument(models.Model):
    _inherit = "product.document"

    gdrive_file_id = fields.Char(index=True)
    gdrive_md5 = fields.Char()
