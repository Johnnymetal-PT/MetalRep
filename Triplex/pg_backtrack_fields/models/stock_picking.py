# -*- coding: utf-8 -*-
"""Reconstrói a venda/OF de origem de uma receção, seguindo a cadeia pelo campo `origin`.

Ver o __manifest__.py para o objetivo e os avisos (ligação por nome, campo Studio).
"""
import re

from odoo import models, fields, api

# Quantas guias se seguem em cadeia ao resolver uma devolução. As devoluções encadeiam-se
# ("Retorno de X", em que X é ele mesmo um retorno), e o limite evita percorrer sem fim.
MAX_SALTOS_GUIA = 3


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    so_id = fields.Many2one('sale.order', string='Source SO', compute='_compute_so_fields', store=True)
    mo_id = fields.Many2one('mrp.production', string='Source MO', compute='_compute_so_fields', store=True)
    po_id = fields.Many2one('purchase.order', string='Source PO', compute='_compute_so_fields', store=True)
    po_name = fields.Char(string='PO Name', compute='_compute_so_fields', store=True)
    so_name = fields.Char(string='SO Name', compute='_compute_so_fields', store=True)
    customer_ref = fields.Char(string='Customer Reference', compute='_compute_so_fields', store=True)
    mo_product_id = fields.Many2one('product.product', string='MO Product', compute='_compute_so_fields', store=True)

    @staticmethod
    def _pg_origin_tokens(texto):
        """Documentos referidos num campo `origin`.

        Divide por vírgulas **e por espaços**. As vírgulas porque o standard junta várias
        origens no mesmo campo (o `purchase_stock` escreve `', '.join(origins)` quando uma
        compra serve vários pedidos de reabastecimento). Os espaços porque há origens em
        texto livre onde o documento vem no meio de uma frase — medido a 28/07/2026:
        **164 compras** com origem `"Merged PO for SO S01762"`, cuja venda existe e ficava
        sem ser encontrada por se comparar a frase inteira.

        Nomes de documento não contêm espaços, pelo que dividir por eles é seguro: no pior
        caso produz palavras que não correspondem a documento nenhum e são ignoradas.
        """
        return [parte for parte in re.split(r"[\s,;]+", texto or "") if parte]

    def _pg_venda_por_nome(self, tokens):
        """Primeira encomenda de venda cujo nome esteja entre os tokens."""
        if not tokens:
            return self.env['sale.order'].browse()
        return self.env['sale.order'].search([('name', 'in', tokens)], limit=1)

    def _pg_venda_por_guia(self, tokens):
        """Venda alcançada seguindo guias referidas na origem — o caso das devoluções.

        Uma devolução tem `origin` = "Retorno de WH/OUT/00211", e a guia original conhece a
        venda no seu `sale_id`. Como uma devolução pode ser devolução de outra devolução,
        segue-se a cadeia até `MAX_SALTOS_GUIA`, com registo das já visitadas.
        """
        vistos = set()
        fronteira = list(tokens)
        for _ in range(MAX_SALTOS_GUIA):
            if not fronteira:
                break
            guias = self.env['stock.picking'].search([('name', 'in', fronteira)])
            guias = guias.filtered(lambda g: g.id not in vistos)
            if not guias:
                break
            vistos.update(guias.ids)

            com_venda = guias.filtered('sale_id')[:1]
            if com_venda:
                return com_venda.sale_id

            seguintes = []
            for guia in guias:
                seguintes += self._pg_origin_tokens(guia.origin)
            venda = self._pg_venda_por_nome(seguintes)
            if venda:
                return venda
            fronteira = seguintes
        return self.env['sale.order'].browse()

    @api.depends('origin')
    def _compute_so_fields(self):
        for picking in self:
            picking.so_id = False
            picking.mo_id = False
            picking.po_id = False
            picking.po_name = False
            picking.so_name = False
            picking.customer_ref = False
            picking.mo_product_id = False

            if picking.picking_type_code != 'incoming':
                continue

            nomes_compra = self._pg_origin_tokens(picking.origin)
            if not nomes_compra:
                continue

            po = self.env['purchase.order'].search([('name', 'in', nomes_compra)], limit=1)
            if not po:
                # Sem compra na origem: pode ser uma devolução, cuja origem aponta para
                # outra guia. Medido a 28/07/2026: é a única via para esses casos.
                venda = self._pg_venda_por_guia(nomes_compra)
                if venda:
                    picking.so_id = venda
                    picking.so_name = venda.name
                    if 'x_studio_customer_ref' in venda._fields:
                        picking.customer_ref = venda.x_studio_customer_ref
                continue
            # A compra fica registada mesmo quando não leva a venda nenhuma. É o que permite
            # à etiqueta ter uma referência de recurso nas compras soltas — as que são feitas
            # sem encomenda de venda associada, como as de tecido comprado para stock.
            picking.po_id = po
            picking.po_name = po.name

            if not po.origin:
                continue

            origens_compra = self._pg_origin_tokens(po.origin)
            venda = self.env['sale.order'].browse()

            # Caminho 1: a compra aponta a uma ordem de fabrico, e essa à venda.
            mo = self.env['mrp.production'].search([('name', 'in', origens_compra)], limit=1)
            if mo:
                picking.mo_id = mo
                picking.mo_product_id = mo.product_id
                if mo.origin:
                    venda = self.env['sale.order'].search(
                        [('name', 'in', self._pg_origin_tokens(mo.origin))], limit=1)

            # Caminho 2: a compra aponta DIRECTAMENTE à venda. É o caso das compras geradas
            # por reabastecimento, que levam o nome da encomenda no documento de origem e
            # nunca passam por uma ordem de fabrico. Antes de 28/07/2026 estes casos ficavam
            # sem venda: o código procurava só uma ordem de fabrico e desistia. Medido numa
            # amostra de 150 receções sem venda resolvida, 84 resolviam-se por aqui.
            if not venda:
                venda = self._pg_venda_por_nome(origens_compra)

            if venda:
                picking.so_id = venda
                picking.so_name = venda.name
                # `x_studio_customer_ref` é um campo Studio: pode não existir noutra base.
                if 'x_studio_customer_ref' in venda._fields:
                    picking.customer_ref = venda.x_studio_customer_ref

    def pg_recompute_backtrack(self):
        """Recalcula a venda/OF de origem nas receções já existentes.

        Necessário porque os campos são armazenados e dependem apenas do `origin` da própria
        guia: alterações na cadeia a montante — ou uma correção da própria lógica, como a de
        28/07/2026 — não os fazem recalcular sozinhos.

        Método público de propósito, para poder ser chamado depois de importações de dados.
        """
        alvo = self if self else self.search([('picking_type_code', '=', 'incoming')])
        for nome in ('so_id', 'mo_id', 'po_id', 'po_name', 'so_name', 'customer_ref',
                     'mo_product_id'):
            self.env.add_to_compute(self._fields[nome], alvo)
        alvo.flush_recordset()
        return {'recalculadas': len(alvo)}
