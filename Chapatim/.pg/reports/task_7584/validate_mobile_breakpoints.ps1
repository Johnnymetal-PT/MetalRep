$ErrorActionPreference = 'Stop'
$pythonSource = @'
from playwright.sync_api import sync_playwright
pages = {
 "home":"https://chapatim.odoo.com/",
 "shop":"https://chapatim.odoo.com/shop",
 "product":"https://chapatim.odoo.com/shop/roll-line-base-dance-17",
 "contactos":"https://chapatim.odoo.com/contactos",
}
with sync_playwright() as p:
 b=p.chromium.launch()
 for width in (320,360,375,390,430):
  ctx=b.new_context(viewport={"width":width,"height":844},is_mobile=True,has_touch=True,locale="pt-PT")
  for name,url in pages.items():
   pg=ctx.new_page(); response=pg.goto(url,wait_until="domcontentloaded",timeout=30000); pg.wait_for_timeout(350)
   dims=pg.evaluate("() => ({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight})")
   print(width,name,response.status if response else None,dims,"overflow",dims['scroll']-dims['client'])
   pg.close()
  ctx.close()
 b.close()
'@
$tempScript = Join-Path $env:TEMP 'validate_chapatim_mobile_breakpoints.py'
Set-Content -LiteralPath $tempScript -Value $pythonSource -Encoding UTF8
python $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Mobile breakpoint validation failed.' }
