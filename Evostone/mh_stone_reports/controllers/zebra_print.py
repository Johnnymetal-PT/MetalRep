import json
import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZebraPrintController(http.Controller):

    @http.route('/mh_stone_reports/zpl/render', type='json', auth='user')
    def render_zpl(self, report_name, res_ids, data=None):
        """Renderiza um relatório qweb-text (ZPL) e devolve o texto.

        Args:
            report_name: Nome do relatório (ex: 'mh_stone_reports.report_stickers_zpl')
            res_ids: Lista de IDs dos registos
            data: Dados adicionais (opcional)

        Returns:
            dict com 'zpl' (texto ZPL) ou 'error'
        """
        try:
            report = request.env['ir.actions.report']._get_report_from_name(report_name)
            if not report:
                return {'error': f'Relatório não encontrado: {report_name}'}

            result = report._render(report.report_name, res_ids, data=data)
            # result é tupla (content_bytes, report_type)
            zpl_bytes = result[0] if isinstance(result, tuple) else result
            if isinstance(zpl_bytes, bytes):
                zpl_text = zpl_bytes.decode('utf-8')
            else:
                zpl_text = str(zpl_bytes)

            _logger.info('ZPL renderizado (%d bytes): %s...', len(zpl_text.strip()), zpl_text.strip()[:200])
            return {'zpl': zpl_text.strip()}

        except Exception as e:
            _logger.exception('Erro ao renderizar ZPL: %s', e)
            return {'error': str(e)}

    @http.route('/mh_stone_reports/zpl/register_url', type='json', auth='public')
    def register_print_server_url(self, url):
        """O print agent regista o seu URL publico (ngrok)."""
        request.env['ir.config_parameter'].sudo().set_param(
            'mh_stone_reports.zebra_print_server_url', url
        )
        _logger.info('Zebra Print Server URL registado: %s', url)
        return {'ok': True, 'url': url}

    @http.route('/mh_stone_reports/zpl/settings', type='json', auth='user')
    def get_print_settings(self):
        """Devolve as configurações do print server ZPL."""
        ICP = request.env['ir.config_parameter'].sudo()
        return {
            'print_server_url': ICP.get_param(
                'mh_stone_reports.zebra_print_server_url',
                default='https://localhost:8099'
            ),
        }

    @http.route('/mh_stone_reports/zpl/job_done', type='json', auth='user')
    def mark_job_done(self, job_id, success=True, error_msg=None):
        """Marca um print job como concluido ou com erro."""
        job = request.env['zebra.print.job'].browse(job_id)
        if job.exists():
            if success:
                job.write({
                    'state': 'done',
                    'print_date': fields.Datetime.now(),
                })
            else:
                job.write({
                    'state': 'error',
                    'error_message': error_msg or 'Unknown error',
                })
            return {'ok': True}
        return {'ok': False, 'error': 'Job not found'}

    @http.route('/mh_stone_reports/zpl/pending_jobs', type='json', auth='user')
    def get_pending_jobs(self, timeout=30):
        """Long-polling: espera ate haver jobs pendentes ou timeout.
        Verifica a cada 0.5s — delay imperceptivel."""
        import time as _time
        deadline = _time.time() + min(timeout, 30)

        while _time.time() < deadline:
            # Novo cursor para ver commits de outras transaccoes
            request.env.cr.execute("""
                SELECT id FROM zebra_print_job
                WHERE state = 'pending'
                ORDER BY create_date ASC
                LIMIT 10
            """)
            job_ids = [r[0] for r in request.env.cr.fetchall()]
            if job_ids:
                jobs = request.env['zebra.print.job'].browse(job_ids)
                jobs.write({'state': 'printing'})
                return [{
                    'id': j.id,
                    'zpl': j.zpl,
                    'method': j.method,
                    'name': j.name,
                    'label_count': j.label_count,
                } for j in jobs]
            _time.sleep(0.5)

        return []
