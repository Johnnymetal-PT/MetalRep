# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    """
    Inherit res.config.settings to add website configuration options
    for displaying product sales count and selecting the time range
    for sold out product statistics on the website.
    """
    _inherit = 'res.config.settings'

    active_last_month_count = fields.Boolean(
        related='website_id.active_last_month_count',
        string='Product Sales Count',
        help='This is used to show the sold out product count in the website.',
        readonly=False
    )
    time_range = fields.Selection([
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
    ], string='Time Range', default='last_month',
       config_parameter='atharva_theme_base.product_sales_count_time_range',
       help='Select the time range for the sold out product.\n\n')
