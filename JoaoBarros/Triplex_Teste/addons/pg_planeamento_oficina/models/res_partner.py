# -*- coding: utf-8 -*-
from odoo import fields, models


SUPPLIER_TYPES = [
    ('tecido', 'Tecido'),
    ('casco', 'Casco'),
    ('polidor', 'Polidor'),
    ('inox', 'Inox / Metais'),
    ('embalagem', 'Embalagem'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_supplier_type = fields.Selection(
        SUPPLIER_TYPES,
        string='Tipo de Fornecedor',
        help="Categoria do fornecedor para o painel de planeamento da oficina. "
             "Usada para classificar os componentes de BOM nas colunas Tecido / "
             "Casco / Inox / Polidor / Embalagem.",
    )
