Remote crawler contract for Odoo.sh-compatible Eldisser flow

Overview
- Odoo does not run the crawler.
- Odoo triggers an external service.
- The external service runs the crawler and produces a CSV.
- Odoo refreshes job status and imports the returned CSV URL.

Expected trigger request
- Method: POST
- URL: value of `remote_crawler_trigger_url`
- Headers:
  - `Authorization: Bearer <token>` if configured
  - `Accept: application/json`
- JSON body:

```json
{
  "vendor_code": "inteldisser",
  "vendor_name": "Eldisser",
  "source_url": "https://example.com/original-site-to-crawl",
  "adapter_key": "pg_mielectro",
  "login_url": "https://b2b.eldisser.com/",
  "login_username": "your-user",
  "login_password": "your-password",
  "force_tienda_view": true,
  "...": "anything from remote_crawler_payload_json"
}
```

Accepted trigger response formats

Immediate result:

```json
{
  "status": "done",
  "csv_url": "https://crawler.example.com/results/eldisser.csv"
}
```

Queued job:

```json
{
  "job_id": "job_123",
  "status": "queued",
  "status_url": "https://crawler.example.com/jobs/job_123"
}
```

Expected status request
- Method: GET
- URL: value of `remote_crawler_status_url`
- If the URL contains `{job_id}`, Odoo replaces it with the stored job id.

Accepted status response formats

Still running:

```json
{
  "job_id": "job_123",
  "status": "running",
  "meta": {
    "visited_pages": 124,
    "discovered_products": 57,
    "progress_note": "Scanning category listings."
  }
}
```

Finished:

```json
{
  "job_id": "job_123",
  "status": "done",
  "csv_url": "https://crawler.example.com/results/eldisser.csv"
}
```

Failed:

```json
{
  "job_id": "job_123",
  "status": "failed",
  "error": "Login failed"
}
```

Recommended external deployment
- Small VPS or container
- FastAPI or Flask API with two endpoints:
  - `POST /crawl/start`
  - `GET /jobs/<job_id>`
- Background job runs Scrapy/Playwright/ZenRows
- On success, upload the CSV to a stable URL and return that URL to Odoo

Optional Odoo-hosted result flow
- Instead of serving the final CSV from the crawler server, the crawler can upload the generated CSV back into Odoo.
- `hiper_sync` now exposes a secure upload endpoint:
  - `POST /hiper_sync/crawler/upload`
- Odoo can include these fields automatically in the trigger payload when a global upload token is configured:
  - `odoo_upload_url`
  - `odoo_upload_token`
- The crawler posts the finished CSV file there and Odoo returns a `csv_url` backed by `ir.attachment` and `/web/content/...`.
- This lets users work entirely from Odoo while the crawler server remains private.

Optional adapter selection
- If the crawler bot supports multiple site adapters, Odoo can send an explicit `adapter_key`.
- `hiper_sync` now exposes `pg_remote_crawler_adapter_key` on the supplier form and includes it automatically in the trigger payload when set.

Optional authenticated crawler fields
- `hiper_sync` can now send these explicitly from supplier fields instead of forcing them into raw JSON:
  - `login_url`
  - `login_username`
  - `login_password`
  - `force_tienda_view`
