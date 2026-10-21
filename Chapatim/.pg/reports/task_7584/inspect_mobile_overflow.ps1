$ErrorActionPreference = 'Stop'
$pythonSource = @'
from playwright.sync_api import sync_playwright
urls = [
 "https://chapatim.odoo.com/",
 "https://chapatim.odoo.com/shop",
 "https://chapatim.odoo.com/shop/category/acessorios-treino-117",
 "https://chapatim.odoo.com/contactos",
]
with sync_playwright() as p:
 b=p.chromium.launch(); ctx=b.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True)
 for url in urls:
  pg=ctx.new_page(); pg.goto(url,wait_until="networkidle")
  rows=pg.evaluate("""() => {
   const vw=document.documentElement.clientWidth;
   return [...document.querySelectorAll('body *')].filter(e=>{
    const r=e.getBoundingClientRect(),s=getComputedStyle(e);
    return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&(r.right>vw+2||r.left<-2);
   }).map(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e); return {
    tag:e.tagName.toLowerCase(),id:e.id||'',cls:String(e.className||'').slice(0,150),
    left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width),
    cssWidth:s.width,minWidth:s.minWidth,overflowX:s.overflowX,
    parent:(e.parentElement?.tagName.toLowerCase()||'')+'.'+String(e.parentElement?.className||'').slice(0,80),
    text:String(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,80)
   }}).slice(-35)
  }""")
  print('\nURL',url,'DOC',pg.evaluate("() => [document.documentElement.clientWidth,document.documentElement.scrollWidth]"))
  for row in rows: print(row)
  pg.close()
 ctx.close(); b.close()
'@
$tempScript = Join-Path $env:TEMP 'inspect_chapatim_mobile_overflow.py'
Set-Content -LiteralPath $tempScript -Value $pythonSource -Encoding UTF8
python $tempScript
if ($LASTEXITCODE -ne 0) { throw 'Overflow inspection failed.' }
