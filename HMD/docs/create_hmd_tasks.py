#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cria todas as tarefas do PLANO_2026Q2_HMD no Odoo interno PG.
Fonte: PLANO_2026Q2_HMD.md + reuniao 2026-05-20
"""
import xmlrpc.client
import sys
import re

URL       = 'https://parametroglobal.odoo.com'
LOGIN     = 'pedro.coelho@parametro.global'
API_KEY   = '9e000dc8997ff1c2f3afe4920138dfe03ffe6973'
FIND_FROM_TASK_ID = 5641  # descobrir projeto a partir desta tarefa
PROJ_DATE_START = '2026-05-25'
PROJ_DATE_END   = '2027-01-31'

# ============================================================
# LISTA DE TAREFAS
# start/deadline : YYYY-MM-DD
# priority       : '0'=normal  '1'=urgente
# ============================================================
TASKS = [
    # ── SPRINT IMEDIATO (até 2026-06-15) ─────────────────────
    {
        'name': '[P1+P2+P3] Reformular fases projeto HMD — 3 fases globais + fases tarefa + 4 templates',
        'description': (
            '<p><strong>Objetivo:</strong> Reduzir project.project.stage a Novo / Em Progresso / Concluído.<br/>'
            'Criar fases de tarefa por projeto: Desenho / Compras / Produção / Montagem / Concluído.<br/>'
            'Criar 4 templates de projeto: Encomenda Cliente, Projeto Interno, Formação, Desenvolvimento.<br/>'
            'Preservar filtros existentes para projetos internos/formação.<br/>'
            'Reaproveitar template "produtos novos" já existente.</p>'
        ),
        'start': '2026-05-25', 'deadline': '2026-06-06', 'priority': '1',
    },
    {
        'name': '[V2] Configurar Spreadsheet Calculator de transportes',
        'description': (
            '<p>Ativar documents_spreadsheet (enterprise).<br/>'
            'Reunir tabelas de custo dos paranistários com Sérgio (input obrigatório antes).<br/>'
            'Criar spreadsheet de cálculo de custo/transporte ligada ao orçamento.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-13', 'priority': '1',
    },
    {
        'name': '[C5] Reformular template QWeb recibo de adiantamento',
        'description': (
            '<p>Ajuste de layout do relatório QWeb existente em ptplus_sale_advance_payment.<br/>'
            '<strong>Atenção:</strong> apenas layout — NÃO alterar documento de fatura certificada PT.<br/>'
            'Cliente confirmou: só layout, sem mexer no documento.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-13', 'priority': '1',
    },
    {
        'name': '[C6] Gravar vídeo: fluxo pagamentos sem fatura (IRS / IVA / SS)',
        'description': (
            '<p>Documentar e gravar vídeo curto HMD-specific:<br/>'
            '1. Criar diário tipo Diversos "Custos Pessoal/Impostos"<br/>'
            '2. Criar fornecedores-entidade: Segurança Social, AT-IRS, AT-IVA<br/>'
            '3. Lançar pagamentos sem fatura<br/>'
            'Alojar no chatter da tarefa-template correspondente.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-13', 'priority': '0',
    },
    {
        'name': '[V3] Levantar pré-requisitos WhatsApp Business (conta Meta + número dedicado)',
        'description': (
            '<p><strong>URGENTE</strong> — templates Meta podem demorar semanas a aprovar.<br/>'
            'Passos: abrir conta Meta Business, definir número de telefone dedicado, '
            'preparar templates de mensagem para submissão à Meta.<br/>'
            'Coordenar com Mónica (HMD).</p>'
        ),
        'start': '2026-05-25', 'deadline': '2026-06-15', 'priority': '1',
    },
    {
        'name': '[V5] Cleanup contactos PHC vs Odoo — pedir extracção + script matching',
        'description': (
            '<p><strong>BLOQUEIA NO CLIENTE</strong> — pedir extracção PHC ao cliente.<br/>'
            'Preparar script de matching por VAT/email para detectar contactos em falta sem duplicar.<br/>'
            'Método: custom leve (script de import).</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-15', 'priority': '0',
    },
    {
        'name': '[W2] Confirmar acerto contratual O365 / alojamento com Cláudio',
        'description': (
            '<p><strong>BLOQUEIA NO CLIENTE</strong> — Cláudio a fazer acerto contratual.<br/>'
            'Decisão: OneDrive/O365 para arquivo fotográfico pesado vs alojamento original.<br/>'
            'Define onde fica o arquivo fotográfico HMD.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },

    # ── BACKLOG — PROJETOS ────────────────────────────────────
    {
        'name': '[P4] Auto-criação projeto ao qualificar lead CRM (custom leve)',
        'description': (
            '<p>Hook de qualificação sobre pg_crm_project_opportunities.<br/>'
            'Resultado: qualificar lead → cria projeto com tarefas copiadas do template.<br/>'
            'Base já existe; falta o hook + cópia das tarefas template.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-09-30', 'priority': '0',
    },
    {
        'name': '[P5] Verificar espelhamento item venda → tarefa projeto (1 SOL = 1 task)',
        'description': (
            '<p>Confirmar cobertura do módulo existente em novos SO.<br/>'
            'Verificar comportamento em SO em rascunho vs confirmado.</p>'
        ),
        'start': '2026-06-15', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[P6] Vista agregada tarefas entre projetos por etapa operacional',
        'description': (
            '<p>Vista kanban/lista de project.task agrupada por etapa, cruzando todos os projetos HMD.<br/>'
            'Configuração standard — disponível após P1+P2 concluídos.</p>'
        ),
        'start': '2026-06-07', 'deadline': '2026-06-20', 'priority': '0',
    },
    {
        'name': '[P7] Configurar custo/hora por colaborador (hr.employee.hourly_cost)',
        'description': (
            '<p>Preencher campo hr.employee.hourly_cost para elementos que fazem análise pré-venda.<br/>'
            'Não requer timesheet detalhado por tarefa.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-15', 'priority': '0',
    },

    # ── BACKLOG — CRM / VENDAS ────────────────────────────────
    {
        'name': '[V1] Templates de cotação por linha de produto (sale.order.template)',
        'description': (
            '<p>Ativar "Usar modelos de orçamento" em Vendas > Configuração.<br/>'
            'Criar templates para caixas de amostra e modelos por linha de produto frequente.<br/>'
            'Não confundir com calculadora de preço (hmd_sale_price_calculator).</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[V3b] Instalar módulo WhatsApp enterprise + configurar canal por SO',
        'description': (
            '<p>Instalar whatsapp + whatsapp_sale (enterprise).<br/>'
            'Pré-condição: aprovação Meta e número configurado (ver tarefa V3).<br/>'
            'whatsapp_sale cria canal WhatsApp por SO automaticamente (zero config adicional).</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },
    {
        'name': '[V7] Documento exportação/intrastat anexo à fatura (HS Code + peso + cubicagem)',
        'description': (
            '<p>1. Instalar account_intrastat enterprise (HS Code + códigos Intrastat em product.template).<br/>'
            '2. Criar relatório QWeb pg_export_document sobre account.move.<br/>'
            '3. Reaproveitar peso/cubicagem de pg_packing_list.<br/>'
            '<strong>NÃO mexer no documento de fatura certificada PT.</strong><br/>'
            'Imprimível sob pedido a partir do botão Imprimir da fatura.</p>'
        ),
        'start': '2026-08-01', 'deadline': '2026-08-31', 'priority': '0',
    },
    {
        'name': '[V8] Botão IDU — impressão direta única para encomendas e faturas',
        'description': (
            '<p>Validar se já existe via Studio.<br/>'
            'Se não, criar action shortcut de impressão direta.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },

    # ── BACKLOG — QC ─────────────────────────────────────────
    {
        'name': '[Q1] Configurar painel QC com filtros guardados + kanban',
        'description': (
            '<p>Em quality.check: criar filtros guardados por Estado=Pendente, por Tipo, por Fornecedor.<br/>'
            'Guardar como vistas favoritas. Configuração standard Odoo 18.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[Q2] Criar atalho mobile criação espontânea QC no terreno',
        'description': (
            '<p>Action shortcut para quality.check direto (foto + nota) sem passar por Quality Control Point.<br/>'
            'Ativar acesso mobile para utilizadores da produção (browser).</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[Q3] Vista gallery em quality.check (custom leve)',
        'description': (
            '<p>Vista galeria de imagens/fotos das verificações QC.<br/>'
            'Alta utilidade segundo Mónica. Custom leve.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },
    {
        'name': '[Q4] Painel encomendas fornecedor com QC associadas (smart button)',
        'description': (
            '<p>Vista purchase.order com smart button para quality.check associadas.<br/>'
            'Integrar com vista P6 se possível.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },

    # ── BACKLOG — CONTABILIDADE ───────────────────────────────
    {
        'name': '[C1] Instalar account_loans + importar empréstimos históricos até 2026',
        'description': (
            '<p>Instalar módulo enterprise account_loans.<br/>'
            'Substituir hack manual atual. Importar empréstimos históricos.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[C2] Activar cash-flow 30/60/90 + previsão recebimentos/pagamentos',
        'description': (
            '<p>Ativar account_reports enterprise (se não ativo).<br/>'
            'Configurar aging report e cash flow dashboard.<br/>'
            'Ensinar equipa HMD a usar.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[C3] Relatório depósitos 40% (Advance Payment) — controlo de adiantamentos',
        'description': (
            '<p>Base existe em ptplus_sale_advance_payment.<br/>'
            'Criar relatório de controlo sobre account.payment linked a sale.order.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },
    {
        'name': '[C6b] Configurar diário Custos Pessoal + fornecedores-entidade',
        'description': (
            '<p>Criar diário tipo Diversos "Custos Pessoal/Impostos".<br/>'
            'Criar fornecedores: Segurança Social, AT-IRS, AT-IVA.<br/>'
            'Demonstrado na reunião de 20/05 — falta só documentar e configurar.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[C7] Configurar permissões por diário contabilístico',
        'description': (
            '<p>Validar granularidade requerida pelo cliente.<br/>'
            'Configurar restrict_mode_hash_table + grupos por utilizador em account.journal.</p>'
        ),
        'start': '2026-06-15', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[C8] Configurar contas cartão de crédito',
        'description': (
            '<p>Criar diário tipo Bank para cartão de crédito.<br/>'
            'Configurar statement import.</p>'
        ),
        'start': '2026-06-15', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[C9] Instalar hr_expense + configurar categorias por cartão',
        'description': (
            '<p>Instalar hr_expense (enterprise standard).<br/>'
            'Criar categorias de despesa por tipo de cartão.<br/>'
            'Configurar acesso restrito ao próprio utilizador.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },
    {
        'name': '[C11] Alerta pagamento cliente → mudar estado SO automaticamente (server action)',
        'description': (
            '<p>Server action em account.payment → atualizar state em sale.order.<br/>'
            'Fluxo: Nina envia transferência → Sérgio confirma → SO muda automaticamente.</p>'
        ),
        'start': '2026-08-01', 'deadline': '2026-08-31', 'priority': '0',
    },
    {
        'name': '[C12] Alertas pagamentos sem fatura impostos (cron / atividade recorrente)',
        'description': (
            '<p>Configurar cron ou atividade recorrente para alertar pagamentos de impostos pendentes.<br/>'
            'Configuração standard simples.</p>'
        ),
        'start': '2026-07-01', 'deadline': '2026-07-31', 'priority': '0',
    },

    # ── BACKLOG — WEBSITE / MARKETING ────────────────────────
    {
        'name': '[W3] Avaliar e ativar Marketing Automation + Email Marketing',
        'description': (
            '<p>Módulo standard enterprise já disponível.<br/>'
            'Avaliar após CRM/projetos estarem estáveis.<br/>'
            'Configurar listas de mailing separadas dos contactos comerciais (res.partner.category).</p>'
        ),
        'start': '2026-09-01', 'deadline': '2026-09-30', 'priority': '0',
    },

    # ── MIGRAÇÃO v19 ─────────────────────────────────────────
    {
        'name': '[v19] Decisão go/no-go upgrade Odoo 18→19 — aprovação cliente',
        'description': (
            '<p>Cliente deve aprovar janela de upgrade Dez/Jan 2026-27.<br/>'
            'Define ordem das melhorias Jun-Set. Prazo limite: 2026-06-30.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-30', 'priority': '0',
    },
    {
        'name': '[v19] Aprovar instalação WhatsApp enterprise (custos Meta) — decisão cliente',
        'description': (
            '<p>Decisão do cliente sobre instalação do módulo WhatsApp enterprise e conta Meta Business.<br/>'
            'Bloqueia V3 e V4.</p>'
        ),
        'start': '2026-05-25', 'deadline': '2026-06-15', 'priority': '1',
    },
    {
        'name': '[v19] Clone tenant HMD para ambiente de testes + correr upgrade v19',
        'description': (
            '<p>Clonar tenant em ambiente isolado.<br/>'
            'Correr odoo-bin --upgrade-path para v19.<br/>'
            'Identificar falhas em módulos custom pg_*/hmd_* (especialmente 3D viewer e website).</p>'
        ),
        'start': '2026-10-01', 'deadline': '2026-10-31', 'priority': '0',
    },
    {
        'name': '[v19] Refactor módulos custom para compatibilidade Odoo 19',
        'description': (
            '<p>Refactor dos módulos afetados pela migração v19.<br/>'
            'Atenção especial: pg_3d_viewer, pg_3d_ecommerce, pg_product_model_viewer.<br/>'
            'Refazer alterações de website com blocos standard v19.</p>'
        ),
        'start': '2026-11-01', 'deadline': '2026-11-30', 'priority': '0',
    },
    {
        'name': '[v19] Upgrade produção Odoo 18→19 + go-live (janela Dez/Jan)',
        'description': (
            '<p>Upgrade em produção com rollback preparado (snapshot completo).<br/>'
            'Testes em staging com utilizadores HMD durante 1-2 semanas antes do go-live.<br/>'
            'Janela: semana de baixa atividade após fecho de mês.</p>'
        ),
        'start': '2026-12-01', 'deadline': '2027-01-15', 'priority': '1',
    },

    # ── OPERAÇÃO CONSULTIVA ───────────────────────────────────
    {
        'name': '[OPS] Sessões semanais HMD — Quinta 10h-10h30 (a partir 2026-05-28)',
        'description': (
            '<p>Reuniões semanais 30min a partir de 2026-05-28.<br/>'
            'Cliente envia agenda até Quarta 12h.<br/>'
            'Substituir modelo de tickets por sessões consultivas + vídeos HMD-specific.</p>'
        ),
        'start': '2026-05-28', 'deadline': '2027-01-31', 'priority': '0',
    },
    {
        'name': '[OPS] Vídeo HMD-specific: criação de projeto-template',
        'description': (
            '<p>Vídeo curto sobre como criar e usar projeto-template no Odoo HMD.<br/>'
            'Alojar no chatter da tarefa-template correspondente.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-20', 'priority': '0',
    },
    {
        'name': '[OPS] Vídeo HMD-specific: fluxo QC espontâneo no terreno',
        'description': (
            '<p>Vídeo curto sobre criação espontânea de verificação de qualidade no terreno.<br/>'
            'Alojar no chatter da tarefa-template correspondente.</p>'
        ),
        'start': '2026-06-01', 'deadline': '2026-06-20', 'priority': '0',
    },
]


# ============================================================
# CONEXÃO
# ============================================================
import io
from datetime import date as _date
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def log(msg):
    print(msg, flush=True)

log(f"Connecting to {URL} ...")

# Descobrir base de dados via JSON-RPC session (funciona em Odoo SaaS odoo.com)
import urllib.request
import urllib.error
import json as _json

db = None

def jsonrpc(endpoint, method, params):
    payload = _json.dumps({
        'jsonrpc': '2.0', 'method': 'call', 'id': 1,
        'params': params,
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{URL}{endpoint}',
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return _json.loads(r.read())

# 1) Tentar autenticar via JSON-RPC sem especificar DB (Odoo SaaS resolve automaticamente)
try:
    res = jsonrpc('/web/session/authenticate', 'call', {
        'db': False, 'login': LOGIN, 'password': API_KEY,
    })
    session_db = (res.get('result') or {}).get('db')
    if session_db:
        db = session_db
        log(f"  Database discovered via session: {db}")
except Exception as e:
    log(f"  Session auth probe: {e}")

# 2) Fallback: tentar listar via XML-RPC /db
if not db:
    try:
        db_svc = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/db', allow_none=True)
        databases = db_svc.list()
        if databases:
            db = databases[0]
            log(f"  Databases via XML-RPC: {databases} -> using {db}")
    except Exception as e:
        log(f"  XML-RPC db list: {e}")

# 3) Fallback final: nome conhecido
if not db:
    db = 'parametro-main-29950773'
    log(f"  Using known db name: {db}")

# Autenticar via XML-RPC
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(db, LOGIN, API_KEY, {})
if not uid:
    log(f"ERROR: Authentication failed (db={db}, login={LOGIN})")
    sys.exit(1)
log(f"  Authenticated: uid={uid}, db={db}")

models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def exe(model, method, args, kw=None):
    return models.execute_kw(db, uid, API_KEY, model, method, args, kw or {})


# ============================================================
# ENCONTRAR PROJETO A PARTIR DA TAREFA DE REFERÊNCIA
# ============================================================
log(f"\nReading reference task {FIND_FROM_TASK_ID} ...")
ref_tasks = exe('project.task', 'read', [[FIND_FROM_TASK_ID]], {'fields': ['id', 'name', 'project_id']})
if not ref_tasks or not ref_tasks[0].get('project_id'):
    log(f"ERROR: Could not read task {FIND_FROM_TASK_ID} or it has no project.")
    sys.exit(1)

project_id   = ref_tasks[0]['project_id'][0]
project_name = ref_tasks[0]['project_id'][1]
log(f"  Project: {project_name} (id={project_id})")

# Atualizar datas do projeto
log(f"\nUpdating project dates ({PROJ_DATE_START} -> {PROJ_DATE_END}) ...")
try:
    exe('project.project', 'write', [[project_id], {
        'date_start': PROJ_DATE_START,
        'date':       PROJ_DATE_END,
    }])
    log("  Project dates updated.")
except Exception as e:
    log(f"  Warning (dates): {e}")


# ============================================================
# VERIFICAR CAMPOS DISPONÍVEIS EM project.task
# ============================================================
log("\nChecking project.task fields ...")
task_fields = exe('project.task', 'fields_get', [], {'attributes': ['string', 'type']})
has_planned_begin = 'planned_date_begin' in task_fields
log(f"  planned_date_begin available: {has_planned_begin}")


# ============================================================
# LER STAGES EXISTENTES — SEM CRIAR NENHUM NOVO
# ============================================================
log("\nReading existing stages for this project ...")
existing_stages = exe(
    'project.task.type', 'search_read',
    [[['project_ids', 'in', [project_id]]]],
    {'fields': ['id', 'name', 'sequence'], 'order': 'sequence asc'}
)
if not existing_stages:
    # fallback: stages sem projecto associado (stages globais)
    existing_stages = exe(
        'project.task.type', 'search_read',
        [[['project_ids', '=', False]]],
        {'fields': ['id', 'name', 'sequence'], 'order': 'sequence asc'}
    )

for s in existing_stages:
    log(f"  stage id={s['id']}  seq={s['sequence']}  name={s['name']}")

if not existing_stages:
    log("ERROR: No stages found for this project.")
    sys.exit(1)

# Mapear stages por palavras-chave (case-insensitive)
# Sprint -> primeiro stage com "sprint", "progresso", "curso", "doing", "in progress"
# Backlog -> stage com "backlog", "todo", "a fazer", "new"
# Fallback: usar os dois primeiros stages por sequência

_kw_sprint  = ('sprint', 'progresso', 'curso', 'doing', 'in progress', 'in_progress', 'ativo')
_kw_backlog = ('backlog', 'todo', 'a fazer', 'new', 'novo', 'incoming')

stage_sprint  = next((s['id'] for s in existing_stages if any(k in s['name'].lower() for k in _kw_sprint)),  None)
stage_backlog = next((s['id'] for s in existing_stages if any(k in s['name'].lower() for k in _kw_backlog)), None)

# Se não encontrou por keywords, usa os dois primeiros por sequência
if stage_sprint is None:
    stage_sprint = existing_stages[0]['id']
if stage_backlog is None:
    stage_backlog = existing_stages[1]['id'] if len(existing_stages) > 1 else existing_stages[0]['id']

_sprint_name  = next(s['name'] for s in existing_stages if s['id'] == stage_sprint)
_backlog_name = next(s['name'] for s in existing_stages if s['id'] == stage_backlog)
log(f"  -> Sprint stage : [{stage_sprint}] {_sprint_name}")
log(f"  -> Backlog stage: [{stage_backlog}] {_backlog_name}")

SPRINT_CUTOFF = _date(2026, 6, 15)

def pick_stage(deadline_str):
    d = _date.fromisoformat(deadline_str)
    return stage_sprint if d <= SPRINT_CUTOFF else stage_backlog


# ============================================================
# CRIAR TAREFAS
# ============================================================
log(f"\nCreating {len(TASKS)} tasks ...")
created = 0
errors  = 0

for t in TASKS:
    stage_id = pick_stage(t['deadline'])
    vals = {
        'name':         t['name'],
        'project_id':   project_id,
        'description':  t.get('description', ''),
        'date_deadline': t['deadline'],
        'priority':     t.get('priority', '0'),
        'stage_id':     stage_id,
    }
    if has_planned_begin:
        vals['planned_date_begin'] = t['start'] + ' 08:00:00'

    try:
        tid = exe('project.task', 'create', [vals])
        log(f"  ✓  [{tid}] {t['name'][:70]}")
        created += 1
    except Exception as e:
        log(f"  ✗  ERROR '{t['name'][:55]}': {e}")
        errors += 1

log(f"\n{'='*60}")
log(f"DONE — {created} tasks created, {errors} errors")
log(f"Project dates: {PROJ_DATE_START} → {PROJ_DATE_END}")
log(f"{'='*60}")
