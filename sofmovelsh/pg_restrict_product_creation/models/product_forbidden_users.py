"""Modelo da blocklist de emails que nao podem criar produtos.

Pertence ao modulo `pg_restrict_product_creation`. Port V17->V19:
- removido `name_get()` (removido em v17); `_rec_name='email'` chega para o
  display_name;
- unicidade do email garantida por SQL constraint (o kwarg `unique=True` num
  `fields.Char` nao criava constraint em BD).
"""
from odoo import models, fields


class ProductForbiddenUsers(models.Model):
    """Cada record representa um email bloqueado para criar produtos."""

    _name = 'product.forbidden.users'
    _description = 'List of Forbidden Users for Product Creation'
    _rec_name = 'email'

    email = fields.Char(string="Email", required=True)

    _email_unique = models.Constraint(
        'unique(email)',
        "Este email já está na lista de utilizadores bloqueados.",
    )
