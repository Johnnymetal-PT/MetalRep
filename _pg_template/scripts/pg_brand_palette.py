#!/usr/bin/env python3
"""
Paleta da marca Parâmetro Global — fonte única para todos os formatos.

PORQUE EXISTE

    A regra da identidade visual do `AGENTS_SHARED.md` diz que dois documentos gerados
    em projetos diferentes têm de sair iguais. Até 2026-09-11 havia **duas paletas**, e
    divergiam:

        pg_pptx_identity.py   azul de acento  #009FE3
        pg_docx_identity.py   azul de acento  #0094E9

    Cada módulo declarava o seu próprio ficheiro-fonte — o template PowerPoint e o
    template Word da marca — pelo que a divergência parecia legítima. Não é.

FONTE DE VERDADE, E A PROVA

    Amostradas as cores efetivamente usadas no conteúdo dos dois ficheiros da marca
    (2026-09-11, contando ocorrências no XML):

        doc_templates/assets/Template_Parametro_PowerPoint_Completo 1.pptx
            #111827 x58   #E7EEF5 x41   #64748B x35   #009FE3 x30

        doc_templates/assets/Template_Parametro_Word.docx
            #121A26 x47   #4F81BD x46   #D3DFEE x28   #EFD3D2 x28

    O `#4F81BD` é o **accent1 do tema de fábrica do Office 2007**, não uma cor da marca;
    e o tema (`theme1.xml`) de ambos os ficheiros traz os esquemas de fábrica do Office,
    diferentes entre si. Ou seja: **a identidade Parâmetro vive no conteúdo do template
    PowerPoint**, e o template Word está em grande parte por marcar.

    Daí esta paleta ser a do PowerPoint. E daí o `#0094E9` do módulo Word não
    corresponder a nenhum dos dois ficheiros — é um valor aproximado, e é o defeito que
    este módulo fecha.

REGRA DE UTILIZAÇÃO

    Nenhum gerador define cores por sua conta. Quem precisar de uma cor importa-a daqui.
    Se faltar uma, acrescenta-se aqui — com a evidência de onde veio — para que todos os
    formatos a passem a ter.

Dependências: nenhuma além da biblioteca standard.
"""
from __future__ import annotations

# --- cores da marca, em hexadecimal ------------------------------------------
# Os nomes são os papéis, não as cores: quem lê "ACENTO" sabe o que está a usar, e a cor
# pode mudar sem que o código que a consome tenha de mudar.

ACENTO = "009FE3"        # azul da marca — barras, numeração, cabeçalhos de tabela
TITULO_CAPA = "0099FF"   # azul do título de capa (mais saturado, só na capa)
TINTA = "111827"         # texto principal e títulos
BARRA_ESCURA = "111E2D"  # barra inferior da capa, fundos escuros
CORPO = "4B5563"         # texto corrente sobre fundo claro
SUAVE = "64748B"         # texto secundário, legendas, rodapés
CLARO = "E7EEF5"         # fundos de realce, linhas alternadas
LINHA = "CBD5E1"         # bordas e separadores
BRANCO = "FFFFFF"

# Semáforo — usado em estados e indicadores. Amostrados do mesmo ficheiro da marca.
VERDE = "16A34A"
LARANJA = "F97316"


def para_rgb(hexadecimal: str):
    """(r, g, b) a partir de 'RRGGBB'. Para python-docx e python-pptx."""
    valor = hexadecimal.lstrip("#")
    if len(valor) != 6:
        raise ValueError("Cor hexadecimal invalida: %r" % (hexadecimal,))
    return tuple(int(valor[i:i + 2], 16) for i in (0, 2, 4))


def para_css(hexadecimal: str) -> str:
    """'#RRGGBB' — para HTML/CSS, no caminho do PDF."""
    return "#" + hexadecimal.lstrip("#").upper()
