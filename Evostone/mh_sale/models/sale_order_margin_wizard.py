from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class SaleOrderMarginWizard(models.TransientModel):
    _name = 'sale.order.margin.wizard'
    _description = 'Aviso de Margem Não Positiva ao Confirmar'

    order_id = fields.Many2one(
        'sale.order',
        string='Cotação',
        required=True,
        readonly=True
    )

    confirmation_message = fields.Text(
        string='Aviso',
        readonly=True
    )

    line_ids = fields.Many2many(
        'sale.order.line',
        string='Linhas com margem ≤ 0',
        readonly=True
    )

    def action_confirm_margin(self):
        """Confirmar a venda apesar de linhas com margem ≤ 0.

        Só um aprovador pode forçar. Regista no chatter quais as linhas
        e re-chama action_confirm a saltar este aviso.
        """
        self.ensure_one()

        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_(
                'Apenas um administrador de vendas pode confirmar uma venda '
                'com margem ≤ 0.\n'
                'Contacte um administrador de vendas.'
            ))

        order = self.order_id

        linhas_html = ''.join(
            '<li>%s — Qtd %s × %.2f | Custo %.2f → <b>Margem %.2f (%.2f%%)</b></li>' % (
                line.product_id.display_name,
                line.product_uom_qty,
                line.price_unit,
                line.purchase_price,
                line.margin_amount,
                line.margin_percent * 100,
            )
            for line in self.line_ids
        )

        order.message_post(
            body=Markup(
                '<p><b>Venda confirmada com margem ≤ 0 por %s.</b></p>'
                '<p>Linhas abaixo do custo ou com custo por apurar:</p>'
                '<ul>%s</ul>' % (self.env.user.name, linhas_html)
            ),
            subject='Confirmação com margem não positiva'
        )

        return order.with_context(skip_margin_check=True).action_confirm()
