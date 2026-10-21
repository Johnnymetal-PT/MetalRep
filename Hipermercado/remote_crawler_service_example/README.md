Remote crawler service example

Purpose
- This is an example external service for the Odoo `hiper_sync` remote crawler flow.
- Odoo triggers `POST /crawl/start`
- Odoo polls `GET /jobs/{job_id}`
- When the crawler finishes, the service exposes a stable CSV URL under `/files/<vendor>.csv`

Environment variables
- `REMOTE_CRAWLER_TOKEN`
- `PUBLIC_BASE_URL`
- `ELDISSER_CRAWLER_WORKDIR`
- `ELDISSER_CRAWLER_COMMAND`
- `ELDISSER_CRAWLER_OUTPUT_FILE`

Example

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export REMOTE_CRAWLER_TOKEN="change-me"
export PUBLIC_BASE_URL="https://crawler.example.com"
export ELDISSER_CRAWLER_WORKDIR="/opt/eldisser/scrapper"
export ELDISSER_CRAWLER_COMMAND="./run_spider.sh"
export ELDISSER_CRAWLER_OUTPUT_FILE="/opt/eldisser/download"

uvicorn app:app --host 0.0.0.0 --port 8000
```

Suggested Odoo vendor configuration
- `Source Kind`: `CSV URL`
- `Feed URL`: leave blank initially
- `Remote Crawler Trigger URL`: `https://crawler.example.com/crawl/start`
- `Remote Crawler Status URL`: `https://crawler.example.com/jobs/{job_id}`
- `Remote Crawler Auth Token`: same value as `REMOTE_CRAWLER_TOKEN`
- `Remote Crawler Source URL`: original supplier site URL if you want to pass it to the worker

Notes
- This example keeps jobs in memory. Use Redis/database storage for production.
- Exposed files are served directly by FastAPI for simplicity. Use object storage or nginx in production.
