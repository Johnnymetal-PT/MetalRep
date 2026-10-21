"""Extensoes a ``res.company`` para a hierarquia de armazens do PG.

Acrescenta 4 campos ``Many2one`` (primario, secundario, loja, fornecedor
virtual) e expoe os helpers ``_pg_get_*`` consumidos pelos restantes models
do modulo. O metodo ``_pg_apply_stock_hierarchy`` mantem a configuracao do
Odoo (rules ``mts_else_mto``, ``resupply_wh_ids``, default de SO warehouse)
sincronizada com a hierarquia escolhida sempre que esta muda.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PgResCompany(models.Model):
    """Empresa com hierarquia de armazens configuravel.

    Os 4 campos sao opcionais individualmente: pode existir so o primario, ou
    primario + virtual, etc. Os helpers tratam de devolver os armazens
    presentes pela ordem definida.
    """

    _inherit = "res.company"

    pg_sale_primary_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Primary Sales Warehouse",
        domain="[('company_id', '=', id)]",
        help="Default warehouse used for sales orders and the first level of the stock hierarchy.",
    )
    pg_sale_secondary_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Secondary Sales Warehouse",
        domain="[('company_id', '=', id)]",
        help="Second warehouse used when the primary warehouse has insufficient stock.",
    )
    pg_sale_store_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Store Warehouse",
        domain="[('company_id', '=', id)]",
        help="Store warehouse used after the primary and secondary warehouses.",
    )
    pg_supplier_virtual_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Virtual Supplier Warehouse",
        domain="[('company_id', '=', id)]",
        help="Reference warehouse used to identify supplier-backed availability imported by the sync.",
    )

    @api.constrains(
        "pg_sale_primary_warehouse_id",
        "pg_sale_secondary_warehouse_id",
        "pg_sale_store_warehouse_id",
        "pg_supplier_virtual_warehouse_id",
    )
    def _pg_constrain_stock_hierarchy(self):
        for company in self:
            company._pg_validate_stock_hierarchy()

    @api.model_create_multi
    def create(self, vals_list):
        # Apos o create, aplica a hierarquia apenas para as empresas cujo
        # vals continha um dos 4 campos rastreados (evita trabalho inutil).
        companies = super().create(vals_list)
        companies._pg_apply_stock_hierarchy_if_needed(vals_list)
        return companies

    def write(self, vals):
        # ``vals`` e o mesmo dicionario para todas as empresas no write
        # multiplo do Odoo: replicamo-lo para o helper iterar com zip.
        res = super().write(vals)
        self._pg_apply_stock_hierarchy_if_needed([vals] * len(self))
        return res

    def _pg_apply_stock_hierarchy_if_needed(self, vals_list):
        tracked_fields = {
            "pg_sale_primary_warehouse_id",
            "pg_sale_secondary_warehouse_id",
            "pg_sale_store_warehouse_id",
            "pg_supplier_virtual_warehouse_id",
        }
        companies_to_apply = self.env["res.company"]
        for company, vals in zip(self, vals_list):
            if tracked_fields.intersection(vals):
                companies_to_apply |= company
        if companies_to_apply:
            companies_to_apply._pg_apply_stock_hierarchy()

    def _pg_validate_stock_hierarchy(self):
        self.ensure_one()
        configured = self.env["stock.warehouse"]
        for warehouse in (
            self.pg_sale_primary_warehouse_id,
            self.pg_sale_secondary_warehouse_id,
            self.pg_sale_store_warehouse_id,
            self.pg_supplier_virtual_warehouse_id,
        ):
            if warehouse:
                configured |= warehouse
        if len(configured.ids) != len(set(configured.ids)):
            raise ValidationError("The configured PG warehouse hierarchy cannot contain duplicates.")
        if any(warehouse.company_id != self for warehouse in configured):
            raise ValidationError("All warehouses in the PG hierarchy must belong to the same company.")

    def _pg_get_sale_stock_hierarchy(self):
        """Devolve os armazens internos (primario/secundario/loja) pela ordem.

        Nao inclui o ``pg_supplier_virtual_warehouse_id`` (esse e tratado
        a parte porque a sua "quantidade" e teorica, vinda do Hiper Sync).
        """
        self.ensure_one()
        ordered_ids = []
        seen_ids = set()
        for warehouse in (
            self.pg_sale_primary_warehouse_id,
            self.pg_sale_secondary_warehouse_id,
            self.pg_sale_store_warehouse_id,
        ):
            if not warehouse or warehouse.id in seen_ids:
                continue
            ordered_ids.append(warehouse.id)
            seen_ids.add(warehouse.id)
        return self.env["stock.warehouse"].browse(ordered_ids)

    def _pg_get_supplier_virtual_qty(self, product):
        """Quantidade vinda do Hiper Sync (campo ``hiper_supplier_qty``).

        E sempre lido do ``product.template`` (mesmo quando recebemos uma
        ``product.product``) porque o sync trabalha ao nivel do template.
        Negativos sao tratados como zero.
        """
        self.ensure_one()
        template = product.product_tmpl_id if product._name == "product.product" else product
        return max(template.hiper_supplier_qty or 0.0, 0.0)

    def _pg_get_total_internal_sale_available_qty(self, product):
        self.ensure_one()
        hierarchy = self._pg_get_sale_stock_hierarchy()
        if not hierarchy:
            return product.free_qty
        return sum(product.with_context(warehouse_id=warehouse.id).free_qty for warehouse in hierarchy)

    def _pg_get_internal_sale_available_qty(self, product, warehouse=None):
        self.ensure_one()
        if warehouse:
            return product.with_context(warehouse_id=warehouse.id).free_qty
        return self._pg_get_total_internal_sale_available_qty(product)

    def _pg_get_sale_available_qty(self, product, warehouse=None):
        self.ensure_one()
        return self._pg_get_internal_sale_available_qty(product, warehouse=warehouse) + self._pg_get_supplier_virtual_qty(product)

    def _pg_get_sale_supply_routes(self, order_warehouse=None):
        self.ensure_one()
        routes = self.env["stock.route"]
        buy_source_wh = order_warehouse or self.pg_sale_primary_warehouse_id
        if buy_source_wh and buy_source_wh.buy_pull_id and buy_source_wh.buy_pull_id.route_id:
            routes |= buy_source_wh.buy_pull_id.route_id
        return routes

    def _pg_get_sale_stock_locations(self):
        self.ensure_one()
        return self._pg_get_sale_stock_hierarchy().mapped("lot_stock_id")

    def _pg_get_website_available_qty(self, product):
        self.ensure_one()
        website_warehouse = self.env["website"].get_current_website().warehouse_id
        return self._pg_get_sale_available_qty(product, warehouse=website_warehouse or self.pg_sale_primary_warehouse_id)

    def _pg_get_expected_resupply_map(self):
        self.ensure_one()
        mapping = {}
        hierarchy = self._pg_get_sale_stock_hierarchy()
        for warehouse in hierarchy:
            if warehouse:
                mapping[warehouse] = self.env["stock.warehouse"]
        virtual_wh = self.pg_supplier_virtual_warehouse_id
        if virtual_wh:
            mapping[virtual_wh] = self.env["stock.warehouse"]
        return mapping

    def _pg_apply_stock_hierarchy(self):
        """Aplica a hierarquia configurada na infraestrutura de stock.

        Re-executavel sem efeitos colaterais: garante que ``ir.default``,
        ``procure_method`` das delivery rules e ``resupply_wh_ids`` reflectem
        a hierarquia corrente. ``buy_to_resupply`` e desligado no armazem de
        fornecedor virtual (e apenas um indicador de stock externo) e ligado
        nos restantes. Usa ``sudo()`` no ``ir.default`` porque o user que
        configura pode nao ter permissoes para escrever defaults globais.
        """
        ir_default_model = self.env["ir.default"].sudo()
        for company in self:
            company._pg_validate_stock_hierarchy()
            hierarchy = company._pg_get_sale_stock_hierarchy()
            expected_resupply = company._pg_get_expected_resupply_map()

            primary_wh = company.pg_sale_primary_warehouse_id
            ir_default_model.set(
                "sale.order",
                "warehouse_id",
                primary_wh.id if primary_wh else False,
                company_id=company.id,
            )

            for warehouse in hierarchy:
                delivery_rule = warehouse.delivery_route_id.rule_ids.filtered(
                    lambda rule: rule.action in ("pull", "pull_push") and rule.location_src_id == warehouse.lot_stock_id
                )[:1]
                if delivery_rule and delivery_rule.procure_method != "mts_else_mto":
                    delivery_rule.procure_method = "mts_else_mto"

            for warehouse, supplier_whs in expected_resupply.items():
                expected_ids = supplier_whs.ids
                if set(warehouse.resupply_wh_ids.ids) != set(expected_ids):
                    warehouse.write({"resupply_wh_ids": [(6, 0, expected_ids)]})

            virtual_wh = company.pg_supplier_virtual_warehouse_id
            if virtual_wh and virtual_wh.buy_to_resupply:
                virtual_wh.buy_to_resupply = False

            for warehouse in hierarchy:
                should_buy = True
                if warehouse.buy_to_resupply != should_buy:
                    warehouse.buy_to_resupply = should_buy

            for supplied_wh, supplier_whs in expected_resupply.items():
                for supplier_wh in supplier_whs:
                    route = supplied_wh.resupply_route_ids.filtered(lambda record: record.supplier_wh_id == supplier_wh)[:1]
                    if not route:
                        continue
                    resupply_rule = route.rule_ids.filtered(
                        lambda rule: rule.action in ("pull", "pull_push") and rule.location_src_id == supplier_wh.lot_stock_id
                    )[:1]
                    if resupply_rule and resupply_rule.procure_method != "mts_else_mto":
                        resupply_rule.procure_method = "mts_else_mto"
