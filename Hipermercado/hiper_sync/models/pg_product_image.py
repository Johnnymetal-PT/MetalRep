"""Extensao a ``product.image`` para guardar a URL origem da imagem importada."""

from odoo import fields, models


class PgProductImage(models.Model):
    """Acrescenta ``pg_source_url`` a ``product.image``.

    Necessario para ``product.template._apply_pg_hiper_extra_media`` reconciliar
    imagens existentes com as URLs do feed (sem este campo, cada sync poderia
    criar duplicados em vez de reutilizar registos).
    """

    _inherit = "product.image"

    pg_source_url = fields.Char(index=True, readonly=True, copy=False)
