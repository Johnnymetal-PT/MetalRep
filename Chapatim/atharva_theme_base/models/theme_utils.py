# -*- coding: utf-8 -*-

from odoo import api, models

class ThemeUtils(models.AbstractModel):
    _inherit = 'theme.utils'

    attribute_layout_templates = [
        'theme_alan.as_attribute_layout_1',
        'theme_alan.as_attribute_layout_2',
        'theme_alan.as_attribute_layout_3',
        'theme_alan.as_attribute_layout_4',
        'theme_alan.as_attribute_layout_5',
    ]

    @api.model
    def enable_view(self, xml_id):
        """Override of `theme.utils` to disable all sttribute style templates when enabling one."""
        if xml_id in self.attribute_layout_templates:
            for template in self.attribute_layout_templates:
                self.disable_view(template)
        super().enable_view(xml_id)
