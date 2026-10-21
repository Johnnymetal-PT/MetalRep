# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools.translate import html_translate

class ProductLabel(models.Model):
    """
    Product Label
    =============
    Defines a reusable label that can be attached to products
    (e.g., "New", "Sale", "Limited Edition").
    Each label has text, colors, and different display options.
    """

    _name = 'as.product_label'
    _description = 'Product Label'

    name = fields.Char(string='Name', required=True, translate=True, help='Name of the label')
    label_text_color = fields.Char(string='Text Color',
        help='Select a Individual HTML Color code (e.g. #ff0000) to display the color of label text.')
    label_color = fields.Char( string='Color',
        help='Select a Individual HTML Color code (e.g. #ff0000) to display the color of label.')
    label_option = fields.Selection([
        ('option_1', 'Option 1'),
        ('option_2', 'Option 2'),
        ('option_3', 'Option 3'),
        ('option_4', 'Option 4'),
        ('option_5', 'Option 5')
    ], string='Select the Option for label', required=True, default='option_1', readonly=False)
    label_preview = fields.Html('Label Preview', translate=html_translate, sanitize_form=False, sanitize_attributes=False, compute='_compute_label_preview')
    ribbon_id = fields.Many2one('product.ribbon', string='Website Ribbon', help='Linked ribbon from product.ribbon model')

    @api.depends('name', 'label_text_color', 'label_color', 'label_option')
    def _compute_label_preview(self):
        """
        Compute the HTML preview for the label.
        Different options apply different CSS classes or icon.
        """
        for rec in self:
            label_class = rec.label_option.replace('option_', '')
            rec.label_preview = f'<div class="as-ribbon-wrpa"><div class="ribbon-style-{label_class}" t-att-id="{rec.label_option}"><span style="background-color:{rec.label_color}; color:{rec.label_text_color}">{rec.name if rec.name else "New"}</span></div></div>'

            if rec.label_option == 'option_5':
                rec.label_preview = f'<div class="class="as-ribbon-wrpa"><div class="ribbon-style-{label_class}" t-att-id="{rec.label_option}"><span style="background-color:{rec.label_color} ; color:{rec.label_text_color}"><i class="fa fa-tag"/>{rec.name if rec.name else "New"}</span></div></div>'

class ProductLabelLine(models.Model):
    _name = 'as.product_label.line'
    _description = 'Product Template Label Line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template Id', required=True)
    website_id = fields.Many2one('website', string='Website', required=True)
    label = fields.Many2one('as.product_label', required=True, string='Label', help='Name of the product label')

    # === Constraints ===
    _unique_product_label = models.Constraint(
        'unique(product_tmpl_id, website_id)',
        'Website must be unique!',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProductLabelLine, self).create(vals_list)
        for record in records:
            if record.label and record.product_tmpl_id:
                if record.label.name:
                    ribbon = self.env['product.ribbon'].sudo().search([('name', '=', record.label.name)], limit=1)
                    if ribbon:
                        try:
                            record.product_tmpl_id.sudo().write({'website_ribbon_id': ribbon.id})
                        except Exception:
                            try:
                                record.product_tmpl_id.website_ribbon_id = ribbon.id
                            except Exception:
                                pass
        return records

    def write(self, vals):
        result = super(ProductLabelLine, self).write(vals)
        for record in self:
            if record.label and record.product_tmpl_id:
                ribbon = False
                target_ribbon = record.label.ribbon_id or ribbon
                if target_ribbon:
                    try:
                        record.product_tmpl_id.sudo().write({'website_ribbon_id': target_ribbon.id})
                    except Exception:
                        try:
                            record.product_tmpl_id.website_ribbon_id = target_ribbon.id
                        except Exception:
                            pass
        return result

    def unlink(self):
        products_to_update = self.mapped('product_tmpl_id')
        result = super(ProductLabelLine, self).unlink()
        for product in products_to_update:
            if not product.pro_label_line_ids:
                product.write({'website_ribbon_id': False})

        return result