"""
Gerador de Orçamento Excel — Waterdetails / Virgin Details, Lda
Parâmetro Global · 2026-05-20

Config sheet layout (spec-exact):
  Row 1: title
  Row 2: blank (spacer)
  Row 3: column headers  (Parâmetro | Valor | Descrição)
  Row 4:  Taxa Consultor (€/h)       → B4 = 65
  Row 5:  Taxa Gestor (€/h)          → B5 = 90
  Row 6:  Horas por Dia              → B6 = 8
  Row 7:  N.º Utilizadores Odoo      → B7 = 5
  Row 8:  Desconto 1.º Ano (%)       → B8 = 0.20
  Row 9:  Data da Proposta           → B9
  Row 10: Válido até                 → B10
  Row 11: IVA (%)                    → B11 = 0.23
  Row 12: Apoio Após Venda (€/ano)   → B12 = 2400
"""

import os
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── Palette ───────────────────────────────────────────────────────────────────
DARK_BLUE  = "1F3864"
LIGHT_BLUE = "DEEAF1"
YELLOW     = "FFF2CC"
AMBER      = "FFF8E1"
WHITE      = "FFFFFF"
GRAY_BDR   = "BFBFBF"
ORANGE_TAB = "ED7D31"
BLUE_TAB   = "4472C4"
GRAY_TAB   = "808080"

# ── Config cell references (single source of truth) ───────────────────────────
CFG_TAXA_CONSULTOR  = "Config!$B$4"   # 65
CFG_TAXA_GESTOR     = "Config!$B$5"   # 90
CFG_HORAS_DIA       = "Config!$B$6"   # 8
CFG_NUM_USERS       = "Config!$B$7"   # 5
CFG_DESC_ODOO       = "Config!$B$8"   # 0.20
CFG_IVA             = "Config!$B$11"  # 0.23
CFG_AAV             = "Config!$B$12"  # 2400

# ── Style helpers ─────────────────────────────────────────────────────────────
def mk_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def mk_border():
    s = Side(style="thin", color=GRAY_BDR)
    return Border(left=s, right=s, top=s, bottom=s)

FMT_EURO  = '_-* #,##0.00 "€"_-;-* #,##0.00 "€"_-;_-* "-"?? "€"_-;_-@_-'
FMT_PCT   = "0%"
FMT_NUM1  = "0.0"
FMT_NUM0  = "0"

def hdr_font():
    return Font(name="Calibri", bold=True, color=WHITE, size=11)

def bold_fnt(color="000000", size=11):
    return Font(name="Calibri", bold=True, color=color, size=size)

def norm_fnt(size=10):
    return Font(name="Calibri", size=size)

def set_hdr(cell, value, *, bg=DARK_BLUE, wrap=True):
    cell.value = value
    cell.fill = mk_fill(bg)
    cell.font = hdr_font()
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=wrap)
    cell.border = mk_border()

def set_title(ws, row, col, value, colspan=1, size=13):
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = mk_fill(DARK_BLUE)
    cell.font = Font(name="Calibri", bold=True, color=WHITE, size=size)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    cell.border = mk_border()
    if colspan > 1:
        ws.merge_cells(start_row=row, start_column=col,
                       end_row=row, end_column=col + colspan - 1)
    return cell

def band_row(ws, row, col_start, col_end, bg):
    for c in range(col_start, col_end + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = mk_fill(bg)
        cell.border = mk_border()
        cell.font = norm_fnt()
        cell.alignment = Alignment(vertical="center")

def subtotal_row(ws, row, col_start, col_end):
    for c in range(col_start, col_end + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = mk_fill(LIGHT_BLUE)
        cell.font = bold_fnt()
        cell.border = mk_border()
        cell.alignment = Alignment(vertical="center")

def grandtotal_row(ws, row, col_start, col_end):
    for c in range(col_start, col_end + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = mk_fill(DARK_BLUE)
        cell.font = Font(name="Calibri", bold=True, color=WHITE, size=11)
        cell.border = mk_border()
        cell.alignment = Alignment(vertical="center")

# ── Project data ──────────────────────────────────────────────────────────────
# (empresa, fase_code, desc, tipo, perfil, horas, por_validar, notas)
FASE1 = [
    ("Virgin Details, Lda", "01.Gestão de Projeto",
     "Kick-off interno e cliente; reuniões quinzenais; reporting de progresso; encerramento de fase",
     "Gestão de Projeto", "CS_Gestor", 32, "", ""),
    ("Virgin Details, Lda", "02.Configuração Inicial",
     "Setup empresa Virgin Details; criação e config. 5 utilizadores; grupos de acesso; e-mail e templates",
     "Parametrização", "CS_Consultor", 16, "", ""),
    ("Virgin Details, Lda", "03.Contactos",
     "Tipificação de contactos; etiquetas; regras de preço por perfil; múltiplos endereços",
     "Parametrização", "CS_Consultor", 8, "", ""),
    ("Virgin Details, Lda", "04.CRM",
     "Pipeline; fases e probabilidades; templates e-mail por fase; atividades; dashboards",
     "Parametrização", "CS_Consultor", 16, "", ""),
    ("Virgin Details, Lda", "05.Vendas",
     "Templates orçamento; listas de preço (margens 40-60% por marca); descontos; moradas entrega variáveis (dropshipping); portal B2B base",
     "Parametrização", "CS_Consultor", 24, "", ""),
    ("Virgin Details, Lda", "06.Compras",
     "Fornecedores europeus (4 marcas); preços custo; lead times; regras MTO; encomenda automática",
     "Parametrização", "CS_Consultor", 16, "", ""),
    ("Virgin Details, Lda", "07.Inventário e Logística",
     "Armazém (Maia PT); rotas MTO+Comprar; receção Itália (Starplast/Sunerg); dropshipping Espanha (HASA/Jeremias); guias transporte",
     "Parametrização", "CS_Consultor", 16, "", ""),
    ("Virgin Details, Lda", "08.Financeiro — l10n_pt",
     "Plano contas PT; grupos IVA; SAF-T; plugin certificação AT; condições pagamento; adiantamentos; reconciliação bancária",
     "Parametrização", "CS_Consultor", 24, "", "Plugin AT licenciado separadamente"),
    ("Virgin Details, Lda", "09.Migração de Dados",
     "Importação catálogo produtos (23 templates, 31+ SKUs); clientes e fornecedores de PHC GO/Excel; saldos em aberto",
     "Migração", "CS_Consultor", 24, "", "Cliente fornece dados em Excel limpo"),
    ("Virgin Details, Lda", "10.Migração Pipedrive",
     "Exportação, mapeamento e importação de contactos e histórico CRM (10+ anos) do Pipedrive para Odoo",
     "Migração", "CS_Consultor", 16, "SIM", "Esforço depende do volume e qualidade dos dados"),
    ("Virgin Details, Lda", "11.Testes e Validação",
     "Testes end-to-end do fluxo completo (lead→orçamento→encomenda→compra→receção→entrega→fatura→pagamento); validação cliente; correções",
     "Testes", "CS_Consultor", 16, "", ""),
    ("Virgin Details, Lda", "12.Formação e Arranque",
     "Formação utilizadores (5 pessoas, por perfis); suporte go-live; documentação de utilização",
     "Formação", "CS_Consultor", 24, "", ""),
]

FASE2 = [
    ("Expansão (Fase 2)", "13.Manufatura (BoM)",
     "Listas de Materiais (depósitos+acessórios, kits); Ordens de Fabrico; controlo componentes; custo produto final",
     "Parametrização", "CS_Consultor", 32, "SIM", "Âmbito depende de levantamento dos kits mais frequentes"),
    ("Expansão (Fase 2)", "14.Multiempresa — Starplast SRLE",
     "Configuração 2.ª empresa do grupo; utilizadores partilhados; transações intercompany; relatórios consolidados",
     "Parametrização", "CS_Consultor", 24, "SIM", "Depende de confirmação estrutura legal 2.ª empresa"),
    ("Expansão (Fase 2)", "15.Contabilidade Analítica",
     "Contas analíticas por projeto / marca (4 marcas) / cliente; reporting de margem",
     "Parametrização", "CS_Consultor", 16, "", ""),
    ("Expansão (Fase 2)", "16.Módulos Adicionais",
     "Sign (aprovação eletrónica), Barcode (armazém), Documents, Helpdesk — a definir por prioridade",
     "Parametrização", "CS_Consultor", 0, "SIM", "A orçamentar após levantamento de prioridades"),
]

ALL_TASKS = FASE1 + FASE2

CRON_F1 = [
    ("01.Gestão de Projeto",       "Kick-off e acompanhamento",           4,  1, 12, "Transversal à Fase 1"),
    ("02.Configuração Inicial",    "Setup empresa e utilizadores",         2,  1,  2, ""),
    ("03.Contactos",               "Contactos e regras de preço",          1,  2,  2, ""),
    ("04.CRM",                     "Pipeline comercial",                   2,  3,  4, ""),
    ("05.Vendas",                  "Orçamentos e encomendas",              3,  3,  5, ""),
    ("06.Compras",                 "Compras e fornecedores",               2,  4,  5, ""),
    ("07.Inventário e Logística",  "Armazém e rotas",                      2,  5,  6, ""),
    ("08.Financeiro",              "Faturação PT e contabilidade",         3,  6,  8, ""),
    ("09.Migração de Dados",       "Catálogo, clientes, saldos",           3,  8, 10, "Cliente fornece dados em Excel"),
    ("10.Migração Pipedrive",      "Histórico CRM Pipedrive",              2,  9, 10, "[POR VALIDAR]"),
    ("11.Testes e Validação",      "Testes end-to-end",                    2, 10, 11, ""),
    ("12.Formação e Arranque",     "Formação e go-live",                   3, 11, 12, ""),
]

CRON_F2 = [
    ("13.Manufatura (BoM)",        "Listas materiais e fabrico",           4, 17, 19, "[POR VALIDAR] Fase 2"),
    ("14.Multiempresa",            "Starplast SRLE — 2.ª empresa",         3, 19, 21, "[POR VALIDAR] Fase 2"),
    ("15.Contabilidade Analítica", "Analítica por projeto/marca",          2, 20, 21, "Fase 2"),
    ("16.Módulos Adicionais",      "Sign, Barcode, Helpdesk",              0, "—", "—", "[POR VALIDAR] — a definir"),
]

# ─────────────────────────────────────────────────────────────────────────────
wb = Workbook()
wb.remove(wb.active)

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Config
# ═════════════════════════════════════════════════════════════════════════════
ws_cfg = wb.create_sheet("Config")
ws_cfg.sheet_properties.tabColor = "70AD47"

set_title(ws_cfg, 1, 1, "CONFIGURAÇÃO — Parâmetros Editáveis", colspan=3)
ws_cfg.row_dimensions[1].height = 28

# Row 2 = spacer (keep empty row as per spec)
# Row 3 = headers
for col, label in enumerate(["Parâmetro", "Valor", "Descrição"], 1):
    set_hdr(ws_cfg.cell(row=3, column=col), label)

# Params starting at row 4 (matching spec: B4=65, B5=90, B6=8, B7=5, B8=0.2,
#                                           B9=date, B10=valid, B11=0.23, B12=2400)
params = [
    # (param_label, value, description, number_format_or_None)
    ("Taxa Consultor (€/h)",         65,           "CS_Consultor — taxa horária base",           None),
    ("Taxa Gestor de Projeto (€/h)", 90,           "CS_Gestor — taxa horária base",              None),
    ("Horas por Dia",                8,            "Horas úteis por dia de trabalho",            None),
    ("N.º Utilizadores Odoo",        5,            "Utilizadores ativos na licença",             None),
    ("Desconto 1.º Ano Odoo (%)",    0.2,          "Desconto aplicado no 1.º ano de licença",    FMT_PCT),
    ("Data da Proposta",             "20/05/2026", "Data de emissão do orçamento",               None),
    ("Válido até",                   "20/06/2026", "Prazo de validade da proposta",              None),
    ("IVA (%)",                      0.23,         "Taxa de IVA aplicável",                      FMT_PCT),
    ("Apoio Após Venda (€/ano)",     2400,         "Valor anual do contrato de suporte",         FMT_EURO),
]

for idx, (pname, val, desc, fmt) in enumerate(params):
    row = 4 + idx   # rows 4 through 12
    c_a = ws_cfg.cell(row=row, column=1, value=pname)
    c_b = ws_cfg.cell(row=row, column=2, value=val)
    c_c = ws_cfg.cell(row=row, column=3, value=desc)
    for c in (c_a, c_b, c_c):
        c.border = mk_border()
        c.font = norm_fnt()
        c.alignment = Alignment(vertical="center")
    c_a.font = bold_fnt()
    c_b.fill = mk_fill(YELLOW)
    c_b.font = bold_fnt()
    if fmt:
        c_b.number_format = fmt

ws_cfg.column_dimensions["A"].width = 32
ws_cfg.column_dimensions["B"].width = 18
ws_cfg.column_dimensions["C"].width = 42

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: artigos
# ═════════════════════════════════════════════════════════════════════════════
ws_art = wb.create_sheet("artigos")
ws_art.sheet_properties.tabColor = "A9D18E"

for col, label in enumerate(["Código", "Taxa (€/h)"], 1):
    set_hdr(ws_art.cell(row=1, column=col), label)

# artigos row 2 = CS_Consultor → Config B4
# artigos row 3 = CS_Gestor    → Config B5
artigos_rows = [
    ("CS_Consultor", f"={CFG_TAXA_CONSULTOR}"),
    ("CS_Gestor",    f"={CFG_TAXA_GESTOR}"),
]
for i, (cod, formula) in enumerate(artigos_rows):
    r = i + 2
    c_a = ws_art.cell(row=r, column=1, value=cod)
    c_b = ws_art.cell(row=r, column=2, value=formula)
    for c in (c_a, c_b):
        c.border = mk_border()
        c.font = norm_fnt()
        c.alignment = Alignment(vertical="center")
    c_b.number_format = FMT_EURO

ws_art.column_dimensions["A"].width = 20
ws_art.column_dimensions["B"].width = 16

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: tarefas
# ═════════════════════════════════════════════════════════════════════════════
ws_tar = wb.create_sheet("tarefas")
ws_tar.sheet_properties.tabColor = "A9D18E"

for col, label in enumerate(["Tipo", "Fator"], 1):
    set_hdr(ws_tar.cell(row=1, column=col), label)

for i, tipo in enumerate([
    "Consultadoria", "Desenvolvimento", "Formação",
    "Gestão de Projeto", "Migração", "Orçamentação",
    "Parametrização", "Testes",
]):
    r = i + 2
    c_a = ws_tar.cell(row=r, column=1, value=tipo)
    c_b = ws_tar.cell(row=r, column=2, value=1)
    for c in (c_a, c_b):
        c.border = mk_border()
        c.font = norm_fnt()
        c.alignment = Alignment(vertical="center")

ws_tar.column_dimensions["A"].width = 22
ws_tar.column_dimensions["B"].width = 10

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: DB
# ═════════════════════════════════════════════════════════════════════════════
ws_db = wb.create_sheet("DB")
ws_db.sheet_properties.tabColor = GRAY_TAB

DB_COLS = [
    ("Empresa",    25), ("Fase",          28), ("Descrição",   55),
    ("Tipo",       22), ("Perfil",         18), ("Taxa (€/h)",  12),
    ("Horas",      10), ("Dias",           10), ("Valor (€)",   14),
    ("Por Validar",14), ("Notas",          40),
]

for col, (label, width) in enumerate(DB_COLS, 1):
    set_hdr(ws_db.cell(row=1, column=col), label)
    ws_db.column_dimensions[get_column_letter(col)].width = width

ws_db.row_dimensions[1].height = 28
ws_db.freeze_panes = "A2"

db_row = 2
for task in ALL_TASKS:
    empresa, fase, desc, tipo, perfil, horas, por_validar, notas = task
    is_f2 = empresa == "Expansão (Fase 2)"
    bg = AMBER if is_f2 else "FFFFFF"
    band_row(ws_db, db_row, 1, 11, bg)

    r = db_row
    ws_db.cell(row=r, column=1).value  = empresa
    ws_db.cell(row=r, column=2).value  = fase
    ws_db.cell(row=r, column=3).value  = desc
    ws_db.cell(row=r, column=4).value  = tipo
    ws_db.cell(row=r, column=5).value  = perfil
    # F = rate from artigos lookup, fallback to Config B4 (Consultor)
    ws_db.cell(row=r, column=6).value  = (
        f"=IFERROR(VLOOKUP(E{r},artigos!$A:$B,2,FALSE),{CFG_TAXA_CONSULTOR})"
    )
    ws_db.cell(row=r, column=7).value  = horas
    # H = hours / horas_dia
    ws_db.cell(row=r, column=8).value  = f"=IF(G{r}>0,G{r}/{CFG_HORAS_DIA},0)"
    # I = rate * hours
    ws_db.cell(row=r, column=9).value  = f"=F{r}*G{r}"
    ws_db.cell(row=r, column=10).value = por_validar
    ws_db.cell(row=r, column=11).value = notas

    ws_db.cell(row=r, column=3).alignment = Alignment(vertical="center", wrap_text=True)
    ws_db.cell(row=r, column=6).number_format = FMT_EURO
    ws_db.cell(row=r, column=8).number_format = FMT_NUM1
    ws_db.cell(row=r, column=9).number_format = FMT_EURO

    if por_validar == "SIM":
        ws_db.cell(row=r, column=10).fill = mk_fill(YELLOW)
        ws_db.cell(row=r, column=10).font = bold_fnt()

    ws_db.row_dimensions[r].height = 42
    db_row += 1

last_data = db_row - 1   # last row with task data

# Separator
sep = db_row
for c in range(1, 12):
    ws_db.cell(row=sep, column=c).fill = mk_fill("D9D9D9")
db_row += 1

# Subtotal Fase 1
st1 = db_row
subtotal_row(ws_db, st1, 1, 11)
ws_db.cell(row=st1, column=1).value = "Virgin Details, Lda"
ws_db.cell(row=st1, column=2).value = "SUBTOTAL — Fase 1 (Core Operacional)"
ws_db.cell(row=st1, column=7).value = f'=SUMIF($A$2:$A${last_data},"Virgin Details, Lda",$G$2:$G${last_data})'
ws_db.cell(row=st1, column=8).value = f"=G{st1}/{CFG_HORAS_DIA}"
ws_db.cell(row=st1, column=9).value = f'=SUMIF($A$2:$A${last_data},"Virgin Details, Lda",$I$2:$I${last_data})'
ws_db.cell(row=st1, column=8).number_format = FMT_NUM1
ws_db.cell(row=st1, column=9).number_format = FMT_EURO
db_row += 1

# Subtotal Fase 2
st2 = db_row
subtotal_row(ws_db, st2, 1, 11)
ws_db.cell(row=st2, column=1).value = "Expansão (Fase 2)"
ws_db.cell(row=st2, column=2).value = "SUBTOTAL — Fase 2 (Expansão)"
ws_db.cell(row=st2, column=7).value = f'=SUMIF($A$2:$A${last_data},"Expansão (Fase 2)",$G$2:$G${last_data})'
ws_db.cell(row=st2, column=8).value = f"=G{st2}/{CFG_HORAS_DIA}"
ws_db.cell(row=st2, column=9).value = f'=SUMIF($A$2:$A${last_data},"Expansão (Fase 2)",$I$2:$I${last_data})'
ws_db.cell(row=st2, column=8).number_format = FMT_NUM1
ws_db.cell(row=st2, column=9).number_format = FMT_EURO
db_row += 1

# Grand total
gt = db_row
grandtotal_row(ws_db, gt, 1, 11)
ws_db.cell(row=gt, column=2).value = "TOTAL GERAL"
ws_db.cell(row=gt, column=7).value = f"=G{st1}+G{st2}"
ws_db.cell(row=gt, column=8).value = f"=G{gt}/{CFG_HORAS_DIA}"
ws_db.cell(row=gt, column=9).value = f"=I{st1}+I{st2}"
ws_db.cell(row=gt, column=8).number_format = FMT_NUM1
ws_db.cell(row=gt, column=9).number_format = FMT_EURO

DB_LAST_DATA = last_data
DB_ST1 = st1
DB_ST2 = st2
DB_GT  = gt

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Serviços
# ═════════════════════════════════════════════════════════════════════════════
ws_svc = wb.create_sheet("Serviços")
ws_svc.sheet_properties.tabColor = BLUE_TAB

set_title(ws_svc, 1, 1, "Detalhe de Serviços — Implementação Odoo", colspan=5)
ws_svc.row_dimensions[1].height = 30

ws_svc.column_dimensions["A"].width = 30
ws_svc.column_dimensions["B"].width = 50
ws_svc.column_dimensions["C"].width = 12
ws_svc.column_dimensions["D"].width = 10
ws_svc.column_dimensions["E"].width = 18

SVC_HDR_LABELS = ["Fase", "Descrição", "Horas", "Dias", "Valor (€)"]

def svc_section_hdr(ws, row, label, color="2E75B6"):
    cell = ws.cell(row=row, column=1, value=label)
    cell.fill = mk_fill(color)
    cell.font = Font(name="Calibri", bold=True, color=WHITE, size=11)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells(f"A{row}:E{row}")
    ws.row_dimensions[row].height = 22

def svc_col_hdr(ws, row):
    for col, label in enumerate(SVC_HDR_LABELS, 1):
        set_hdr(ws.cell(row=row, column=col), label)

def svc_data_row(ws, row, fase_code, desc, bg="FFFFFF", highlight_pv=False):
    c_a = ws.cell(row=row, column=1, value=fase_code)
    c_b = ws.cell(row=row, column=2, value=desc)
    c_c = ws.cell(row=row, column=3, value=f'=SUMIFS(DB!$G:$G,DB!$B:$B,"{fase_code}")')
    c_d = ws.cell(row=row, column=4, value=f"=C{row}/{CFG_HORAS_DIA}")
    c_e = ws.cell(row=row, column=5, value=f'=SUMIFS(DB!$I:$I,DB!$B:$B,"{fase_code}")')
    for c in (c_a, c_b, c_c, c_d, c_e):
        c.border = mk_border()
        c.font = norm_fnt()
        c.alignment = Alignment(vertical="center")
        c.fill = mk_fill(bg)
    c_c.number_format = FMT_NUM0
    c_d.number_format = FMT_NUM1
    c_e.number_format = FMT_EURO
    if highlight_pv:
        c_a.fill = mk_fill(YELLOW)

# Phase 1
svc_r = 2
svc_section_hdr(ws_svc, svc_r, "FASE 1 — Core Operacional (Virgin Details, Lda)")
svc_r += 1
svc_col_hdr(ws_svc, svc_r)
svc_r += 1

F1_META = [
    ("01.Gestão de Projeto",      "Kick-off, reuniões quinzenais, reporting, encerramento"),
    ("02.Configuração Inicial",   "Setup empresa, utilizadores, grupos de acesso, e-mail"),
    ("03.Contactos",              "Tipificação, etiquetas, regras de preço, múltiplos endereços"),
    ("04.CRM",                    "Pipeline, fases, probabilidades, templates, dashboards"),
    ("05.Vendas",                 "Orçamentos, listas de preço por marca, portal B2B"),
    ("06.Compras",                "Fornecedores, preços custo, lead times, regras MTO"),
    ("07.Inventário e Logística", "Armazém Maia, rotas MTO, receção Itália, dropshipping Espanha"),
    ("08.Financeiro — l10n_pt",   "Plano contas PT, IVA, SAF-T, certificação AT, banca"),
    ("09.Migração de Dados",      "Catálogo produtos, clientes/fornecedores PHC GO/Excel, saldos"),
    ("10.Migração Pipedrive",     "Exportação, mapeamento e importação CRM Pipedrive"),
    ("11.Testes e Validação",     "Testes end-to-end, validação cliente, correções"),
    ("12.Formação e Arranque",    "Formação 5 utilizadores, suporte go-live, documentação"),
]

f1_svc_s = svc_r
for fase_code, desc in F1_META:
    highlight = fase_code.startswith("10.")
    svc_data_row(ws_svc, svc_r, fase_code, desc, highlight_pv=highlight)
    svc_r += 1
f1_svc_e = svc_r - 1

# Phase 1 subtotal
st1_svc = svc_r
subtotal_row(ws_svc, st1_svc, 1, 5)
ws_svc.cell(row=st1_svc, column=1).value = "SUBTOTAL FASE 1"
ws_svc.cell(row=st1_svc, column=3).value = f"=SUM(C{f1_svc_s}:C{f1_svc_e})"
ws_svc.cell(row=st1_svc, column=4).value = f"=C{st1_svc}/{CFG_HORAS_DIA}"
ws_svc.cell(row=st1_svc, column=5).value = f"=SUM(E{f1_svc_s}:E{f1_svc_e})"
ws_svc.cell(row=st1_svc, column=3).number_format = FMT_NUM0
ws_svc.cell(row=st1_svc, column=4).number_format = FMT_NUM1
ws_svc.cell(row=st1_svc, column=5).number_format = FMT_EURO
svc_r += 2  # spacer row

# Phase 2
svc_section_hdr(ws_svc, svc_r, "FASE 2 — Expansão (Indicativo — Valores por Validar)", color="ED7D31")
svc_r += 1
svc_col_hdr(ws_svc, svc_r)
svc_r += 1

F2_META = [
    ("13.Manufatura (BoM)",             "Listas de Materiais, Ordens Fabrico, controlo componentes"),
    ("14.Multiempresa — Starplast SRLE","2.ª empresa, utilizadores partilhados, intercompany"),
    ("15.Contabilidade Analítica",      "Analítica por projeto / marca (4 marcas) / cliente"),
    ("16.Módulos Adicionais",           "Sign, Barcode, Documents, Helpdesk — a definir"),
]

f2_svc_s = svc_r
PV_F2 = {"13.Manufatura (BoM)", "14.Multiempresa — Starplast SRLE", "16.Módulos Adicionais"}
for fase_code, desc in F2_META:
    svc_data_row(ws_svc, svc_r, fase_code, desc, bg=AMBER, highlight_pv=fase_code in PV_F2)
    svc_r += 1
f2_svc_e = svc_r - 1

# Phase 2 subtotal
st2_svc = svc_r
subtotal_row(ws_svc, st2_svc, 1, 5)
ws_svc.cell(row=st2_svc, column=1).value = "SUBTOTAL FASE 2 (base)"
ws_svc.cell(row=st2_svc, column=3).value = f"=SUM(C{f2_svc_s}:C{f2_svc_e})"
ws_svc.cell(row=st2_svc, column=4).value = f"=C{st2_svc}/{CFG_HORAS_DIA}"
ws_svc.cell(row=st2_svc, column=5).value = f"=SUM(E{f2_svc_s}:E{f2_svc_e})"
ws_svc.cell(row=st2_svc, column=3).number_format = FMT_NUM0
ws_svc.cell(row=st2_svc, column=4).number_format = FMT_NUM1
ws_svc.cell(row=st2_svc, column=5).number_format = FMT_EURO
svc_r += 2

# Grand total
gt_svc = svc_r
grandtotal_row(ws_svc, gt_svc, 1, 5)
ws_svc.cell(row=gt_svc, column=1).value = "TOTAL GERAL SERVIÇOS"
ws_svc.cell(row=gt_svc, column=3).value = f"=C{st1_svc}+C{st2_svc}"
ws_svc.cell(row=gt_svc, column=4).value = f"=C{gt_svc}/{CFG_HORAS_DIA}"
ws_svc.cell(row=gt_svc, column=5).value = f"=E{st1_svc}+E{st2_svc}"
ws_svc.cell(row=gt_svc, column=3).number_format = FMT_NUM0
ws_svc.cell(row=gt_svc, column=4).number_format = FMT_NUM1
ws_svc.cell(row=gt_svc, column=5).number_format = FMT_EURO

SVC_ST1_ROW = st1_svc
SVC_ST2_ROW = st2_svc
SVC_GT_ROW  = gt_svc

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Empresa
# ═════════════════════════════════════════════════════════════════════════════
ws_emp = wb.create_sheet("Empresa")
ws_emp.sheet_properties.tabColor = "4BACC6"

set_title(ws_emp, 1, 1, "Resumo por Empresa / Fase", colspan=3)
ws_emp.row_dimensions[1].height = 28

for col, label in enumerate(["Empresa / Fase", "Horas", "Valor (€)"], 1):
    set_hdr(ws_emp.cell(row=2, column=col), label)

emp_rows_data = [
    ("Virgin Details, Lda",
     '=SUMIFS(DB!$G:$G,DB!$A:$A,"Virgin Details, Lda")',
     '=SUMIFS(DB!$I:$I,DB!$A:$A,"Virgin Details, Lda")'),
    ("Expansão (Fase 2)",
     '=SUMIFS(DB!$G:$G,DB!$A:$A,"Expansão (Fase 2)")',
     '=SUMIFS(DB!$I:$I,DB!$A:$A,"Expansão (Fase 2)")'),
]

emp_s = 3
for i, (label, h_f, v_f) in enumerate(emp_rows_data):
    r = emp_s + i
    c_a = ws_emp.cell(row=r, column=1, value=label)
    c_b = ws_emp.cell(row=r, column=2, value=h_f)
    c_c = ws_emp.cell(row=r, column=3, value=v_f)
    for c in (c_a, c_b, c_c):
        c.border = mk_border()
        c.font = norm_fnt()
        c.alignment = Alignment(vertical="center")
    c_b.number_format = FMT_NUM0
    c_c.number_format = FMT_EURO

emp_tot = emp_s + len(emp_rows_data)
grandtotal_row(ws_emp, emp_tot, 1, 3)
ws_emp.cell(row=emp_tot, column=1).value = "Total Geral"
ws_emp.cell(row=emp_tot, column=2).value = f"=SUM(B{emp_s}:B{emp_tot-1})"
ws_emp.cell(row=emp_tot, column=3).value = f"=SUM(C{emp_s}:C{emp_tot-1})"
ws_emp.cell(row=emp_tot, column=2).number_format = FMT_NUM0
ws_emp.cell(row=emp_tot, column=3).number_format = FMT_EURO

ws_emp.column_dimensions["A"].width = 30
ws_emp.column_dimensions["B"].width = 14
ws_emp.column_dimensions["C"].width = 18

EMP_F1_ROW  = emp_s      # row 3 = Virgin Details
EMP_TOT_ROW = emp_tot    # row 5

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Software
# ═════════════════════════════════════════════════════════════════════════════
ws_sw = wb.create_sheet("Software")
ws_sw.sheet_properties.tabColor = ORANGE_TAB

set_title(ws_sw, 1, 1, "Licenciamento Odoo — Proposta de Software", colspan=8)
ws_sw.row_dimensions[1].height = 30

note_cell = ws_sw.cell(row=2, column=1,
    value="⚠  Valores a confirmar por Stefano Biglieri — preencher células amarelas C5, C10, C11")
note_cell.font = Font(name="Calibri", italic=True, color="FF0000", size=10)
note_cell.alignment = Alignment(horizontal="left", vertical="center")
ws_sw.merge_cells("A2:H2")

SW_HDR = [
    "Descrição", "Utilizadores", "Valor/Mês/User (€)",
    "Desconto 1.º Ano", "Valor c/ Desc. Mensal",
    "Total Mensal (€)", "Total 1.º Ano (€)", "Total Anos Seg. (€)"
]
for col, label in enumerate(SW_HDR, 1):
    set_hdr(ws_sw.cell(row=3, column=col), label)
ws_sw.row_dimensions[3].height = 28

# Section header: Odoo Enterprise
ws_sw.cell(row=4, column=1).value = "Licenciamento Odoo Enterprise (Odoo SH)"
ws_sw.cell(row=4, column=1).fill  = mk_fill("2E75B6")
ws_sw.cell(row=4, column=1).font  = Font(name="Calibri", bold=True, color=WHITE, size=11)
ws_sw.cell(row=4, column=1).alignment = Alignment(horizontal="left", vertical="center")
ws_sw.merge_cells("A4:H4")
ws_sw.row_dimensions[4].height = 22

# Row 5: Odoo Enterprise + SH subscription
r5 = 5
ws_sw.cell(row=r5, column=1).value = "Odoo Enterprise + Odoo SH"
ws_sw.cell(row=r5, column=2).value = f"={CFG_NUM_USERS}"
ws_sw.cell(row=r5, column=3).value = 38          # INPUT YELLOW — €/month/user placeholder
ws_sw.cell(row=r5, column=4).value = f"={CFG_DESC_ODOO}"
ws_sw.cell(row=r5, column=5).value = f"=C{r5}*(1-D{r5})"
ws_sw.cell(row=r5, column=6).value = f"=E{r5}*B{r5}"
ws_sw.cell(row=r5, column=7).value = f"=F{r5}*12"
ws_sw.cell(row=r5, column=8).value = f"=C{r5}*B{r5}*12"

for col in range(1, 9):
    c = ws_sw.cell(row=r5, column=col)
    c.border = mk_border()
    c.font   = norm_fnt()
    c.alignment = Alignment(vertical="center", horizontal="center")
ws_sw.cell(row=r5, column=1).alignment = Alignment(vertical="center", horizontal="left")
ws_sw.cell(row=r5, column=3).fill = mk_fill(YELLOW)
ws_sw.cell(row=r5, column=3).font = bold_fnt()
ws_sw.cell(row=r5, column=4).number_format = FMT_PCT
for col in (5, 6, 7, 8):
    ws_sw.cell(row=r5, column=col).number_format = FMT_EURO
ws_sw.cell(row=r5, column=2).number_format = FMT_NUM0

# Subtotal Odoo (rows 6-8 spacer, subtotal at row 6 for clarity)
sw_st_odoo = 6
subtotal_row(ws_sw, sw_st_odoo, 1, 8)
ws_sw.cell(row=sw_st_odoo, column=1).value = "TOTAL Odoo Enterprise"
ws_sw.cell(row=sw_st_odoo, column=7).value = f"=G{r5}"
ws_sw.cell(row=sw_st_odoo, column=8).value = f"=H{r5}"
ws_sw.cell(row=sw_st_odoo, column=7).number_format = FMT_EURO
ws_sw.cell(row=sw_st_odoo, column=8).number_format = FMT_EURO

# Section header: Plugin AT
ws_sw.cell(row=8, column=1).value = "Plugin de Certificação de Faturas (AT)"
ws_sw.cell(row=8, column=1).fill  = mk_fill("2E75B6")
ws_sw.cell(row=8, column=1).font  = Font(name="Calibri", bold=True, color=WHITE, size=11)
ws_sw.cell(row=8, column=1).alignment = Alignment(horizontal="left", vertical="center")
ws_sw.merge_cells("A8:H8")
ws_sw.row_dimensions[8].height = 22

# Row 10: AT subscription base
r10 = 10
ws_sw.cell(row=r10, column=1).value = "Subscrição base plugin AT (anual)"
ws_sw.cell(row=r10, column=2).value = "—"
ws_sw.cell(row=r10, column=3).value = 420         # INPUT YELLOW — annual fee placeholder
ws_sw.cell(row=r10, column=4).value = f"={CFG_DESC_ODOO}"
ws_sw.cell(row=r10, column=5).value = f"=C{r10}*(1-D{r10})/12"
ws_sw.cell(row=r10, column=6).value = f"=E{r10}"
ws_sw.cell(row=r10, column=7).value = f"=C{r10}*(1-D{r10})"
ws_sw.cell(row=r10, column=8).value = f"=C{r10}"

for col in range(1, 9):
    c = ws_sw.cell(row=r10, column=col)
    c.border = mk_border()
    c.font   = norm_fnt()
    c.alignment = Alignment(vertical="center", horizontal="center")
ws_sw.cell(row=r10, column=1).alignment = Alignment(vertical="center", horizontal="left")
ws_sw.cell(row=r10, column=3).fill = mk_fill(YELLOW)
ws_sw.cell(row=r10, column=3).font = bold_fnt()
ws_sw.cell(row=r10, column=4).number_format = FMT_PCT
for col in (5, 6, 7, 8):
    ws_sw.cell(row=r10, column=col).number_format = FMT_EURO

# Row 11: AT per user/year
r11 = 11
ws_sw.cell(row=r11, column=1).value = "Taxa por utilizador — plugin AT (anual)"
ws_sw.cell(row=r11, column=2).value = f"={CFG_NUM_USERS}"
ws_sw.cell(row=r11, column=3).value = 48          # INPUT YELLOW — per user/year placeholder
ws_sw.cell(row=r11, column=4).value = f"={CFG_DESC_ODOO}"
ws_sw.cell(row=r11, column=5).value = f"=C{r11}*(1-D{r11})/12"
ws_sw.cell(row=r11, column=6).value = f"=E{r11}*B{r11}"
ws_sw.cell(row=r11, column=7).value = f"=C{r11}*(1-D{r11})*B{r11}"
ws_sw.cell(row=r11, column=8).value = f"=C{r11}*B{r11}"

for col in range(1, 9):
    c = ws_sw.cell(row=r11, column=col)
    c.border = mk_border()
    c.font   = norm_fnt()
    c.alignment = Alignment(vertical="center", horizontal="center")
ws_sw.cell(row=r11, column=1).alignment = Alignment(vertical="center", horizontal="left")
ws_sw.cell(row=r11, column=3).fill = mk_fill(YELLOW)
ws_sw.cell(row=r11, column=3).font = bold_fnt()
ws_sw.cell(row=r11, column=4).number_format = FMT_PCT
for col in (5, 6, 7, 8):
    ws_sw.cell(row=r11, column=col).number_format = FMT_EURO
ws_sw.cell(row=r11, column=2).number_format = FMT_NUM0

# Row 12: AT total
r12 = 12
subtotal_row(ws_sw, r12, 1, 8)
ws_sw.cell(row=r12, column=1).value = "TOTAL Plugin AT"
ws_sw.cell(row=r12, column=7).value = f"=G{r10}+G{r11}"
ws_sw.cell(row=r12, column=8).value = f"=H{r10}+H{r11}"
ws_sw.cell(row=r12, column=7).number_format = FMT_EURO
ws_sw.cell(row=r12, column=8).number_format = FMT_EURO

# Row 15: Grand total Software
r_sw_gt = 15
grandtotal_row(ws_sw, r_sw_gt, 1, 8)
ws_sw.cell(row=r_sw_gt, column=1).value = "TOTAL SOFTWARE"
ws_sw.cell(row=r_sw_gt, column=7).value = f"=G{sw_st_odoo}+G{r12}"
ws_sw.cell(row=r_sw_gt, column=8).value = f"=H{sw_st_odoo}+H{r12}"
ws_sw.cell(row=r_sw_gt, column=7).number_format = FMT_EURO
ws_sw.cell(row=r_sw_gt, column=8).number_format = FMT_EURO

SW_WIDTHS = [40, 14, 22, 16, 22, 18, 18, 22]
for i, w in enumerate(SW_WIDTHS, 1):
    ws_sw.column_dimensions[get_column_letter(i)].width = w

# References for Resumo
SW_ODOO_1Y = f"Software!G{sw_st_odoo}"   # Total Odoo 1st year
SW_ODOO_NY = f"Software!H{sw_st_odoo}"   # Total Odoo subsequent years
SW_AT_1Y   = f"Software!G{r12}"          # Total AT 1st year
SW_AT_NY   = f"Software!H{r12}"          # Total AT subsequent years

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Cronograma
# ═════════════════════════════════════════════════════════════════════════════
ws_crn = wb.create_sheet("Cronograma")
ws_crn.sheet_properties.tabColor = "70AD47"

set_title(ws_crn, 1, 1, "Cronograma Indicativo — Implementação Odoo", colspan=6)
ws_crn.row_dimensions[1].height = 28

for col, label in enumerate(["Fase", "Descrição", "Dias", "Sem. Início", "Sem. Fim", "Observações"], 1):
    set_hdr(ws_crn.cell(row=2, column=col), label)

for i, w in enumerate([30, 42, 10, 14, 12, 38], 1):
    ws_crn.column_dimensions[get_column_letter(i)].width = w

crn_r = 3
for fase, desc, dias, s_ini, s_fim, obs in CRON_F1:
    band_row(ws_crn, crn_r, 1, 6, "FFFFFF")
    for col, val in enumerate([fase, desc, dias, s_ini, s_fim, obs], 1):
        ws_crn.cell(row=crn_r, column=col).value = val
    crn_r += 1

# Phase 1 total
cron_st1 = crn_r
subtotal_row(ws_crn, cron_st1, 1, 6)
ws_crn.cell(row=cron_st1, column=1).value = "FASE 1 TOTAL"
ws_crn.cell(row=cron_st1, column=3).value = 29
crn_r += 1

# Spacer
for c in range(1, 7):
    ws_crn.cell(row=crn_r, column=c).fill = mk_fill("D9D9D9")
crn_r += 1

# Phase 2 section header
ws_crn.cell(row=crn_r, column=1).value = "FASE 2 — Expansão (Indicativo)"
ws_crn.cell(row=crn_r, column=1).fill  = mk_fill("ED7D31")
ws_crn.cell(row=crn_r, column=1).font  = Font(name="Calibri", bold=True, color=WHITE, size=11)
ws_crn.cell(row=crn_r, column=1).alignment = Alignment(horizontal="left", vertical="center")
ws_crn.merge_cells(f"A{crn_r}:F{crn_r}")
crn_r += 1

for fase, desc, dias, s_ini, s_fim, obs in CRON_F2:
    band_row(ws_crn, crn_r, 1, 6, AMBER)
    for col, val in enumerate([fase, desc, dias, s_ini, s_fim, obs], 1):
        ws_crn.cell(row=crn_r, column=col).value = val
    crn_r += 1

# Phase 2 total
cron_st2 = crn_r
subtotal_row(ws_crn, cron_st2, 1, 6)
ws_crn.cell(row=cron_st2, column=1).value = "FASE 2 TOTAL (base)"
ws_crn.cell(row=cron_st2, column=3).value = 9

# ═════════════════════════════════════════════════════════════════════════════
# SHEET: Resumo
# ═════════════════════════════════════════════════════════════════════════════
ws_res = wb.create_sheet("Resumo")
ws_res.sheet_properties.tabColor = DARK_BLUE

set_title(ws_res, 1, 1, "Virgin Details, Lda — Orçamento Odoo", colspan=3, size=14)
ws_res.row_dimensions[1].height = 36

sub_cell = ws_res.cell(row=2, column=1, value="Parâmetro Global · Consultoria Informática · 20/05/2026")
sub_cell.font = Font(name="Calibri", italic=True, size=11, color="4472C4")
sub_cell.alignment = Alignment(horizontal="left", vertical="center")
ws_res.merge_cells("A2:C2")
ws_res.row_dimensions[2].height = 20

ws_res.column_dimensions["A"].width = 48
ws_res.column_dimensions["B"].width = 22
ws_res.column_dimensions["C"].width = 36

def res_sec_hdr(ws, row, label, color="2E75B6"):
    ws.cell(row=row, column=1).value     = label
    ws.cell(row=row, column=1).fill      = mk_fill(color)
    ws.cell(row=row, column=1).font      = Font(name="Calibri", bold=True, color=WHITE, size=11)
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells(f"A{row}:C{row}")
    ws.row_dimensions[row].height = 22

def res_col_hdr(ws, row):
    for col, label in enumerate(["Rúbrica", "Valor (€)", "Notas"], 1):
        set_hdr(ws.cell(row=row, column=col), label)

def res_data(ws, row, label, formula, note="", bg="FFFFFF"):
    c_a = ws.cell(row=row, column=1, value=label)
    c_b = ws.cell(row=row, column=2, value=formula)
    c_c = ws.cell(row=row, column=3, value=note)
    for c in (c_a, c_b, c_c):
        c.border  = mk_border()
        c.font    = norm_fnt()
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.fill    = mk_fill(bg)
    c_b.number_format = FMT_EURO

def res_total(ws, row, label, formula, note="", bg=DARK_BLUE):
    grandtotal_row(ws, row, 1, 3)
    ws.cell(row=row, column=1).value = label
    ws.cell(row=row, column=2).value = formula
    ws.cell(row=row, column=3).value = note
    ws.cell(row=row, column=2).number_format = FMT_EURO

def res_subtot(ws, row, label, formula, note=""):
    subtotal_row(ws, row, 1, 3)
    ws.cell(row=row, column=1).value = label
    ws.cell(row=row, column=2).value = formula
    ws.cell(row=row, column=3).value = note
    ws.cell(row=row, column=2).number_format = FMT_EURO

# ── Section 1: Implementação ──────────────────────────────────────────────────
res_r = 4
res_sec_hdr(ws_res, res_r, "1. IMPLEMENTAÇÃO — Custo Único (Fase 1)")
res_r += 1
res_col_hdr(ws_res, res_r)
res_r += 1

s1_s = res_r
res_data(ws_res, res_r, "Serviços — Fase 1 (Core Operacional)",
         '=SUMIFS(DB!$I:$I,DB!$A:$A,"Virgin Details, Lda")',
         "Detalhe em sheet Serviços")
res_r += 1
res_data(ws_res, res_r, "Software Odoo Enterprise — 1.º Ano",
         f"={SW_ODOO_1Y}",
         "⚠ Placeholder — confirmar c/ Stefano")
res_r += 1
res_data(ws_res, res_r, "Plugin Certificação AT — 1.º Ano",
         f"={SW_AT_1Y}",
         "⚠ Placeholder — confirmar c/ Stefano")
res_r += 1
s1_e = res_r - 1

res_total(ws_res, res_r, "TOTAL 1.º ANO (sem IVA)",
          f"=SUM(B{s1_s}:B{s1_e})")
tot_sem_iva = res_r
res_r += 1

# IVA row
iva_r = res_r
iva_c_a = ws_res.cell(row=iva_r, column=1, value="IVA (23%)")
iva_c_b = ws_res.cell(row=iva_r, column=2, value=f"=B{tot_sem_iva}*{CFG_IVA}")
iva_c_c = ws_res.cell(row=iva_r, column=3, value="")
for c in (iva_c_a, iva_c_b, iva_c_c):
    c.border  = mk_border()
    c.font    = bold_fnt()
    c.fill    = mk_fill(LIGHT_BLUE)
    c.alignment = Alignment(vertical="center")
iva_c_b.number_format = FMT_EURO
res_r += 1

# Total with VAT
res_subtot(ws_res, res_r, "TOTAL 1.º ANO (com IVA)",
           f"=B{tot_sem_iva}+B{iva_r}",
           "Valor final faturável")
res_r += 2

# ── Section 2: Exploração ─────────────────────────────────────────────────────
res_sec_hdr(ws_res, res_r, "2. EXPLORAÇÃO — Valores Anuais (a partir do 2.º Ano)", color="ED7D31")
res_r += 1
res_col_hdr(ws_res, res_r)
res_r += 1

s2_s = res_r
res_data(ws_res, res_r, "Software Odoo Enterprise (anos seguintes)",
         f"={SW_ODOO_NY}",
         "⚠ Placeholder — confirmar c/ Stefano")
res_r += 1
res_data(ws_res, res_r, "Plugin Certificação AT (anos seguintes)",
         f"={SW_AT_NY}",
         "⚠ Placeholder — confirmar c/ Stefano")
res_r += 1
res_data(ws_res, res_r, "Apoio Após Venda — Parâmetro Global",
         f"={CFG_AAV}",
         "Contrato anual suporte e manutenção")
res_r += 1
s2_e = res_r - 1

res_total(ws_res, res_r, "TOTAL ANUAL (sem IVA)",
          f"=SUM(B{s2_s}:B{s2_e})")
res_r += 2

# ── Section 3: Expansão Fase 2 ────────────────────────────────────────────────
res_sec_hdr(ws_res, res_r, "3. EXPANSÃO — Fase 2 (Indicativo — Valores por Validar)", color="7030A0")
res_r += 1
res_col_hdr(ws_res, res_r)
res_r += 1

s3_s = res_r
res_data(ws_res, res_r, "Serviços — Fase 2 base (indicativo)",
         '=SUMIFS(DB!$I:$I,DB!$A:$A,"Expansão (Fase 2)")',
         "Âmbito por confirmar — ver sheet Serviços")
res_r += 1
s3_e = res_r - 1

res_total(ws_res, res_r, "SUBTOTAL FASE 2 (sem IVA)",
          f"=SUM(B{s3_s}:B{s3_e})",
          bg="7030A0")
res_r += 2

# Note
note_r = res_r
nc = ws_res.cell(row=note_r, column=1,
    value=("Nota: Licenciamento Odoo a confirmar por Stefano Biglieri. "
           "Valores na sheet Software são placeholders (€/user/mês + plugin AT a preencher). "
           "Fase 2 sujeita a levantamento de requisitos adicional. "
           "Proposta válida até 20/06/2026."))
nc.font = Font(name="Calibri", italic=True, size=9, color="595959")
nc.alignment = Alignment(wrap_text=True, vertical="top")
ws_res.merge_cells(f"A{note_r}:C{note_r}")
ws_res.row_dimensions[note_r].height = 48

# ═════════════════════════════════════════════════════════════════════════════
# Sheet ordering: Resumo, Software, Serviços, Cronograma, Config, DB, tarefas, artigos
# (Empresa hidden at end — useful reference but not a client-facing sheet)
# ═════════════════════════════════════════════════════════════════════════════
TARGET_ORDER = ["Resumo", "Software", "Serviços", "Cronograma", "Config", "DB", "tarefas", "artigos", "Empresa"]
for i, name in enumerate(TARGET_ORDER):
    wb.move_sheet(name, offset=i - wb.sheetnames.index(name))

# ═════════════════════════════════════════════════════════════════════════════
# Save
# ═════════════════════════════════════════════════════════════════════════════
OUT = r"C:\Projetos\Waterdetails\docs\ORCAMENTO_WATERDETAILS_V1.xlsx"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)

print(f"[OK] Ficheiro guardado: {OUT}")
size_kb = os.path.getsize(OUT) / 1024
print(f"[OK] Tamanho: {size_kb:.1f} KB")
print(f"[OK] Folhas: {wb.sheetnames}")

# ─── Quick sanity check ───────────────────────────────────────────────────────
from openpyxl import load_workbook as lw
wb2 = lw(OUT)
ws2_cfg = wb2["Config"]
ws2_db  = wb2["DB"]
ws2_art = wb2["artigos"]

print(f"\n[CHECK] Config B4 (Taxa Consultor): {ws2_cfg['B4'].value}")
print(f"[CHECK] Config B5 (Taxa Gestor):    {ws2_cfg['B5'].value}")
print(f"[CHECK] Config B6 (Horas/Dia):      {ws2_cfg['B6'].value}")
print(f"[CHECK] Config B7 (Utilizadores):   {ws2_cfg['B7'].value}")
print(f"[CHECK] Config B8 (Desconto):       {ws2_cfg['B8'].value}")
print(f"[CHECK] Config B11 (IVA):           {ws2_cfg['B11'].value}")
print(f"[CHECK] Config B12 (AAV):           {ws2_cfg['B12'].value}")
print(f"[CHECK] artigos B2 formula:         {ws2_art['B2'].value}")
print(f"[CHECK] artigos B3 formula:         {ws2_art['B3'].value}")
print(f"[CHECK] DB F2 formula:              {ws2_db['F2'].value}")
print(f"[CHECK] DB G2 (horas):              {ws2_db['G2'].value}")
print(f"[CHECK] DB H2 formula:              {ws2_db['H2'].value}")
print(f"[CHECK] DB I2 formula:              {ws2_db['I2'].value}")
print(f"[CHECK] DB rows total:              {ws2_db.max_row}")
