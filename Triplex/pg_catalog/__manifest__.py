{
    'name': 'PG Product Catalog',
    'version': '1.2',
    'category': 'Sales',
    'summary': 'Imprime catálogos de produto em PDF em várias versões (Standard, 255, USA, USA-EUR, Maison Dorée, NET 2026, NET DISPLAY 2026)',
    'description': """
PG Product Catalog
==================

Objetivo de negócio
-------------------
Gerar catálogos de produto em PDF, prontos a enviar a clientes/mercados diferentes, sem
montar o documento à mão. Existem várias versões consoante a tabela de preço/mercado.

Pré-requisitos
--------------
- Módulos: `product`.
- Produtos com imagem, preço e atributos preenchidos (é o que alimenta o catálogo).
- Permissões definidas em security/ir.model.access.csv.

Como funciona
-------------
Estende `product.template` com vários botões de impressão, um por versão do catálogo:
- `action_print_catalog`            -> versão Standard
- `action_print_catalog_255`        -> versão "255"
- `action_print_catalog_usa`        -> versão USA
- `action_print_catalog_usaeur`     -> versão USA - EUR
- `action_print_catalog_usaeur16`   -> versão USA - EUR 16
- `action_print_catalog_maisondoree`-> versão Maison Dorée
- `action_print_catalog_net2026`    -> versão NET 2026 (preço da variante x 1,2368; suplementos de tecido sem acréscimo)
- `action_print_catalog_netdisplay2026` -> versão NET DISPLAY 2026 (preço da variante, sem acréscimo)
Cada botão dispara a respetiva ação de relatório (report/*.xml) para os produtos
selecionados. Os templates QWeb estão divididos em "pdf" (documento) e "pages" (páginas).

Passo a passo de utilização
---------------------------
1. Na lista de produtos, selecionar os produtos a incluir no catálogo.
2. No menu de ação/impressão, escolher a versão de catálogo pretendida.
3. O PDF é gerado com os produtos selecionados nessa versão.

Exemplo prático
---------------
Selecionar 20 produtos -> "Imprimir Catálogo (USA - EUR)" gera um PDF com esses 20 produtos
formatados para o mercado USA com preços em EUR.

FAQ / Resolução de problemas
----------------------------
- P: Dá erro "No products selected".
  R: É preciso selecionar pelo menos um produto antes de imprimir.
- P: Faltam preços/atributos no catálogo.
  R: O catálogo reflete os dados do produto; preencher imagem, preço e atributos em falta.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- O método `compute_catalog_prices` está incompleto (devolve sempre lista vazia) — parece
  código não terminado; o cálculo de preços do catálogo é feito nos templates.
- As várias versões correspondem a mercados/tabelas distintos; manter os templates alinhados.
""",
    'author': 'Your Name',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'report/product_template_pdf.xml',
        'report/product_template_pdf_255.xml',
        'report/product_template_pdf_usa.xml',
        'report/product_template_pdf_usaeur.xml',
        'report/product_template_pdf_usaeur16.xml',
        'report/product_template_pages.xml',
        'report/product_template_pages_255.xml',
        'report/product_template_pages_usa.xml',
        'report/product_template_pages_usaeur.xml',
        'report/product_template_pages_usaeur16.xml',
        'report/product_template_pdf_maisondoree.xml',
        'report/product_template_pages_maisondoree.xml',
        'report/product_template_pdf_net2026.xml',
        'report/product_template_pages_net2026.xml',
        'report/product_template_pdf_netdisplay2026.xml',
        'report/product_template_pages_netdisplay2026.xml',
        'report/product_template_report_action.xml'
    ],
    'installable': True,
    'application': False,
}

