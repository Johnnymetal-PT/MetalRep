{
    'name': 'PG Fabric Consumption V2',
    'version': '1.7',
    'summary': 'Controle automático de consumo de tecido - Versão V7 com correções',
    'sequence': 1,
    'description': """
        Versão V7 com correções importantes:
        - BOMs duplicadas mantêm origem na BOM original
        - Fornecedores são copiados para produtos duplicados
        - Validação antes de gerar ordem de fabricação
        - Verificação se variantes existem nas tabelas
    """,
    'category': 'Manufacturing',
    'author': 'Manus AI',
    'depends': ['mrp', 'stock', 'product', 'sale', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/fabric_variant_views.xml',
        'views/product_template_views.xml',
        #'views/mrp_bom_views.xml',
        'views/mrp_bom_form_view_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

