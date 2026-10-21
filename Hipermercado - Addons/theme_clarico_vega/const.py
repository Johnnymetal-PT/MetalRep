# -*- coding: utf-8 -*-

from . import const

const.SNIPPET_DEFAULTS.update({
    'theme_clarico_vega.s_dynamic_snippet_category': {
        'template_key': 'theme_clarico_vega.dynamic_filter_template_product_public_category_style_1',
        'data_attributes': {
            'snippet': 's_dynamic_snippet_category',
            'carousel-interval': '5000',
            'product-category-id': 'all',
            'number-of-elements': '4',
            'number-of-elements-small-devices': '2',
            'show-variants': 'true',
        },
        'add_classes': [
            'o_wsale_products_opt_design_cards',
            'o_wsale_products_opt_has_comparison',
            {
                's_dynamic_snippet_title': 's_dynamic_snippet_title_aside col-lg-3 flex-lg-column justify-content-lg-start',
            },
        ],
        'remove_classes': [
            'o_wsale_products_opt_design_thumbs',
            'o_wsale_products_opt_has_description',
        ],
    },
    'theme_clarico_vega.s_dynamic_snippet_brands': {
        'template_key': 'theme_clarico_vega.dynamic_filter_template_product_brand_brands_item',
        'data_attributes': {
            'snippet': 's_dynamic_snippet_brands',
            'carousel-interval': '5000',
            'product-category-id': 'all',
            'number-of-elements': '4',
            'number-of-elements-small-devices': '2',
            'show-variants': 'true',
        },
        'add_classes': [
            'o_wsale_products_opt_design_cards',
            'o_wsale_products_opt_has_comparison',
            {
                's_dynamic_snippet_title': 's_dynamic_snippet_title_aside col-lg-3 flex-lg-column justify-content-lg-start',
            },
        ],
        'remove_classes': [
            'o_wsale_products_opt_design_thumbs',
            'o_wsale_products_opt_has_description',
        ],
    },
})
