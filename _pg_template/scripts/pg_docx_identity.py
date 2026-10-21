#!/usr/bin/env python3
"""
Identidade visual Parâmetro Global para documentos Word (python-docx).

FONTE DE VERDADE
    doc_templates/assets/Template_Parametro_Word.docx
    doc_templates/assets/create_parametro_word_template.py

Toda a paleta, tipografia e geometria deste módulo foi extraída desses ficheiros
(o template oficial da Parâmetro Global e o script que o gera) e não reinventada.
O documento base `assets/pg_base_doc.docx` é esse mesmo template sem corpo, para
que os estilos, o tema e os tipos de letra venham da marca e não do template
genérico do Word.

REGRA DE UTILIZAÇÃO
    Este módulo é a única fonte de identidade para geração de documentos Word.
    Os templates executáveis (Levantamento de Âmbito, Proposta Técnica, ...)
    compõem o documento a partir dos componentes daqui e nunca redesenham cores,
    margens ou cabeçalhos por sua conta. É isto que garante que dois documentos
    gerados em projetos diferentes saem iguais.

    É o equivalente Word do pg_pptx_identity.py.

Dependências:
    pip install python-docx
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# A paleta vem toda de pg_brand_palette.py, fonte unica para todos os formatos.
# Ver la a prova de qual e a cor da marca, e porque havia duas.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
from pg_brand_palette import (  # noqa: E402
    ACENTO, TITULO_CAPA, TINTA, BARRA_ESCURA, CORPO, SUAVE, para_rgb,
)


# --------------------------------------------------------------------------
# Assets da marca
# --------------------------------------------------------------------------

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
BASE_DOC = ASSETS_DIR / "pg_base_doc.docx"
LOGO_WORDMARK = ASSETS_DIR / "pg_logo_wordmark.png"  # capa e cabeçalho

# --------------------------------------------------------------------------
# Paleta e tipografia (create_parametro_word_template.py)
# --------------------------------------------------------------------------

# CORRIGIDO em 2026-09-11: o azul era #0094E9, que nao corresponde nem ao template
# Word nem ao PowerPoint da marca -- era um valor aproximado. Passa a ser o da marca,
# #009FE3, verificado 30 vezes no conteudo do template PowerPoint. O escuro alinha pela
# mesma razao. Ver a prova em pg_brand_palette.py.
BLUE = RGBColor(*para_rgb(ACENTO))
DARK = RGBColor(*para_rgb(BARRA_ESCURA))
TEXT = RGBColor(31, 41, 55)          # tom de corpo, sem equivalente na marca
MUTED = RGBColor(*para_rgb(SUAVE))

LIGHT_LINE = "D5E2EE"
LIGHT_BLUE = "EBF7FF"
DARK_HEX = BARRA_ESCURA

FONT = "Aptos"
MONO_FONT = "Consolas"  # trechos `codigo`; a marca nao define monoespacada propria

# Corpo a 10.5pt, títulos 18/14, legendas 8/9 — ver setup_doc_styles do script oficial.
SIZE_TITLE = 24
SIZE_SUBTITLE = 20
SIZE_H1 = 18
SIZE_H2 = 13
SIZE_H3 = 11
SIZE_BODY = 10.5
SIZE_SMALL = 9
SIZE_CAPTION = 8


# --------------------------------------------------------------------------
# Primitivas
# --------------------------------------------------------------------------


def add_run(paragraph, text, size=SIZE_BODY, bold=False, italic=False, color=TEXT,
            font=None):
    run = paragraph.add_run(text)
    run.font.name = font or FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return run


# Marcacao inline suportada nos componentes de texto: **negrito**, *italico* e
# `codigo`. Fica aqui, e nao no conversor de Markdown, para que qualquer template
# executavel a obtenha de graca ao usar add_body/add_bullet/add_table.
_INLINE = re.compile(r"(\*\*.+?\*\*|(?<!\*)\*[^*\n]+?\*(?!\*)|`[^`\n]+`)")
_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def add_rich_text(paragraph, text, size=SIZE_BODY, color=TEXT, bold=False, italic=False):
    """Escreve texto interpretando a marcacao inline, um run por segmento.

    O negrito e o italico acumulam com os valores base recebidos, para que um
    trecho **assim** dentro de um paragrafo ja italico saia italico e negrito.
    """
    text = _LINK.sub(r"\1", text or "")
    if not text:
        return paragraph

    for token in _INLINE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            add_run(paragraph, token[2:-2], size=size, bold=True, italic=italic, color=color)
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            add_run(paragraph, token[1:-1], size=size, bold=bold, italic=italic,
                    color=DARK, font=MONO_FONT)
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            add_run(paragraph, token[1:-1], size=size, bold=bold, italic=True, color=color)
        else:
            add_run(paragraph, token, size=size, bold=bold, italic=italic, color=color)
    return paragraph


def add_horizontal_line(paragraph, color=LIGHT_LINE, size="6"):
    p_pr = paragraph._p.get_or_add_pPr()
    pbdr = p_pr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr")
        p_pr.append(pbdr)
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_border(cell, color=LIGHT_LINE, size="4"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "bottom"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
    for edge in ("left", "right"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "nil")


# --------------------------------------------------------------------------
# Estrutura do documento
# --------------------------------------------------------------------------


# A4 (21 cm) menos as margens de 2,0 cm de cada lado definidas em set_margins.
LARGURA_UTIL_CM = 17.0


def new_document() -> Document:
    """Documento a partir do template da marca (estilos, tema e fontes herdados)."""
    if not BASE_DOC.exists():
        raise FileNotFoundError(
            f"Documento base da marca nao encontrado: {BASE_DOC}. "
            "E gerado a partir de doc_templates/assets/Template_Parametro_Word.docx."
        )
    return Document(str(BASE_DOC))


def set_margins(section):
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.7)


def configure_header_footer(section, doc_label: str, with_logo: bool = True):
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if with_logo and LOGO_WORDMARK.exists():
        hp.add_run().add_picture(str(LOGO_WORDMARK), width=Cm(3.2))
    add_horizontal_line(header.add_paragraph())

    footer = section.footer
    footer.is_linked_to_previous = False
    add_horizontal_line(footer.paragraphs[0])
    table = footer.add_table(rows=1, cols=2, width=Cm(17))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    left, right = table.cell(0, 0), table.cell(0, 1)
    left.width = Cm(12)
    right.width = Cm(5)
    add_run(left.paragraphs[0], doc_label, size=SIZE_CAPTION, color=MUTED)

    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(rp, "Página ", size=SIZE_CAPTION, color=MUTED)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run = rp.add_run()
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    run.font.size = Pt(SIZE_CAPTION)
    run.font.color.rgb = BLUE


def add_cover(doc: Document, title: str, subtitle: str = "", description: str = "",
              meta_lines: Sequence[str] = ()):
    """Capa da marca: logo, título azul, subtítulo escuro e assinatura da PG."""
    section = doc.sections[0]
    set_margins(section)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if LOGO_WORDMARK.exists():
        p.add_run().add_picture(str(LOGO_WORDMARK), width=Cm(7.5))

    doc.add_paragraph("\n")
    add_run(doc.add_paragraph(), title, size=SIZE_TITLE, color=BLUE)
    if subtitle:
        add_run(doc.add_paragraph(), subtitle, size=SIZE_SUBTITLE, bold=True, color=DARK)
    if description:
        add_run(doc.add_paragraph(), description, size=11, color=TEXT)

    if meta_lines:
        doc.add_paragraph("")
        for line in meta_lines:
            add_run(doc.add_paragraph(), line, size=SIZE_SMALL, color=MUTED)

    for _ in range(max(0, 12 - len(meta_lines))):
        doc.add_paragraph("")

    add_run(doc.add_paragraph(), "Preparado por Parâmetro Global", size=SIZE_SMALL, color=TEXT)
    add_horizontal_line(doc.add_paragraph(), color=DARK_HEX, size="24")

    doc.add_section(WD_SECTION.NEW_PAGE)
    set_margins(doc.sections[-1])


def add_section_title(doc: Document, title: str, description: str = ""):
    add_run(doc.add_paragraph(), title, size=SIZE_H1, bold=True, color=DARK)
    if description:
        add_run(doc.add_paragraph(), description, size=SIZE_SMALL, color=MUTED)
    add_horizontal_line(doc.add_paragraph())


def add_subtitle(doc: Document, text: str):
    add_run(doc.add_paragraph(), text, size=SIZE_H2, bold=True, color=BLUE)


def add_minor_title(doc: Document, text: str):
    add_run(doc.add_paragraph(), text, size=SIZE_H3, bold=True, color=DARK)


def add_body(doc: Document, text: str, italic: bool = False, color=TEXT):
    add_rich_text(doc.add_paragraph(), text, size=SIZE_BODY, italic=italic, color=color)


def add_bullet(doc: Document, text: str, level: int = 0):
    style = "List Bullet" if level == 0 else f"List Bullet {min(level + 1, 3)}"
    try:
        p = doc.add_paragraph(style=style)
    except KeyError:
        p = doc.add_paragraph()
    add_rich_text(p, text, size=SIZE_BODY)
    return p


def add_checkbox(doc: Document, text: str, checked: bool = False):
    """Item de checklist. Usado nos guiões de levantamento e nos pontos por validar."""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.6)
    add_run(p, "☒ " if checked else "☐ ", size=SIZE_BODY, color=BLUE)
    add_rich_text(p, text, size=SIZE_BODY)
    return p


def add_table(doc: Document, headers: Sequence[str], rows: Iterable[Sequence[str]],
              widths: Sequence[float] | None = None):
    """Tabela leve da marca: cabeçalho em azul claro, filetes só em cima e em baixo."""
    data = [list(r) for r in rows]
    table = doc.add_table(rows=len(data) + 1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for col, header in enumerate(headers):
        cell = table.cell(0, col)
        cell.text = ""
        set_cell_shading(cell, LIGHT_BLUE)
        set_cell_border(cell)
        add_run(cell.paragraphs[0], str(header), size=SIZE_SMALL, bold=True, color=DARK)

    for row_index, row in enumerate(data, start=1):
        for col in range(len(headers)):
            cell = table.cell(row_index, col)
            cell.text = ""
            set_cell_border(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            value = str(row[col]) if col < len(row) else ""
            add_rich_text(cell.paragraphs[0], value, size=SIZE_SMALL)

    if widths:
        for col, width in enumerate(widths):
            for row in table.rows:
                row.cells[col].width = Cm(width)

    doc.add_paragraph("")
    return table


def add_note(doc: Document, text: str):
    """Caixa de nota — destaque discreto para pressupostos e avisos."""
    table = doc.add_table(rows=1, cols=1)
    cell = table.cell(0, 0)
    cell.text = ""
    set_cell_shading(cell, LIGHT_BLUE)
    set_cell_border(cell)
    add_rich_text(cell.paragraphs[0], text, size=SIZE_SMALL, color=DARK)
    doc.add_paragraph("")
    return table


def add_caption(doc: Document, text: str):
    add_run(doc.add_paragraph(), text, size=SIZE_CAPTION, color=MUTED)


def save(doc: Document, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return out


def add_image(doc: Document, caminho, largura_cm: float = LARGURA_UTIL_CM, alt: str = ""):
    """Insere uma imagem centrada, a toda a largura util da pagina.

    As capturas de ecra dos relatorios sao largas (tipicamente 16:9) e, a largura
    inteira, ficam com cerca de 10 cm de altura numa A4 — cabem com o texto a volta.
    Uma imagem mais alta do que larga seria reduzida para nao ocupar a pagina toda.
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    largura = Cm(largura_cm)
    run = p.add_run()
    run.add_picture(str(caminho), width=largura)
    forma = run._element.findall(
        ".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")
    if alt and forma:
        forma[0].set("descr", alt)
    # Retratos: `add_picture` respeita a largura pedida e a altura cresce sem limite.
    # Acima de 18 cm a imagem empurra tudo para a pagina seguinte.
    imagem = run._element.findall(
        ".//{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
    if imagem:
        cx = int(imagem[0].get("cx") or 0)
        cy = int(imagem[0].get("cy") or 0)
        maximo = Cm(18)
        if cy > maximo and cx:
            escala = maximo / cy
            for ext in imagem:
                ext.set("cx", str(int(cx * escala)))
                ext.set("cy", str(int(cy * escala)))
    return p
