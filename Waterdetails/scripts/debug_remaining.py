import sys
sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation

SRC = "c:/Projetos/Waterdetails/docs/WaterDetails.pptx"
p = Presentation(SRC)

# Slide 2 metric boxes and slide 4 investment rows
targets = {
    (1, "CaixaDeTexto 11"): "slide2 odoo-valor",
    (1, "CaixaDeTexto 13"): "slide2 acessos-valor",
    (1, "CaixaDeTexto 15"): "slide2 dias",
    (1, "CaixaDeTexto 19"): "slide2 total-1ano",
    (1, "CaixaDeTexto 20"): "slide2 recorrencia",
    (3, "CaixaDeTexto 11"): "slide4 servicos-detalhe",
    (3, "CaixaDeTexto 20"): "slide4 suporte",
    (3, "CaixaDeTexto 23"): "slide4 total-linha",
    (4, "CaixaDeTexto 13"): "slide5 cloud-detalhe",
    (4, "CaixaDeTexto 17"): "slide5 hardware-detalhe",
    (4, "CaixaDeTexto 21"): "slide5 servicos-detalhe",
    (4, "CaixaDeTexto 23"): "slide5 total-linha",
    (4, "CaixaDeTexto 28"): "slide5 exclusao",
}

for (si, sname), label in targets.items():
    slide = p.slides[si]
    for shape in slide.shapes:
        if shape.name == sname and shape.has_text_frame:
            full = "".join(pa.text for pa in shape.text_frame.paragraphs)
            print(f"[{label}] repr: {repr(full)}")
