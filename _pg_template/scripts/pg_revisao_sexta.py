r"""Ficha da revisão de sexta-feira: o que cada pessoa e cada gestor tem de validar.

Só LÊ o Odoo da Parâmetro Global (search_read). Nunca escreve. Prepara o terreno para o
manual de sexta-feira (Parte A: o meu quadro; Parte B: os meus projetos): em vez de a
pessoa abrir três vistas no Odoo, o agente corre isto e percorre a ficha ponto a ponto.

Universo: projetos com a etiqueta «Odoo» (project.tags). Projetos de outros ERP e internos
ficam fora desta revisão (decisão de 2026-10-10).

Dados que mostra: cada número vem do Odoo no momento em que corre. O ficheiro gerado vai
para FORA do repositório (%USERPROFILE%/.pg/revisao/), porque traz nomes de clientes.

Uso:
  py .pg_framework\scripts\pg_revisao_sexta.py
  py .pg_framework\scripts\pg_revisao_sexta.py --parte A
  py .pg_framework\scripts\pg_revisao_sexta.py --parte B --projeto-key <project_key>
  py .pg_framework\scripts\pg_revisao_sexta.py --login outra.pessoa@parametro.global --stdout
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# --------------------------------------------------------------------------------------
# Regras (iguais às do manual). Estão aqui, num sítio só, para o teste as poder fixar.
# --------------------------------------------------------------------------------------

ETIQUETA_ODOO = "Odoo"
ETAPAS_EM_CURSO = ("In Progress", "To Do", "Support", "Em planear")

# Variantes de nome que existem no Odoo da Parâmetro Global (cada projeto tem as suas etapas).
SPRINT_BACKLOG = ("Sprint Backlog", "Lista de pendências da sprint")
SPRINT_EM_CURSO = ("Sprint in Progress", "Sprint em andamento", "Spint in Progress")
SPRINT_COMPLETA = ("Sprint Complete", "Sprint concluída", "Old Completed Sprint",
                   "Sprint anterior concluído")

DIAS_PARADA_ALERTA = 30
DIAS_PARADA_DEVOLVER = 90
HORAS_MAX_CLIENTE_DIA = 7.5          # TPL_TIMESHEET_INSTRUCOES 1.2.0, Passo 1A
JANELA_ATIVIDADE_DIAS = 28

CORES_ORDEM = {"sem_dados": 0, "verde": 1, "amarelo": 2, "vermelho": 3}
# Palavras e não ícones: a cor não pode ser a única forma de dizer o estado, e a consola do
# Windows (cp1252) rebenta com emojis em `--stdout`.
ICONE = {"verde": "verde", "amarelo": "AMARELO", "vermelho": "VERMELHO", "sem_dados": "sem dados"}


def grupo_etapa(nome: str | None) -> str:
    """backlog | sprint_backlog | sprint_em_curso | sprint_completa | concluida | outra."""
    if not nome:
        return "outra"
    if nome == "Backlog":
        return "backlog"
    if nome in SPRINT_BACKLOG:
        return "sprint_backlog"
    if nome in SPRINT_EM_CURSO:
        return "sprint_em_curso"
    if nome in SPRINT_COMPLETA:
        return "sprint_completa"
    if nome in ("Concluídos", "Entregue", "Delivered"):
        return "concluida"
    return "outra"


def em_sprint(grupo: str) -> bool:
    return grupo in ("sprint_backlog", "sprint_em_curso")


def _data(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.strptime(valor[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(valor[:10], "%Y-%m-%d")
        except ValueError:
            return None


def dias_desde(valor: str | None, hoje: date) -> int | None:
    d = _data(valor)
    return None if d is None else (hoje - d.date()).days


def classificar_tarefa(t: dict, hoje: date) -> dict:
    """Marca uma tarefa aberta e sugere o que fazer (as 7 perguntas do manual, Parte A)."""
    etapa = (t.get("stage_id") or [None, ""])[1]
    grupo = grupo_etapa(etapa)
    parada = dias_desde(t.get("write_date"), hoje)
    na_etapa = dias_desde(t.get("date_last_stage_update"), hoje)
    prazo = _data(t.get("date_deadline"))
    horas = float(t.get("allocated_hours") or 0)
    flags = {
        "grupo": grupo,
        "etapa": etapa,
        "parada_dias": parada,
        "etapa_dias": na_etapa,
        "parada_30": parada is not None and parada > DIAS_PARADA_ALERTA,
        "parada_90": parada is not None and parada > DIAS_PARADA_DEVOLVER,
        "sem_dono": not (t.get("user_ids") or []),
        "sem_horas_alocadas": horas <= 0,
        "sem_hora_lancada": float(t.get("effective_hours") or 0) == 0,
        "sem_prazo": prazo is None,
        "vencida": prazo is not None and prazo.date() < hoje,
    }
    flags["completa_tres_campos"] = not (
        flags["sem_dono"] or flags["sem_horas_alocadas"] or flags["sem_prazo"])

    if grupo == "sprint_completa":
        acao = "Fechar: já está em Sprint Complete mas continua aberta."
    elif em_sprint(grupo):
        if flags["parada_90"]:
            acao = "Devolver ao Backlog ou fechar como não necessária (parada há mais de 90 dias)."
        elif flags["parada_30"]:
            acao = ("Aplicar as sete perguntas: se não vai ser feita nas próximas 2 semanas, "
                    "volta ao Backlog.")
        elif flags["vencida"]:
            acao = "Replanear com nova data e motivo escrito, ou fechar."
        elif flags["sem_dono"]:
            acao = "Atribuir responsável."
        elif flags["sem_horas_alocadas"]:
            acao = "Estimar as horas que faltam (horas de cliente)."
        elif flags["sem_prazo"]:
            acao = "Pôr um prazo realista."
        else:
            acao = "Sem ação."
    else:
        acao = ""
    flags["acao"] = acao
    return flags


def semaforo_horas(efetivas: float, alocadas: float) -> tuple[str, float | None]:
    """Consumo = efetivas ÷ alocadas. Verde até 80 %, amarelo até 110 %, vermelho acima."""
    if not alocadas or alocadas <= 0:
        return "sem_dados", None
    consumo = efetivas / alocadas
    if consumo <= 0.80:
        return "verde", consumo
    if consumo <= 1.10:
        return "amarelo", consumo
    return "vermelho", consumo


def semaforo_atividade(horas_28d: float) -> str:
    if horas_28d >= 10:
        return "verde"
    if horas_28d > 0:
        return "amarelo"
    return "vermelho"


def semaforo_quadro(completas: int, total_sprint: int) -> str:
    """Tarefas em sprint com dono, horas e prazo: verde ≥ 90 %, amarelo ≥ 55 %."""
    if total_sprint <= 0:
        return "sem_dados"
    pct = completas / total_sprint
    if pct >= 0.90:
        return "verde"
    if pct >= 0.55:
        return "amarelo"
    return "vermelho"


def semaforo_prazo(data_fim: str | None, hoje: date) -> str:
    """Provisório (sem baseline): só olha para a data de fim.

    Sem data não há atraso para medir. Passada a data: até 14 dias de calendário (cerca de
    10 úteis) é amarelo, acima é vermelho.
    """
    d = _data(data_fim)
    if d is None:
        return "sem_dados"
    atraso = (hoje - d.date()).days
    if atraso <= 0:
        return "verde"
    return "amarelo" if atraso <= 14 else "vermelho"


def cor_global(cores: list[str]) -> str:
    """A pior das medidas com dados; sem_dados só se nenhuma tiver."""
    com_dados = [c for c in cores if c != "sem_dados"]
    if not com_dados:
        return "sem_dados"
    return max(com_dados, key=lambda c: CORES_ORDEM[c])


def tipo_projeto(horas_28d: float, alocadas: float) -> str:
    """A: ≥ 40 h em 4 semanas ou ≥ 300 h alocadas; B: 10 a 40 h; C: menos; Parado: nenhuma.

    «Go-live em 30 dias» e «cliente estratégico» também fazem um A, mas não estão no Odoo:
    decide-os o gestor.
    """
    if horas_28d <= 0:
        return "Parado"
    if horas_28d >= 40 or alocadas >= 300:
        return "A"
    if horas_28d >= 10:
        return "B"
    return "C"


def dias_uteis(inicio: date, fim: date) -> list[date]:
    dias = []
    d = inicio
    while d <= fim:
        if d.weekday() < 5:
            dias.append(d)
        d += timedelta(days=1)
    return dias


def segunda_da_semana(hoje: date) -> date:
    return hoje - timedelta(days=hoje.weekday())


def verificar_timesheet(linhas: list[dict], dias: list[date],
                        cliente_de_projeto: dict[int, str]) -> dict:
    """Dias úteis sem horas, linhas sem tarefa e excesso por cliente e dia (Passo 1A)."""
    por_dia: dict[str, float] = defaultdict(float)
    por_cliente_dia: dict[tuple[str, str], float] = defaultdict(float)
    sem_tarefa = 0
    for ln in linhas:
        horas = float(ln.get("unit_amount") or 0)
        dia = str(ln.get("date"))
        por_dia[dia] += horas
        if not ln.get("task_id"):
            sem_tarefa += 1
        proj = ln.get("project_id")
        cliente = cliente_de_projeto.get(proj[0], "(sem cliente)") if proj else "(sem projeto)"
        por_cliente_dia[(dia, cliente)] += horas
    sem_horas = [d.isoformat() for d in dias if por_dia.get(d.isoformat(), 0) <= 0]
    excesso = sorted(
        ((dia, cli, round(h, 2)) for (dia, cli), h in por_cliente_dia.items()
         if h > HORAS_MAX_CLIENTE_DIA + 1e-9))
    return {"por_dia": {k: round(v, 2) for k, v in sorted(por_dia.items())},
            "dias_sem_horas": sem_horas, "linhas_sem_tarefa": sem_tarefa,
            "excesso_por_cliente_dia": excesso, "total_linhas": len(linhas)}


# --------------------------------------------------------------------------------------
# Leitura do Odoo
# --------------------------------------------------------------------------------------

def ler(cliente, model: str, domain: list, fields: list[str], pagina: int = 2000,
        maximo: int = 20000) -> list[dict]:
    todos: list[dict] = []
    offset = 0
    while True:
        bloco = cliente.call_kw(model, "search_read", args=[domain],
                                kwargs={"fields": fields, "limit": pagina,
                                        "offset": offset, "order": "id asc"})
        todos.extend(bloco)
        if len(bloco) < pagina or len(todos) >= maximo:
            return todos
        offset += pagina


def url_registo(base: str, model: str, rid: int) -> str:
    return f"{base.rstrip('/')}/odoo/{model}/{rid}"


# --------------------------------------------------------------------------------------
# Montagem da ficha
# --------------------------------------------------------------------------------------

def parte_a(cliente, base, uid, nome, projetos, ids_odoo, hoje, maximo_linhas) -> dict:
    tarefas = ler(cliente, "project.task",
                  [["is_closed", "=", False], ["project_id", "in", ids_odoo],
                   ["user_ids", "in", [uid]]],
                  ["name", "project_id", "stage_id", "write_date", "date_last_stage_update",
                   "allocated_hours", "effective_hours", "date_deadline", "user_ids"])
    classificadas = []
    for t in tarefas:
        c = classificar_tarefa(t, hoje)
        classificadas.append({"id": t["id"], "nome": t["name"],
                              "projeto": (t.get("project_id") or [None, ""])[1],
                              "horas": float(t.get("allocated_hours") or 0),
                              "prazo": (t.get("date_deadline") or "")[:10], **c})
    sprint = [c for c in classificadas if em_sprint(c["grupo"])]
    completas_abertas = [c for c in classificadas if c["grupo"] == "sprint_completa"]
    para_rever = sprint + completas_abertas
    para_rever.sort(key=lambda c: (-(c["parada_dias"] or 0)))

    contagem = {
        "abertas": len(classificadas),
        "em_sprint": len(sprint),
        "sprint_completa_abertas": len(completas_abertas),
        "sprint_parada_30": sum(1 for c in sprint if c["parada_30"]),
        "sprint_parada_90": sum(1 for c in sprint if c["parada_90"]),
        "sprint_sem_horas": sum(1 for c in sprint if c["sem_horas_alocadas"]),
        "sprint_sem_prazo": sum(1 for c in sprint if c["sem_prazo"]),
        "sprint_vencidas": sum(1 for c in sprint if c["vencida"]),
        "sprint_completas_3_campos": sum(1 for c in sprint if c["completa_tres_campos"]),
    }

    # Timesheet da semana (segunda a hoje) e a anterior, se hoje for segunda.
    segunda = segunda_da_semana(hoje)
    dias = dias_uteis(segunda, hoje)
    linhas = ler(cliente, "account.analytic.line",
                 [["user_id", "=", uid], ["project_id", "!=", False],
                  ["date", ">=", segunda.isoformat()], ["date", "<=", hoje.isoformat()]],
                 ["date", "unit_amount", "task_id", "project_id"])
    ids_proj = sorted({ln["project_id"][0] for ln in linhas if ln.get("project_id")})
    cliente_de = {}
    if ids_proj:
        for p in ler(cliente, "project.project", [["id", "in", ids_proj],
                                                  ["active", "in", [True, False]]],
                     ["partner_id"]):
            cliente_de[p["id"]] = (p.get("partner_id") or [None, f"(projeto {p['id']})"])[1]
    ts = verificar_timesheet(linhas, dias, cliente_de)

    return {"contagem": contagem, "para_rever": para_rever[:maximo_linhas],
            "para_rever_total": len(para_rever), "timesheet": ts,
            "dias_semana": [d.isoformat() for d in dias]}


def parte_b(cliente, base, uid, projetos, ids_odoo, hoje, projeto_key=None,
            quadro_na_cor: bool = False) -> dict:
    meus = [p for p in projetos
            if p.get("user_id") and p["user_id"][0] == uid
            and (p.get("stage_id") or [None, ""])[1] in ETAPAS_EM_CURSO]
    if projeto_key:
        # Dentro de um repositório de projeto, o foco é o projeto desse repositório,
        # mesmo que a pessoa não seja o gestor dele.
        alvo = [p for p in projetos if p.get("pg_project_key") == projeto_key]
        meus = alvo or meus
    ids = [p["id"] for p in meus]
    if not ids:
        return {"projetos": [], "sem_gestor_em_curso": []}

    desde = (hoje - timedelta(days=JANELA_ATIVIDADE_DIAS)).isoformat()
    linhas = ler(cliente, "account.analytic.line",
                 [["project_id", "in", ids], ["date", ">=", desde],
                  ["date", "<=", hoje.isoformat()]], ["project_id", "unit_amount"])
    horas_28d: dict[int, float] = defaultdict(float)
    for ln in linhas:
        horas_28d[ln["project_id"][0]] += float(ln.get("unit_amount") or 0)

    tarefas = ler(cliente, "project.task",
                  [["is_closed", "=", False], ["project_id", "in", ids]],
                  ["project_id", "stage_id", "write_date", "allocated_hours",
                   "date_deadline", "user_ids"])
    por_proj: dict[int, list[dict]] = defaultdict(list)
    for t in tarefas:
        por_proj[t["project_id"][0]].append(t)

    marcos = ler(cliente, "project.milestone",
                 [["project_id", "in", ids], ["is_reached", "=", False]],
                 ["name", "deadline", "project_id"])
    proximo: dict[int, dict] = {}
    for m in marcos:
        pid = m["project_id"][0]
        if m.get("deadline") and (pid not in proximo or m["deadline"] < proximo[pid]["deadline"]):
            proximo[pid] = m

    saida = []
    for p in meus:
        pid = p["id"]
        ts = por_proj.get(pid, [])
        classif = [classificar_tarefa(t, hoje) for t in ts]
        sprint = [c for c in classif if em_sprint(c["grupo"])]
        completas = sum(1 for c in sprint if c["completa_tres_campos"])
        h28 = round(horas_28d.get(pid, 0.0), 1)
        aloc = float(p.get("allocated_hours") or 0)
        efet = float(p.get("effective_hours") or 0)
        cor_h, consumo = semaforo_horas(efet, aloc)
        cor_a = semaforo_atividade(h28)
        cor_q = semaforo_quadro(completas, len(sprint))
        cor_p = semaforo_prazo(p.get("date"), hoje)
        saida.append({
            "id": pid, "nome": p["name"], "url": url_registo(base, "project.project", pid),
            "etapa": (p.get("stage_id") or [None, ""])[1],
            "tipo": tipo_projeto(h28, aloc),
            "gestor": (p.get("user_id") or [None, "sem gestor"])[1],
            "data_fim": (p.get("date") or "")[:10] or None,
            "alocadas": aloc, "efetivas": round(efet, 1),
            "consumo": None if consumo is None else round(consumo, 3),
            "horas_28d": h28,
            "estado_projeto": p.get("last_update_status") or "to_define",
            "proximo_marco": ({"nome": proximo[pid]["name"], "data": proximo[pid]["deadline"]}
                              if pid in proximo else None),
            "tarefas_abertas": len(ts), "tarefas_em_sprint": len(sprint),
            "tarefas_sprint_completas": completas,
            "tarefas_vencidas": sum(1 for c in classif if c["vencida"]),
            "cores": {"horas": cor_h, "prazo": cor_p, "atividade": cor_a, "quadro": cor_q},
            # Nas duas primeiras sextas o quadro está por limpar e deixava todos os projetos
            # vermelhos, o que esconde a diferença entre eles. Entra na cor com --quadro-na-cor.
            "cor": cor_global([cor_h, cor_p, cor_a] + ([cor_q] if quadro_na_cor else [])),
        })
    ordem = {"vermelho": 0, "amarelo": 1, "verde": 2, "sem_dados": 3}
    saida.sort(key=lambda s: (ordem[s["cor"]], -s["horas_28d"]))

    sem_gestor = [{"nome": p["name"], "url": url_registo(base, "project.project", p["id"])}
                  for p in projetos
                  if not p.get("user_id") and (p.get("stage_id") or [None, ""])[1] in ETAPAS_EM_CURSO]
    return {"projetos": saida, "sem_gestor_em_curso": sem_gestor, "quadro_na_cor": quadro_na_cor}


# --------------------------------------------------------------------------------------
# Saída em markdown
# --------------------------------------------------------------------------------------

def _linha_tabela(celulas: list[str]) -> str:
    limpas = [str(c).replace("|", "/").replace("\n", " ") for c in celulas]
    return "| " + " | ".join(limpas) + " |"


def render_markdown(ctx: dict) -> str:
    L: list[str] = []
    L.append(f"# Revisão de sexta-feira · {ctx['hoje']} · {ctx['nome']}")
    L.append("")
    L.append(f"Universo: projetos com a etiqueta Odoo. Gerado a partir do Odoo da Parâmetro "
             f"Global ({ctx['login']}). Só leitura: nada foi alterado.")
    if ctx["hoje_dia_semana"] != 4:
        L.append("")
        L.append("> Hoje não é sexta-feira. A ficha serve na mesma, mas o bloco protegido é à sexta.")

    a = ctx.get("a")
    if a:
        c = a["contagem"]
        L.append("")
        L.append("## Parte A: o meu quadro (45 min)")
        L.append("")
        L.append("Contagem **antes** (anota-a: no fim voltas a contar):")
        L.append("")
        L.append(f"- Tarefas abertas em que sou responsável: **{c['abertas']}**, das quais "
                 f"**{c['em_sprint']}** em sprint.")
        L.append(f"- Em sprint: **{c['sprint_parada_30']}** paradas há mais de 30 dias "
                 f"({c['sprint_parada_90']} há mais de 90), **{c['sprint_sem_horas']}** sem horas, "
                 f"**{c['sprint_sem_prazo']}** sem prazo, **{c['sprint_vencidas']}** vencidas.")
        L.append(f"- Em sprint com dono, horas e prazo: **{c['sprint_completas_3_campos']} de "
                 f"{c['em_sprint']}**.")
        L.append(f"- Em Sprint Complete e ainda abertas: **{c['sprint_completa_abertas']}**.")

        ts = a["timesheet"]
        L.append("")
        L.append("### 1. Horas da semana")
        L.append("")
        if ts["dias_sem_horas"]:
            L.append("- Dias úteis **sem horas lançadas**: " + ", ".join(ts["dias_sem_horas"])
                     + ". Lançar o que falta (hoje conta, se já acabou o trabalho do dia).")
        else:
            L.append("- Todos os dias úteis da semana têm horas lançadas.")
        L.append(f"- Linhas sem tarefa: **{ts['linhas_sem_tarefa']}** de {ts['total_linhas']}. "
                 "Cada linha deve apontar a uma tarefa.")
        if ts["excesso_por_cliente_dia"]:
            L.append(f"- Acima de {HORAS_MAX_CLIENTE_DIA:g} h por cliente e dia (regra do "
                     "timesheet, Passo 1A): " + "; ".join(
                         f"{d} · {cli} · {h:g} h" for d, cli, h in ts["excesso_por_cliente_dia"]))
        L.append("")
        L.append("| Dia | Horas |")
        L.append("| --- | --- |")
        for dia in a["dias_semana"]:
            L.append(_linha_tabela([dia, f"{ts['por_dia'].get(dia, 0):g}"]))

        L.append("")
        L.append("### 2. Tarefas em sprint, da menos editada para a mais recente")
        L.append("")
        L.append("Para cada uma, as sete perguntas: feita? vai ser feita em 2 semanas? tem dono? "
                 "horas? prazo? etapa certa? prazo passado?")
        L.append("")
        if not a["para_rever"]:
            L.append("Nenhuma tarefa em sprint em que sejas responsável.")
        else:
            L.append("| # | Tarefa | Projeto | Etapa | Sem edição (d) | Horas | Prazo | Ação sugerida |")
            L.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
            for i, t in enumerate(a["para_rever"], 1):
                L.append(_linha_tabela([
                    i, f"[{t['nome']}]({url_registo(ctx['url'], 'project.task', t['id'])})",
                    t["projeto"], t["etapa"], t["parada_dias"] if t["parada_dias"] is not None else "",
                    f"{t['horas']:g}" if t["horas"] else "–", t["prazo"] or "–", t["acao"]]))
            if a["para_rever_total"] > len(a["para_rever"]):
                L.append("")
                L.append(f"Mostradas {len(a['para_rever'])} de {a['para_rever_total']}. "
                         "Corre de novo com `--max-tarefas` maior para ver todas.")

    b = ctx.get("b")
    if b is not None:
        L.append("")
        L.append("## Parte B: os meus projetos (45 a 60 min)")
        L.append("")
        if not b["projetos"]:
            L.append("Nenhum projeto Odoo em curso em que sejas gestor.")
        else:
            L.append("Cada gestor valida dez pontos por projeto; abaixo, o que o Odoo já diz. "
                     "O prazo é provisório: sem baseline só olha para a data de fim.")
            L.append("")
            L.append("| Cor | Tipo | Projeto | Horas | Atividade 4 sem. | Quadro | Prazo | "
                     "Próximo marco | Vencidas |")
            L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
            for p in b["projetos"]:
                cores = p["cores"]
                consumo = "–" if p["consumo"] is None else f"{round(p['consumo'] * 100)} %"
                marco = (f"{p['proximo_marco']['data']} · {p['proximo_marco']['nome']}"
                         if p["proximo_marco"] else "sem marco")
                L.append(_linha_tabela([
                    ICONE[p["cor"]], p["tipo"], f"[{p['nome']}]({p['url']})",
                    f"{ICONE[cores['horas']]} {consumo} ({p['efetivas']:g}/{p['alocadas']:g} h)",
                    f"{ICONE[cores['atividade']]} {p['horas_28d']:g} h",
                    f"{ICONE[cores['quadro']]} {p['tarefas_sprint_completas']}/{p['tarefas_em_sprint']}",
                    (f"{ICONE[cores['prazo']]} {p['data_fim']}" if p["data_fim"] else "sem data"),
                    marco, p["tarefas_vencidas"]]))
            if not b.get("quadro_na_cor"):
                L.append("")
                L.append("A cor é a pior de horas, prazo e atividade. O quadro mostra-se mas ainda "
                         "não entra na cor: passa a entrar quando a limpeza das duas primeiras "
                         "sextas estiver feita (`--quadro-na-cor`).")
            L.append("")
            L.append("### Decisões a registar (uma linha por ponto fora do verde)")
            L.append("")
            for p in b["projetos"]:
                if p["cor"] in ("amarelo", "vermelho", "sem_dados") or p["tipo"] == "Parado":
                    L.append(f"- **{p['nome']}** ({p['tipo']}, {p['cor']}): "
                             "`[Dono] Ação: descrição, até dia e hora`")
        if b["sem_gestor_em_curso"]:
            L.append("")
            L.append(f"### Projetos Odoo em curso sem gestor ({len(b['sem_gestor_em_curso'])})")
            L.append("")
            L.append("Sem gestor não há revisão. Atribuir ou decidir na reunião de segunda-feira.")
            L.append("")
            for p in b["sem_gestor_em_curso"][:40]:
                L.append(f"- [{p['nome']}]({p['url']})")
            if len(b["sem_gestor_em_curso"]) > 40:
                L.append(f"- … e mais {len(b['sem_gestor_em_curso']) - 40}")

    L.append("")
    L.append("## Fecho e síntese")
    L.append("")
    L.append("1. **Quadro:** tarefas em sprint com dono, horas e prazo, antes e depois: ____ de ____ → ____ de ____")
    L.append("2. **Projetos:** verdes ____, amarelos ____, vermelhos ____, parados ____")
    L.append("3. **Preciso da direção para:** ____ (até ____)")
    L.append("")
    L.append("Nenhuma linha sai do bloco sem dono e sem hora.")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------

def _pasta_saida(explicita: str | None) -> pathlib.Path:
    if explicita:
        return pathlib.Path(explicita)
    raiz = os.environ.get("USERPROFILE") or os.environ.get("HOME") or "."
    return pathlib.Path(raiz) / ".pg" / "revisao"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--parte", choices=["A", "B", "ambas"], default="ambas")
    ap.add_argument("--login", default="", help="login Odoo da pessoa (por defeito, quem corre)")
    ap.add_argument("--projeto-key", default="",
                    help="project_key do repositório atual: a Parte B foca esse projeto")
    ap.add_argument("--hoje", default="", help="AAAA-MM-DD (por defeito, hoje); serve aos testes")
    ap.add_argument("--max-tarefas", type=int, default=60)
    ap.add_argument("--quadro-na-cor", action="store_true",
                    help="inclui o quadro (tarefas em sprint completas) na cor do projeto; "
                         "ligar depois das duas primeiras sextas de limpeza")
    ap.add_argument("--saida", default="", help="pasta de saída (fora de repositórios)")
    ap.add_argument("--stdout", action="store_true", help="imprime a ficha em vez de a gravar")
    ap.add_argument("--json", action="store_true", help="grava também o JSON ao lado")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from pg_doc_templates_common import OdooKnowledgeClient
    from pg_odoo_credentials import ErroDeCredenciais, resolver_credenciais_pg

    try:
        cred = resolver_credenciais_pg(login=args.login or None)
    except ErroDeCredenciais as exc:
        print("ERRO: " + str(exc), file=sys.stderr)
        return 2
    cliente = OdooKnowledgeClient(cred["url"], cred["db"], cred["login"], cred["api_key"])
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()

    utilizadores = cliente.call_kw("res.users", "search_read",
                                   args=[[["login", "=", cred["login"]]]],
                                   kwargs={"fields": ["name"], "limit": 1})
    if not utilizadores:
        print(f"ERRO: o login '{cred['login']}' não existe como utilizador no Odoo.", file=sys.stderr)
        return 2
    uid, nome = utilizadores[0]["id"], utilizadores[0]["name"]

    projetos = ler(cliente, "project.project",
                   [["tag_ids.name", "=", ETIQUETA_ODOO], ["active", "=", True]],
                   ["name", "stage_id", "user_id", "allocated_hours", "effective_hours",
                    "date", "last_update_status", "pg_project_key"])
    ids_odoo = [p["id"] for p in projetos]
    if not ids_odoo:
        print("ERRO: nenhum projeto com a etiqueta Odoo. Confirmar a etiqueta no Odoo.", file=sys.stderr)
        return 2

    ctx = {"hoje": hoje.isoformat(), "hoje_dia_semana": hoje.weekday(), "nome": nome,
           "login": cred["login"], "url": cred["url"]}
    if args.parte in ("A", "ambas"):
        ctx["a"] = parte_a(cliente, cred["url"], uid, nome, projetos, ids_odoo, hoje,
                           args.max_tarefas)
    if args.parte in ("B", "ambas"):
        ctx["b"] = parte_b(cliente, cred["url"], uid, projetos, ids_odoo, hoje,
                           args.projeto_key or None, args.quadro_na_cor)

    md = render_markdown(ctx)
    if args.stdout:
        print(md)
        return 0

    pasta = _pasta_saida(args.saida or None)
    pasta.mkdir(parents=True, exist_ok=True)
    base = f"{hoje.isoformat()}_{cred['login'].split('@')[0]}"
    (pasta / f"{base}.md").write_text(md, encoding="utf-8")
    if args.json:
        (pasta / f"{base}.json").write_text(
            json.dumps(ctx, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"ficha gravada em: {pasta / (base + '.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
