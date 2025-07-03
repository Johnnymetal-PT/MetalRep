from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'


    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')

def create_from_ui(self, orders, draft=False):
    for order in orders:
        pos_order_data = order['data']
        payment_method_id = pos_order_data.get('payment_method_id')
        
        # Create the order and store the payment method ID
        pos_order = self.create({
            **pos_order_data,
            'payment_method_id': payment_method_id,
        })

    return super(PosOrder, self).create_from_ui(orders, draft)