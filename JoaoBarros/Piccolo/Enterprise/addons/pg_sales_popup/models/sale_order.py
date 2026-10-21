from odoo import models, api
import re

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_comment_popup(self):
        if self.partner_id and self.partner_id.comment:
            html = self.partner_id.comment

            # Replace <br>, <br/>, </p> with newline
            html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</p\s*>', '\n', html, flags=re.IGNORECASE)

            # Strip all other HTML tags
            plain_text = re.sub(r'<[^>]+>', '', html)

            # Normalize multiple line breaks and trim
            clean_comment = re.sub(r'\n+', '\n', plain_text).strip()

            return {
                'warning': {
                    'title': "Comentário do Cliente",
                    'message': clean_comment,
                }
            }

