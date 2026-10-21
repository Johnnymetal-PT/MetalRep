# -*- coding: utf-8 -*-

from odoo import fields, models


class StockValuationLayer(models.Model):
    """
    Extensão do stock.valuation.layer para mh_purchase.

    NOTA: A criação de SVL é controlada pelo mh_stock_valuation.
    Este módulo apenas adiciona campos informativos para rastreabilidade.
    """
    _inherit = 'stock.valuation.layer'

    # Campo renomeado para consistência com mh_stock_valuation
    base_lot_name = fields.Char(
        string='Nome Base do Lote',
        help='Nome base do lote sem prefixo sequencial (ex: LOTE_ABC)'
    )

    # Rastreabilidade de Import Document
    import_document_id = fields.Many2one(
        'import.document',
        string='Documento de Importação',
        help='Documento de importação que gerou este layer'
    )

    # Campos para entrada provisória (Import Document)
    is_provisional = fields.Boolean(
        string='Entrada Provisória',
        default=False,
        help='Indica se é uma entrada provisória com custo FOB (sem custos adicionais)'
    )
    provisional_updated_date = fields.Datetime(
        string='Data Atualização Definitiva',
        help='Data em que a entrada provisória foi atualizada com custos definitivos'
    )

    # Campos informativos
    is_import_adjustment = fields.Boolean(
        string='Ajuste de Importação',
        help='Indica se é um ajuste de valor devido a importação'
    )
    is_pcmp_adjustment = fields.Boolean(
        string='Ajuste PCMP',
        help='Indica se é um ajuste de PCMP'
    )
    landed_cost_amount = fields.Monetary(
        string='Custo Adicional Distribuído',
        currency_field='currency_id',
        help='Valor de custos adicionais (frete, impostos, etc.) distribuído'
    )
