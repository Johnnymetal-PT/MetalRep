from __future__ import annotations

import os
import re
from pathlib import Path

from .pg_registry import pg_get_crawler_class


PG_RESERVED_PAYLOAD_KEYS = {
    "vendor_code",
    "vendor_name",
    "source_url",
    "adapter_key",
    "max_pages",
    "pg_max_runtime_minutes",
    "pg_resume",
    "pg_resume_save_interval",
    "pg_clear_resume_state",
    "pg_resume_state_path",
    "pg_login_timeout_seconds",
    "pg_login_retry_count",
    "quantity_instock",
    "quantity_outofstock",
    "odoo_upload_url",
    "odoo_upload_token",
}


def _safe_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or "result"


def _state_dir() -> Path:
    directory = Path(
        os.getenv("PG_CRAWLER_STATE_DIR", str(Path(__file__).resolve().parent / "pg_state"))
    ).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def pg_resume_state_path(payload: dict) -> Path:
    explicit_path = str(payload.get("pg_resume_state_path") or "").strip()
    if explicit_path:
        path = Path(explicit_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    crawler_class = pg_get_crawler_class(payload.get("source_url") or "", payload.get("adapter_key"))
    vendor_code = _safe_filename_part(str(payload.get("vendor_code") or "vendor"))
    adapter_key = _safe_filename_part(crawler_class.adapter_key)
    return _state_dir() / f"{vendor_code}_{adapter_key}_resume.json"


def pg_run_crawl(payload: dict, *, progress_callback=None):
    crawler_class = pg_get_crawler_class(payload.get("source_url") or "", payload.get("adapter_key"))
    extra_payload = {key: value for key, value in payload.items() if key not in PG_RESERVED_PAYLOAD_KEYS}
    vendor_code = _safe_filename_part(str(payload.get("vendor_code") or "vendor"))
    adapter_key = _safe_filename_part(crawler_class.adapter_key)
    storage_state_path = _state_dir() / f"{vendor_code}_{adapter_key}_state.json"
    resume_state_path = pg_resume_state_path(payload)
    crawler = crawler_class(
        payload.get("source_url") or "",
        max_pages=int(payload.get("max_pages") or 1500),
        quantity_instock=int(payload.get("quantity_instock") or 1),
        quantity_outofstock=int(payload.get("quantity_outofstock") or 0),
        pg_max_runtime_minutes=int(payload.get("pg_max_runtime_minutes") or 0),
        pg_resume=bool(payload.get("pg_resume") or False),
        pg_resume_save_interval=int(payload.get("pg_resume_save_interval") or 200),
        pg_resume_state_path=str(resume_state_path),
        pg_login_timeout_seconds=int(payload.get("pg_login_timeout_seconds") or 0),
        pg_login_retry_count=int(payload.get("pg_login_retry_count") or 0),
        vendor_code=payload.get("vendor_code") or "",
        storage_state_path=str(storage_state_path),
        progress_callback=progress_callback,
        **extra_payload,
    )
    result = crawler.crawl()
    return crawler_class, result
