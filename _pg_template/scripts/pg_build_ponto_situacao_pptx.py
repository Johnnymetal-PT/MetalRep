#!/usr/bin/env python3
"""
Gera o deck PowerPoint de Ponto de Situação com a identidade Parâmetro Global.

O deck é sempre o mesmo para todos os clientes e projetos: a estrutura de slides é
fixa e a identidade vem de `pg_pptx_identity.py`. O que varia é apenas o conteúdo,
lido de um payload JSON. Mesmo payload => mesmo deck, byte a byte.

As secções do deck mapeiam 1:1 as secções de `doc_templates/TPL_PONTO_SITUACAO.md`,
que continua a ser a fonte do conteúdo e do tom de discurso.

Uso:
    python pg_build_ponto_situacao_pptx.py --payload dados.json --out deck.pptx

Schema do payload: ver `doc_templates/TPL_PONTO_SITUACAO_PPTX.md` (Passo 2).

Dependências:
    pip install python-pptx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pg_pptx_identity import (  # noqa: E402
    ACCENT, BAND, BODY, CONTENT_BOTTOM, CONTENT_L, CONTENT_TOP, CONTENT_W,
    Deck, GREEN, INK, MUTED, ORANGE, altura_linha, estimar_linhas,
)

COLS = 3
MAX_ATIVIDADES = 6


def _parse_horas(texto):
    """'13h15' -> 13.25 ; '8h' -> 8.0 ; '3,5' -> 3.5. Devolve 0.0 se não parsear."""
    if texto is None:
        return 0.0
    if isinstance(texto, (int, float)):
        return float(texto)
    s = str(texto).strip().lower().replace(",", ".")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*h\s*(\d{1,2})?$", s)
    if m:
        horas = float(m.group(1))
        return horas + (int(m.group(2)) / 60.0 if m.group(2) else 0.0)
    try:
        return float(s)
    except ValueError:
        return 0.0


def _req(payload, chave):
    valor = payload.get(chave)
    if valor in (None, "", [], {}):
        raise SystemExit(f"ERRO: campo obrigatório em falta no payload: '{chave}'")
    return valor


# --------------------------------------------------------------------------
# Slides
# --------------------------------------------------------------------------

def slide_capa(deck, p):
    # o projeto já é o subtítulo da capa; aqui fica só o que não está lá acima
    _req(p, "projeto")
    meta = [f"Cliente: {_req(p, 'cliente')}", f"Data: {_req(p, 'data')}"]
    if p.get("periodo"):
        meta.append(f"Período: {p['periodo']}")
    if p.get("preparado_por"):
        meta.append(f"Consultor responsável: {p['preparado_por']}")
    deck.cover(
        title="Ponto de Situação",
        subtitle=p["projeto"],
        description=p.get("descricao", ""),
        meta=meta,
    )


def slide_dashboard(deck, p):
    """
    Slide 1: Dashboard Executivo Visual orientado ao Cliente.
    Reúne KPIs de topo, progresso visual por área com barras, destaques de valor
    entregue e decisões prioritárias do cliente numa vista única e intuitiva.
    """
    resumo = p.get("resumo", {})
    horas = p.get("horas", {})
    s = deck.content("1. Painel Executivo do Projeto",
                     "Visão consolidada do progresso, marcos atingidos e prioridades para o cliente")

    # 1. Top KPI Row (4 indicadores de topo com badges de estado)
    # sem `saude_projeto` no payload o estado é desconhecido: não se afirma «No Prazo» por omissão
    saude = p.get("saude_projeto") or ""
    saude_badge = p.get("saude_badge", "EM DIA")
    saude_status = "ok" if saude.lower() in ("no prazo", "em dia", "excelente", "normal") else "warning"
    saude_cor = GREEN if saude_status == "ok" else ORANGE

    progresso_pct = p.get("progresso_global_pct")
    progresso_txt = f"{int(progresso_pct)}%" if progresso_pct is not None else (str(p.get("fase", "Em Curso")))

    horas_total = str(horas.get("total", "0h"))
    saldo_txt = str(horas.get("saldo_horas", horas.get("total_contratado", f"{len(p.get('areas', []))} áreas")))
    saldo_label = "Saldo de horas disponível" if horas.get("saldo_horas") else ("Frentes com atividade" if not horas.get("total_contratado") else "Total contratado")

    # O cartão de estado global é opcional: `mostrar_estado_global: false` no payload
    # retira-o e a fila reparte a largura pelos restantes indicadores.
    kpi_items = []
    if saude and p.get("mostrar_estado_global", True):
        kpi_items.append((saude, "Estado global do projeto", saude_cor, saude_badge, saude_status))
    kpi_items += [
        (progresso_txt, p.get("progresso_rotulo") or "Progresso global estimado", ACCENT),
        # `rotulo_curto` deixa o payload dizer o que o número é: há decks que reportam o
        # esforço DO PERÍODO e outros o ACUMULADO do projeto, e o rótulo fixo «no período»
        # tornava o segundo caso numa afirmação falsa.
        (horas_total, horas.get("rotulo_curto") or "Horas executadas no período", INK),
        (saldo_txt, saldo_label, ACCENT if horas.get("saldo_horas") else INK),
    ]
    y_kpi_end = s.kpi_row(kpi_items, y=CONTENT_TOP, h=2.55, gap=0.38)

    # 2. Main Content: Duas colunas (Esquerda: Progresso/Gráfico por área; Direita: Destaques & Decisões)
    y_body = y_kpi_end + 0.40
    gap = 0.42
    larg_esq = 14.50
    x_dir = CONTENT_L + larg_esq + gap
    larg_dir = CONTENT_W - larg_esq - gap
    h_total = CONTENT_BOTTOM - y_body

    # --- Coluna Esquerda: Cartão de Progresso por Área / Módulo ---
    s.card(CONTENT_L, y_body, larg_esq, h_total)
    s.rect(CONTENT_L, y_body, larg_esq, 0.10, fill=ACCENT)
    s.text(p.get("progresso_titulo") or "Progresso por Frente de Trabalho",
           CONTENT_L + 0.55, y_body + 0.42, larg_esq - 1.10, 0.60,
           size=12, bold=True, color=INK)
    s.text(p.get("progresso_subtitulo") or "Estado de avanço das principais áreas de negócio",
           CONTENT_L + 0.55, y_body + 1.05, larg_esq - 1.10, 0.40,
           size=8, color=MUTED)

    # Obter lista de progresso por área ou derivar das áreas existentes.
    # A derivação é uma escada fixa pela ordem das áreas (100, 85, 70, ...): serve de
    # marcador visual, NAO e uma medicao. Num documento para o cliente, declarar
    # `progresso_areas` com valores reais (ou usar `rotulo` para mostrar horas em vez
    # de percentagem) — caso contrario o deck afirma um avanco que ninguem mediu.
    prog_areas = p.get("progresso_areas", [])
    if not prog_areas and p.get("areas"):
        n_areas = len(p["areas"])
        for i, a in enumerate(p["areas"]):
            prog_areas.append({
                "area": a.get("nome", f"Área {i+1}"),
                "progresso": int(max(20, min(100, 100 - i * 15))),
                "estado": a.get("estado", "Em progresso"),
            })

    y_bar = y_body + 1.60
    pitch_bar = min(1.30, max(0.95, (h_total - 3.20) / max(1, len(prog_areas))))
    for item in prog_areas[:5]:
        area_nome = item.get("area", "")
        pct = item.get("progresso", 50)
        s.text(area_nome, CONTENT_L + 0.55, y_bar, larg_esq - 1.10, 0.42, size=9, bold=True, color=INK, wrap=False)
        s.progress_bar(CONTENT_L + 0.55, y_bar + 0.46, larg_esq - 1.10, h=0.32, pct=pct, fill=ACCENT,
                       label=item.get("rotulo"))
        y_bar += pitch_bar

    # Caixa inferior de síntese executiva na coluna esquerda
    if resumo.get("avaliacao") or resumo.get("paragrafo"):
        txt_sintese = resumo.get("avaliacao") or resumo.get("paragrafo")
        box_y = max(y_bar + 0.20, y_body + h_total - 1.80)
        box_h = y_body + h_total - box_y - 0.25
        s.rect(CONTENT_L + 0.45, box_y, larg_esq - 0.90, box_h, fill=BAND)
        s.text(f"Síntese: {txt_sintese}", CONTENT_L + 0.65, box_y + 0.18, larg_esq - 1.30, box_h - 0.36,
               size=8, color=BODY, line_spacing=1.15)

    # --- Coluna Direita (2 Cartões: Destaques de Valor + Decisões do Cliente) ---
    h_dir_top = 5.30
    h_dir_bot = h_total - h_dir_top - 0.35

    # Cartão Superior: Destaques e Valor Entregue ao Cliente
    s.card(x_dir, y_body, larg_dir, h_dir_top)
    s.rect(x_dir, y_body, larg_dir, 0.10, fill=ACCENT)
    s.text("Principais Conquistas & Valor Entregue", x_dir + 0.55, y_body + 0.42, larg_dir - 1.10, 0.60,
           size=12, bold=True, color=INK)
    s.text("Resultados concretos e marcos funcionais atingidos", x_dir + 0.55, y_body + 1.05, larg_dir - 1.10, 0.40,
           size=8, color=MUTED)

    destaques = p.get("destaques_cliente") or resumo.get("focos") or []
    if not destaques and resumo.get("paragrafo"):
        destaques = [resumo["paragrafo"]]
    if destaques:
        s.bullets(destaques[:4], x_dir + 0.55, y_body + 1.65, larg_dir - 1.10, size=9.5, gap=0.22)

    # Cartão Inferior: Decisões e Ações Prioritárias do Cliente
    y_bot_card = y_body + h_dir_top + 0.35
    s.card(x_dir, y_bot_card, larg_dir, h_dir_bot)
    decisoes = p.get("decisoes_pendentes", [])
    cor_topo_bot = ORANGE if decisoes else ACCENT
    s.rect(x_dir, y_bot_card, larg_dir, 0.10, fill=cor_topo_bot)

    titulo_bot = "Ações & Decisões Prioritárias do Cliente" if decisoes else "Próximos Marcos do Cliente"
    s.text(titulo_bot, x_dir + 0.55, y_bot_card + 0.38, larg_dir - 1.10, 0.55,
           size=11.5, bold=True, color=INK)

    if decisoes:
        d = decisoes[0]
        dec_txt = f"{d.get('decisao', '')} (Prazo: {d.get('prazo', 'A definir')})"
        s.text(f"• {dec_txt}", x_dir + 0.55, y_bot_card + 1.05, larg_dir - 1.10, 0.55,
               size=9, bold=True, color=INK)
        if d.get("impacto"):
            s.text(f"Impacto no projeto: {d.get('impacto')}", x_dir + 0.75, y_bot_card + 1.65,
                   larg_dir - 1.40, 0.90, size=8, color=MUTED, line_spacing=1.15)
    else:
        proximos = p.get("proximos_passos", [])[:2]
        if proximos:
            s.bullets(proximos, x_dir + 0.55, y_bot_card + 1.05, larg_dir - 1.10, size=9, gap=0.18)
        else:
            s.text("Sem bloqueios ou decisões pendentes neste período.", x_dir + 0.55, y_bot_card + 1.10,
                   larg_dir - 1.10, 0.50, size=9, color=GREEN)


def _altura_area(area, largura_cartao):
    """Altura que o cartão de uma área precisa, dado o comprimento do seu conteúdo."""
    largura = largura_cartao - 1.10
    h = 1.80  # topo + título
    contexto = area.get("contexto", "")
    if contexto:
        h += altura_linha(8.5) * estimar_linhas(contexto, largura, 8.5) + 0.45
    for atividade in area.get("atividades", [])[:MAX_ATIVIDADES]:
        h += altura_linha(8.5) * estimar_linhas(atividade, largura, 8.5) + 0.16
    return h + 0.40


def _desenhar_cartao_area(s, area, cx, cy, cw, ch):
    s.card(cx, cy, cw, ch)
    s.rect(cx, cy, cw, 0.10, fill=ACCENT)
    s.text(area.get("nome", ""), cx + 0.55, cy + 0.55, cw - 1.10, 1.10,
           size=11.5, bold=True, color=INK)
    yy = cy + 1.80
    contexto = area.get("contexto", "")
    if contexto:
        ctx_h = altura_linha(8.5) * estimar_linhas(contexto, cw - 1.10, 8.5)
        s.text(contexto, cx + 0.55, yy, cw - 1.10, ctx_h + 0.06, size=8.5,
               color=MUTED, line_spacing=1.2)
        yy += ctx_h + 0.45
    s.bullets(area.get("atividades", [])[:MAX_ATIVIDADES], cx + 0.55, yy, cw - 1.10,
              size=8.5, gap=0.16)


def slides_trabalhos(deck, p):
    """
    Grelha de cartões em filas de três. Cada fila tem a altura do seu cartão mais
    alto e só se abre nova slide quando a fila seguinte deixa de caber — assim o
    conteúdo nunca é cortado nem se desperdiça meia slide em branco.
    """
    areas = p.get("areas", [])
    if not areas:
        return

    gap, gap_fila = 0.42, 0.50
    cw = (CONTENT_W - gap * (COLS - 1)) / COLS
    disponivel = CONTENT_BOTTOM - CONTENT_TOP
    alturas = [_altura_area(a, cw) for a in areas]

    paginas, pagina, altura_pagina = [], [], 0.0
    for i in range(0, len(areas), COLS):
        fila = list(range(i, min(i + COLS, len(areas))))
        h_fila = min(max(alturas[j] for j in fila), disponivel)
        acrescimo = h_fila + (gap_fila if pagina else 0.0)
        if pagina and altura_pagina + acrescimo > disponivel + 0.01:
            paginas.append(pagina)
            pagina, altura_pagina, acrescimo = [], 0.0, h_fila
        pagina.append((fila, h_fila))
        altura_pagina += acrescimo
    if pagina:
        paginas.append(pagina)

    for n, pagina in enumerate(paginas, start=1):
        sufixo = f" ({n}/{len(paginas)})" if len(paginas) > 1 else ""
        s = deck.content(f"2. Trabalhos realizados{sufixo}",
                         "Detalhe das atividades por área funcional")
        cy = CONTENT_TOP
        for fila, h_fila in pagina:
            for k, idx in enumerate(fila):
                _desenhar_cartao_area(s, areas[idx], CONTENT_L + k * (cw + gap),
                                      cy, cw, h_fila)
            cy += h_fila + gap_fila


def slide_horas(deck, p):
    horas = p.get("horas", {})
    if not horas:
        return
    # O subtítulo não nomeia a fonte: o deck vai para o cliente, e `PG_EFFORT_SYNC.json` é
    # maquinaria interna da consultora — a mesma regra que o TPL_TIMESHEET_INSTRUCOES aplica
    # às descrições de timesheet. A rastreabilidade da fonte vive no PG_CONTEXT, não no deck.
    s = deck.content("3. Carga horária registada",
                     "Distribuição do esforço por área e por consultor")

    y = CONTENT_TOP
    if horas.get("total"):
        # `rotulo_total` permite dizer a verdade sobre o que o número é: há decks que
        # reportam o esforço DO PERÍODO e outros o ACUMULADO do projeto, e o rótulo fixo
        # «no período» tornava o segundo caso numa afirmação falsa.
        s.kpi_row([(str(horas["total"]),
                    horas.get("rotulo_total") or "Total de horas registadas no período")],
                  y=y, h=2.30)
        y += 2.95

    por_area = horas.get("por_area", [])
    por_consultor = horas.get("por_consultor", [])

    # duas colunas quando há ambos, para o conteúdo nunca passar o rodapé
    gap = 0.42
    if por_area and por_consultor:
        larg_esq = 19.60
        x_dir, larg_dir = CONTENT_L + larg_esq + gap, CONTENT_W - larg_esq - gap
    elif por_area:
        larg_esq, x_dir, larg_dir = CONTENT_W, None, 0
    else:
        larg_esq, x_dir, larg_dir = 0, CONTENT_L, CONTENT_W

    if por_area:
        s.section_label("Distribuição por área", CONTENT_L, y, w=14)
        y_area = y + 0.80
        itens = [(a.get("area", ""), _parse_horas(a.get("valor", a.get("horas"))),
                  str(a.get("horas", ""))) for a in por_area]
        pitch = min(1.15, max(0.58, (CONTENT_BOTTOM - y_area) / len(itens)))
        s.hbars(itens, y=y_area, x=CONTENT_L, w=larg_esq,
                label_w=min(9.0, larg_esq * 0.42), pitch=pitch,
                bar_h=min(0.50, pitch * 0.44))

    if por_consultor:
        s.section_label("Distribuição por consultor", x_dir, y, w=14)
        y_cons = y + 0.80
        linhas = [[c.get("consultor", ""), str(c.get("horas", ""))] for c in por_consultor]
        pitch = min(1.32, max(0.70, (CONTENT_BOTTOM - y_cons - 1.42) / max(1, len(linhas))))
        s.table(["Consultor", "Horas"], linhas, y=y_cons, x=x_dir, w=larg_dir,
                widths=[7, 3], pitch=pitch)


def slide_estado(deck, p):
    estado = p.get("estado_atual", [])
    proximos = p.get("proximos_passos", [])
    if not estado and not proximos:
        return
    s = deck.content("4. Estado atual e próximos passos",
                     "Frentes com progresso relevante e trabalhos planeados")

    gap = 0.42
    cw = (CONTENT_W - gap) / 2
    ch = CONTENT_BOTTOM - CONTENT_TOP

    s.card(CONTENT_L, CONTENT_TOP, cw, ch)
    s.rect(CONTENT_L, CONTENT_TOP, cw, 0.10, fill=ACCENT)
    s.text("Estado atual", CONTENT_L + 0.60, CONTENT_TOP + 0.60, cw - 1.20, 0.70,
           size=13, bold=True, color=INK)
    s.bullets(estado, CONTENT_L + 0.60, CONTENT_TOP + 1.80, cw - 1.20, size=10, gap=0.26)

    x2 = CONTENT_L + cw + gap
    s.card(x2, CONTENT_TOP, cw, ch)
    s.rect(x2, CONTENT_TOP, cw, 0.10, fill=ACCENT)
    s.text("Próximos passos", x2 + 0.60, CONTENT_TOP + 0.60, cw - 1.20, 0.70,
           size=13, bold=True, color=INK)
    s.bullets(proximos, x2 + 0.60, CONTENT_TOP + 1.80, cw - 1.20, size=10, gap=0.26)


def _altura_risco(risco):
    """Altura do cartão de risco, adaptada ao comprimento da descrição."""
    linhas = estimar_linhas(risco.get("descricao", ""), CONTENT_W - 1.10, 8.5)
    return 1.00 + altura_linha(8.5) * linhas + 0.45


def _desenhar_riscos(s, riscos, y, etiqueta=True):
    if etiqueta:  # omitida quando o título da slide já diz o mesmo
        s.section_label("Riscos e pontos de atenção", CONTENT_L, y, w=14)
        y += 0.85
    for r in riscos:
        h = _altura_risco(r)
        s.card(CONTENT_L, y, CONTENT_W, h)
        s.rect(CONTENT_L, y, 0.10, h, fill=ORANGE)
        s.text(r.get("titulo", ""), CONTENT_L + 0.55, y + 0.30, CONTENT_W - 1.10, 0.50,
               size=10.5, bold=True, color=INK)
        s.text(r.get("descricao", ""), CONTENT_L + 0.55, y + 1.00, CONTENT_W - 1.10,
               h - 1.30, size=8.5, color=MUTED, line_spacing=1.15)
        y += h + 0.25
    return y


def _desenhar_decisoes(s, decisoes, y, etiqueta=True):
    if etiqueta:
        s.section_label("Decisões pendentes do cliente", CONTENT_L, y, w=14)
        y += 0.80
    linhas = [[d.get("decisao", ""), d.get("impacto", ""), d.get("prazo", "")]
              for d in decisoes]
    return s.table(["Decisão necessária", "Impacto se não decidido", "Prazo"], linhas,
                   y=y, widths=[11, 15, 4])


def slides_riscos(deck, p):
    """
    Riscos e decisões numa só slide quando cabem; em duas quando não cabem.
    Evita o transbordo do rodapé em períodos com muitos pontos em aberto.
    """
    riscos = p.get("riscos", [])
    decisoes = p.get("decisoes_pendentes", [])
    if not riscos and not decisoes:
        return

    h_riscos = 0.85 + sum(_altura_risco(r) + 0.25 for r in riscos) if riscos else 0
    h_decisoes = 0.80 + 1.42 + 1.32 * len(decisoes) if decisoes else 0
    separador = 0.35 if riscos and decisoes else 0
    cabe_junto = (h_riscos + separador + h_decisoes) <= (CONTENT_BOTTOM - CONTENT_TOP)

    if cabe_junto:
        s = deck.content("5. Riscos e decisões pendentes",
                         "Pontos de atenção e decisões que dependem do cliente")
        y = CONTENT_TOP
        if riscos:
            y = _desenhar_riscos(s, riscos, y) + separador
        if decisoes:
            _desenhar_decisoes(s, decisoes, y)
        return

    if riscos:
        s = deck.content("5. Riscos e pontos de atenção",
                         "Pontos de atenção do período e respetiva mitigação")
        _desenhar_riscos(s, riscos, CONTENT_TOP, etiqueta=False)
    if decisoes:
        numero = 6 if riscos else 5
        s = deck.content(f"{numero}. Decisões pendentes do cliente",
                         "Decisões que dependem do cliente para o projeto avançar")
        _desenhar_decisoes(s, decisoes, CONTENT_TOP, etiqueta=False)


def slide_fecho(deck, p):
    s = deck.content("Próximos passos e contacto", "Fecho do ponto de situação")
    passos = p.get("acoes_fecho", [])
    if passos:
        s.numbered([(a.get("titulo", ""), a.get("detalhe", "")) for a in passos[:4]])
    contacto = p.get("mensagem_fecho",
                     "Ficamos disponíveis para qualquer esclarecimento adicional.")
    autor = p.get("preparado_por", "")
    s.band(f"{contacto}   ·   {autor} · Parâmetro Global" if autor else contacto)


# --------------------------------------------------------------------------

def build(payload, out_path):
    ano = re.search(r"(20\d{2})", str(payload.get("data", "")))
    doc_label = f"Ponto de Situação · {payload.get('cliente', '')} | {ano.group(1) if ano else ''}".strip(" |")
    deck = Deck(doc_label=doc_label)

    slide_capa(deck, payload)
    slide_dashboard(deck, payload)
    slides_trabalhos(deck, payload)
    slide_horas(deck, payload)
    slide_estado(deck, payload)
    slides_riscos(deck, payload)
    slide_fecho(deck, payload)

    return deck.save(out_path)


def main():
    ap = argparse.ArgumentParser(description="Gera o deck de Ponto de Situação (identidade Parâmetro Global).")
    ap.add_argument("--payload", required=True, help="Ficheiro JSON com o conteúdo do ponto de situação")
    ap.add_argument("--out", required=True, help="Caminho do .pptx a gerar")
    args = ap.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    destino = build(payload, args.out)
    print(f"OK: deck gerado em {destino.resolve()}")


if __name__ == "__main__":
    main()
