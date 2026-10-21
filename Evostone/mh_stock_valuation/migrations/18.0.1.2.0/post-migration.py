# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    ProductCategory = env['product.category'].with_context(active_test=False)

    for company in env['res.company'].with_context(active_test=False).search([]):
        categories = ProductCategory.with_company(company).search([]).filtered(
            lambda category: category.property_cost_method == 'pcmp'
        )
        if not categories:
            continue

        categories.with_company(company).write({'property_cost_method': 'average'})
        _logger.info(
            "Migrated %d product categories from legacy PCMP to standard AVCO for company %s",
            len(categories),
            company.display_name,
        )
