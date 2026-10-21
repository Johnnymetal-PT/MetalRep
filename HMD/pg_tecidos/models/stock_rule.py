# -*- coding: utf-8 -*-
"""Override de `_run_manufacture` para criar MOs com fallbacks robustos.

1. Tenta encontrar BoM por variante (`product_id`).
2. Fallback: BoM por template (`product_tmpl_id` + `product_id=False`).
3. Resolve `location_src_id` com fallback para `stock_location_stock`.
4. Cria a MO ligada ao procurement_group e adiciona-a ao grupo.

Ver `__manifest__.py` para o guia completo.
"""

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _run_manufacture(self, procurements):
        for procurement, rule in procurements:
            product = procurement.product_id
            company = procurement.company_id

            # 1. Busca BoM por variante
            bom = self.env['mrp.bom'].search([
                ('product_id', '=', product.id),
                ('company_id', '=', company.id),
                ('type', '=', 'normal')
            ], limit=1)

            # 2. Fallback: busca BoM por template
            if not bom:
                bom = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('product_id', '=', False),
                    ('company_id', '=', company.id),
                    ('type', '=', 'normal')
                ], limit=1)

            if not bom:
                raise ValueError(f"Nenhuma BoM encontrada para o produto: {product.display_name}")

            try:
                # 3. Data planejada
                planned_date = getattr(procurement, 'planned_date', fields.Datetime.now())

                # 4. Localização de componentes com fallback
                location_src = rule.location_src_id
                if not location_src:
                    location_src = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
                    _logger.warning(f"[MRP] Regra '{rule.name}' sem location_src_id — usando 'stock_location_stock' como fallback.")

                if not location_src:
                    raise ValueError(f"[MRP] Nenhuma localização de origem definida nem fallback disponível para a regra: {rule.name}")

                # 5. Dados da MO
                production_vals = {
                    'origin': procurement.origin,
                    'product_id': product.id,
                    'product_qty': procurement.product_qty,
                    'product_uom_id': procurement.product_uom.id,
                    'bom_id': bom.id,
                    'company_id': company.id,
                    'date_start': planned_date,
                    'procurement_group_id': getattr(getattr(procurement, 'group_id', None), 'id', False),
                    'location_src_id': location_src.id,
                    'location_dest_id': procurement.location_id.id,
                }

                # 5b. Projeto da venda: como este override não chama o super, o
                # `project_id` que o standard (sale_project_stock/project_mrp) põe nos
                # valores do procurement tem de ser passado aqui.
                values = getattr(procurement, 'values', None) or {}
                project_id = values.get('project_id')
                if not project_id:
                    # Fallback: projeto da venda a que o grupo de procurement pertence.
                    group = values.get('group_id') or getattr(procurement, 'group_id', None)
                    sale = getattr(group, 'sale_id', False)
                    project_id = sale.sudo().project_id.id if sale else False
                if project_id:
                    production_vals['project_id'] = project_id

                # 6. Criação da MO
                mo = self.env['mrp.production'].create(production_vals)

                # 7. Log no chatter
                mo.message_post(
                    body=(f"Ordem de Fabrico criada automaticamente (Origem: {procurement.origin}"
                          f"; projeto: {mo.project_id.display_name or 'nenhum'})"),
                    subtype_id=self.env.ref('mail.mt_note').id
                )

                # 8. Associação ao grupo
                group = getattr(procurement, 'group_id', None)
                if group and hasattr(group, 'mrp_production_ids'):
                    group.mrp_production_ids = [(4, mo.id)]

                _logger.info(f"[MRP] Ordem de Fabrico criada: {mo.name} para {product.display_name}")

            except Exception as e:
                _logger.exception(f"[MRP ERROR] Falha ao criar MO para '{product.name}': {e}")
                raise
