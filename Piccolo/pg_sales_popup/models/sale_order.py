"""Popup informativo com o comentario interno do cliente.

Quando o comercial escolhe o ``partner_id`` numa ``sale.order``, esta
extensao injecta um ``warning`` Odoo (popup amarelo) com o texto do
campo ``res.partner.comment``, ja convertido de HTML para texto plano.
"""
from odoo import models, api
import re


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def _onchange_partner_comment_popup(self):
        if self.partner_id and self.partner_id.comment:
            html = self.partner_id.comment

            # Quebras de linha relevantes para texto plano: <br>, <br/>
            # e fim de paragrafo viram '\n' antes da limpeza geral.
            html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
            html = re.sub(r'</p\s*>', '\n', html, flags=re.IGNORECASE)

            # Remove qualquer outra tag HTML restante.
            plain_text = re.sub(r'<[^>]+>', '', html)

            # Colapsa quebras de linha repetidas e remove whitespace nas pontas.
            clean_comment = re.sub(r'\n+', '\n', plain_text).strip()

            return {
                'warning': {
                    'title': "Comentário do Cliente",
                    'message': clean_comment,
                }
            }
