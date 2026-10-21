"""Job persistente para processamento assincrono da importacao Kave.

Pertence ao modulo `pg_custom_product_import_extension`. Hoje funciona como
placeholder: o cron `cron_process_jobs` marca qualquer job em "queued" como
"failed" porque o worker assincrono ainda nao foi implementado. O wizard de
importacao corre sincrono.

[PONTO POR VALIDAR] decidir se este modelo deve continuar a existir ou se
deve ser removido.
"""
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductImportKaveJob(models.Model):
    """Job persistente (queued/running/done/failed) para importacao Kave."""

    _name = "product.import.kave.job"
    _description = "Queued Kave import job"

    name = fields.Char(default="Kave Import Job")
    state = fields.Selection(
        [
            ("queued", "Queued"),
            ("running", "Running"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="queued",
        required=True,
    )
    file_data = fields.Binary("Excel File", attachment=True)
    filename = fields.Char("Filename")
    total_rows = fields.Integer("Total Rows", default=0)
    processed_rows = fields.Integer("Processed Rows", default=0)
    error_message = fields.Text("Last Error")

    @api.model
    def cron_process_jobs(self):
        """Placeholder processor for queued Kave import jobs.

        This keeps the cron from crashing during module installation while
        deferring the actual import implementation to future work.
        """
        # Comportamento atual deliberado: marcar como failed para tornar visivel
        # que ainda nao existe worker assincrono implementado.
        queued_jobs = self.search([("state", "=", "queued")])
        for job in queued_jobs:
            _logger.info(
                "Marking queued Kave import job as failed because processing is not implemented",
                extra={"job_id": job.id, "filename": job.filename},
            )
            job.write(
                {
                    "state": "failed",
                    "error_message": "Automatic job processing is not implemented.",
                }
            )
        return True
