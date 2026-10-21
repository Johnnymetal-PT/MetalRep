#!/usr/bin/env python3
"""
Gera um template PowerPoint reutilizavel para a Parametro Global.

Dependencias:
    pip install python-pptx pillow

Uso:
    python create_parametro_powerpoint_template.py --logo logo_preto.webp --out Template_Parametro_PowerPoint_Completo.pptx

Notas:
- O ficheiro gerado fica com capa branca, logo preto, cabecalhos/rodapes e layouts base.
- Tambem cria uma copia .potx se for indicado --potx.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Cm, Pt

# Paleta Parametro Global
BLUE = RGBColor(0, 148, 233)
DARK = RGBColor(21, 29, 43)
TEXT = RGBColor(31, 41, 55)
MUTED = RGBColor(100, 116, 139)
LIGHT_LINE = RGBColor(213, 226, 238)
LIGHT_BLUE = RGBColor(235, 247, 255)
WHITE = RGBColor(255, 255, 255)
BLACK = RGBColor(0, 0, 0)
GREEN = RGBColor(22, 163, 74)
ORANGE = RGBColor(249, 115, 22)
RED = RGBColor(239, 68, 68)

SLIDE_W = Cm(33.867)
SLIDE_H = Cm(19.05)


def prepare_logo(logo_path: str | None) -> str | None:
    if not logo_path:
        return None
    src = Path(logo_path)
    if not src.exists():
        return None
    suffix = src.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg"}:
        return str(src)
    img = Image.open(src).convert("RGBA")
    tmp = Path(tempfile.gettempdir()) / "parametro_logo_tmp.png"
    img.save(tmp)
    return str(tmp)


def set_text(box, text: str, size: int = 18, bold: bool = False, color=TEXT, font="Aptos"):
    tf = box.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = font
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    return p


def add_text(slide, text, x, y, w, h, size=18, bold=False, color=TEXT, align=None):
    box = slide.shapes.add_textbox(x, y, w, h)
    p = set_text(box, text, size=size, bold=bold, color=color)
    if align:
        p.alignment = align
    return box


def add_footer(slide, doc_label="[Documento] | [Ano]", page="02"):
    # linha superior do rodape
    line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Cm(1.1), Cm(17.75), Cm(31.6), Cm(0.03))
    line.fill.solid(); line.fill.fore_color.rgb = LIGHT_LINE
    line.line.color.rgb = LIGHT_LINE
    add_text(slide, doc_label, Cm(1.1), Cm(18.05), Cm(8), Cm(0.35), size=7, color=MUTED)
    add_text(slide, page, Cm(31.8), Cm(18.03), Cm(0.8), Cm(0.35), size=8, bold=True, color=BLUE, align=PP_ALIGN.RIGHT)


def add_header(slide, title="[Titulo]", subtitle="[Descricao curta da pagina]", logo=None, page="02"):
    add_text(slide, title, Cm(1.4), Cm(1.05), Cm(22), Cm(0.9), size=24, bold=True, color=DARK)
    add_text(slide, subtitle, Cm(1.4), Cm(2.25), Cm(20), Cm(0.45), size=8, color=MUTED)
    line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Cm(1.1), Cm(3.15), Cm(31.6), Cm(0.03))
    line.fill.solid(); line.fill.fore_color.rgb = LIGHT_LINE
    line.line.color.rgb = LIGHT_LINE
    if logo:
        slide.shapes.add_picture(logo, Cm(28.3), Cm(0.35), width=Cm(3.6))
    add_footer(slide, page=page)


def add_cover(prs, logo=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    if logo:
        slide.shapes.add_picture(logo, Cm(2.3), Cm(1.1), width=Cm(7.8))
    # canto superior direito preto
    corner = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.PIE, Cm(28.4), Cm(0.1), Cm(4.6), Cm(4.6))
    corner.fill.solid(); corner.fill.fore_color.rgb = BLACK
    corner.line.color.rgb = BLACK
    corner.rotation = 270
    # conteudo
    add_text(slide, "Receipt Split (pg_pdf)", Cm(2.2), Cm(5.6), Cm(15), Cm(0.75), size=26, color=BLUE)
    add_text(slide, "Manual de Utilizacao e Documentacao Tecnica", Cm(2.2), Cm(7.0), Cm(21), Cm(0.7), size=20, bold=True, color=BLACK)
    add_text(slide, "Modulo Odoo 17 para processamento de recibos em lote, geracao de PDFs individuais e upload\nFTP/FTPS/SFTP.", Cm(2.2), Cm(8.35), Cm(20), Cm(1.0), size=11, color=TEXT)
    add_text(slide, "Preparado por Parametro Global", Cm(2.2), Cm(16.85), Cm(8), Cm(0.4), size=8, color=TEXT)
    bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Cm(0), Cm(18.25), SLIDE_W, Cm(0.8))
    bar.fill.solid(); bar.fill.fore_color.rgb = DARK
    bar.line.color.rgb = DARK
    return slide


def add_blank_content(prs, logo=None, page="02"):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid(); slide.background.fill.fore_color.rgb = WHITE
    add_header(slide, page=page, logo=logo)
    return slide


def add_table_slide(prs, logo=None, page="03"):
    slide = add_blank_content(prs, logo, page)
    add_text(slide, "[Tabela leve]", Cm(1.4), Cm(4.0), Cm(8), Cm(0.5), size=12, bold=True, color=BLUE)
    rows, cols = 5, 3
    table = slide.shapes.add_table(rows, cols, Cm(1.4), Cm(4.8), Cm(25), Cm(4.5)).table
    widths = [Cm(6), Cm(9), Cm(10)]
    for i, w in enumerate(widths):
        table.columns[i].width = w
    headers = ["Campo", "Descricao", "Resultado"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT_BLUE
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(9); p.font.bold = True; p.font.color.rgb = DARK
    for r in range(1, rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = "[Texto]"
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(9); p.font.color.rgb = TEXT
    return slide


def add_process_slide(prs, logo=None, page="04"):
    slide = add_blank_content(prs, logo, page)
    add_text(slide, "[Processo / fluxo]", Cm(1.4), Cm(4.0), Cm(8), Cm(0.5), size=12, bold=True, color=BLUE)
    labels = ["Entrada", "Processamento", "Validacao", "Entrega"]
    x = Cm(2.0)
    for i, label in enumerate(labels):
        box = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, x + Cm(i*7.3), Cm(7.0), Cm(5.3), Cm(1.4))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT_BLUE
        box.line.color.rgb = LIGHT_LINE
        add_text(slide, label, x + Cm(i*7.3)+Cm(0.3), Cm(7.35), Cm(4.7), Cm(0.4), size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)
        if i < len(labels)-1:
            add_text(slide, "→", x + Cm(i*7.3)+Cm(5.7), Cm(7.25), Cm(1), Cm(0.5), size=22, bold=True, color=BLUE)
    return slide


def add_gantt_slide(prs, logo=None, page="05"):
    slide = add_blank_content(prs, logo, page)
    add_text(slide, "[Gantt / planeamento]", Cm(1.4), Cm(4.0), Cm(8), Cm(0.5), size=12, bold=True, color=BLUE)
    # eixos simples
    y0 = Cm(5.2)
    for i in range(5):
        add_text(slide, f"Fase {i+1}", Cm(1.5), y0+Cm(i*1.25), Cm(4), Cm(0.4), size=9, color=TEXT)
        line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Cm(6.0), y0+Cm(i*1.25)+Cm(0.18), Cm(22), Cm(0.02))
        line.fill.solid(); line.fill.fore_color.rgb = LIGHT_LINE; line.line.color.rgb = LIGHT_LINE
    bars = [(6.2,5.25,5.0,BLUE),(9.5,6.5,6.2,GREEN),(14,7.75,5.5,ORANGE),(17.5,9.0,7.5,BLUE),(22,10.25,4.5,RED)]
    for x,y,w,col in bars:
        bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Cm(x), Cm(y), Cm(w), Cm(0.55))
        bar.fill.solid(); bar.fill.fore_color.rgb = col; bar.line.color.rgb = col
    return slide


def add_chart_slide(prs, logo=None, page="06"):
    slide = add_blank_content(prs, logo, page)
    add_text(slide, "[Indicadores / diagrama]", Cm(1.4), Cm(4.0), Cm(8), Cm(0.5), size=12, bold=True, color=BLUE)
    x0 = Cm(2.0)
    vals = [("PDF", 8, BLUE), ("OK", 10, GREEN), ("FTP", 7, ORANGE)]
    for i, (label, height, color) in enumerate(vals):
        x = x0 + Cm(i*5)
        bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, x, Cm(12.0-height*0.45), Cm(2.0), Cm(height*0.45))
        bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.color.rgb = color
        add_text(slide, label, x-Cm(0.2), Cm(12.3), Cm(2.4), Cm(0.5), size=12, bold=True, color=DARK, align=PP_ALIGN.CENTER)
    return slide


def build_pptx(out: str, logo_path: str | None, potx: str | None = None):
    logo = prepare_logo(logo_path)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    add_cover(prs, logo)
    add_blank_content(prs, logo, "02")
    add_table_slide(prs, logo, "03")
    add_process_slide(prs, logo, "04")
    add_gantt_slide(prs, logo, "05")
    add_chart_slide(prs, logo, "06")
    prs.save(out)
    if potx:
        shutil.copyfile(out, potx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logo", default="logo_preto.webp", help="Caminho para o logotipo preto")
    parser.add_argument("--out", default="Template_Parametro_PowerPoint_Completo.pptx")
    parser.add_argument("--potx", default="Template_Parametro_PowerPoint_Completo.potx")
    args = parser.parse_args()
    build_pptx(args.out, args.logo, args.potx)
    print(f"Gerado: {args.out}")
    if args.potx:
        print(f"Gerado: {args.potx}")


if __name__ == "__main__":
    main()
