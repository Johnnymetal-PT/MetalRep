import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ZebraPrintJob(models.Model):
    _name = 'zebra.print.job'
    _description = 'Zebra Print Job'
    _order = 'create_date asc'

    name = fields.Char('Description', required=True, default='ZPL Label')
    zpl = fields.Text('ZPL Code', required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('printing', 'Printing'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='pending', required=True, index=True)
    method = fields.Selection([
        ('auto', 'Auto'),
        ('usb', 'USB'),
        ('ble', 'Bluetooth'),
    ], default='auto')
    user_id = fields.Many2one('res.users', default=lambda s: s.env.uid, required=True)
    error_message = fields.Text('Error')
    print_date = fields.Datetime('Printed At')
    label_count = fields.Integer('Labels', compute='_compute_label_count', store=True)

    @api.depends('zpl')
    def _compute_label_count(self):
        for rec in self:
            rec.label_count = rec.zpl.count('^XZ') if rec.zpl else 0

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Notificar o print server via bus.bus
        for rec in records:
            self.env['bus.bus']._sendone(
                'zebra_print_jobs',
                'new_print_job',
                {
                    'id': rec.id,
                    'zpl': rec.zpl,
                    'method': rec.method,
                    'name': rec.name,
                    'label_count': rec.label_count,
                    'user_id': rec.user_id.id,
                }
            )
        _logger.info('Zebra print job(s) created: %s', records.ids)
        return records

    def action_retry(self):
        self.write({'state': 'pending', 'error_message': False})
        for rec in self:
            self.env['bus.bus']._sendone(
                'zebra_print_jobs',
                'new_print_job',
                {
                    'id': rec.id,
                    'zpl': rec.zpl,
                    'method': rec.method,
                    'name': rec.name,
                    'label_count': rec.label_count,
                    'user_id': rec.user_id.id,
                }
            )

    def _cron_cleanup_old_jobs(self):
        """Remove jobs done/error com mais de 7 dias."""
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=7)
        old = self.search([
            ('state', 'in', ['done', 'error']),
            ('create_date', '<', cutoff),
        ])
        old.unlink()
        _logger.info('Cleaned up %d old print jobs', len(old))
