from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PgCrawlRequest(BaseModel):
    vendor_code: str
    vendor_name: str | None = None
    source_url: str
    adapter_key: str | None = None
    max_pages: int = 1500
    pg_max_runtime_minutes: int = 480
    pg_resume: bool = False
    pg_resume_save_interval: int = 200
    pg_login_timeout_seconds: int = 90
    pg_login_retry_count: int = 2
    pg_browser_restart_pages: int = 150
    pg_browser_restart_minutes: int = 20
    quantity_instock: int = 1
    quantity_outofstock: int = 0

    model_config = ConfigDict(extra="allow")

    def to_job_payload(self) -> dict[str, Any]:
        return self.model_dump()
