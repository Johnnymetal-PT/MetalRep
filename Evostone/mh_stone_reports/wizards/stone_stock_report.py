# -*- coding: utf-8 -*-
import logging
from odoo import models, api, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StoneStockListingReport(models.AbstractModel):
    """Modelo de relatório para Listagem de Stock de Pedras"""
    _name = 'report.mh_stone_reports.report_stone_stock_listing'
    _description = 'Relatório de Listagem de Stock de Pedras'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Obter valores para o relatório"""
        _logger.info("=== Gerando relatório de stock de pedras ===")
        _logger.info(f"docids recebidos: {docids}")

        # docids contém o ID do wizard
        wizard = self.env['stone.stock.report.wizard'].sudo().browse(docids)

        if not wizard.exists():
            _logger.error(f"Wizard não encontrado para docids: {docids}")
            raise UserError("Erro: Wizard não encontrado. Por favor, tente novamente.")

        wizard.ensure_one()
        _logger.info(f"Wizard encontrado: {wizard.id}, company: {wizard.company_id.name}")

        # Obter dados do wizard
        stock_data = wizard._get_stock_data()
        _logger.info(f"Registros encontrados: {len(stock_data.get('records', []))}")

        # Mapear labels
        form_labels = {
            'all': 'Todas as Formas',
            'block': 'Blocos',
            'slab': 'Placas',
            'strip': 'Bandas',
            'tiles': 'Ladrilhos',
        }

        return {
            'doc_ids': docids,
            'doc_model': 'stone.stock.report.wizard',
            'docs': wizard,
            'data': data,
            'title': wizard._get_report_title(),
            'stock_data': stock_data,
            'show_detail': wizard.show_detail,
            'filters': {
                'products': ', '.join(wizard.product_ids.mapped('name')) if wizard.product_ids else 'Todos',
                'form': form_labels.get(wizard.product_form, 'Todas'),
                'locations': ', '.join(wizard.location_ids.mapped('name')) if wizard.location_ids else 'Todas',
            },
            'company': wizard.company_id,
            'report_date': wizard.create_date if wizard.create_date else fields.Datetime.now(),
        }
