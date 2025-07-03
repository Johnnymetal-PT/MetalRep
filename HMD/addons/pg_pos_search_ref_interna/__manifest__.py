{
    'name': 'PG POS Search Ref Interna',
    'version': '1.0',
    'summary': 'Search products in POS by internal custom reference',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pg_pos_search_ref_interna/static/src/js/product_search.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
