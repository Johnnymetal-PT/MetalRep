PG Crawler Bot

Purpose
- Self-hosted generic crawler bot for product websites
- Runs completely outside Odoo
- Exposes the same remote crawler contract already expected by `hiper_sync`
- Produces a CSV feed that Odoo can import through `csv_url`

Why this shape
- Odoo core references used:
  - [account_move.py](/c:/Users/Utilizador/Desktop/Repos/Hipermercado/vendor/odoo_core/odoo/addons/account/models/account_move.py)
  - [decorators.py](/c:/Users/Utilizador/Desktop/Repos/Hipermercado/vendor/odoo_core/odoo/orm/decorators.py)
- These are useful only as references for chunked/background-job behavior.
- There is no Odoo core crawler pattern for turning arbitrary retail websites into supplier feeds.
- The crawler itself is custom development.

Architecture
- generic API/job engine
- adapter registry by domain or explicit `adapter_key`
- site adapters for high-quality extraction
- generic fallback adapter for unknown domains with looser heuristics

Included adapters
- `pg_eldisser_b2b`
- `pg_mielectro`
- `pg_generic`

Endpoints
- `POST /crawl/start`
- `GET /jobs/{job_id}`
- `GET /files/{vendor_code}.csv`
- `GET /health`

Request format

```json
{
  "vendor_code": "pg_mielectro",
  "vendor_name": "Mi Electro",
  "source_url": "https://www.mielectro.es/",
  "adapter_key": "pg_mielectro",
  "max_pages": 1500,
  "pg_max_runtime_minutes": 480,
  "pg_resume": false,
  "pg_resume_save_interval": 200,
  "pg_login_timeout_seconds": 90,
  "pg_login_retry_count": 2,
  "quantity_instock": 1,
  "quantity_outofstock": 0
}
```

Authenticated adapter payloads can pass extra fields through as-is, for example:

```json
{
  "vendor_code": "inteldisser",
  "vendor_name": "Eldisser",
  "source_url": "https://b2b.eldisser.com/",
  "adapter_key": "pg_eldisser_b2b",
  "max_pages": 40000,
  "pg_max_runtime_minutes": 480,
  "pg_resume": true,
  "pg_resume_save_interval": 200,
  "pg_login_timeout_seconds": 90,
  "pg_login_retry_count": 2,
  "login_username": "your-user",
  "login_password": "your-password",
  "login_url": "https://b2b.eldisser.com/",
  "force_tienda_view": true
}
```

Response format
- immediate queued job:

```json
{
  "job_id": "abc123",
  "vendor_code": "pg_mielectro",
  "status": "queued",
  "status_url": "https://crawler.example.com/jobs/abc123"
}
```

- finished job:

```json
{
  "job_id": "abc123",
  "vendor_code": "pg_mielectro",
  "status": "done",
  "csv_url": "https://crawler.example.com/files/pg_mielectro.csv",
  "meta": {
    "adapter_key": "pg_mielectro"
  }
}
```

Important limitation
- this is not a magic no-config crawler for every e-commerce site
- the reusable part is the bot platform
- extraction quality still depends on per-site adapters for serious suppliers
- `pg_generic` is a fallback, not a substitute for a real adapter

Local run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

export REMOTE_CRAWLER_TOKEN="change-me"
export PG_CRAWLER_PORT="4040"
export PUBLIC_BASE_URL="http://localhost:4040"

uvicorn pg_crawler_bot.pg_app:app --host 0.0.0.0 --port 4040
```

Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:REMOTE_CRAWLER_TOKEN="change-me"
$env:PG_CRAWLER_PORT="4040"
$env:PUBLIC_BASE_URL="http://localhost:4040"

uvicorn pg_crawler_bot.pg_app:app --host 0.0.0.0 --port 4040
```

Suggested Odoo supplier config
- `Source Kind`: `CSV URL`
- `Feed URL`: leave blank initially
- `Remote Crawler Trigger URL`: `https://your-server/crawl/start`
- `Remote Crawler Status URL`: `https://your-server/jobs/{job_id}`
- `Remote Crawler Auth Token`: same value as `REMOTE_CRAWLER_TOKEN`
- `Remote Crawler Source URL`: supplier website root URL

Production notes
- SQLite is used for job tracking for simplicity
- static CSV files are served directly by FastAPI for simplicity
- nginx or object storage is better for file serving in production
- if a site is heavily JS-rendered, add Playwright in the adapter instead of forcing it globally
