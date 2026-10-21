from __future__ import annotations

import os
import logging
import re
import shutil
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .pg_csv import pg_write_csv
from .pg_engine import pg_resume_state_path, pg_run_crawl
from .pg_job_store import PgJobStore
from .pg_models import PgCrawlRequest


_logger = logging.getLogger(__name__)


class PgJobCancelled(RuntimeError):
    pass

def _configure_pg_logging() -> None:
    level_name = str(os.getenv("PG_CRAWLER_LOG_LEVEL") or "INFO").strip().upper()
    level = getattr(logging, level_name, logging.INFO)
    namespace_logger = logging.getLogger("pg_crawler_bot")
    namespace_logger.setLevel(level)
    if namespace_logger.handlers:
        for handler in namespace_logger.handlers:
            handler.setLevel(level)
        return
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    namespace_logger.addHandler(handler)
    namespace_logger.propagate = False


_configure_pg_logging()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("PG_CRAWLER_OUTPUT_DIR", str(BASE_DIR / "pg_served"))).resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv("PG_CRAWLER_DB_PATH", str(BASE_DIR / "pg_jobs.sqlite3"))).resolve()
TOKEN = os.getenv("REMOTE_CRAWLER_TOKEN", "")
PG_CRAWLER_PORT = int(str(os.getenv("PG_CRAWLER_PORT") or "4040").strip())
PG_CRAWLER_STALE_TIMEOUT_MINUTES = int(str(os.getenv("PG_CRAWLER_STALE_TIMEOUT_MINUTES") or "20").strip())
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", f"http://localhost:{PG_CRAWLER_PORT}").rstrip("/")
JOB_STORE = PgJobStore(DB_PATH)

app = FastAPI(title="PG Crawler Bot")
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")


@app.on_event("startup")
def pg_recover_unfinished_jobs() -> None:
    recovered = JOB_STORE.fail_unfinished_jobs(
        error="Crawler service restarted before the job finished.",
        finished_at=datetime.now(timezone.utc).isoformat(),
    )
    if recovered:
        _logger.warning("Recovered %s unfinished crawler job(s) after service startup.", recovered)


def _authorize(authorization: str | None) -> None:
    if TOKEN and authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _job_status_url(job_id: str) -> str:
    return f"{PUBLIC_BASE_URL}/jobs/{job_id}"


def _csv_url(filename: str) -> str:
    return f"{PUBLIC_BASE_URL}/files/{filename}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_last_heartbeat_at(job: dict) -> datetime | None:
    meta = job.get("meta") or {}
    if isinstance(meta, dict):
        raw_value = str(meta.get("last_heartbeat_at") or "").strip()
        if raw_value:
            try:
                return datetime.fromisoformat(raw_value)
            except ValueError:
                pass
    for key in ("started_at", "created_at"):
        raw_value = str(job.get(key) or "").strip()
        if not raw_value:
            continue
        try:
            return datetime.fromisoformat(raw_value)
        except ValueError:
            continue
    return None


def _job_is_stale(job: dict) -> bool:
    status = str(job.get("status") or "").strip().lower()
    if status not in {"queued", "running", "processing"}:
        return False
    heartbeat = _job_last_heartbeat_at(job)
    if not heartbeat:
        return False
    if heartbeat.tzinfo is None:
        heartbeat = heartbeat.replace(tzinfo=timezone.utc)
    stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=PG_CRAWLER_STALE_TIMEOUT_MINUTES)
    return heartbeat < stale_cutoff


def _job_cancel_requested(job_id: str) -> bool:
    job = JOB_STORE.get_job(job_id)
    if not job:
        return False
    meta = job.get("meta") or {}
    return bool(isinstance(meta, dict) and meta.get("cancel_requested"))


def _job_with_meta_counters(job: dict) -> dict:
    meta = job.get("meta") or {}
    if not isinstance(meta, dict):
        return job
    normalized = dict(job)
    for key in ("visited_pages", "discovered_products", "progress_note"):
        if key in meta and meta.get(key) is not None:
            normalized[key] = meta.get(key)
    return normalized


def _mark_job_as_stale(job: dict) -> dict:
    job_id = str(job.get("job_id") or "")
    error = (
        "Crawler job marked failed after stale heartbeat timeout "
        f"({PG_CRAWLER_STALE_TIMEOUT_MINUTES} minutes without progress)."
    )
    finished_at = _utc_now_iso()
    meta = dict(job.get("meta") or {})
    meta["progress_note"] = "Crawler job marked failed after stale heartbeat timeout."
    meta["stale_timeout_minutes"] = PG_CRAWLER_STALE_TIMEOUT_MINUTES
    meta["last_heartbeat_at"] = str(meta.get("last_heartbeat_at") or "")
    JOB_STORE.update_job(
        job_id,
        status="failed",
        error=error,
        finished_at=finished_at,
        meta=meta,
    )
    refreshed = JOB_STORE.get_job(job_id)
    return refreshed or {
        **job,
        "status": "failed",
        "error": error,
        "finished_at": finished_at,
        "meta": meta,
    }


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or "result"


def _result_filenames(payload: dict, finished_at: datetime) -> tuple[str, str]:
    domain = _safe_filename_part(urlparse(str(payload.get("source_url") or "")).netloc.replace("www.", ""))
    vendor_code = _safe_filename_part(str(payload.get("vendor_code") or "vendor"))
    timestamp = finished_at.strftime("%Y%m%d_%H%M%S")
    historical = f"{vendor_code}_{domain}_{timestamp}.csv"
    latest = f"{vendor_code}_{domain}_latest.csv"
    return historical, latest


def _upload_csv_to_odoo(
    payload: dict,
    target_name: str,
    target_path: Path,
    *,
    job_id: str | None = None,
    result_meta: dict | None = None,
) -> dict:
    upload_url = str(payload.get("odoo_upload_url") or "").strip()
    upload_token = str(payload.get("odoo_upload_token") or "").strip()
    if not upload_url or not upload_token:
        return {}
    result_meta = result_meta or {}
    with target_path.open("rb") as handle:
        response = requests.post(
            upload_url,
            data={
                "vendor_code": str(payload.get("vendor_code") or ""),
                "vendor_name": str(payload.get("vendor_name") or ""),
                "source_url": str(payload.get("source_url") or ""),
                "filename": target_name,
                "adapter_key": str(payload.get("adapter_key") or ""),
                "job_id": str(job_id or ""),
                "status": "done",
                "visited_pages": str(result_meta.get("visited_pages") or 0),
                "discovered_products": str(result_meta.get("discovered_products") or 0),
                "progress_note": str(result_meta.get("progress_note") or "Crawler job finished."),
            },
            files={
                "file": (target_name, handle, "text/csv"),
            },
            headers={"Authorization": f"Bearer {upload_token}"},
            timeout=120,
        )
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or not result.get("csv_url"):
        raise RuntimeError("Odoo upload completed without returning csv_url.")
    return result


def _run_job(job_id: str, payload: dict) -> None:
    started_at = _utc_now_iso()
    if _job_cancel_requested(job_id):
        JOB_STORE.update_job(
            job_id,
            status="cancelled",
            finished_at=started_at,
            meta={
                "progress_note": "Crawler job cancelled before start.",
                "last_heartbeat_at": started_at,
            },
        )
        _logger.info("Crawler job id=%s cancelled before start.", job_id)
        return
    running_meta = {
        "visited_pages": 0,
        "discovered_products": 0,
        "progress_note": "Crawler job started.",
        "last_heartbeat_at": started_at,
    }
    meta_lock = threading.Lock()
    JOB_STORE.update_job(
        job_id,
        status="running",
        started_at=started_at,
        meta=running_meta,
    )
    _logger.info(
        "Starting crawler job id=%s vendor_code=%s adapter_key=%s source_url=%s",
        job_id,
        payload.get("vendor_code"),
        payload.get("adapter_key"),
        payload.get("source_url"),
    )
    try:
        def progress_callback(progress_meta: dict) -> None:
            with meta_lock:
                running_meta.update(progress_meta or {})
                running_meta["last_heartbeat_at"] = _utc_now_iso()
                JOB_STORE.update_job(job_id, status="running", meta=dict(running_meta))
            if _job_cancel_requested(job_id):
                raise PgJobCancelled("Crawler job cancelled.")

        crawler_class, result = pg_run_crawl(payload, progress_callback=progress_callback)
        if not result.records:
            finished_at = datetime.now(timezone.utc)
            warning = (
                "Crawler finished with zero product records. "
                f"visited_pages={result.visited_pages}; "
                f"last_status_code={result.meta.get('last_status_code')}; "
                f"last_content_type={result.meta.get('last_content_type')}; "
                f"fetch_failures={result.meta.get('fetch_failures')}"
            )
            JOB_STORE.update_job(
                job_id,
                status="done",
                csv_url="",
                finished_at=finished_at.isoformat(),
                meta={
                    "adapter_key": crawler_class.adapter_key,
                    "adapter_label": crawler_class.adapter_label,
                    "visited_pages": result.visited_pages,
                    "discovered_products": 0,
                    "progress_note": "Crawler finished with zero product records.",
                    "warning": warning,
                    **result.meta,
                },
            )
            _logger.warning("Crawler job id=%s finished with zero products: %s", job_id, warning)
            return

        finished_at = datetime.now(timezone.utc)
        target_name, latest_name = _result_filenames(payload, finished_at)
        target_path = OUTPUT_DIR / target_name
        latest_path = OUTPUT_DIR / latest_name
        pg_write_csv(result.records, target_path)
        shutil.copyfile(target_path, latest_path)
        upload_result = _upload_csv_to_odoo(
            payload,
            target_name,
            target_path,
            job_id=job_id,
            result_meta={
                "visited_pages": result.visited_pages,
                "discovered_products": result.discovered_products,
                "progress_note": "Crawler job finished.",
            },
        )
        final_csv_url = upload_result.get("csv_url") or _csv_url(target_name)
        JOB_STORE.update_job(
            job_id,
            status="done",
            csv_url=final_csv_url,
            finished_at=finished_at.isoformat(),
            meta={
                "adapter_key": crawler_class.adapter_key,
                "adapter_label": crawler_class.adapter_label,
                "visited_pages": result.visited_pages,
                "discovered_products": result.discovered_products,
                "output_file": str(target_path),
                "latest_output_file": str(latest_path),
                "latest_csv_url": _csv_url(latest_name),
                "csv_filename": target_name,
                "latest_csv_filename": latest_name,
                "odoo_upload": upload_result or False,
                **result.meta,
            },
        )
        _logger.info(
            "Finished crawler job id=%s status=done discovered_products=%s visited_pages=%s csv_url=%s",
            job_id,
            result.discovered_products,
            result.visited_pages,
            final_csv_url,
        )
    except Exception as exc:
        if isinstance(exc, PgJobCancelled):
            JOB_STORE.update_job(
                job_id,
                status="cancelled",
                finished_at=_utc_now_iso(),
                meta={
                    **(JOB_STORE.get_job(job_id) or {}).get("meta", {}),
                    "progress_note": "Crawler job cancelled.",
                },
            )
            _logger.warning("Crawler job id=%s cancelled.", job_id)
            return
        JOB_STORE.update_job(
            job_id,
            status="failed",
            error=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        _logger.exception("Crawler job id=%s failed: %s", job_id, exc)


@app.get("/health")
def pg_healthcheck() -> dict:
    return {"status": "ok"}


@app.post("/crawl/start")
def pg_start_crawl(payload: PgCrawlRequest, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    job_payload = payload.to_job_payload()
    active_job = JOB_STORE.find_active_job(payload.vendor_code)
    if active_job:
        if _job_is_stale(active_job):
            _logger.warning(
                "Marking stale active crawler job as failed before accepting new start vendor_code=%s job_id=%s",
                payload.vendor_code,
                active_job.get("job_id"),
            )
            active_job = _mark_job_as_stale(active_job)
        if str(active_job.get("status") or "").strip().lower() in {"queued", "running", "processing", "cancelling"}:
            _logger.warning(
                "Rejecting overlapping crawler start vendor_code=%s existing_job_id=%s existing_status=%s",
                payload.vendor_code,
                active_job.get("job_id"),
                active_job.get("status"),
            )
            return JSONResponse(_job_with_meta_counters(active_job), status_code=202)
    job_id = uuid.uuid4().hex
    if bool(job_payload.get("pg_clear_resume_state")):
        try:
            resume_path = pg_resume_state_path(job_payload)
            resume_path.unlink(missing_ok=True)
            _logger.info("Cleared crawler resume state before starting fresh job path=%s", resume_path)
        except Exception as exc:
            _logger.warning("Could not clear crawler resume state before new job: %s", exc)
    job = {
        "job_id": job_id,
        "vendor_code": payload.vendor_code,
        "vendor_name": payload.vendor_name,
        "source_url": payload.source_url,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status_url": _job_status_url(job_id),
        "payload": job_payload,
    }
    JOB_STORE.create_job(job)
    thread = threading.Thread(target=_run_job, args=(job_id, job_payload), daemon=True)
    thread.start()
    return JSONResponse(JOB_STORE.get_job(job_id), status_code=202)


@app.get("/jobs/{job_id}")
def pg_get_job(job_id: str, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    job = JOB_STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if _job_is_stale(job):
        _logger.warning(
            "Marking stale crawler job as failed job_id=%s status=%s stale_timeout_minutes=%s",
            job_id,
            job.get("status"),
            PG_CRAWLER_STALE_TIMEOUT_MINUTES,
        )
        job = _mark_job_as_stale(job)
    return _job_with_meta_counters(job)


@app.post("/jobs/{job_id}/cancel")
def pg_cancel_job(job_id: str, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    job = JOB_STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    status = str(job.get("status") or "").strip().lower()
    if status in {"done", "failed", "cancelled"}:
        return _job_with_meta_counters(job)
    meta = dict(job.get("meta") or {})
    meta["cancel_requested"] = True
    meta["progress_note"] = "Cancellation requested."
    meta["last_heartbeat_at"] = _utc_now_iso()
    JOB_STORE.update_job(job_id, status="cancelling", meta=meta)
    updated = JOB_STORE.get_job(job_id) or job
    return _job_with_meta_counters(updated)
