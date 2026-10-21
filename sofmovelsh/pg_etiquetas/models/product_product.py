from odoo import fields, models

from .product_template import (
    CAMPOS_CODIGO_BARRAS,
    CAMPOS_PRECO_ANTERIOR,
    CAMPOS_REFERENCIA,
)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    pg_label_type = fields.Selection(
        related='product_tmpl_id.pg_label_type',
        store=True,
        readonly=False,
    )

    # -- dados para as etiquetas -------------------------------------------
    # A variante tem referência e código de barras próprios; o preço anterior é do
    # artigo. Daí uns campos serem lidos aqui e outros delegados no template.

    def _pg_label_reference(self):
        self.ensure_one()
        return self._pg_primeiro_valor(CAMPOS_REFERENCIA)

    def _pg_label_barcode(self):
        self.ensure_one()
        return self._pg_primeiro_valor(CAMPOS_CODIGO_BARRAS)

    def _pg_primeiro_valor(self, nomes):
        self.ensure_one()
        for nome in nomes:
            if nome in self._fields and self[nome]:
                return self[nome]
        return ''

    def _pg_label_compare_price(self):
        self.ensure_one()
        for nome in CAMPOS_PRECO_ANTERIOR:
            if nome in self._fields and self[nome]:
                return self[nome]
        return self.product_tmpl_id._pg_label_compare_price()

    def _pg_label_pricelist(self):
        self.ensure_one()
        return self.product_tmpl_id._pg_label_pricelist()

    def _pg_label_prices(self, pricelist=None):
        """Como no artigo, mas a base do preço pode vir do `x_variant_sale_price`.

        Esse campo é do `pg_update_variant_prices` e guarda o preço da variante
        calculado a partir das regras da lista. É um instantâneo: só é actualizado
        quando alguém corre a acção nessa lista, pelo que a etiqueta pode imprimir
        um preço velho — ver alínea (g) do manifest. Fica primeiro porque é o que a
        etiqueta ZPL da V17 usava, e mudá-lo alterava o preço impresso hoje.
        """
        self.ensure_one()
        pricelist = pricelist or self._pg_label_pricelist()
        moeda = pricelist.currency_id or self.currency_id

        base = 0.0
        if 'x_variant_sale_price' in self._fields:
            base = self.x_variant_sale_price or 0.0
        if not base and pricelist:
            base = pricelist._get_product_price(self, 1, currency=moeda)
        if base in (0.0, 1.0) and self.product_tmpl_id._pg_label_fallback_lst_price():
            base = self.lst_price

        anterior = self._pg_label_compare_price()
        return base, (anterior if anterior > base else 0.0)

    def _pg_label_logo_url(self):
        self.ensure_one()
        return self.product_tmpl_id._pg_label_logo_url()

    def _pg_label_variant_values(self):
        self.ensure_one()
        return self.product_template_variant_value_ids

    # -- acções ------------------------------------------------------------

    def action_pg_print_label_a5(self):
        return self.env.ref('pg_etiquetas.action_report_pg_etiqueta_a5_variant').report_action(self)
