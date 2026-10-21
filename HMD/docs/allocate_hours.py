#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aloca horas estimadas às tarefas HMD com base no tipo de trabalho.
Critério: configuração standard 1-2h | módulo adicional 2-4h |
          custom leve 4-8h | custom estrutural 16-40h | migração 8-40h
"""
import xmlrpc.client, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

URL   = 'https://parametroglobal.odoo.com'
DB    = 'parametro-main-29950773'
LOGIN = 'pedro.coelho@parametro.global'
KEY   = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'

# ── Estimativas por tarefa (task_id: horas) ──────────────────
# Tipo | Racional
HOURS = {
    # ─── M1 Sprint Imediato ───────────────────────────────────
    5670:  4.0,  # P1+P2+P3  config standard complexa (stages + 4 templates)
    5671:  3.0,  # V2        spreadsheet calc (config + setup com Sérgio)
    5672:  4.0,  # C5        template QWeb adiantamento (custom leve)
    5673:  2.0,  # C6        vídeo pagamentos sem fatura (gravar + alojar)
    5674:  2.0,  # V3        levantar pré-requisitos WhatsApp (análise + reunião)
    5675:  4.0,  # V5        cleanup PHC vs Odoo (script matching + execução)
    5676:  1.0,  # W2        confirmação contratual O365 (reunião/email)
    5680:  1.0,  # P7        custo/hora por colaborador (config standard, 5 min)
    5700:  1.0,  # v19-WA    decisão cliente WhatsApp (acompanhamento)
    5704: 16.0,  # OPS       sessões semanais Quinta (≈8 meses × 2h/mês)
    5705:  2.0,  # OPS       vídeo projeto-template
    5706:  2.0,  # OPS       vídeo QC espontâneo

    # ─── M2 Estabilização Comercial & QC ─────────────────────
    5678:  2.0,  # P5        verificar espelhamento SO→task (análise + teste)
    5679:  1.0,  # P6        vista agregada tarefas (config standard)
    5681:  2.0,  # V1        templates cotação (config standard)
    5684:  1.0,  # V8        botão IDU (Studio ou action shortcut)
    5685:  2.0,  # Q1        painel QC filtros guardados (config standard)
    5686:  2.0,  # Q2        atalho mobile QC (config standard)
    5689:  4.0,  # C1        account_loans: instalar + importar empréstimos
    5690:  3.0,  # C2        cash-flow 30/60/90 (módulo + config + formação)
    5692:  2.0,  # C6b       diário custos pessoal + fornecedores (config standard)
    5693:  2.0,  # C7        permissões por diário (config standard)
    5694:  1.0,  # C8        cartão crédito journal (config standard)
    5699:  2.0,  # v19       go/no-go: análise + reunião cliente

    # ─── M3 Funcionalidades Avançadas ────────────────────────
    5677:  8.0,  # P4        auto-criação projeto CRM (custom leve sobre módulo existente)
    5682:  4.0,  # V3b       instalar WhatsApp enterprise + configurar canal SO
    5683: 12.0,  # V7        doc intrastat (instalar módulo + custom QWeb pg_export_document)
    5687:  6.0,  # Q3        vista gallery quality.check (custom leve)
    5688:  3.0,  # Q4        painel encomendas + QC (config + smart button)
    5691:  6.0,  # C3        relatório depósitos 40% (custom leve sobre módulo existente)
    5695:  3.0,  # C9        hr_expense: instalar + categorias por cartão
    5696:  6.0,  # C11       alerta pagamento → mudar estado SO (server action custom)
    5697:  2.0,  # C12       alertas impostos cron (config standard)
    5698:  4.0,  # W3        Marketing Automation (módulo + config inicial)

    # ─── M4 Preparação Upgrade v19 ───────────────────────────
    5701:  8.0,  # v19       clone tenant + upgrade-path v19 + relatório de falhas

    # ─── M5 Upgrade Produção & Fecho ─────────────────────────
    5702: 40.0,  # v19       refactor módulos custom (estrutural — 30+ módulos pg_/hmd_)
    5703: 16.0,  # v19       upgrade produção + staging + go-live
}

# ── Ligação Odoo ─────────────────────────────────────────────
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid    = common.authenticate(DB, LOGIN, KEY, {})
print(f'Authenticated: uid={uid}')
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def exe(model, method, args, kw=None):
    return models.execute_kw(DB, uid, KEY, model, method, args, kw or {})

# ── Aplicar horas ─────────────────────────────────────────────
print(f'\nAllocating hours to {len(HOURS)} tasks...\n')

MILESTONE_LABELS = {
    range(5670, 5677): 'M1',
    range(5677, 5700): 'M2/M3',
    range(5700, 5702): 'M4/v19',
    range(5702, 5707): 'M5',
}

updated = 0
errors  = 0
total   = 0.0
by_milestone = {}  # label -> (count, hours)

# Ler nomes para o relatório
tasks_info = exe('project.task', 'read', [list(HOURS.keys())],
                 {'fields': ['id', 'name', 'milestone_id']})
name_by_id      = {t['id']: t['name'] for t in tasks_info}
milestone_by_id = {t['id']: (t['milestone_id'][1] if t.get('milestone_id') else '—')
                   for t in tasks_info}

print(f'  {"ID":<6} {"h":>5}  {"Milestone":<38} Tarefa')
print(f'  {"-"*100}')

for task_id, hours in sorted(HOURS.items()):
    try:
        exe('project.task', 'write', [[task_id], {'allocated_hours': hours}])
        name = name_by_id.get(task_id, '?')[:60]
        ms   = milestone_by_id.get(task_id, '—')[:35]
        print(f'  {task_id:<6} {hours:>4.1f}h  {ms:<38} {name}')
        updated += 1
        total   += hours
        by_milestone[ms] = (by_milestone.get(ms, (0, 0.0))[0] + 1,
                            by_milestone.get(ms, (0, 0.0))[1] + hours)
    except Exception as e:
        print(f'  ERROR [{task_id}]: {e}')
        errors += 1

# ── Resumo por milestone ──────────────────────────────────────
print(f'\n  {"─"*60}')
print(f'  {"Milestone":<40} {"Tarefas":>8} {"Horas":>8}')
print(f'  {"─"*60}')
for ms, (cnt, hrs) in sorted(by_milestone.items()):
    print(f'  {ms:<40} {cnt:>8}  {hrs:>7.1f}h')
print(f'  {"─"*60}')
print(f'  {"TOTAL":<40} {updated:>8}  {total:>7.1f}h')
print(f'\n  = {total/8:.1f} dias de trabalho (a 8h/dia)')
print(f'  = {total:.0f} horas estimadas para concluir o projecto')
print(f'\n  {updated} tasks updated, {errors} errors')
