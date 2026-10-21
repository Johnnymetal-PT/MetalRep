# -*- coding: utf-8 -*-

#######################################################################################
# Theme Clarico Vega Module Manifest File.
#
# This file contains the metadata for the Theme Clarico Vega module, including:
#     - Module name, version, and category
#     - Summary and description
#     - Author and license information
#     - Dependencies on other modules
#     - Data, demo, and security files to load
#     - Application, install, and auto-install flags
#
# Odoo uses this file to identify, install, and manage the module.
#######################################################################################

{
    # Theme information
    'name': 'Theme Clarico Vega',
    'category': 'Theme/eCommerce',
    'summary': 'An Odoo eCommerce Solution with a lot of well-analized features. Suitable for all kind of eCommerce Businesses like Furniture, Fashion, Electronics, Beauty, Fitness, Jewelry, etc.',
    'version': '19.0.0.10',
    'license': 'OPL-1',
    'depends': ['emipro_theme_base', 'html_editor', 'website_sale_stock', 'website_mass_mailing',
                'website_sale_stock_wishlist', ],

    'data': [
        'data/category_snippet_template_data.xml',
        'data/brand_snippet_template_data.xml',
        'data/product_snippet_template_data.xml',
        'templates/header.xml',
        'templates/footer.xml',
        'templates/product.xml',
        'templates/shop.xml',
        'templates/cart_popover.xml',
        'templates/image_hotspot_popup.xml',
        'templates/brand_listing.xml',
        'templates/brand_page.xml',
        'templates/login_popup.xml',
        'templates/cart.xml',
        'templates/quick_view.xml',
        'templates/compare.xml',
        'templates/wishlist.xml',
        'templates/wishlist_collection_templates.xml',
        'templates/snippets/snippets.xml',
        'templates/snippets/s_dynamic_snippet_category.xml',
        'templates/snippets/s_dynamic_snippet_category_preview_data.xml',
        'templates/snippets/s_dynamic_snippet_brand.xml',
        'templates/snippets/emipro_static_snippet.xml',
        'templates/snippets/s_dynamic_snippet_brand_preview.xml',
        'templates/voice_search.xml',
        'templates/one_page_checkout.xml'
    ],

    'assets': {
        "portal.assets_chatter_style": [],
        'web._assets_frontend_helpers': [
            'theme_clarico_vega/static/lib/para_size.scss',
        ],
        'web.assets_frontend': [
            'theme_clarico_vega/static/lib/jquery-ui.min.js',
            'theme_clarico_vega/static/src/js/price_table.js',
            'theme_clarico_vega/static/src/scss/mixins.scss',
            'theme_clarico_vega/static/src/scss/header.scss',
            'theme_clarico_vega/static/src/scss/footer.scss',
            'theme_clarico_vega/static/src/js/frontend/owl.carousel.js',
            'theme_clarico_vega/static/src/js/frontend/theme_script.js',
            'theme_clarico_vega/static/src/js/frontend/categories_popover_view.js',
            'theme_clarico_vega/static/src/js/frontend/search_popover_view.js',
            'theme_clarico_vega/static/src/js/frontend/search_placeholder_carousel.js',
            'theme_clarico_vega/static/src/js/frontend/mixins.js',
            'theme_clarico_vega/static/src/js/frontend/wishlist_collection.js',
            'theme_clarico_vega/static/src/interactions/**/*',
            'theme_clarico_vega/static/src/xml/search_sidebar.xml',
            'theme_clarico_vega/static/src/xml/product_configurator_dialog.xml',
            'theme_clarico_vega/static/src/scss/owl.carousel.min.css',
            'theme_clarico_vega/static/src/scss/shop.scss',
            'theme_clarico_vega/static/src/scss/search.scss',
            'theme_clarico_vega/static/src/scss/cart.scss',
            'theme_clarico_vega/static/src/js/cart_popover.js',
            'theme_clarico_vega/static/src/scss/megamenu.scss',
            'theme_clarico_vega/static/src/scss/brand_listing.scss',
            'theme_clarico_vega/static/src/js/frontend/dynamic_menu.js',
            'theme_clarico_vega/static/src/scss/button_style.scss',
            'theme_clarico_vega/static/src/scss/login_popup.scss',
            'theme_clarico_vega/static/src/js/frontend/login_popup.js',
            'theme_clarico_vega/static/src/scss/product.scss',
            'theme_clarico_vega/static/src/js/frontend/similar_product_view.js',
            'theme_clarico_vega/static/src/scss/wishlist.scss',
            'theme_clarico_vega/static/src/scss/product_design_panel.scss',
            'theme_clarico_vega/static/src/js/frontend/quick_view.js',
            'theme_clarico_vega/static/src/scss/quick_view.scss',
            'theme_clarico_vega/static/src/scss/sale_label.scss',
            'theme_clarico_vega/static/src/snippets/**/*.js',
            'theme_clarico_vega/static/src/snippets/s_dynamic_snippet_brands/dynamic_snippet_brands.js',
            'theme_clarico_vega/static/src/scss/snippets.scss',
            # 'theme_clarico_vega/static/src/js/frontend/range_filter.js',
            'theme_clarico_vega/static/src/scss/hotspot.scss',
            'theme_clarico_vega/static/src/js/frontend/voice_search.js',
            'theme_clarico_vega/static/src/scss/age_verification.scss',
            'theme_clarico_vega/static/src/js/frontend/age_verification.js',
            'theme_clarico_vega/static/src/js/frontend/one_page_checkout.js',
        ],
        'website.assets_wysiwyg': [
            'theme_clarico_vega/static/lib/jquery-ui.min.js',
        ],
        'web_editor.assets_wysiwyg': [],
        'website.website_builder_assets': [
            ('include', 'html_builder.assets'),
            'theme_clarico_vega/static/src/builder/**/*',
            'theme_clarico_vega/static/src/website_builder/**/*',
        ],
        "web.assets_editor": [
            "theme_clarico_vega/static/src/builder/plugins/image/image_tool_option_plugin.js",
        ],
    },

    # Author
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'https://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'live_test_url': 'https://claricovega.theme19.demo.emiprotechnologies.com',

    'images': [
        'static/description/main_poster.jpg',
        'static/description/main_screenshot.gif',
    ],

    # Technical
    'installable': True,
    'auto_install': False,
    'price': 249.00,
    'currency': 'USD',
}
