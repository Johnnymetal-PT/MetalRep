# -*- coding: utf-8 -*-
{
    'name': 'PG A4 Label',
    'version': '1.0',
    'summary': 'Print A4 labels for all lines in stock.picking',
    'description': 'This module ensures one label is printed for each line in the stock.picking on A4 sheets.',
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
