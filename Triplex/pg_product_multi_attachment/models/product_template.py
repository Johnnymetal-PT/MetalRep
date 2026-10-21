# -*- coding: utf-8 -*-
"""
Extensoes no template de produto para gerir anexos partilhados entre variantes.

Modulo: pg_product_multi_attachment.
Ficheiro: pg_product_multi_attachment\models\product_template.py.
Modelo principal: product.template.
"""

###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """inherited product.template to add field"""
    _inherit = 'product.template'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments',
                                      help='Added product attachments')
