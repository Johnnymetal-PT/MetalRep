#!/usr/bin/env python3
"""
Gera um template Word reutilizavel para a Parametro Global.

Dependencias:
    pip install python-docx pillow

Uso:
    python create_parametro_word_template.py --logo logo_preto.webp --out Template_Parametro_Word_Completo.docx

Notas:
- O ficheiro gerado fica com capa branca, logo preto, cabecalhos/rodapes e estilos base.
- Tambem cria uma copia .dotx se for indicado --dotx.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BLUE = RGBColor(0, 148, 233)
DARK = RGBColor(21, 29, 43)
TEXT = RGBColor(31, 41, 55)
MUTED = RGBColor(100, 116, 139)
LIGHT_LINE = "D5E2EE"
LIGHT_BLUE = "EBF7FF"
BLACK_HEX = "000000"
DARK_HEX = "151D2B"


def prepare_logo(logo_path: str | None) -> str | None:
    if not logo_path:
        return None
    src = Path(logo_path)
    if not src.exists():
        return None
    if src.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        return str(src)
    img = Image.open(src).convert("RGBA")
    tmp = Path(tempfile.gettempdir()) / "parametro_logo_tmp.png"
    img.save(tmp)
    return str(tmp)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_border(cell, color="D5E2EE", size="4"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
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


def add_horizontal_line(paragraph, color=LIGHT_LINE, size="6"):
    p = paragraph._p
    p_pr = p.get_or_add_pPr()
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


def add_run(p, text, size=11, bold=False, color=TEXT):
    r = p.add_run(text)
    r.font.name = "Aptos"
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return r


def setup_doc_styles(doc: Document):
    styles = doc.styles
    for name, size, bold, color in [
        ("Normal", 10.5, False, TEXT),
        ("Title", 28, True, DARK),
        ("Heading 1", 18, True, DARK),
        ("Heading 2", 14, True, DARK),
        ("Caption", 8, False, MUTED),
    ]:
        s = styles[name]
        s.font.name = "Aptos"
        s.font.size = Pt(size)
        s.font.bold = bold
        s.font.color.rgb = color


def set_margins(section):
    section.top_margin = Cm(1.6)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.8)
    section.footer_distance = Cm(0.7)


def configure_header_footer(section, logo=None, doc_label="[Documento] | [Ano]"):
    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if logo:
        hp.add_run().add_picture(logo, width=Cm(3.2))
    p = header.add_paragraph()
    add_horizontal_line(p)

    footer = section.footer
    fp = footer.paragraphs[0]
    add_horizontal_line(fp)
    table = footer.add_table(rows=1, cols=2, width=Cm(17))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    left, right = table.cell(0,0), table.cell(0,1)
    left.width = Cm(12)
    right.width = Cm(5)
    add_run(left.paragraphs[0], doc_label, size=8, color=MUTED)
    rp = right.paragraphs[0]
    rp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_run(rp, "Página ", size=8, color=MUTED)
    # Campo PAGE
    fld_begin = OxmlElement('w:fldChar'); fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = 'PAGE'
    fld_end = OxmlElement('w:fldChar'); fld_end.set(qn('w:fldCharType'), 'end')
    r = rp.add_run()
    r._r.append(fld_begin); r._r.append(instr); r._r.append(fld_end)
    r.font.size = Pt(8); r.font.color.rgb = BLUE


def add_cover(doc: Document, logo=None):
    section = doc.sections[0]
    set_margins(section)
    p = doc.add_paragraph()
    if logo:
        p.add_run().add_picture(logo, width=Cm(7.5))
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph("\n")
    p = doc.add_paragraph()
    add_run(p, "Receipt Split (pg_pdf)", size=24, color=BLUE)
    p = doc.add_paragraph()
    add_run(p, "Manual de Utilização e Documentação Técnica", size=20, bold=True, color=DARK)
    p = doc.add_paragraph()
    add_run(p, "Módulo Odoo 17 para processamento de recibos em lote, geração de PDFs individuais e upload FTP/FTPS/SFTP.", size=11, color=TEXT)
    for _ in range(15):
        doc.add_paragraph("")
    p = doc.add_paragraph()
    add_run(p, "Preparado por Parâmetro Global", size=9, color=TEXT)
    p = doc.add_paragraph()
    add_horizontal_line(p, color=DARK_HEX, size="24")
    doc.add_section(WD_SECTION.NEW_PAGE)


def add_section_title(doc, title="[Título]", desc="[Descrição curta da página]"):
    p = doc.add_paragraph()
    add_run(p, title, size=18, bold=True, color=DARK)
    p = doc.add_paragraph()
    add_run(p, desc, size=9, color=MUTED)
    p = doc.add_paragraph()
    add_horizontal_line(p)


def add_light_table(doc):
    doc.add_paragraph("")
    table = doc.add_table(rows=4, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Campo", "Descrição", "Resultado"]
    for c, h in enumerate(headers):
        cell = table.cell(0,c)
        cell.text = h
        set_cell_shading(cell, LIGHT_BLUE)
        set_cell_border(cell)
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = DARK
    for r in range(1,4):
        for c in range(3):
            cell = table.cell(r,c)
            cell.text = "[Texto]"
            set_cell_border(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9); run.font.color.rgb = TEXT


def add_process(doc):
    p = doc.add_paragraph()
    add_run(p, "Processo / fluxo", size=13, bold=True, color=BLUE)
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    labels = ["Entrada", "Processamento", "Validação", "Entrega"]
    for i, label in enumerate(labels):
        cell = table.cell(0,i)
        cell.text = label
        set_cell_shading(cell, LIGHT_BLUE)
        set_cell_border(cell)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True; r.font.size = Pt(9); r.font.color.rgb = DARK


def add_gantt(doc):
    p = doc.add_paragraph()
    add_run(p, "Gantt / planeamento", size=13, bold=True, color=BLUE)
    table = doc.add_table(rows=6, cols=5)
    headers = ["Fase", "S1", "S2", "S3", "S4"]
    for c,h in enumerate(headers):
        table.cell(0,c).text = h
        set_cell_shading(table.cell(0,c), LIGHT_BLUE)
        set_cell_border(table.cell(0,c))
    for r in range(1,6):
        table.cell(r,0).text = f"Fase {r}"
        for c in range(5):
            set_cell_border(table.cell(r,c))
        for c in range(1,5):
            if c == ((r-1) % 4) + 1:
                table.cell(r,c).text = "■■■"
                set_cell_shading(table.cell(r,c), "DFF3EA")


def build_docx(out: str, logo_path: str | None, dotx: str | None = None):
    logo = prepare_logo(logo_path)
    doc = Document()
    setup_doc_styles(doc)
    add_cover(doc, logo)
    # aplicar cabecalho e rodape a todas as secoes interiores
    for s in doc.sections:
        set_margins(s)
    for idx, s in enumerate(doc.sections):
        if idx > 0:
            configure_header_footer(s, logo)
    # paginas modelo
    titles = ["[Título]", "[Tabela leve]", "[Processo]", "[Gantt]", "[Imagem / screenshot]", "[Indicadores]"]
    for i, title in enumerate(titles):
        if i > 0:
            doc.add_page_break()
        add_section_title(doc, title)
        if "Tabela" in title:
            add_light_table(doc)
        elif "Processo" in title:
            add_process(doc)
        elif "Gantt" in title:
            add_gantt(doc)
        elif "Imagem" in title:
            p = doc.add_paragraph("\n\n")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_run(p, "[Inserir imagem ou screenshot aqui]", size=11, color=MUTED)
        elif "Indicadores" in title:
            add_light_table(doc)
    doc.save(out)
    if dotx:
        shutil.copyfile(out, dotx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logo", default="logo_preto.webp", help="Caminho para o logotipo preto")
    parser.add_argument("--out", default="Template_Parametro_Word_Completo.docx")
    parser.add_argument("--dotx", default="Template_Parametro_Word_Completo.dotx")
    args = parser.parse_args()
    build_docx(args.out, args.logo, args.dotx)
    print(f"Gerado: {args.out}")
    if args.dotx:
        print(f"Gerado: {args.dotx}")


if __name__ == "__main__":
    main()
