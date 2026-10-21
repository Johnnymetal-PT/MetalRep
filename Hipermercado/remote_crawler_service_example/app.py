import os
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "served"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

JOBS = {}
TOKEN = os.getenv("REMOTE_CRAWLER_TOKEN", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
CRAWLER_WORKDIR = Path(os.getenv("ELDISSER_CRAWLER_WORKDIR", BASE_DIR)).resolve()
CRAWLER_COMMAND = os.getenv("ELDISSER_CRAWLER_COMMAND", "./run_spider.sh")
CRAWLER_OUTPUT_FILE = Path(
    os.getenv("ELDISSER_CRAWLER_OUTPUT_FILE", str(CRAWLER_WORKDIR / "../download"))
).resolve()


class CrawlRequest(BaseModel):
    vendor_code: str
    vendor_name: str | None = None
    source_url: str | None = None


app = FastAPI(title="Remote Crawler Example")
app.mount("/files", StaticFiles(directory=str(OUTPUT_DIR)), name="files")


def _authorize(authorization: str | None):
    if TOKEN and authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")


def _latest_csv_file():
    if CRAWLER_OUTPUT_FILE.is_file():
        return CRAWLER_OUTPUT_FILE
    if CRAWLER_OUTPUT_FILE.is_dir():
        candidates = sorted(CRAWLER_OUTPUT_FILE.glob("*.csv"), key=lambda item: item.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None
    return None


def _job_status_url(job_id: str):
    return f"{PUBLIC_BASE_URL}/jobs/{job_id}"


def _csv_url(filename: str):
    return f"{PUBLIC_BASE_URL}/files/{filename}"


def _run_job(job_id: str):
    job = JOBS[job_id]
    job["status"] = "running"
    try:
        completed = subprocess.run(
            CRAWLER_COMMAND,
            cwd=str(CRAWLER_WORKDIR),
            shell=True,
            capture_output=True,
            text=True,
            timeout=7200,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "Crawler command failed").strip())

        latest_csv = _latest_csv_file()
        if not latest_csv or not latest_csv.exists():
            raise RuntimeError("Crawler finished but no CSV file was found.")

        target_name = f"{job['vendor_code']}.csv"
        target_path = OUTPUT_DIR / target_name
        shutil.copyfile(latest_csv, target_path)

        job["status"] = "done"
        job["csv_url"] = _csv_url(target_name)
        job["finished_at"] = datetime.now(timezone.utc).isoformat()
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        job["finished_at"] = datetime.now(timezone.utc).isoformat()


@app.post("/crawl/start")
def start_crawl(payload: CrawlRequest, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {
        "job_id": job_id,
        "vendor_code": payload.vendor_code,
        "vendor_name": payload.vendor_name,
        "source_url": payload.source_url,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status_url": _job_status_url(job_id),
    }
    thread = threading.Thread(target=_run_job, args=(job_id,), daemon=True)
    thread.start()
    return JSONResponse(JOBS[job_id], status_code=202)


@app.get("/jobs/{job_id}")
def get_job(job_id: str, authorization: str | None = Header(default=None)):
    _authorize(authorization)
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
