$ErrorActionPreference = 'Stop'
$pythonSource = @'
from playwright.sync_api import sync_playwright

url = "https://chapatim.odoo.com/"
menu_names = [
    "Art\u00edstica sobre Rodas",
    "Vestu\u00e1rio",
    "Acess\u00f3rios",
    "Outros Desportos",
]
widths = [992, 1100, 1199, 1200, 1440, 1600, 1920]
failures = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in widths:
        page = browser.new_page(viewport={"width": width, "height": 900}, locale="pt-PT")
        page.goto(url, wait_until="networkidle")
        if width == 1920:
            names = menu_names
        elif width == 1100:
            # At this breakpoint the fourth item moves into the header overflow menu.
            names = menu_names[:3]
        else:
            names = menu_names[:1]
        for name in names:
            toggle = page.locator("header a.dropdown-toggle:visible").filter(has_text=name).first
            toggle.click(force=True)
            page.wait_for_timeout(350)
            result = page.evaluate("""() => {
                const mega = [...document.querySelectorAll('.o_mega_menu')].find(e => e.offsetParent);
                const header = document.querySelector('header nav .o_main_nav');
                if (!mega || !header) return null;
                const m = mega.getBoundingClientRect();
                const h = header.getBoundingClientRect();
                return {
                    mega: [Math.round(m.left), Math.round(m.right), Math.round(m.width)],
                    header: [Math.round(h.left), Math.round(h.right), Math.round(h.width)],
                };
            }""")
            if not result:
                failures.append(f"{width} {name}: menu/header not found")
                continue
            delta = max(abs(result["mega"][i] - result["header"][i]) for i in range(3))
            print(width, name, "mega", result["mega"], "header", result["header"], "delta", delta)
            if delta > 1:
                failures.append(f"{width} {name}: delta={delta}")
            toggle.click(force=True)
        page.close()
    browser.close()

if failures:
    raise SystemExit("FAILED: " + "; ".join(failures))
print("OK all tested mega menus align with the header container")
'@

$tempScript = Join-Path $env:TEMP 'validate_chapatim_mega_menu_width.py'
Set-Content -LiteralPath $tempScript -Value $pythonSource -Encoding UTF8
python $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Live mega-menu validation failed.' }
