#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1. Cria milestones no projecto Odoo - HMD (id=93)
2. Associa as tarefas criadas (5670-5706) a cada milestone
3. Gera HTML + PDF do planeamento para enviar ao cliente
"""
import xmlrpc.client, sys, io, os, subprocess, textwrap
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL     = 'https://parametroglobal.odoo.com'
DB      = 'parametro-main-29950773'
LOGIN   = 'pedro.coelho@parametro.global'
API_KEY = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'
PROJECT_ID = 93
OUT_DIR    = r'c:\Projetos\HMD\.pg'

# ── Milestones e tasks associadas ────────────────────────────
MILESTONES = [
    {
        'name': 'M1 — Sprint Imediato',
        'deadline': '2026-06-15',
        'desc': 'Prioridades imediatas: reorganização de projetos, templates, WhatsApp, vídeos de formação.',
        'task_ids': [5670, 5671, 5672, 5673, 5674, 5675, 5680, 5700, 5704, 5705, 5706],
    },
    {
        'name': 'M2 — Estabilização Comercial & QC',
        'deadline': '2026-06-30',
        'desc': 'Templates de cotação, painel QC, cash-flow, empréstimos, permissões contabilísticas.',
        'task_ids': [5676, 5678, 5679, 5681, 5684, 5685, 5686, 5689, 5690, 5692, 5693, 5694, 5699],
    },
    {
        'name': 'M3 — Funcionalidades Avançadas',
        'deadline': '2026-09-30',
        'desc': 'WhatsApp ativo, documento intrastat, galeria QC, automações de pagamento, Marketing Automation.',
        'task_ids': [5677, 5682, 5683, 5687, 5688, 5691, 5695, 5696, 5697, 5698],
    },
    {
        'name': 'M4 — Preparação Upgrade Odoo 19',
        'deadline': '2026-10-31',
        'desc': 'Clone do tenant, testes de upgrade, identificação de módulos a refactorizar.',
        'task_ids': [5701],
    },
    {
        'name': 'M5 — Upgrade Produção & Fecho de Projeto',
        'deadline': '2027-01-15',
        'desc': 'Refactor de módulos custom, upgrade em produção, go-live Odoo 19, fecho formal do projeto.',
        'task_ids': [5702, 5703],
    },
]

# ── Ligação Odoo ─────────────────────────────────────────────
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid    = common.authenticate(DB, LOGIN, API_KEY, {})
print(f'Authenticated: uid={uid}')
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def exe(model, method, args, kw=None):
    return models.execute_kw(DB, uid, API_KEY, model, method, args, kw or {})

# ── Verificar se milestone_id existe em project.task ─────────
task_fields = exe('project.task', 'fields_get', [], {'attributes': ['string']})
has_milestone = 'milestone_id' in task_fields
print(f'milestone_id field available: {has_milestone}')

# ── Criar milestones ─────────────────────────────────────────
print('\nCreating milestones...')
milestone_map = {}  # name -> odoo_id

for m in MILESTONES:
    # verificar se já existe
    existing = exe('project.milestone', 'search',
                   [[['name', '=', m['name']], ['project_id', '=', PROJECT_ID]]])
    if existing:
        mid = existing[0]
        print(f'  already exists: [{mid}] {m["name"]}')
    else:
        mid = exe('project.milestone', 'create', [{
            'name':       m['name'],
            'project_id': PROJECT_ID,
            'deadline':   m['deadline'],
        }])
        print(f'  created: [{mid}] {m["name"]} deadline={m["deadline"]}')
    milestone_map[m['name']] = mid

# ── Associar tarefas a milestones ────────────────────────────
if has_milestone:
    print('\nAssociating tasks to milestones...')
    for m in MILESTONES:
        mid = milestone_map[m['name']]
        if m['task_ids']:
            exe('project.task', 'write', [m['task_ids'], {'milestone_id': mid}])
            print(f'  [{mid}] {m["name"]}: {len(m["task_ids"])} tasks assigned')
else:
    print('WARNING: milestone_id not available on project.task — skipping task association')

# ── Ler nomes das tarefas para o documento ───────────────────
print('\nReading task names...')
all_task_ids = [tid for m in MILESTONES for tid in m['task_ids']]
tasks_data = exe('project.task', 'read', [all_task_ids],
                 {'fields': ['id', 'name', 'date_deadline', 'planned_date_begin', 'priority']})
task_by_id = {t['id']: t for t in tasks_data}

print(f'  Read {len(tasks_data)} tasks')


# ════════════════════════════════════════════════════════════
# GERAÇÃO DO HTML / PDF
# ════════════════════════════════════════════════════════════

def fmt_date(d):
    if not d:
        return '—'
    return str(d)[:10]

def priority_label(p):
    return '★ Urgente' if p == '1' else 'Normal'

def clean_name(name):
    # remover prefixo [Xxx] do nome da tarefa
    import re
    return re.sub(r'^\[[^\]]+\]\s*', '', name)

# Cores por milestone
COLORS = ['#1a5276', '#1e8449', '#7d6608', '#784212', '#512e5f']
LIGHT  = ['#d6eaf8', '#d5f5e3', '#fef9e7', '#fdebd0', '#f5eef8']

rows_by_milestone = []
for i, m in enumerate(MILESTONES):
    rows = []
    for tid in m['task_ids']:
        t = task_by_id.get(tid)
        if not t:
            continue
        rows.append({
            'id':       tid,
            'name':     clean_name(t['name']),
            'start':    fmt_date(t.get('planned_date_begin')),
            'deadline': fmt_date(t.get('date_deadline')),
            'priority': priority_label(t.get('priority', '0')),
        })
    rows_by_milestone.append((m, rows, COLORS[i], LIGHT[i]))

# Gantt simples em HTML (tabela de semanas)
from datetime import date, timedelta

proj_start = date(2026, 5, 25)
proj_end   = date(2027, 1, 15)

milestone_rows_html = ''
for m, rows, color, light in rows_by_milestone:
    mid_id = milestone_map[m['name']]
    n = len(rows)
    milestone_rows_html += f'''
        <tr class="milestone-header" style="background:{color};color:#fff;">
            <td colspan="4"><strong>{m["name"]}</strong> — entrega: {m["deadline"]}</td>
            <td style="text-align:center">{n} tarefa{"s" if n!=1 else ""}</td>
        </tr>
        <tr style="background:{light};font-size:0.85em;font-style:italic;">
            <td colspan="5" style="padding:4px 12px;">{m["desc"]}</td>
        </tr>
    '''
    for r in rows:
        prio_style = 'color:#c0392b;font-weight:bold;' if r['priority'] == '★ Urgente' else ''
        milestone_rows_html += f'''
        <tr>
            <td style="width:36px;color:#888;font-size:0.8em">{r["id"]}</td>
            <td>{r["name"]}</td>
            <td style="text-align:center">{r["start"]}</td>
            <td style="text-align:center">{r["deadline"]}</td>
            <td style="text-align:center;{prio_style}">{r["priority"]}</td>
        </tr>'''

# Timeline visual (milestones como blocos)
timeline_html = ''
total_days = (proj_end - proj_start).days
for i, m in enumerate(MILESTONES):
    dl = date.fromisoformat(m['deadline'])
    pct_end   = min(100, (dl - proj_start).days / total_days * 100)
    prev_dl   = date.fromisoformat(MILESTONES[i-1]['deadline']) if i > 0 else proj_start
    pct_start = max(0, (prev_dl - proj_start).days / total_days * 100)
    width = pct_end - pct_start
    short = m['name'].replace('M', '').split('—')[0].strip()
    timeline_html += f'''
        <div style="position:absolute;left:{pct_start:.1f}%;width:{width:.1f}%;
                    background:{COLORS[i]};color:#fff;font-size:0.7em;
                    padding:4px 2px;box-sizing:border-box;text-align:center;
                    border-right:2px solid #fff;overflow:hidden;white-space:nowrap;">
            {m["name"].split("—")[0].strip()}<br/>
            <small>{m["deadline"]}</small>
        </div>'''

HTML = f'''<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8"/>
<title>Plano de Projeto — HMD Interiors — Odoo 18 Enterprise</title>
<style>
  @page {{ size: A4; margin: 18mm 15mm; }}
  body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    color: #222;
    margin: 0;
    padding: 0;
  }}
  h1 {{ font-size: 16pt; color: #1a5276; margin-bottom: 2px; }}
  h2 {{ font-size: 12pt; color: #1a5276; border-bottom: 2px solid #1a5276;
        padding-bottom: 4px; margin-top: 22px; }}
  .meta {{ color: #555; font-size: 9pt; margin-bottom: 18px; }}
  .meta span {{ margin-right: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th {{ background: #2e4057; color: #fff; padding: 6px 8px; text-align: left; font-size: 9pt; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #e0e0e0; vertical-align: top; }}
  tr:hover {{ background: #f9f9f9; }}
  .milestone-header td {{ padding: 8px 12px; font-size: 10pt; }}
  .summary-box {{
    display: inline-block; background: #f0f4f8; border-left: 4px solid #1a5276;
    padding: 8px 16px; margin: 6px 12px 6px 0; border-radius: 2px; font-size: 9pt;
  }}
  .summary-box strong {{ display: block; font-size: 13pt; color: #1a5276; }}
  .timeline-wrap {{
    position: relative; height: 54px; background: #eee;
    border-radius: 4px; margin: 12px 0 6px 0; overflow: hidden;
  }}
  .axis {{ display:flex; justify-content:space-between; font-size:8pt; color:#888; margin-top:2px; }}
  .note {{ font-size: 8.5pt; color: #555; margin-top: 16px; border-top: 1px solid #ddd; padding-top: 8px; }}
  .footer {{ font-size: 8pt; color: #888; text-align: center; margin-top: 24px; }}
  @media print {{
    body {{ font-size: 9pt; }}
    h1 {{ font-size: 14pt; }}
  }}
</style>
</head>
<body>

<h1>Plano de Projeto — HMD Interiors</h1>
<div class="meta">
  <span><strong>Cliente:</strong> HMD INTERIORS — Edição Produção de Mobiliário Lda</span>
  <span><strong>Projeto:</strong> Odoo 18 Enterprise — Implementação & Evolução</span><br/>
  <span><strong>Período:</strong> 25 Maio 2026 → 15 Janeiro 2027</span>
  <span><strong>Elaborado:</strong> 25/05/2026</span>
  <span><strong>Gestor:</strong> João Barros — Parâmetro Global</span>
</div>

<h2>Resumo Executivo</h2>
<p>O projeto HMD encontra-se em fase de evolução e estabilização, com 30+ módulos custom implementados
nas áreas de CRM, Vendas, Compras, Produção, eCommerce e Qualidade.
O presente plano organiza o trabalho restante em <strong>5 milestones</strong> até Janeiro de 2027,
incluindo a migração para Odoo 19.</p>

<div>
  <div class="summary-box"><strong>37</strong> Tarefas planeadas</div>
  <div class="summary-box"><strong>5</strong> Milestones</div>
  <div class="summary-box"><strong>2026-05-25</strong> Início</div>
  <div class="summary-box"><strong>2027-01-15</strong> Fecho</div>
  <div class="summary-box"><strong>Quinta 10h–10h30</strong> PDS semanal</div>
</div>

<h2>Timeline de Milestones</h2>
<div class="timeline-wrap">
  {timeline_html}
</div>
<div class="axis">
  <span>Mai 2026</span><span>Jun 2026</span><span>Set 2026</span>
  <span>Out 2026</span><span>Nov 2026</span><span>Jan 2027</span>
</div>

<h2>Milestones e Tarefas</h2>
<table>
  <thead>
    <tr>
      <th style="width:36px">#</th>
      <th>Tarefa</th>
      <th style="width:90px;text-align:center">Início</th>
      <th style="width:90px;text-align:center">Entrega</th>
      <th style="width:70px;text-align:center">Prioridade</th>
    </tr>
  </thead>
  <tbody>
    {milestone_rows_html}
  </tbody>
</table>

<h2>Modelo de Acompanhamento</h2>
<table>
  <thead><tr><th>Mecanismo</th><th>Detalhe</th></tr></thead>
  <tbody>
    <tr><td>PDS Semanal</td><td>Sessão Quinta-feira 10h–10h30 a partir de 28/05/2026. Agenda enviada pelo cliente até Quarta 12h.</td></tr>
    <tr><td>Plano de Acção</td><td>Tarefas visíveis e rastreáveis no Odoo interno PG (projecto "Odoo - HMD"). Estado actualizado semanalmente.</td></tr>
    <tr><td>Formação & Procedimentos</td><td>Vídeos curtos HMD-specific alojados no chatter de cada tarefa-template. Prioridades: projecto-template, QC espontâneo, pagamentos sem fatura.</td></tr>
    <tr><td>Migração Odoo 19</td><td>Decisão go/no-go até 30/06/2026. Upgrade em produção planeado para Dezembro 2026 / Janeiro 2027.</td></tr>
  </tbody>
</table>

<div class="note">
  <strong>Notas:</strong>
  Tarefas marcadas ★ Urgente requerem acção imediata ou dependem de decisão do cliente.
  O plano será revisto e actualizado em cada sessão semanal de quinta-feira.
  Versão do Odoo: 18.0 Enterprise On-Premise.
</div>

<div class="footer">
  Parâmetro Global — Consultoria Informática, S.A. &nbsp;|&nbsp;
  joao.barros@parametro.global &nbsp;|&nbsp;
  www.parametro.global &nbsp;|&nbsp;
  Documento gerado em 25/05/2026
</div>

</body>
</html>
'''

html_path = os.path.join(OUT_DIR, 'PLANO_HMD_2026Q2.html')
pdf_path  = os.path.join(OUT_DIR, 'PLANO_HMD_2026Q2.pdf')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f'\nHTML saved: {html_path}')

# ── Converter para PDF via Edge ou Chrome headless ───────────
def find_browser():
    candidates = [
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

browser = find_browser()
if browser:
    cmd = [
        browser,
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={pdf_path}',
        '--print-to-pdf-no-header',
        html_path,
    ]
    print(f'Converting to PDF using: {os.path.basename(browser)}...')
    result = subprocess.run(cmd, capture_output=True, timeout=30)
    if os.path.exists(pdf_path):
        size_kb = os.path.getsize(pdf_path) // 1024
        print(f'PDF generated: {pdf_path} ({size_kb} KB)')
    else:
        print(f'PDF generation failed. stderr: {result.stderr.decode("utf-8","replace")[:200]}')
        print(f'Open the HTML manually and print to PDF: {html_path}')
else:
    print('No browser found for PDF conversion.')
    print(f'Open the HTML manually and print to PDF: {html_path}')

print(f'\n{"="*55}')
print(f'Milestones created: {len(milestone_map)}')
print(f'Tasks associated  : {sum(len(m["task_ids"]) for m in MILESTONES)}')
print(f'HTML output       : {html_path}')
print(f'PDF output        : {pdf_path if os.path.exists(pdf_path) else "see above"}')
print(f'{"="*55}')
