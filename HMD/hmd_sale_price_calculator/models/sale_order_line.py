# -*- coding: utf-8 -*-
"""Calculadora de preco por linha de venda com fallback de custo.

Para cada linha de venda, este modulo adiciona campos para guardar a
margem aplicada e helpers para obter o custo do produto com varios
fallbacks (standard_price -> ultima PO -> BoM agregada por
fornecedor). Usado pelo wizard `sale.order.line.price.calculator`.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    calculator_cost_price = fields.Float(
        string="Preço de Custo",
        digits="Product Price",
        help="Cost value used by the price calculator.",
    )
    calculator_margin_type = fields.Selection(
        selection=[("fixed", "Fixed Amount"), ("percent", "Margem (% s/ PV)")],
        string="Tipo de Margem",
        default="fixed",
        help="Montante fixo, ou margem comercial percentual sobre o preço de "
        "venda (PV = custo / (1 - margem%)).",
    )
    calculator_margin_value = fields.Float(
        string="Valor da Margem",
        digits="Product Price",
        help="User input value for the margin (fixed amount or percentage).",
    )
    calculator_margin_amount = fields.Float(
        string="Montante da Margem",
        digits="Product Price",
        help="Computed margin amount that was applied to the cost price.",
    )
    calculator_observation = fields.Text(
        string="Observações",
        help="User observations captured from the price calculator.",
    )

    # ------------------------------------------------------------------
    # Calculo de preco por componentes (CALCULO PRECOS.xlsx)
    # PC TOTAL = PC1+PC2+PC3+PC4
    # PRECO CLIENTE = (CAIXA + PC_TOTAL) / 0,6 + P.RECOLHA
    # PVP = PRECO CLIENTE * 2 ; FATURADO = PVP * 0,6
    # ------------------------------------------------------------------
    calc_pc1 = fields.Float(string="PC1", digits="Product Price")
    calc_forn1 = fields.Char(string="Fornecedor 1")
    calc_pc2 = fields.Float(string="PC2", digits="Product Price")
    calc_forn2 = fields.Char(string="Fornecedor 2")
    calc_pc3 = fields.Float(string="PC3", digits="Product Price")
    calc_forn3 = fields.Char(string="Fornecedor 3")
    calc_pc4 = fields.Float(string="PC4", digits="Product Price")
    calc_forn4 = fields.Char(string="Fornecedor 4")
    calc_box_cost = fields.Float(string="Caixa", digits="Product Price")
    calc_pickup_cost = fields.Float(string="P. Recolha", digits="Product Price")
    calc_pc_total = fields.Float(
        string="PC Total", compute="_compute_calc_components", store=True,
        digits="Product Price",
    )
    calc_price_client = fields.Float(
        string="Preço Cliente", compute="_compute_calc_components", store=True,
        digits="Product Price",
    )
    calc_pvp = fields.Float(
        string="PVP", compute="_compute_calc_components", store=True,
        digits="Product Price",
    )
    calc_invoiced = fields.Float(
        string="Preço Faturado", compute="_compute_calc_components", store=True,
        digits="Product Price",
    )
    calc_margin_real = fields.Float(
        string="Margem Real", compute="_compute_calc_components", store=True,
        help="(Preço Faturado + PC Total) / Preço Faturado.",
    )

    @api.depends(
        "calc_pc1", "calc_pc2", "calc_pc3", "calc_pc4",
        "calc_box_cost", "calc_pickup_cost",
    )
    def _compute_calc_components(self):
        for line in self:
            pc_total = (
                (line.calc_pc1 or 0.0) + (line.calc_pc2 or 0.0)
                + (line.calc_pc3 or 0.0) + (line.calc_pc4 or 0.0)
            )
            client = ((line.calc_box_cost or 0.0) + pc_total) / 0.6 + (
                line.calc_pickup_cost or 0.0
            )
            pvp = client * 2.0
            invoiced = pvp * 0.6
            line.calc_pc_total = pc_total
            line.calc_price_client = client
            line.calc_pvp = pvp
            line.calc_invoiced = invoiced
            line.calc_margin_real = (invoiced + pc_total) / invoiced if invoiced else 0.0

    def action_open_components_calculator(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Calculadora de Preços",
            "res_model": "sale.order.line.components.calculator",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_line_id": self.id,
                "default_pc1": self.calc_pc1,
                "default_forn1": self.calc_forn1,
                "default_pc2": self.calc_pc2,
                "default_forn2": self.calc_forn2,
                "default_pc3": self.calc_pc3,
                "default_forn3": self.calc_forn3,
                "default_pc4": self.calc_pc4,
                "default_forn4": self.calc_forn4,
                "default_box_cost": self.calc_box_cost,
                "default_pickup_cost": self.calc_pickup_cost,
            },
        }

    def action_open_price_calculator(self):
        self.ensure_one()
        cost = self._get_calculator_cost()
        return {
            "type": "ir.actions.act_window",
            "name": "Price Calculator",
            "res_model": "sale.order.line.price.calculator",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_line_id": self.id,
                "default_cost_price": cost,
                "default_margin_type": self.calculator_margin_type or "fixed",
                "default_margin_value": self.calculator_margin_value,
                "default_observation": self.calculator_observation,
            },
        }

    def _get_calculator_cost(self):
        """Pipeline de fallback para obter o custo do produto.

        Tenta nesta ordem (primeiro com variante, depois com template):
          1. `standard_price` (custo medio standard);
          2. ultima PO line do produto (`_get_latest_purchase_price`);
          3. agregacao BoM + supplierinfo (`_get_bom_cost`).
        Devolve 0.0 se nenhuma fonte tem dados.
        """
        self.ensure_one()
        product_variant = self.product_id
        product_template = (
            self.product_template_id
            or (product_variant.product_tmpl_id if product_variant else False)
        )

        products_to_check = [p for p in [product_variant, product_template] if p]
        for product in products_to_check:
            cost = product.standard_price or 0.0
            if not cost:
                cost = self._get_latest_purchase_price(product)

            if not cost:
                cost = self._get_bom_cost(product)

            if cost:
                return cost

        return 0.0

    def _convert_to_target_currency(self, price, source_currency):
        if not price:
            return 0.0

        order = self.order_id
        company = self.company_id or (order.company_id if order else self.env.company)
        target_currency = self.currency_id or (
            order.currency_id if order else company.currency_id
        )
        if source_currency and target_currency and source_currency != target_currency:
            convert_date = (
                order.date_order if order and order.date_order else fields.Date.context_today(self)
            )
            price = source_currency._convert(price, target_currency, company, convert_date)
        return price

    def _get_latest_purchase_price(self, product):
        self.ensure_one()
        PurchaseLine = self.env["purchase.order.line"]
        company = self.company_id.id if self.company_id else False
        if product._name == "product.template":
            product_ids = product.product_variant_ids.ids
            if not product_ids:
                return 0.0
            domain = [("product_id", "in", product_ids)]
        else:
            domain = [("product_id", "=", product.id)]

        if company:
            domain.append(("company_id", "=", company))
        else:
            domain.append(("company_id", "=", self.env.company.id))

        pol = PurchaseLine.search(
            domain
            + [
                ("state", "in", ["purchase", "done"]),
            ],
            order="date_planned desc, id desc",
            limit=1,
        )
        if not pol:
            return 0.0

        price = pol.price_unit
        if pol.product_uom and pol.product_uom != product.uom_id:
            price = pol.product_uom._compute_price(price, product.uom_id)

        return self._convert_to_target_currency(price, pol.currency_id)

    def _get_component_supplier_cost(self, component):
        SupplierInfo = self.env["product.supplierinfo"]

        company_id = self.company_id.id if self.company_id else False

        if component._name == "product.template":
            template = component
            domain = [("product_tmpl_id", "=", template.id)]
        else:
            template = component.product_tmpl_id
            domain = [
                ("product_tmpl_id", "=", template.id),
                ("product_id", "in", [component.id, False]),
            ]

        if company_id:
            domain.append(("company_id", "in", [company_id, False]))

        supplier = SupplierInfo.search(
            domain,
            order="write_date desc, create_date desc, id desc",
            limit=1,
        )

        if not supplier:
            return 0.0

        price = supplier.price or 0.0
        supplier_uom = getattr(supplier, "product_uom", False)
        component_uom = component.uom_id
        if supplier_uom and component_uom and supplier_uom != component_uom:
            price = supplier_uom._compute_price(price, component_uom)
        elif not supplier_uom and component_uom:
            purchase_uom = template.uom_po_id
            if purchase_uom and purchase_uom != component_uom:
                price = purchase_uom._compute_price(price, component_uom)

        currency = getattr(supplier, "currency_id", False)
        return self._convert_to_target_currency(price, currency)

    def _get_bom_cost(self, product):
        self.ensure_one()
        BoM = self.env["mrp.bom"]
        company_id = self.company_id.id if self.company_id else False

        domain = []
        if company_id:
            domain.append(("company_id", "in", [company_id, False]))

        bom = BoM.browse()
        if product._name == "product.product":
            bom = BoM.search(
                domain + [("product_id", "=", product.id)],
                order="create_date asc, id asc",
                limit=1,
            )
            if not bom:
                bom = BoM.search(
                    domain + [("product_tmpl_id", "=", product.product_tmpl_id.id)],
                    order="create_date asc, id asc",
                    limit=1,
                )
        else:
            bom = BoM.search(
                domain + [("product_tmpl_id", "=", product.id)],
                order="create_date asc, id asc",
                limit=1,
            )

        if not bom:
            return 0.0

        variant_ptavs = set()
        if product._name == "product.product":
            variant_ptavs = set(product.product_template_attribute_value_ids.ids)

        total_cost = 0.0
        for line in bom.bom_line_ids:
            if (
                line.bom_product_template_attribute_value_ids
                and (
                    not variant_ptavs
                    or not set(line.bom_product_template_attribute_value_ids.ids).issubset(
                        variant_ptavs
                    )
                )
            ):
                continue
            component = line.product_id
            if not component:
                continue
            qty = line.product_qty
            if line.product_uom_id and component.uom_id:
                qty = line.product_uom_id._compute_quantity(qty, component.uom_id)
            component_cost = self._get_component_supplier_cost(component)
            total_cost += component_cost * qty

        bom_qty = bom.product_qty
        if bom.product_uom_id and product.uom_id:
            bom_qty = bom.product_uom_id._compute_quantity(bom_qty, product.uom_id)
        if not bom_qty:
            return 0.0
        return total_cost / bom_qty
