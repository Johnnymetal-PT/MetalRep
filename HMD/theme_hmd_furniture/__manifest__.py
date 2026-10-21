{
    "name": "HMD Furniture Theme",
    "summary": "Tema do website HMD Furniture a partir do desenho XD de Monica Hedderich",
    "description": """
HMD Furniture — tema do website
================================

Implementa o desenho aprovado (Adobe XD, Agosto 2026) para o website da
HMD Furniture: barra de topo, cabecalho com mega-menu de categorias,
paginas editoriais e pagina de produto de e-commerce.

Fontes do desenho em ``Website_Design/`` (SVG e PDF, desktop 1920px e
mobile 393px).
""",
    "category": "Theme/Creative",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://parametro.global",
    "license": "LGPL-3",
    "depends": [
        "website",
        "website_sale",
        "website_sale_wishlist",
        "website_sale_comparison",
        # A pagina /fabrics agrupa por familia e liga a pagina de
        # especificacoes; ambas vem deste modulo.
        "hmd_website_fabrics",
        # O formulario de pedido de conta escreve nos campos que este modulo
        # acrescenta ao crm.lead — sem ele o website recusa esses campos.
        "hmd_partner_request",
    ],
    "data": [
        "views/layout.xml",
        "views/pages.xml",
        "views/shop.xml",
        "views/snippet_options.xml",
    ],
    "assets": {
        # append (nao prepend): primary_variables.scss faz map-merge sobre
        # $o-color-palettes e $o-theme-font-configs, que sao definidos em
        # website/static/src/scss/primary_variables.scss. A prepend corre
        # antes dessas definicoes e a compilacao do bundle falha com
        # "Undefined variable", deixando o site inteiro sem CSS.
        "web._assets_primary_variables": [
            "theme_hmd_furniture/static/src/scss/primary_variables.scss",
        ],
        "web.assets_frontend": [
            "theme_hmd_furniture/static/src/scss/tokens.scss",
            "theme_hmd_furniture/static/src/scss/layout.scss",
            "theme_hmd_furniture/static/src/scss/pages.scss",
            "theme_hmd_furniture/static/src/scss/shop.scss",
            "theme_hmd_furniture/static/src/js/hmd_navigation.js",
            "theme_hmd_furniture/static/src/js/hmd_fabrics.js",
            "theme_hmd_furniture/static/src/js/hmd_product_configurator.js",
        ],
    },
    "images": ["static/description/cover.png"],
    "installable": True,
    "application": False,
}
