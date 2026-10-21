from __future__ import annotations

import json
import sqlite3
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any


class PgJobStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._job_cache: dict[str, dict[str, Any]] = {}
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pg_jobs (
                    job_id TEXT PRIMARY KEY,
                    vendor_code TEXT NOT NULL,
                    vendor_name TEXT,
                    source_url TEXT,
                    status TEXT NOT NULL,
                    status_url TEXT,
                    csv_url TEXT,
                    error TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    finished_at TEXT,
                    payload_json TEXT,
                    meta_json TEXT
                )
                """
            )
            connection.commit()

    def create_job(self, job: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pg_jobs (
                    job_id, vendor_code, vendor_name, source_url, status, status_url,
                    csv_url, error, created_at, started_at, finished_at, payload_json, meta_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job["job_id"],
                    job["vendor_code"],
                    job.get("vendor_name"),
                    job.get("source_url"),
                    job["status"],
                    job.get("status_url"),
                    job.get("csv_url"),
                    job.get("error"),
                    job.get("created_at"),
                    job.get("started_at"),
                    job.get("finished_at"),
                    json.dumps(job.get("payload", {}), ensure_ascii=True),
                    json.dumps(job.get("meta", {}), ensure_ascii=True),
                ),
            )
            connection.commit()
        self._set_cached_job(
            {
                "job_id": job["job_id"],
                "vendor_code": job["vendor_code"],
                "vendor_name": job.get("vendor_name"),
                "source_url": job.get("source_url"),
                "status": job["status"],
                "status_url": job.get("status_url"),
                "csv_url": job.get("csv_url"),
                "error": job.get("error"),
                "created_at": job.get("created_at"),
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
                "payload": dict(job.get("payload") or {}),
                "meta": dict(job.get("meta") or {}),
            }
        )

    def update_job(self, job_id: str, **values: Any) -> None:
        allowed = {
            "status",
            "status_url",
            "csv_url",
            "error",
            "created_at",
            "started_at",
            "finished_at",
            "meta",
            "payload",
        }
        fields = []
        params: list[Any] = []
        for key, value in values.items():
            if key not in allowed:
                continue
            column = f"{key}_json" if key in {"meta", "payload"} else key
            encoded = json.dumps(value, ensure_ascii=True) if key in {"meta", "payload"} else value
            fields.append(f"{column} = ?")
            params.append(encoded)
        if not fields:
            return
        params.append(job_id)
        cached_job = self._get_cached_job(job_id) or {"job_id": job_id}
        for key, value in values.items():
            if key not in allowed:
                continue
            if key in {"meta", "payload"}:
                cached_job[key] = dict(value or {})
            else:
                cached_job[key] = value
        with self._lock, self._connect() as connection:
            connection.execute(f"UPDATE pg_jobs SET {', '.join(fields)} WHERE job_id = ?", params)
            connection.commit()
        self._set_cached_job(cached_job)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        cached_job = self._get_cached_job(job_id)
        if cached_job:
            return cached_job
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM pg_jobs WHERE job_id = ?", (job_id,)).fetchone()
            if not row:
                return None
            job = self._row_to_dict(row)
        self._set_cached_job(job)
        return self._clone_job(job)

    def find_active_job(self, vendor_code: str) -> dict[str, Any] | None:
        vendor_code = str(vendor_code or "").strip()
        if not vendor_code:
            return None
        active_statuses = ("queued", "running", "processing", "cancelling")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                  FROM pg_jobs
                 WHERE vendor_code = ?
                   AND status IN (?, ?, ?, ?)
                 ORDER BY COALESCE(started_at, created_at) DESC, created_at DESC
                 LIMIT 1
                """,
                (vendor_code, *active_statuses),
            ).fetchone()
            if not row:
                return None
            job = self._row_to_dict(row)
        self._set_cached_job(job)
        return self._clone_job(job)

    def fail_unfinished_jobs(self, *, error: str, finished_at: str) -> int:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM pg_jobs WHERE status IN ('queued', 'running', 'cancelling')"
            ).fetchall()
            cursor = connection.execute(
                """
                UPDATE pg_jobs
                   SET status = ?,
                       error = ?,
                       finished_at = ?
                 WHERE status IN ('queued', 'running', 'cancelling')
                """,
                ("failed", error, finished_at),
            )
            connection.commit()
        for row in rows:
            job = self._row_to_dict(row)
            job["status"] = "failed"
            job["error"] = error
            job["finished_at"] = finished_at
            self._set_cached_job(job)
        return int(cursor.rowcount or 0)

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        payload = json.loads(row["payload_json"] or "{}")
        meta = json.loads(row["meta_json"] or "{}")
        job = {
            "job_id": row["job_id"],
            "vendor_code": row["vendor_code"],
            "vendor_name": row["vendor_name"],
            "source_url": row["source_url"],
            "status": row["status"],
            "status_url": row["status_url"],
            "csv_url": row["csv_url"],
            "error": row["error"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
        }
        if payload:
            job["payload"] = payload
        if meta:
            job["meta"] = meta
        return job

    def _set_cached_job(self, job: dict[str, Any]) -> None:
        if not job.get("job_id"):
            return
        with self._cache_lock:
            self._job_cache[str(job["job_id"])] = self._clone_job(job)

    def _get_cached_job(self, job_id: str) -> dict[str, Any] | None:
        with self._cache_lock:
            job = self._job_cache.get(job_id)
            return self._clone_job(job) if job else None

    def _clone_job(self, job: dict[str, Any] | None) -> dict[str, Any] | None:
        if job is None:
            return None
        return deepcopy(job)
