@echo off
setlocal

set HEALTH_URL=http://127.0.0.1:4040/health
set LOG_PATH=C:\Services\pg_crawler_watchdog.log
set TASK_NAME=PgCrawler

powershell -NoProfile -Command ^
  "try { $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 -Uri '%HEALTH_URL%'; if ($resp.StatusCode -ne 200) { exit 2 } } catch { exit 1 }"

if %errorlevel%==0 (
  echo [%date% %time%] health ok >> %LOG_PATH%
  exit /b 0
)

echo [%date% %time%] health failed, restarting task >> %LOG_PATH%

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4040 ^| findstr LISTENING') do (
  taskkill /PID %%a /F > NUL 2>&1
)

schtasks /End /TN "%TASK_NAME%" > NUL 2>&1
timeout /t 2 > NUL
schtasks /Run /TN "%TASK_NAME%" > NUL 2>&1

echo [%date% %time%] restart attempted >> %LOG_PATH%
exit /b 0
