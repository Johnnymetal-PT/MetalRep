# -*- coding: utf-8 -*-
"""
Propagacao de anexos de produto para linhas de venda.

Modulo: pg_product_multi_attachment.
Ficheiro: pg_product_multi_attachment\models\sale_order_line.py.
Modelo principal: sale.order.line.
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
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """inherited sale.order.line to add field"""
    _inherit = 'sale.order.line'

    attachment_ids = fields.Many2many('ir.attachment',
                                      string='Attachments',
                                      help='Product Attachments')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Ao escolher o produto, a linha herda os anexos desse produto.

        Tenta primeiro a variante (product_id); se não tiver anexos, usa os do template.
        """
        for line in self:
            attachment_ids = False
            if line.product_id:
                attachment_ids = line.product_id.attachment_ids.ids
            if attachment_ids:
                line.attachment_ids = [(6, 0, attachment_ids)]  # (6,0,ids) = substituir conjunto
            elif line.product_template_id:
                line.attachment_ids = [
                    (6, 0, line.product_template_id.attachment_ids.ids)]
