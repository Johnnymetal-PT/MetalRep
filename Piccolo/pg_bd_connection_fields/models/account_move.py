"""Campo de ligacao a fatura original na BD destino (Community).

O ``pg_bd_connection`` (BD origem PICCOLO) grava ``x_original_invoice_id``
na move replicada para guardar o id da move de origem. Esse campo so
existe na BD origem (definido em ``pg_bd_connection``); aqui declara-se o
espelho na BD destino (PICCOLO_COMMUNITY) para que:
- o ``create()`` da sincronizacao de faturas possa preenche-lo, e
- a sincronizacao de notas de credito possa localizar a fatura original
  ja replicada (e reconstruir a reversao com ligacao certificavel).
"""
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    # Id da move de origem em PICCOLO. Integer (nao Many2one) porque
    # referencia um registo de OUTRA base de dados.
    x_original_invoice_id = fields.Integer(
        string="Original Invoice ID",
        copy=False,
        index=True,
    )
