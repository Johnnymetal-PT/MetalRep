import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    pg_picking_delivery_address = fields.Boolean(
        string="Morada de entrega gerada por guia",
        default=False,
        copy=False,
        help="Marca as moradas criadas automaticamente pelo módulo de moradas "
             "de entrega na guia. Usado pela limpeza periódica mensal.",
    )

    @api.model
    def _pg_cleanup_picking_delivery_addresses(self):
        """Elimina moradas geradas pelo módulo criadas há mais de 1 mês.

        Executado pelo cron mensal. Cada eliminação corre num savepoint: se
        uma morada não puder ser apagada (ainda referenciada por um documento
        com ondelete restrito), é ignorada e a limpeza prossegue.
        """
        limit_date = fields.Datetime.now() - relativedelta(months=1)
        addresses = self.search([
            ("pg_picking_delivery_address", "=", True),
            ("create_date", "<", limit_date),
        ])
        removed = 0
        for address in addresses:
            try:
                with self.env.cr.savepoint():
                    address.unlink()
                removed += 1
            except Exception:
                _logger.info(
                    "PG: morada de entrega %s não pôde ser eliminada "
                    "(ainda referenciada).", address.id)
                continue
        _logger.info(
            "PG: limpeza de moradas de entrega de guias concluída "
            "(%s eliminada(s) de %s candidata(s)).", removed, len(addresses))
        return removed
