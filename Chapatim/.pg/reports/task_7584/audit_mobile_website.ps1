$ErrorActionPreference = 'Stop'

$reportDir = 'C:\Users\Utilizador\Desktop\Repos\Chapatim\.pg\reports\task_7584\mobile_audit'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$pythonSource = @'
import asyncio, json, pathlib, xml.etree.ElementTree as ET
from urllib.request import urlopen
from playwright.async_api import async_playwright

base = "https://chapatim.odoo.com"
report_dir = pathlib.Path(r"C:\Users\Utilizador\Desktop\Repos\Chapatim\.pg\reports\task_7584\mobile_audit")
xml_data = urlopen(base + "/sitemap.xml", timeout=30).read()
root = ET.fromstring(xml_data)
urls = [node.text for node in root.findall("{*}url/{*}loc") if node.text]
for extra in [base + "/", base + "/shop", base + "/shop/cart"]:
    if extra not in urls:
        urls.insert(0, extra)

async def inspect_page(page, url):
    errors = []
    page.on("console", lambda msg: errors.append(msg.text[:300]) if msg.type == "error" else None)
    result = {"url": url, "status": None, "error": None, "overflow": 0, "overflow_elements": [], "tiny_actions": 0, "tiny_text": 0, "console_errors": []}
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        result["status"] = response.status if response else None
        await page.wait_for_timeout(250)
        await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        await page.wait_for_timeout(200)
        result.update(await page.evaluate("""() => {
            const vw = document.documentElement.clientWidth;
            const sw = document.documentElement.scrollWidth;
            const visible = e => {
                const s = getComputedStyle(e), r = e.getBoundingClientRect();
                return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity !== 0 && r.width > 0 && r.height > 0;
            };
            const out = [];
            for (const e of document.querySelectorAll('body *')) {
                if (!visible(e)) continue;
                const r = e.getBoundingClientRect();
                if (r.right > vw + 3 || r.left < -3) {
                    out.push({
                        tag: e.tagName.toLowerCase(), id: e.id || '',
                        cls: String(e.className || '').slice(0, 180),
                        left: Math.round(r.left), right: Math.round(r.right), width: Math.round(r.width),
                        text: String(e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100)
                    });
                    if (out.length >= 12) break;
                }
            }
            let tinyActions = 0, tinyText = 0;
            for (const e of document.querySelectorAll('a, button, input, select, textarea, [role="button"]')) {
                if (!visible(e)) continue;
                const r = e.getBoundingClientRect();
                if ((r.width < 40 || r.height < 40) && !e.closest('footer')) tinyActions++;
            }
            for (const e of document.querySelectorAll('p, li, label, small')) {
                if (!visible(e)) continue;
                if (parseFloat(getComputedStyle(e).fontSize) < 12) tinyText++;
            }
            return {overflow: Math.max(0, sw - vw), overflow_elements: out, tiny_actions: tinyActions, tiny_text: tinyText,
                    title: document.title, body_height: document.documentElement.scrollHeight};
        }
        """))
    except Exception as exc:
        result["error"] = str(exc)[:500]
    result["console_errors"] = list(dict.fromkeys(errors))[:8]
    return result

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": 390, "height": 844}, locale="pt-PT", is_mobile=True, has_touch=True)
        queue = asyncio.Queue()
        for u in urls: queue.put_nowait(u)
        results = []
        lock = asyncio.Lock()
        async def worker():
            page = await context.new_page()
            while True:
                try: url = queue.get_nowait()
                except asyncio.QueueEmpty: break
                item = await inspect_page(page, url)
                async with lock:
                    results.append(item)
                    if len(results) % 20 == 0: print(f"AUDITED {len(results)}/{len(urls)}", flush=True)
                queue.task_done()
            await page.close()
        await asyncio.gather(*(worker() for _ in range(4)))
        await context.close()
        await browser.close()
    results.sort(key=lambda x: x["url"])
    (report_dir / "mobile_audit_390.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    bad_status = [r for r in results if r["status"] not in (200, 301, 302)]
    errors = [r for r in results if r["error"]]
    overflow = [r for r in results if r["overflow"] > 3]
    console = [r for r in results if r["console_errors"]]
    summary = {
        "audited": len(results), "bad_status": len(bad_status), "navigation_errors": len(errors),
        "horizontal_overflow": len(overflow), "console_error_pages": len(console),
        "overflow_urls": [{"url": r["url"], "pixels": r["overflow"], "elements": r["overflow_elements"][:4]} for r in overflow],
        "bad_status_urls": [{"url": r["url"], "status": r["status"]} for r in bad_status],
        "navigation_error_urls": [{"url": r["url"], "error": r["error"]} for r in errors],
    }
    (report_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))

asyncio.run(main())
'@

$tempScript = Join-Path $env:TEMP 'audit_chapatim_mobile.py'
Set-Content -LiteralPath $tempScript -Value $pythonSource -Encoding UTF8
python $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Mobile website audit failed.' }
