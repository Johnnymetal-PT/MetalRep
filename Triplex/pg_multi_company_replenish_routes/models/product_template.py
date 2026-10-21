# -*- coding: utf-8 -*-
"""Cria/reativa regras de reabastecimento (orderpoints) por armazém para produtos
partilhados entre empresas. Ver o __manifest__.py para o objetivo e os IDs fixos
de armazém/rota usados (têm de ser revistos em cada ambiente).
"""
from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        """Após criar o produto, garante as regras de reabastecimento por armazém.

        Nota: assinatura de criação single-record. Em Odoo 17 o padrão recomendado
        é `@api.model_create_multi` com lista de vals; aqui assume-se criação a um.
        """
        template = super(ProductTemplate, self).create(vals)
        _logger.info("Creating reordering rules for new product: %s", template.name)
        self._create_reordering_rules_for_shared_products(template)
        return template

    def _create_reordering_rules_for_shared_products(self, templates):
        """Cria ou reativa orderpoints para os produtos partilhados (company_id=False).

        Para cada variante: se já existir uma regra inativa, reativa-a; se não existir
        nenhuma regra ativa, cria uma nova com a rota correta para cada armazém.
        """
        # Garante que trabalhamos com um recordset (e não com ids soltos).
        templates = self.browse(templates.ids)

        # IDs FIXOS deste ambiente (rever em qualquer outra base de dados).
        TRIPLEX_WAREHOUSE_ID = 1  # Armazém Triplex
        OFICINNA_WAREHOUSE_ID = 2  # Armazém Oficinna
        BUY_ROUTE_ID = 5  # Rota "Buy" (comprar)
        MANUFACTURE_ROUTE_ID = 9  # Rota "Manufacture" (fabricar)

        # Fetch warehouses explicitly by ID using sudo() to bypass access rules
        triplex_warehouse = self.env['stock.warehouse'].sudo().browse(TRIPLEX_WAREHOUSE_ID)
        oficinna_warehouse = self.env['stock.warehouse'].sudo().browse(OFICINNA_WAREHOUSE_ID)

        # Log warehouse details
        _logger.info("Triplex Warehouse: %s", triplex_warehouse.name or "Not Found")
        _logger.info("Oficinna Warehouse: %s", oficinna_warehouse.name or "Not Found")

        # Só os produtos partilhados (sem empresa) recebem regras nos dois armazéns.
        shared_templates = templates.filtered(lambda t: not t.company_id)
        _logger.info("Shared templates to process: %d", len(shared_templates))

        for template in shared_templates:
            # As orderpoints são por variante (product.product), não por template.
            for variant in template.product_variant_ids:
                _logger.info("Processing variant: %s (ID: %d)", variant.name, variant.id)

                # Check existing rules for Triplex
                triplex_rules = self.env['stock.warehouse.orderpoint'].sudo().search([
                    ('product_id', '=', variant.id),
                    ('warehouse_id', '=', triplex_warehouse.id)
                ])
                triplex_inactive_rules = triplex_rules.filtered(lambda r: not r.active)

                # Check existing rules for Oficinna
                oficinna_rules = self.env['stock.warehouse.orderpoint'].sudo().search([
                    ('product_id', '=', variant.id),
                    ('warehouse_id', '=', oficinna_warehouse.id)
                ])
                oficinna_inactive_rules = oficinna_rules.filtered(lambda r: not r.active)

                # Reactivate inactive rules for Triplex
                if triplex_inactive_rules:
                    _logger.info("Reactivating %d inactive reordering rules for Triplex", len(triplex_inactive_rules))
                    triplex_inactive_rules.sudo().write({'active': True})

                # Create rule for Triplex if no active rule exists
                if not triplex_rules.filtered(lambda r: r.active):
                    _logger.info("Creating reordering rule for Triplex for variant %s", variant.name)
                    self.env['stock.warehouse.orderpoint'].sudo().create({
                        'product_id': variant.id,
                        'location_id': triplex_warehouse.lot_stock_id.id,  # Stock location
                        'warehouse_id': triplex_warehouse.id,
                        'company_id': triplex_warehouse.company_id.id,
                        'route_id': BUY_ROUTE_ID,  # Assign Buy route
                        'product_min_qty': 0,
                        'product_max_qty': 10,
                    })

                # Reactivate inactive rules for Oficinna
                if oficinna_inactive_rules:
                    _logger.info("Reactivating %d inactive reordering rules for Oficinna", len(oficinna_inactive_rules))
                    oficinna_inactive_rules.sudo().write({'active': True})

                # Create rule for Oficinna if no active rule exists
                if not oficinna_rules.filtered(lambda r: r.active):
                    _logger.info("Creating reordering rule for Oficinna for variant %s", variant.name)
                    self.env['stock.warehouse.orderpoint'].sudo().create({
                        'product_id': variant.id,
                        'location_id': oficinna_warehouse.lot_stock_id.id,  # Stock location
                        'warehouse_id': oficinna_warehouse.id,
                        'company_id': oficinna_warehouse.company_id.id,
                        'route_id': MANUFACTURE_ROUTE_ID,  # Assign Manufacture route
                        'product_min_qty': 0,
                        'product_max_qty': 10,
                    })


    @api.model
    def add_routes_to_existing_templates(self):
        """Aplica as regras de reabastecimento a TODOS os produtos já existentes.

        Método utilitário para correr manualmente (ex.: shell Odoo ou ação de servidor)
        numa migração/arranque, garantindo que os produtos antigos também ficam cobertos.
        """
        # Percorre todos os templates; o filtro de "partilhados" é feito no método chamado.
        all_templates = self.search([])
        _logger.info("Processing all existing templates: %d templates found.", len(all_templates))
        self._create_reordering_rules_for_shared_products(all_templates)

