@echo off
set REMOTE_CRAWLER_TOKEN=046960bf71cb4b5aade4c025708ab887
set PUBLIC_BASE_URL=http://erpremoto.dyndns.biz:4040
set PG_CRAWLER_PORT=4040
set PG_CRAWLER_LOG_LEVEL=INFO
set PG_CRAWLER_STALE_TIMEOUT_MINUTES=20

cd /d C:\Services
set LOG_PATH=C:\Services\pg_crawler_task.log

:loop
echo [%date% %time%] Starting pg_crawler_bot >> %LOG_PATH%
C:\Services\.venv\Scripts\python.exe -m uvicorn pg_crawler_bot.pg_app:app --host 0.0.0.0 --port 4040 >> %LOG_PATH% 2>&1
echo [%date% %time%] pg_crawler_bot exited with code %errorlevel% >> %LOG_PATH%
timeout /t 10 > NUL
goto loop
