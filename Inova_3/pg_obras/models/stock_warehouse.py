from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    location_type = fields.Selection(
        selection=[
            ("supplier", "Localização de Fornecedor"),
            ("view", "Ver"),
            ("internal", "Localização Interna"),
            ("customer", "Localização do Cliente"),
            ("inventory", "Perdas de Inventário"),
            ("production", "Produção"),
            ("transit", "Localização Transitória"),
        ],
        string="Tipo de Localização",
        required=True,
        default="internal",
    )
