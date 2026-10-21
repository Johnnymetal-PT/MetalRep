{
    'name': 'PG_Etiquetas_A4',
    'version': '2.0',
    'category': 'Inventory',
    'summary': 'Botões para imprimir etiquetas/documentos A4 a partir de produtos, picking e venda',
    'description': """
PG Etiquetas A4
===============

Objetivo de negócio
-------------------
Permitir imprimir, em A4, etiquetas de produto e documentos (incl. variante "Mythica") a
partir de vários ecrãs: ficha de produto (template e variante), transferências de stock e
encomendas de venda. As etiquetas incluem detalhes do produto, logótipos, etc.

Pré-requisitos
--------------
- Módulos: `base`, `product`, `stock`, `sale`.
- Relatórios criados com os NOMES exatos: "Etiquetas A4" (para produto), "Etiqueta A4" e
  "Etiqueta Mythica A4" (para picking). Os do módulo são carregados pelo manifesto.
- Para a venda: relatórios Studio (`studio_customization.*`) com os UUID referenciados no
  código têm de existir nesta BD.

Como funciona
-------------
Acrescenta o método `action_print_a4_report` (e variante `_mythica`) a vários modelos:
- `product.template` e `product.product`: imprimem o relatório com nome "Etiquetas A4".
- `stock.picking`: imprime "Etiqueta A4" (e "Etiqueta Mythica A4" na variante).
- `sale.order`: dispara relatórios do Odoo Studio (procurados por `report_name`).
Os botões que chamam estes métodos estão nas views deste módulo; os templates QWeb das
etiquetas estão em views/report_*.xml e reports/report_*.xml.

Passo a passo de utilização
---------------------------
1. Abrir uma ficha de produto / picking / encomenda de venda.
2. Carregar no botão "Imprimir Etiqueta A4" (ou "Mythica") adicionado pelo módulo.
3. O Odoo gera o PDF correspondente; imprimir em A4.
4. (Para venda) Os relatórios Studio devem estar publicados na BD para os botões funcionarem.

Exemplo prático
---------------
Selecionar 10 produtos na lista -> "Imprimir Etiqueta A4" gera um PDF com 10 etiquetas
formatadas para A4. Num picking, "Imprimir Etiqueta Mythica A4" gera a versão Mythica do
documento de expedição.

FAQ / Resolução de problemas
----------------------------
- P: Erro "AttributeError: 'NoneType' object has no attribute 'report_action'".
  R: O relatório com o NOME procurado não existe. Confirmar que se chama exatamente
     "Etiquetas A4" / "Etiqueta A4" / "Etiqueta Mythica A4" conforme o caso.
- P: O botão na venda não imprime nada.
  R: O `report_name` aponta para um UUID Studio fixo; esse relatório tem de existir na BD.
- P: Tenho `pg_a4_label` instalado também — qual usar?
  R: Validar qual está realmente em uso; desinstalar o outro para evitar duplicação.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Os relatórios de produto/picking são procurados pelo NOME visível — frágil a renomeações.
- Os de venda dependem de UUIDs `studio_customization.*` fixos no código.
- O nome da pasta do módulo é `PG_Etiquetas_A4` (maiúsculas), fora da convenção `pg_*`.
- Sobrepõe-se conceptualmente a `pg_a4_label`.
""",
    'author': 'Parametro Global',
    'website': 'http://www.parametroglobal.pt',

    'depends': ['base', 'product', 'stock', 'sale'],
    
    'data': [
        'views/product_template_view.xml',
        'views/product_product_view.xml',
        'views/stock_picking_view.xml',
        'views/report_product_labels_a4.xml',
        'reports/report_stock_template.xml',
        'reports/report_stock_product.xml',
        'reports/report_stock_picking.xml',
    ],
    
    'installable': True,
    'application': False,
    'auto_install': False,
}
