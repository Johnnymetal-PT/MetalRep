{
    'name': 'Lusosofá — Identidade do Website',
    'summary': 'Paleta preto e dourado, tipografia e componentes do website da Lusosofá.',
    'description': """
Identidade visual do website da Lusosofá
========================================

Define a paleta, a tipografia e os componentes do website a partir do logótipo
da marca. O dourado ``#84703F`` é o que está no próprio ficheiro do logótipo;
a variante clareada ``#C8B074`` existe porque o dourado da marca sobre preto
dá 4,1:1 e chumba o critério AA para texto corrido.

Referências de implementação (Odoo 18.0):

* ``addons/web_editor/static/src/scss/web_editor.variables.scss`` — ``$o-color-palettes``
* ``addons/website/static/src/scss/primary_variables.scss`` — ``$o-theme-font-configs``,
  ``$o-website-values-palettes``, ``$o-selected-color-palettes-names``
""",
    'version': '18.0.5.1.0',
    'category': 'Website/Website',
    'author': 'Parâmetro Global',
    'website': 'https://www.parametro.global',
    'license': 'LGPL-3',
    'depends': ['website', 'website_sale'],
    'data': [
        'views/sem_publicidade_fornecedor.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'pg_lusosofa_theme/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'pg_lusosofa_theme/static/src/scss/theme.scss',
            'pg_lusosofa_theme/static/src/js/pg_movimento.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
