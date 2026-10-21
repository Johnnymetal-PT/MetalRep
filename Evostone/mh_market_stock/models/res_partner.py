# -*- coding: utf-8 -*-
from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Define automaticamente a posição fiscal do parceiro pelo país.

    Usa a auto-detecção nativa do Odoo (account.fiscal.position._get_fiscal_position,
    baseada em auto_apply + país) para carimbar `property_account_position_id`.
    Assim o parceiro fica com exactamente a mesma posição fiscal que o documento
    (compra/venda) detectaria — consistência total com o mh_market_stock.

    Regras:
    - Só actua quando o campo está VAZIO (respeita a escolha manual da contabilista).
    - Só actua quando há PAÍS (sem país -> deixa vazio).
    - Aplica a clientes e fornecedores (não filtra por rank); ignora contactos filhos.
    - Corre ao criar o parceiro e ao mudar o país.
    """
    _inherit = 'res.partner'

    def _mh_apply_auto_fiscal_position(self):
        FiscalPosition = self.env['account.fiscal.position']
        for partner in self:
            # contactos filhos seguem o parceiro comercial
            if partner.parent_id:
                continue
            # respeitar escolha manual
            if partner.property_account_position_id:
                continue
            # sem país -> deixar vazio
            if not partner.country_id:
                continue

            company = partner.company_id or self.env.company
            fp = FiscalPosition.with_company(company)._get_fiscal_position(partner)
            if fp:
                partner.property_account_position_id = fp.id
                _logger.info(
                    "mh_market_stock: posição fiscal '%s' atribuída a '%s' (país %s)",
                    fp.display_name, partner.display_name, partner.country_id.code)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._mh_apply_auto_fiscal_position()
        return partners

    def write(self, vals):
        res = super().write(vals)
        # só reavaliar quando o país muda (não sobrepõe FP já definida)
        if 'country_id' in vals:
            self._mh_apply_auto_fiscal_position()
        return res
