"""Features tecnicas (chave/valor) importadas dos feeds dos fornecedores."""

from odoo import fields, models


class HiperProductFeatureLine(models.Model):
    """Caracteristica adicional do produto (e.g. "Cor: preto", "RAM: 16GB").

    Modelo simples chave/valor traduzivel. E populado pelo ``publisher`` quando
    o adapter normaliza features do feed.
    """

    _name = "hiper.product.feature.line"
    _description = "Hiper Product Feature"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(required=True, translate=True)
    value = fields.Text(translate=True)
