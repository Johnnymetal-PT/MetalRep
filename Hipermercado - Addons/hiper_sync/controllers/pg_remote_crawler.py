"""Endpoint HTTP usado pelo crawler externo para entregar o CSV ao Odoo.

A rota e ``auth='public'`` -- a autenticacao real e feita por verificacao
de Bearer token contra ``ir.config_parameter`` ``hiper_sync.remote_crawler_upload_token``.
"""

import logging

from odoo import fields, http
from odoo.http import request


_logger = logging.getLogger(__name__)


class PgRemoteCrawlerController(http.Controller):
    """Controller publico para upload do resultado do crawler remoto."""

    @http.route(
        "/hiper_sync/crawler/upload",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
        readonly=True,
    )
    def pg_upload_remote_crawler_result(self, **post):
        """Recebe o CSV gerado pelo crawler externo.

        Fluxo:
            1. Valida o header ``Authorization: Bearer <token>`` contra o
               parametro ``hiper_sync.remote_crawler_upload_token``.
            2. Grava o ficheiro como ``ir.attachment`` (anexado ao vendor se
               ``vendor_code`` for fornecido).
            3. Gera URL publica com ``access_token`` para o adapter CSV URL
               descarregar o ficheiro durante o sync.
            4. Atualiza o estado do crawler no vendor via
               ``_apply_remote_crawler_response`` (job_id, status, meta).

        Parametros POST (form-data):
            * ``file``                -- ficheiro CSV (obrigatorio);
            * ``vendor_code``         -- ``hiper.sync.vendor.code`` para
              associar o anexo ao fornecedor (opcional mas recomendado);
            * ``job_id``, ``status``, ``visited_pages``, ``discovered_products``,
              ``progress_note``, ``source_url`` -- metadados do job remoto.

        Respostas:
            * 200 -- JSON com ``attachment_id``, ``filename``, ``csv_url``.
            * 401 -- token invalido ou em falta.
            * 400 -- ficheiro em falta ou vazio.
        """
        params = request.env["ir.config_parameter"].sudo()
        expected_token = (params.get_param("hiper_sync.remote_crawler_upload_token") or "").strip()
        header_token = (request.httprequest.headers.get("Authorization") or "").strip()
        if not expected_token or header_token != f"Bearer {expected_token}":
            return request.make_json_response({"error": "Unauthorized"}, status=401)

        uploaded_file = request.httprequest.files.get("file")
        if not uploaded_file:
            return request.make_json_response({"error": "Missing file upload."}, status=400)

        vendor_code = (post.get("vendor_code") or "").strip()
        source_url = (post.get("source_url") or "").strip()
        filename = (post.get("filename") or uploaded_file.filename or "crawler_result.csv").strip()
        vendor = request.env["hiper.sync.vendor"].sudo().search([("code", "=", vendor_code)], limit=1) if vendor_code else False
        file_bytes = uploaded_file.read()
        if not file_bytes:
            return request.make_json_response({"error": "Uploaded file is empty."}, status=400)

        attachment_values = {
            "name": filename,
            "raw": file_bytes,
            "mimetype": uploaded_file.mimetype or "text/csv",
            "public": False,
            "description": source_url or False,
        }
        if vendor:
            attachment_values.update(
                {
                    "res_model": vendor._name,
                    "res_id": vendor.id,
                }
            )
        attachment = request.env["ir.attachment"].sudo().create(attachment_values)
        token = attachment.generate_access_token()[0]
        csv_url = "/web/content/%s/%s?download=1&access_token=%s" % (attachment.id, attachment.name, token)
        absolute_csv_url = request.httprequest.host_url.rstrip("/") + csv_url
        if vendor:
            meta = {}
            visited_pages = (post.get("visited_pages") or "").strip()
            discovered_products = (post.get("discovered_products") or "").strip()
            progress_note = (post.get("progress_note") or "").strip()
            if visited_pages:
                try:
                    meta["visited_pages"] = int(visited_pages)
                except (TypeError, ValueError):
                    meta["visited_pages"] = 0
            if discovered_products:
                try:
                    meta["discovered_products"] = int(discovered_products)
                except (TypeError, ValueError):
                    meta["discovered_products"] = 0
            if progress_note:
                meta["progress_note"] = progress_note
            vendor._apply_remote_crawler_response(
                {
                    "job_id": (post.get("job_id") or "").strip(),
                    "status": (post.get("status") or "done").strip() or "done",
                    "csv_url": absolute_csv_url,
                    "meta": meta,
                },
                checked=True,
            )
            vendor.write(
                {
                    "remote_crawler_last_error": False,
                    "remote_crawler_last_checked_at": fields.Datetime.now(),
                }
            )
        _logger.info(
            "Stored remote crawler upload attachment id=%s vendor_code=%s source_url=%s filename=%s",
            attachment.id,
            vendor_code,
            source_url,
            filename,
        )
        return request.make_json_response(
            {
                "status": "done",
                "attachment_id": attachment.id,
                "filename": attachment.name,
                "csv_url": absolute_csv_url,
            }
        )
