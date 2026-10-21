from odoo import fields, models


class ProductTag(models.Model):
    _inherit = 'product.tag'

    hmd_project_page_url = fields.Char(
        string='Project Page URL',
        help='Website URL for the project page linked to this tag.',
    )

