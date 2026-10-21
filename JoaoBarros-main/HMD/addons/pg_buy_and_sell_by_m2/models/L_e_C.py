import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_studio_largura = fields.Float(string="Largura", default=0.00)
    x_studio_comprimento = fields.Float(string="Comprimento", default=0.00)

    @api.onchange('uom_name')
    def _onchange_uom_name(self):
        if self.uom_name == 'm²':
            self.x_studio_largura = 1.00
            self.x_studio_comprimento = 1.00
        else:
            self.x_studio_largura = 0.00
            self.x_studio_comprimento = 0.00

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_studio_largura = fields.Float(string="Largura", store=True)
    x_studio_comprimento = fields.Float(string="Comprimento", store=True)
    total_area = fields.Float(string="Total Area (m²)", compute="_compute_total_area", store=True)

    @api.depends('x_studio_largura', 'x_studio_comprimento', 'product_uom_qty')
    def _compute_total_area(self):
        for line in self:
            if line.product_uom and line.product_uom.name == 'm²':
                line.total_area = line.x_studio_largura * line.x_studio_comprimento * line.product_uom_qty
            else:
                line.total_area = 0.0

    total_area = fields.Float(string="Total Area (m²)", compute="_compute_total_area", store=True)

    @api.depends('product_uom', 'product_id', 'product_uom_qty', 'x_studio_largura', 'x_studio_comprimento', 'order_id.pricelist_id')
    def _compute_price_unit(self):
        for line in self:
            pricelist = line.order_id.pricelist_id
            product = line.product_id
            partner = line.order_id.partner_id
            quantity = line.product_uom_qty
            
            if not product:
                line.price_unit = 0.0
                continue

            if line.product_uom.name == 'm²' and line.x_studio_largura and line.x_studio_comprimento:
                area = line.x_studio_largura * line.x_studio_comprimento
            else:
                area = 1.0  # Default to 1 if not using area-based pricing

            if pricelist:
                price_rule = pricelist._compute_price_rule(
                    products=product,
                    quantity=quantity,
                    partner=partner
                )
                if product.id in price_rule:
                    price, rule_id = price_rule[product.id]
                    line.price_unit = area * price
                else:
                    line.price_unit = area * (product.list_price or 0.0)
            else:
                line.price_unit = area * (product.list_price or 0.0)
                
    @api.onchange('x_studio_largura', 'x_studio_comprimento')
    def _onchange_dimensions(self):
        """Update dimensions in the existing name if both largura and comprimento are non-zero."""
        for line in self:
            if line.x_studio_largura > 0 and line.x_studio_comprimento > 0:
                # Extract existing description and remove old dimensions
                base_description = line.name.split(' - ')[0]
                additional_description = '{} x {} m²'.format(
                    round(line.x_studio_largura, 2),
                    round(line.x_studio_comprimento, 2),
                )
                # Update the name with the new dimensions
                line.name = f'{base_description} - {additional_description}'

    def write(self, vals):
        """Ensure name is updated if dimensions are provided during updates."""
        res = super(SaleOrderLine, self).write(vals)
        for line in self:
            if line.x_studio_largura > 0 and line.x_studio_comprimento > 0:
                additional_description = '{} x {} m²'.format(
                    round(line.x_studio_largura, 2),
                    round(line.x_studio_comprimento, 2),
                )
                if additional_description not in line.name:
                    line.name += f' - {additional_description}'
        return res
    
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, company_id, supplier):
        values = super(SaleOrderLine, self)._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, supplier
        )
        values['sale_line_id'] = self.id
        _logger.info(f"Prepared PO Line for Sale Order Line {self.id}: {values}")
        return values

        
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    x_studio_largura = fields.Float(string="Largura")
    x_studio_comprimento = fields.Float(string="Comprimento")
    total_area = fields.Float(string="Total Area (m²)", compute="_compute_total_area", store=True)
    sale_line_id = fields.Many2one(
        "sale.order.line",
        string="Source Sale Order Line",
        help="The Sale Order Line that originated this Purchase Order Line.",
    )

    @api.depends('x_studio_largura', 'x_studio_comprimento', 'product_qty', 'product_uom')
    def _compute_total_area(self):
        for line in self:
            if line.product_uom.name == 'm²':
                line.total_area = line.x_studio_largura * line.x_studio_comprimento * line.product_qty
            else:
                line.total_area = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        po_lines = super(PurchaseOrderLine, self).create(vals_list)
        for line in po_lines:
            if line.order_id.group_id:
                group = line.order_id.group_id
                # Fetch associated Sale Order Line
                if group.sale_id:
                    sale_lines = group.sale_id.order_line.filtered(lambda l: l.product_id.id == line.product_id.id)
                    if sale_lines:
                        sale_line = sale_lines[0]
                        line.write({'name': sale_line.name, 'sale_line_id': sale_line.id})
                        _logger.info(
                            f"Updated PO Line {line.id} with name '{sale_line.name}' from Sale Order Line {sale_line.id}"
                        )
                        # Extract dimensions and calculate price_unit
                        try:
                            parts = sale_line.name.split(' - ')[1].split(' x ')
                            largura = float(parts[0].strip())
                            comprimento = float(parts[1].replace('m²', '').strip())
                            original_price = line.price_unit
                            line.price_unit = largura * comprimento * original_price
                            _logger.info(
                                f"Updated PO Line {line.id} price_unit: {line.price_unit} "
                                f"(Largura: {largura}, Comprimento: {comprimento}, Original Price: {original_price})"
                            )
                        except Exception as e:
                            _logger.error(
                                f"Failed to update price_unit for PO Line {line.id}: {e}"
                            )
                    else:
                        _logger.warning(f"No matching Sale Order Line found for PO Line {line.id} in Group {group.id}")
                else:
                    _logger.warning(f"No Sale Order linked to Group {group.id} for PO Line {line.id}")
            else:
                _logger.warning(f"PO Line {line.id} has no associated group_id.")
        return po_lines


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_po_line_values_from_so_line(self, sale_order_line, po):
        values = super(PurchaseOrder, self)._get_po_line_values_from_so_line(sale_order_line, po)
        values['sale_line_id'] = sale_order_line.id
        _logger.info(f"PO Line Values from Sale Order Line {sale_order_line.id}: {values}")
        return values



