"""Propagacao de dados da Sale Order para o Stock Picking.

Reconstroi a cadeia ``Picking -> PO -> MO -> SO`` percorrendo o campo
``origin`` em cada salto e copia ``partner_id``, ``client_order_ref``
e ``name`` da SO para tres campos pesquisaveis no Picking.

Os campos mantem o prefixo ``x_studio_`` por compatibilidade com vistas
Studio antigas - nao renomear sem migration coordenada.
"""
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_studio_cliente_1 = fields.Many2one(
        'res.partner', string="Cliente",
        compute='_compute_so_fields', store=True,
    )
    # NOTA: 'referncia' (sem 'e') e typo herdado de Studio. Manter literal -
    # qualquer renomeacao precisa migration nas views Studio que referenciam
    # este nome de campo.
    x_studio_referncia_do_cliente_2 = fields.Char(
        string="Ref Cliente",
        compute='_compute_so_fields', store=True,
    )
    x_studio_sale_order_name = fields.Char(
        string="Encomenda",
        compute='_compute_so_fields', store=True,
    )

    @api.depends('origin')
    def _compute_so_fields(self):
        for record in self:
            # Reset por defeito: se a cadeia falhar a meio, os campos ficam
            # explicitamente vazios em vez de manterem valor antigo.
            record.x_studio_cliente_1 = False
            record.x_studio_referncia_do_cliente_2 = False
            record.x_studio_sale_order_name = False

            if record.origin:
                # Passo 1: Picking.origin == PO.name (caso da receipt de uma compra)
                po = self.env['purchase.order'].search([('name', '=', record.origin)], limit=1)

                if po and po.origin:
                    # Passo 2: PO.origin == MO.name (compra gerada para uma producao)
                    mo = self.env['mrp.production'].search([('name', '=', po.origin)], limit=1)

                    if mo and mo.origin:
                        # Passo 3: MO.origin == SO.name (producao gerada pela venda)
                        so = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)

                        if so:
                            record.x_studio_cliente_1 = so.partner_id.id
                            record.x_studio_referncia_do_cliente_2 = so.client_order_ref
                            record.x_studio_sale_order_name = so.name
