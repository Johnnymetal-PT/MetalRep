from odoo import models, fields, api
import html

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_studio_quantidade = fields.Float(string="Peças", store=True)
    x_studio_largura = fields.Float(string="Largura", default=0, store=True)
    x_studio_comprimento = fields.Float(string="Comprimento (m)", default=0, store=True)

    # Estes campos foram criados via Odoo Studio — já estão presentes
    x_studio_espessura = fields.Float(string="Espessura (mm)", store=True)
    x_studio_densidade = fields.Float(string="Densidade (kg/dm³)", default=8, store=True)

    x_studio_area = fields.Float(string="Área (m²)", compute="_compute_area_peso", store=True)
    x_studio_peso = fields.Float(string="Peso (kg)", compute="_compute_area_peso", store=True)
    x_display_name_area_peso = fields.Char(string="Descrição com Área e Peso", compute="_compute_area_peso", store=True)

    x_studio_unidade_de_medida = fields.Many2one(
        'uom.uom',
        string="Unidade de Medida",
        domain="[('name', 'in', ['ML', 'Kg', 'Unidades'])]"
    )

    product_uom_qty = fields.Float(
        compute="_compute_product_uom_qty",
        store=True,
        readonly=False
    )

    price_unit = fields.Float(string="Unit Price", store=True, readonly=False)

    # ===> CÁLCULO DE ÁREA E PESO <===
    @api.depends('x_studio_quantidade', 'x_studio_comprimento', 'product_id', 'x_studio_densidade', 'x_studio_espessura', 'x_studio_largura')
    def _compute_area_peso(self):
        for line in self:
            comprimento = line.x_studio_comprimento or 0
            largura = 1  # fixo
            largura2 = line.x_studio_largura or 1
            espessura = line.x_studio_espessura or 0
            densidade = line.x_studio_densidade or 8
            peas = line.x_studio_quantidade or 0

            area = comprimento * largura2 * 1
            volume = comprimento * largura2 * (espessura / 1000)
            peso = volume * (densidade * 1000) * peas

            line.x_studio_area = area
            line.x_studio_peso = peso

            nome = line.product_id.display_name or 'Produto'
            line.x_display_name_area_peso = f"{nome} - Área: {area:.2f} m² | Peso: {peso:.2f} kg"

    # ===> CÁLCULO DE QTY PARA ODOO STOCK (não afeta área/peso do cliente) <===
    @api.depends('x_studio_quantidade', 'x_studio_comprimento')
    def _compute_product_uom_qty(self):
        for line in self:
            qty = line.x_studio_quantidade or 0
            comprimento = line.x_studio_comprimento or 0
            largura = 1
            if comprimento == 0:
                line.product_uom_qty = qty
            else:
                line.product_uom_qty = qty * comprimento * largura

    @api.onchange('product_id')
    def _onchange_product_id_set_uom(self):
        for line in self:
            if line.product_id:
                line.x_studio_unidade_de_medida = line.product_id.uom_id.id

    @api.model
    def create(self, vals):
        qty = vals.get('x_studio_quantidade', 0)
        comprimento = vals.get('x_studio_comprimento', 0)
        largura = 1
        if comprimento == 0:
            vals['product_uom_qty'] = qty
        else:
            vals['product_uom_qty'] = qty * comprimento * largura

        if 'x_studio_unidade_de_medida' in vals and vals['x_studio_unidade_de_medida']:
            vals['product_uom'] = vals['x_studio_unidade_de_medida']
        else:
            product = self.env['product.product'].browse(vals.get('product_id', False))
            if product:
                vals['product_uom'] = product.uom_id.id

        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        if any(field in vals for field in ['x_studio_quantidade', 'x_studio_comprimento']):
            qty = vals.get('x_studio_quantidade', self.x_studio_quantidade)
            comprimento = vals.get('x_studio_comprimento', self.x_studio_comprimento)
            largura = 1
            if comprimento == 0:
                vals['product_uom_qty'] = qty
            else:
                vals['product_uom_qty'] = qty * comprimento * largura

        if 'x_studio_unidade_de_medida' in vals:
            vals['product_uom'] = vals['x_studio_unidade_de_medida']
        else:
            vals['product_uom'] = self.product_uom.id

        return super(SaleOrderLine, self).write(vals)
    

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'x_studio_peas': self.x_studio_quantidade,
            'x_studio_largura': self.x_studio_largura,
            'x_studio_comprimento': self.x_studio_comprimento,
        })
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_studio_peas = fields.Float(string="Peças", store= True)
    x_studio_largura = fields.Float(string="Largura", default=0, store= True)
    x_studio_comprimento = fields.Float(string="Comprimento", default=0, store= True)

    x_studio_unidade_de_medida = fields.Many2one(
        'uom.uom', 
        string="Unidade de Medida",
        domain="[('name', 'in', ['ML', 'Kg', 'Unidades'])]"
    )

    quantity = fields.Float(string="Quantidade", store= True)
    price_unit = fields.Float(string="Unit Price", store= True)
    price_subtotal = fields.Monetary(string="Subtotal", store= True)

    @api.onchange('x_studio_peas', 'x_studio_comprimento', 'price_unit')
    def _onchange_compute_values(self):
        for line in self:
            qty = line.x_studio_peas or 0
            comprimento = line.x_studio_comprimento or 0
            largura = 1

            if comprimento == 0:
                line.quantity = qty
            else:
                line.quantity = qty * comprimento * largura

            line.price_subtotal = line.price_unit * line.quantity

    @api.model
    def create(self, vals):
        if 'sale_line_ids' in vals and vals['sale_line_ids']:
            sale_line = self.env['sale.order.line'].browse(vals['sale_line_ids'][0][1])
            vals.update({
                'x_studio_peas': sale_line.x_studio_quantidade,
                'x_studio_largura': sale_line.x_studio_largura,
                'x_studio_comprimento': sale_line.x_studio_comprimento,
                'x_studio_unidade_de_medida': sale_line.x_studio_unidade_de_medida.id,
                'quantity': sale_line.product_uom_qty,
                'price_unit': sale_line.price_unit,
                'price_subtotal': sale_line.price_subtotal,
            })
        return super(AccountMoveLine, self).create(vals)

    def write(self, vals):
        if 'sale_line_ids' in vals and vals['sale_line_ids']:
            sale_line = self.env['sale.order.line'].browse(vals['sale_line_ids'][0][1])
            vals.update({
                'x_studio_peas': sale_line.x_studio_quantidade,
                'x_studio_largura': sale_line.x_studio_largura,
                'x_studio_comprimento': sale_line.x_studio_comprimento,
                'x_studio_unidade_de_medida': sale_line.x_studio_unidade_de_medida.id,
                'quantity': sale_line.product_uom_qty,
                'price_unit': sale_line.price_unit,
                'price_subtotal': sale_line.price_subtotal,
            })
        return super(AccountMoveLine, self).write(vals)
        
        
    def _check_reconciliation(self):
        """Evita reconciliar linhas de NC de cliente automaticamente."""
        lines_to_skip = self.filtered(lambda l: l.move_id.move_type == 'out_refund')
        lines_to_check = self - lines_to_skip
        return super(AccountMoveLine, lines_to_check)._check_reconciliation() if lines_to_check else None
        

class AccountMove(models.Model):
    _inherit = 'account.move'

    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()

        if self.env.context.get('prevent_custom_copy'):
            return super(AccountMove, self).copy(default)

        new_move = super(AccountMove, self.with_context(prevent_custom_copy=True)).copy(default)

        for orig_line, new_line in zip(self.invoice_line_ids, new_move.invoice_line_ids):
            updates = {}

            for field in orig_line._fields:
                if field.startswith('x_studio_'):
                    val = getattr(orig_line, field, False)
                    updates[field] = val.id if hasattr(val, 'id') else (val or 0.0)

            updates.update({
                'quantity': orig_line.quantity,
                'price_unit': orig_line.price_unit,
                'price_subtotal': orig_line.price_subtotal,
                'tax_ids': [(6, 0, orig_line.tax_ids.ids)] if orig_line.tax_ids else [],
                'analytic_distribution': orig_line.analytic_distribution,
                'name': orig_line.name,
                'product_id': orig_line.product_id.id,
            })

            new_line.write(updates)

        return new_move

    def action_post(self):
        res = super().action_post()

        # Aplicar só a Notas de Crédito de Cliente
        for move in self.filtered(lambda m: m.move_type == 'out_refund'):
            lines = move.line_ids.filtered(lambda l: l.reconciled and l.full_reconcile_id)
            reconcile_ids = lines.mapped('full_reconcile_id')

            if reconcile_ids:
                all_lines = self.env['account.move.line'].search([
                    ('full_reconcile_id', 'in', reconcile_ids.ids)
                ])
                all_lines.write({
                    'reconciled': False,
                    'full_reconcile_id': False,
                })
                reconcile_ids.unlink()

            move.payment_state = 'not_paid'

        return res



class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_totais_area_peso_html = fields.Html(
        string="Resumo de Área e Peso por Produto",
        compute="_compute_totais_area_peso_html",
        sanitize=False
    )

    @api.depends('order_line.x_studio_area', 'order_line.x_studio_peso', 'order_line.product_id')
    def _compute_totais_area_peso_html(self):
        for order in self:
            total_area = 0.0
            total_peso = 0.0
            linhas = []

            for line in order.order_line:
                nome = line.product_id.display_name or 'NOTAS'
                area = line.x_studio_area or 0.0
                peso = line.x_studio_peso or 0.0

                linhas.append({'nome': nome, 'area': area, 'peso': peso})
                total_area += area
                total_peso += peso

            html_table = """
                <table style="width: 60%; border-collapse: collapse; font-size:13px;" border="1">
                <thead>
                    <tr>
                    <th style="padding:6px; text-align:left;">Produto</th>
                    <th style="padding:6px; text-align:right;">Área Total (m²)</th>
                    <th style="padding:6px; text-align:right;">Peso Total (kg)</th>
                    </tr>
                </thead>
                <tbody>
            """

            for item in linhas:
                html_table += f"""
                    <tr>
                    <td style="padding:6px;">{html.escape(item['nome'])}</td>
                    <td style="padding:6px; text-align:right;">{item['area']:.2f}</td>
                    <td style="padding:6px; text-align:right;">{item['peso']:.2f}</td>
                    </tr>
                """

            html_table += f"""
                <tr>
                <td style="padding:6px;"><strong>Total</strong></td>
                <td style="padding:6px; text-align:right;"><strong>{total_area:.2f}</strong></td>
                <td style="padding:6px; text-align:right;"><strong>{total_peso:.2f}</strong></td>
                </tr>
            </tbody>
            </table>
            """

            order.x_totais_area_peso_html = html_table

