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

                # 6. Criação da MO
                mo = self.env['mrp.production'].create(production_vals)

                # 7. Log no chatter
                mo.message_post(
                    body=f"Ordem de Fabrico criada automaticamente (Origem: {procurement.origin})",
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
