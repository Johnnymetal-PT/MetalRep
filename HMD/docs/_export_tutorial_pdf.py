"""Markdown -> PDF (HTML estilizado + Edge/Chrome headless). Uso: python _export_tutorial_pdf.py docs/X.md"""
import os, sys, subprocess, tempfile, time, markdown

SRC = sys.argv[1] if len(sys.argv) > 1 else 'docs/TUTORIAL_QC_HMD.md'
base = os.path.splitext(SRC)[0]
html = os.path.abspath(base + '.html')
pdf = os.path.abspath(base + '.pdf')

body = markdown.markdown(open(SRC, encoding='utf-8').read(),
                         extensions=['tables', 'fenced_code', 'sane_lists'])
CSS = ("@page{size:A4;margin:18mm 16mm}"
       "body{font-family:'Segoe UI',Calibri,sans-serif;font-size:11pt;line-height:1.5;color:#1a1a1a}"
       "h1{font-size:21pt;color:#2F5496;border-bottom:3px solid #2F5496;padding-bottom:6px}"
       "h2{font-size:14pt;color:#2F5496;border-bottom:1px solid #d0d7e5;padding-bottom:3px;margin-top:20px}"
       "h3{font-size:12pt;color:#44546A}"
       "blockquote{background:#eef2f9;border-left:4px solid #2F5496;padding:8px 14px;color:#33415c}"
       "table{border-collapse:collapse;width:100%;font-size:10pt;margin:10px 0}"
       "th{background:#2F5496;color:#fff;text-align:left;padding:7px 9px}"
       "td{border:1px solid #c8d0e0;padding:6px 9px}tr:nth-child(even) td{background:#f4f7fb}"
       "code{background:#eef0f3;padding:1px 5px;border-radius:3px;font-family:Consolas,monospace;font-size:9.5pt;color:#b5360a}"
       "ul,ol{padding-left:22px}hr{border:none;border-top:1px solid #d0d7e5;margin:16px 0}"
       "table,blockquote{page-break-inside:avoid}h2,h3{page-break-after:avoid}")
open(html, 'w', encoding='utf-8').write(
    f"<!DOCTYPE html><html lang='pt'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>")


def find_browser():
    for c in [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
              r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
              r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']:
        if os.path.exists(c):
            return c
    return None


b = find_browser()
if not b:
    print('Sem browser; HTML em', html)
    sys.exit(0)
if os.path.exists(pdf):
    os.remove(pdf)
ud = tempfile.mkdtemp(prefix='edgepdf_')
cmd = [b, '--headless=new', '--disable-gpu', '--no-sandbox', f'--user-data-dir={ud}',
       '--run-all-compositor-stages-before-draw', '--no-pdf-header-footer',
       f'--print-to-pdf={pdf}', 'file:///' + html.replace(os.sep, '/')]
subprocess.run(cmd, capture_output=True, timeout=90)
for _ in range(12):                       # Edge escreve o PDF de forma assincrona
    if os.path.exists(pdf) and os.path.getsize(pdf) > 1000:
        break
    time.sleep(1)
if os.path.exists(html):
    os.remove(html)
print(f'PDF: {pdf} ({os.path.getsize(pdf)//1024} KB)' if os.path.exists(pdf) else 'PDF falhou')
