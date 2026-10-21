# -*- coding: utf-8 -*-
{
    'name': 'PG A4 Label',
    'version': '1.0',
    'summary': 'Imprime etiquetas A4 (uma por linha) a partir de uma transferência de stock',
    'description': """
PG A4 Label
===========

Objetivo de negócio
-------------------
Permitir imprimir, em folha A4, uma etiqueta por cada linha de uma transferência de stock
(stock.picking) — por exemplo, na receção/expedição de mercadoria.

Pré-requisitos
--------------
- Módulos: `stock`.
- Impressora capaz de imprimir A4 (qualquer impressora normal serve).
- A ação de relatório `pg_a4_label.action_report_stock_picking_labels` registada
  (vem do reports/stock_picking_label_report.xml).

Como funciona
-------------
- `report.product.report_simple_label4x7` (AbstractModel): modelo de relatório QWeb que,
  em `_get_report_values`, devolve os pickings como `docs` para o template.
- `stock.picking.print_labels()`: dispara a ação de relatório
  `pg_a4_label.action_report_stock_picking_labels` para os pickings selecionados.
- Template do relatório em reports/stock_picking_label_report.xml.

Passo a passo de utilização
---------------------------
1. Abrir uma transferência de stock (receção/expedição) ou selecionar várias na lista.
2. Chamar a ação `print_labels` (via botão na vista — ATENÇÃO: a vista está comentada no
   manifesto; pode ter de ser ativada ou disparada por ação de servidor).
3. O Odoo gera um PDF A4 com uma etiqueta por linha do(s) picking(s).
4. Imprimir.

Exemplo prático
---------------
Picking de receção com 5 linhas (5 produtos diferentes) -> o relatório produz 5 etiquetas
em folha(s) A4, com a informação de cada linha.

FAQ / Resolução de problemas
----------------------------
- P: Não vejo o botão "Imprimir etiquetas" no picking.
  R: A view `views/stock_picking_views.xml` está comentada no manifesto; descomentá-la ou
     chamar o método via ação de servidor.
- P: O PDF sai vazio.
  R: Confirmar que o template `report_simple_label4x7` está carregado e que o picking tem
     linhas com produto.
- P: Tenho dois módulos de etiquetas A4. Qual usar?
  R: Existe também `PG_Etiquetas_A4`; validar qual está em uso no projeto e desinstalar o
     que não estiver a ser usado para evitar confusão.

Pontos de atenção
-----------------
- A view com o botão está comentada no manifesto; o `print_labels` não é chamado por UI
  standard sem ativar a vista.
- Sobrepõe-se conceptualmente ao módulo `PG_Etiquetas_A4`.
""",
    'author': 'Your Name',
    'depends': ['stock'],
    'data': [
        'reports/stock_picking_label_report.xml',
        #'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
