"""Importa lst_price por variante de Excel e forca-o no /shop.

Dois mecanismos:
1. Import - Wizard recebe Excel (cols: id, lst_price) e faz write
   direto em ``product.product.lst_price`` (com ``price_extra=0``).
2. Display - Override de ``_get_combination_info`` substitui ``price``
   e ``price_without_discount`` pelo ``lst_price`` da variante,
   neutralizando ``price_extra``.

Efeitos colaterais relevantes:
- ``lst_price`` deixa de ser computed (store=True) - todo o sistema
  ve este campo como independente do template ``list_price``.
- ``_get_combination_info`` deste modulo IGNORA ``price_extra`` de
  PTAVs. Pricelists standard tambem deixam de aplicar; o valor final
  e SEMPRE ``lst_price`` da variante.
"""
import base64
import pandas as pd
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_import_pricelist(self):
        """Botao no template para abrir o wizard de import de variantes."""
        view_id = self.env.ref('pg_variant_specific_pricing.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Redeclarar lst_price como Float store=True para podermos escrever
    # diretamente (no standard e computed; com compute=False fica
    # mutavel).
    lst_price = fields.Float('Sales Price', compute=False, store=True)

    @api.model
    def create(self, vals):
        # Override sem mudanca semantica - so logging.
        if 'lst_price' in vals:
            vals['lst_price'] = vals.get('lst_price')
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        if 'lst_price' in vals:
            vals['lst_price'] = vals.get('lst_price')
        return super(ProductProduct, self).write(vals)

    @api.model
    def _get_combination_info(self, combination, product_id, add_qty=1, pricelist=None, parent_combination=None, **kwargs):
        """Forca lst_price da variante como preco no /shop.

        NOTA: o ``super()`` chama o metodo do template (cujo class e
        ``ProductTemplate``). Esta classe e ProductProduct - o override
        aplica via heranca multipla.

        Sobrescrevemos ``price``, ``price_without_discount`` e
        ``price_extra`` para garantir que ``lst_price`` da variante
        ganha sobre tudo.
        """
        # super() do ProductTemplate (parent) faz o calculo standard.
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination, product_id, add_qty, pricelist, parent_combination, **kwargs,
        )

        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product:
                # Forcar preco da variante. Ignora pricelists e
                # price_extra de atributos - decisao consultiva.
                combination_info['price'] = product.lst_price
                combination_info['price_without_discount'] = product.lst_price
                # Neutralizar PTAV extras (senao seriam somados ao
                # price abaixo).
                combination_info['price_extra'] = 0.0

        return combination_info

    def action_import_pricelist(self):
        """Botao na variante para abrir o wizard."""
        view_id = self.env.ref('pg_variant_specific_pricing.pricelist_import_wizard_form').id
        return {
            'name': _('Import Pricelist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pricelist.import.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
        }


class PricelistImportWizard(models.TransientModel):
    _name = 'pricelist.import.wizard'
    _description = 'Wizard to Import Pricelist'

    file = fields.Binary('File', required=True)
    filename = fields.Char('Filename')

    def import_pricelist(self):
        """Itera Excel (cols id, lst_price) e atualiza variantes."""
        if self.file:
            file_content = base64.b64decode(self.file)
            df = pd.read_excel(file_content)

            for index, row in df.iterrows():
                external_id = row['id']
                # Resolve external id -> (model, res_id). So aceita
                # variantes (product.product); o resto e ignorado em
                # silencio.
                res_model_res_id = self.env['ir.model.data']._xmlid_to_res_model_res_id(external_id)
                if res_model_res_id:
                    model, res_id = res_model_res_id
                    if model == 'product.product':
                        product_variant = self.env[model].browse(res_id)

                        # sudo para escrever mesmo a partir de users
                        # sem direitos completos em product.product.
                        product_variant.sudo().write({
                            'lst_price': row['lst_price'],
                            'price_extra': 0.0,  # neutraliza PTAV extras
                        })

        return {'type': 'ir.actions.act_window_close'}
