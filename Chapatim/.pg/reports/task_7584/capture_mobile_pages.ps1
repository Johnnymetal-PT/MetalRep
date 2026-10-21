$ErrorActionPreference = 'Stop'
$reportDir = 'C:\Users\Utilizador\Desktop\Repos\Chapatim\.pg\reports\task_7584\mobile_audit'
$pythonSource = @'
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path(r"C:\Users\Utilizador\Desktop\Repos\Chapatim\.pg\reports\task_7584\mobile_audit")
pages = {
    "home": "https://chapatim.odoo.com/",
    "shop": "https://chapatim.odoo.com/shop",
    "category": "https://chapatim.odoo.com/shop/category/acessorios-treino-117",
    "product": "https://chapatim.odoo.com/shop/roll-line-base-dance-17",
    "contactos": "https://chapatim.odoo.com/contactos",
}
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 390, "height": 844}, locale="pt-PT", is_mobile=True, has_touch=True)
    for name, url in pages.items():
        page = context.new_page()
        response = page.goto(url, wait_until="networkidle", timeout=30000)
        page.screenshot(path=str(out / f"{name}_390_top.png"), full_page=False)
        page.screenshot(path=str(out / f"{name}_390_full.png"), full_page=True)
        print(name, response.status if response else None, page.evaluate("() => [document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.scrollHeight]"))
        if name == "home":
            toggles = page.locator("header button[data-bs-target='#top_menu_collapse_mobile']:visible")
            print("header_controls", page.locator("header a:visible, header button:visible").evaluate_all("els => els.map(e => ({tag:e.tagName, cls:e.className, aria:e.getAttribute('aria-label'), title:e.getAttribute('title'), target:e.getAttribute('data-bs-target')}))"))
            if toggles.count():
                toggles.first.click(force=True)
                page.wait_for_timeout(500)
                page.screenshot(path=str(out / "home_390_menu.png"), full_page=False)
        page.close()
    context.close()
    browser.close()
'@
$tempScript = Join-Path $env:TEMP 'capture_chapatim_mobile.py'
Set-Content -LiteralPath $tempScript -Value $pythonSource -Encoding UTF8
python $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Mobile screenshots failed.' }
