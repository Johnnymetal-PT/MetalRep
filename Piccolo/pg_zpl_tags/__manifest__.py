# -*- coding: utf-8 -*-
# OBSOLETO - Nao usar este modulo em novas instalacoes.
# Substituido por: pg_zpl_tags_2
#
# Diferenca face ao substituto:
#   - pg_zpl_tags (v1.0) so tem models/views de base para impressao ZPL.
#   - pg_zpl_tags_2 (v2.0) acrescenta um wizard (`wizard/zpl_tags_wizard.py`)
#     que permite parametrizar a impressao da etiqueta antes do envio.
#
# Mantido apenas por referencia historica.
{
    'name': 'PG ZPL TAGS (OBSOLETO - usar pg_zpl_tags_2)',
    'version': '1.0',
    'summary': '[OBSOLETO] Substituido por pg_zpl_tags_2. Imprimir etiquetas ZPL.',
    'description': """
        OBSOLETO
        ========
        Este modulo foi substituido por **pg_zpl_tags_2**, que e a versao
        atual (v2.0) e mantida.

        Substituto: ``pg_zpl_tags_2``

        Diferenca principal:
        - pg_zpl_tags_2 acrescenta um wizard que permite parametrizar a
          impressao da etiqueta ZPL antes do envio (quantidade, formato,
          etc.). Esta versao apenas dispara a impressao direta.

        Nao instalar este modulo em ambientes novos. Migrar para
        pg_zpl_tags_2.
    """,
    'author': 'PG',
    'website': 'https://www.parametro.pt',

    'depends': ['sale_stock'],

    'assets': {
        'point_of_sale._assets': [
            'pg_zpl_tags/static/src/description/*',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/zpl_tags.xml',
    ],
    'installable': True,
    'application': False
}
