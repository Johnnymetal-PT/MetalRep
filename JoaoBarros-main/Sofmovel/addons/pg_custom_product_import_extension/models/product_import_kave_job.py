import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductImportKaveJob(models.Model):
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
