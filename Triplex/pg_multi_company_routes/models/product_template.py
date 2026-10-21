# -*- coding: utf-8 -*-
"""Força rotas de abastecimento por empresa ao confirmar a encomenda de venda.

ATENÇÃO: apesar do nome do ficheiro (product_template.py), o modelo definido aqui
é o `sale.order`. Ver o __manifest__.py para o objetivo de negócio e os avisos do
módulo — nomeadamente que o __init__.py da raiz está vazio, pelo que este código
não é carregado no estado atual.
"""
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Antes de confirmar a venda, garante que os produtos partilhados das linhas
        # têm as rotas de abastecimento corretas para a empresa que está a vender.
        for order in self:
            company_id = order.company_id.id
            company_name = order.company_id.name
            _logger.warning(f"🔁 action_confirm() triggered for SO: {order.name} | Company: {company_name} (ID: {company_id})")

            # Rotas obrigatórias por empresa. NOTA: IDs de empresa fixos no código —
            # rever caso os IDs reais sejam diferentes neste ambiente.
            if company_id == 1:  # Triplex -> comprar
                required_routes = ['Buy', 'Replenish on Order (MTO)']
            elif company_id == 2:  # Oficinna22 -> fabricar
                required_routes = ['Manufacture', 'Replenish on Order (MTO)']
            else:
                # Empresa não prevista: não mexe nas rotas (evita configurações erradas).
                _logger.warning(f"🚫 Unknown company ID {company_id}. Skipping route assignment.")
                continue

            # Resolve os nomes de rota para os respetivos registos stock.route da empresa.
            available_routes = self.env['stock.route'].search([
                ('name', 'in', required_routes),
                ('company_id', '=', company_id)
            ])
            route_ids = set(available_routes.ids)

            _logger.info(f"📦 Routes to enforce for company {company_name}: {required_routes} => IDs: {list(route_ids)}")

            # Só os produtos partilhados (sem empresa) são ajustados; os produtos
            # específicos de uma empresa mantêm a sua própria configuração de rotas.
            shared_templates = order.order_line.mapped('product_id.product_tmpl_id').filtered(lambda p: not p.company_id)

            for product in shared_templates:
                # Reescreve route_ids apenas quando difere, para evitar writes inúteis.
                old_route_ids = set(product.route_ids.ids)
                if old_route_ids != route_ids:
                    product.route_ids = [(6, 0, list(route_ids))]  # (6,0,ids) = substituir conjunto
                    _logger.warning(f"✅ Product '{product.name}' (ID: {product.id}) updated: {old_route_ids} → {route_ids}")
                else:
                    _logger.info(f"⏩ Product '{product.name}' already has correct routes.")

        # Continua o fluxo normal de confirmação do Odoo.
        return super().action_confirm()

