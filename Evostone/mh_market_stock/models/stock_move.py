# -*- coding: utf-8 -*-
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    """Alinha as contas de stock (entrada/saída) com a posição fiscal da compra.

    A posição fiscal só remapeia a conta da FACTURA. As contas de valorização
    (recepção) vêm da categoria e ignoram o mercado. Aqui aplicamos o MESMO mapa
    de contas da posição fiscal às contas de entrada/saída de stock, para que a
    recepção e a factura caiam na mesma conta (ex.: 21123 nas importações) e a
    conta-ponte de entrada feche a zero.

    A conta de VALORIZAÇÃO (o activo, ex.: 223) é deixada intacta de propósito:
    o bem é o mesmo, venha de que mercado vier.
    """
    _inherit = 'stock.move'

    # ------------------------------------------------------------------
    # Determinar a posição fiscal que define o mercado (Nacional/Externo)
    # ------------------------------------------------------------------
    def _market_fiscal_position(self):
        """Posição fiscal a aplicar às contas de stock deste movimento.

        Só devolve posição fiscal em contexto de COMPRA/fornecedor — nunca para
        vendas nem devoluções de clientes (evita remapear a entrada de um retorno
        de cliente para a conta de importação).
        """
        self.ensure_one()

        # 1) Movimento originado numa ordem de compra
        po = self.purchase_line_id.order_id
        if po and po.fiscal_position_id:
            return po.fiscal_position_id

        # 2) Devolução: herdar a posição fiscal do movimento original
        if self.origin_returned_move_id:
            fp = self.origin_returned_move_id._market_fiscal_position()
            if fp:
                return fp

        # 3) Recepção manual de fornecedor (sem PO): posição fiscal do fornecedor
        partner = self.picking_id.partner_id or self.partner_id
        if partner and partner.supplier_rank > 0:
            fp = partner.property_account_position_id
            if not fp:
                fp = self.env['account.fiscal.position'].with_company(
                    self.company_id)._get_fiscal_position(partner)
            return fp or False

        return False

    # ------------------------------------------------------------------
    # Override: remapear as contas de entrada/saída pela posição fiscal
    # ------------------------------------------------------------------
    def _get_accounting_data_for_valuation(self):
        res = super()._get_accounting_data_for_valuation()
        fp = self._market_fiscal_position()
        if not fp:
            return res

        journal_id, acc_src, acc_dest, acc_valuation = res
        AccountAccount = self.env['account.account']

        def remap(account_id):
            if not account_id:
                return account_id
            mapped = fp.map_account(AccountAccount.browse(account_id))
            return mapped.id if mapped else account_id

        new_src = remap(acc_src)
        new_dest = remap(acc_dest)

        if new_src != acc_src or new_dest != acc_dest:
            _logger.info(
                "mh_market_stock: movimento %s (%s) — posição fiscal '%s' "
                "remapeou contas de stock: src %s->%s, dest %s->%s",
                self.id, self.product_id.display_name, fp.name,
                acc_src, new_src, acc_dest, new_dest)

        # acc_valuation NÃO é remapeada: o activo é o mesmo bem em qualquer mercado.
        return journal_id, new_src, new_dest, acc_valuation
