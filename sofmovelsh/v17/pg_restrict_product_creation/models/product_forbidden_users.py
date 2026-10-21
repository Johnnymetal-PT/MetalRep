"""Modelo da blocklist de emails que nao podem criar produtos.

Pertence ao modulo `pg_restrict_product_creation`. `email` esta marcado
`unique=True` ao nivel ORM (mostrar no UI), mas nao tem SQL constraint.
"""
from odoo import models, fields, api

class ProductForbiddenUsers(models.Model):
    """Cada record representa um email bloqueado para criar produtos."""

    _name = 'product.forbidden.users'
    _description = 'List of Forbidden Users for Product Creation'
    _rec_name = 'email'

    email = fields.Char(string="Email", required=True, unique=True)

    def name_get(self):
        # Mostra sempre o email como label, para leitura rapida em Many2one.
        return [(record.id, record.email or "Unknown") for record in self]
