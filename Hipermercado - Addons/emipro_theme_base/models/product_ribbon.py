# -*- coding: utf-8 -*-
""" Inherit the product ribbon model"""

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

set_default = "set default"


class ProductRibbonEPT(models.Model):
    """
        This model is used to store custom product ribbon style on the product.
    """
    _inherit = "product.ribbon"
    html = fields.Html(string='Ribbon html', translate=True, sanitize=False, default='')
    products_count = fields.Integer('Product Count', compute='_compute_products_count',
                                    help='Number of product counts that configured to label')
    sequence = fields.Integer('Sequence', index=True, default=10)
    product_ids = fields.One2many('product.template', 'website_ribbon_id', 'Products')
    position = fields.Selection(selection_add=[('o_product_label_style_left_badge', 'Badge Left'),
                                               ('o_product_label_style_right_badge', 'Badge Right'),
                                               ('o_product_label_style_1_left', 'Vega Tag Left'),
                                               ('o_product_label_style_1_right', 'Vega Tag Right'),
                                               ('o_product_label_style_2_left', 'Vega Square Shadow Left'),
                                               ('o_product_label_style_2_right', 'Vega Square Shadow Right'),
                                               ('o_product_label_style_3_left', 'Vega Edge Left'),
                                               ('o_product_label_style_3_right', 'Vega Edge Right'),
                                               ('o_product_label_style_4_left', 'Vega Round Left'),
                                               ('o_product_label_style_4_right', 'Vega Round Right'),
                                               ('o_product_label_style_5_left', 'Vega Still Pill Left'),
                                               ('o_product_label_style_5_right', 'Vega Still Pill Right'),
                                               ('o_product_label_style_6_left', 'Vega Glass Left'),
                                               ('o_product_label_style_6_right', 'Vega Glass Right'),
                                               ('o_product_label_style_7_left', 'Vega Outline Left'),
                                               ('o_product_label_style_7_right', 'Vega Outline Right'),
                                               ('o_product_label_style_8_left', 'Vega Micro Minimal Left'),
                                               ('o_product_label_style_8_right', 'Vega Micro Minimal Right')],
                                default='left',
                                ondelete={"o_product_label_style_left_badge": set_default,
                                          "o_product_label_style_right_badge": set_default,
                                          "o_product_label_style_1_left": set_default,
                                          "o_product_label_style_1_right": set_default,
                                          "o_product_label_style_2_left": set_default,
                                          "o_product_label_style_2_right": set_default,
                                          "o_product_label_style_3_left": set_default,
                                          "o_product_label_style_3_right": set_default,
                                          "o_product_label_style_4_left": set_default,
                                          "o_product_label_style_4_right": set_default,
                                          "o_product_label_style_5_left": set_default,
                                          "o_product_label_style_5_right": set_default,
                                          "o_product_label_style_6_left": set_default,
                                          "o_product_label_style_6_right": set_default,
                                          "o_product_label_style_7_left": set_default,
                                          "o_product_label_style_7_right": set_default,
                                          "o_product_label_style_8_left": set_default,
                                          "o_product_label_style_8_right": set_default})

    @api.depends('product_ids')
    def _compute_products_count(self):
        for label in self:
            label.products_count = len(label.product_ids)

    def set_label_wizard(self):
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.label.config',
            'name': "Product Configuration",
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_label_id': self.id},
        }
        return action

    def clear_all_products(self):
        self.product_ids = None

    def _get_css_classes(self):
        """
        Return the CSS classes for this ribbon based on style and position,
        supporting both base and custom styles.
        """
        css_classes = ""

        # Base style logic
        match self.style:
            case 'ribbon':
                css_classes += "o_wsale_ribbon"
            case 'tag':
                css_classes += "o_wsale_badge"

        # Extended position logic
        position_map = {
            'left': 'o_left',
            'right': 'o_right',
            'o_product_label_style_left_badge': 'o_product_label_style_left_badge',
            'o_product_label_style_right_badge': 'o_product_label_style_right_badge',
            'o_product_label_style_1_left': 'o_product_label_style_1_left',
            'o_product_label_style_1_right': 'o_product_label_style_1_right',
            'o_product_label_style_2_left': 'o_product_label_style_2_left',
            'o_product_label_style_2_right': 'o_product_label_style_2_right',
            'o_product_label_style_3_left': 'o_product_label_style_3_left',
            'o_product_label_style_3_right': 'o_product_label_style_3_right',
            'o_product_label_style_4_left': 'o_product_label_style_4_left',
            'o_product_label_style_4_right': 'o_product_label_style_4_right',
            'o_product_label_style_5_left': 'o_product_label_style_5_left',
            'o_product_label_style_5_right': 'o_product_label_style_5_right',
            'o_product_label_style_6_left': 'o_product_label_style_6_left',
            'o_product_label_style_6_right': 'o_product_label_style_6_right',
            'o_product_label_style_7_left': 'o_product_label_style_7_left',
            'o_product_label_style_7_right': 'o_product_label_style_7_right',
            'o_product_label_style_8_left': 'o_product_label_style_8_left',
            'o_product_label_style_8_right': 'o_product_label_style_8_right'
        }

        css_classes += f" {position_map.get(self.position, 'o_right')}"
        return css_classes
