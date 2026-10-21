"""Detalhe linha-a-linha de cada execucao de sincronizacao."""

import json

from odoo import fields, models


class HiperSyncRunLine(models.Model):
    """Uma linha por produto/registo processado num ``hiper.sync.run``.

    Permite auditoria do que aconteceu a cada produto: foi novo (``new``),
    matchado por barcode/reference/fingerprint, publicado, ignorado ou
    falhado. ``payload_json`` guarda a normalizacao do feed para debug;
    ``compare_data_json`` guarda os campos antes/depois para revisao.
    """

    _name = "hiper.sync.run.line"
    _description = "Hiper Sync Run Line"
    _order = "id"

    run_id = fields.Many2one(
        "hiper.sync.run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    vendor_id = fields.Many2one("hiper.sync.vendor", index=True)
    product_tmpl_id = fields.Many2one("product.template", index=True)
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("selected", "Selected"),
            ("published", "Published"),
            ("skipped", "Skipped"),
            ("error", "Error"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    selected = fields.Boolean(index=True)
    match_method = fields.Selection(
        [
            ("barcode", "Barcode"),
            ("reference", "Reference"),
            ("fingerprint", "Fingerprint"),
            ("new", "New Product"),
        ]
    )
    group_key = fields.Char(index=True)
    name = fields.Char()
    brand = fields.Char()
    ean13 = fields.Char(index=True)
    reference = fields.Char(index=True)
    quantity = fields.Float()
    unit_price = fields.Float()
    wholesale_price = fields.Float()
    payload_json = fields.Text()
    compare_data_json = fields.Text()
    publish_note = fields.Text()
    error_message = fields.Text()

    def payload(self):
        self.ensure_one()
        if not self.payload_json:
            return {}
        return json.loads(self.payload_json)
