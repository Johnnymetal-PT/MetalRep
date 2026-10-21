"""Extensoes ao ``product.template`` para suporte do Hiper Sync.

Acrescenta:

* metadados de sincronizacao (fornecedor de origem, EAN/referencia
  registados, ultimo payload, fingerprint para deteccao de alteracoes),
* locks granulares (``hiper_lock_name``, ``hiper_lock_prices``, ...) que
  protegem campos editados manualmente para o sync nao os sobrescrever,
* fila assincrona de imagens: ``hiper_pending_image_source`` /
  ``pg_hiper_pending_media_json`` sao processados por
  ``cron_process_pending_hiper_images`` em lotes (ver
  ``_hiper_image_batch_size`` e ``_hiper_image_max_seconds``), evitando
  bloquear o sync principal a fazer download de imagens.
"""

import base64
import hashlib
import json
import logging
import os
import time
from urllib.parse import urlsplit

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Herda ``product.template`` para guardar estado de sync e fila de imagens."""

    _inherit = "product.template"
    # Limite de templates processados por execucao da cron de imagens.
    _hiper_image_batch_size = 100
    # Limite de tempo (segundos) que a cron de imagens pode gastar por passe.
    _hiper_image_max_seconds = 120

    hiper_skip_sync = fields.Boolean("Skip Sync")
    hiper_lock_name = fields.Boolean("Lock Name")
    hiper_lock_descriptions = fields.Boolean("Lock Descriptions")
    hiper_lock_prices = fields.Boolean("Lock Prices")
    hiper_lock_categories = fields.Boolean("Lock Categories")
    hiper_lock_images = fields.Boolean("Lock Images")
    hiper_lock_features = fields.Boolean("Lock Features")

    hiper_source_vendor_id = fields.Many2one("hiper.sync.vendor", string="Sync Supplier", readonly=True)
    hiper_source_module_code = fields.Char(readonly=True)
    hiper_source_ean13 = fields.Char(readonly=True)
    hiper_last_sync_at = fields.Datetime(readonly=True)
    hiper_sync_match_method = fields.Selection(
        [
            ("barcode", "Barcode"),
            ("reference", "Reference"),
            ("fingerprint", "Fingerprint"),
            ("new", "New Product"),
        ],
        readonly=True,
    )
    hiper_last_feed_payload = fields.Text(readonly=True)
    hiper_last_compare_data = fields.Text(readonly=True)
    hiper_supplier_qty = fields.Float(readonly=True)
    hiper_supplier_price = fields.Float(readonly=True)
    hiper_supplier_wholesale_price = fields.Float(readonly=True)
    hiper_origin_category = fields.Char(readonly=True)
    hiper_origin_sub_category = fields.Char(readonly=True)
    hiper_tags_text = fields.Char("Imported Tags")
    hiper_manual_url = fields.Char("Manual URL")
    hiper_content_fingerprint = fields.Char(index=True, readonly=True)
    hiper_pending_image_source = fields.Char(readonly=True, copy=False)
    hiper_last_image_source = fields.Char(readonly=True, copy=False)
    pg_hiper_pending_media_json = fields.Text(readonly=True, copy=False)
    pg_hiper_last_media_fingerprint = fields.Char(readonly=True, copy=False)
    hiper_image_sync_state = fields.Selection(
        [
            ("idle", "Idle"),
            ("queued", "Queued"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="idle",
        readonly=True,
        copy=False,
    )
    hiper_image_sync_note = fields.Char(readonly=True, copy=False)
    hiper_image_sync_updated_at = fields.Datetime(readonly=True, copy=False)
    hiper_image_sync_retry_count = fields.Integer(readonly=True, default=0, copy=False)
    hiper_feature_line_ids = fields.One2many(
        "hiper.product.feature.line",
        "product_tmpl_id",
        string="Imported Features",
    )

    def hiper_payload(self):
        self.ensure_one()
        if not self.hiper_last_feed_payload:
            return {}
        return json.loads(self.hiper_last_feed_payload)

    def queue_hiper_image_sync(self, image_source):
        """Marca uma imagem principal para download assincrono.

        Devolve ``False`` quando nao ha trabalho a fazer (lock activo, mesma
        fonte ja aplicada e estado ``done``, ou ja em fila com a mesma fonte).
        """
        self.ensure_one()
        if self.hiper_lock_images or not image_source:
            return False
        if (
            image_source == self.hiper_last_image_source
            and self.hiper_image_sync_state == "done"
            and not self.hiper_pending_image_source
        ):
            return False
        if (
            image_source == self.hiper_pending_image_source
            and self.hiper_image_sync_state == "queued"
        ):
            return False
        values = {
            "hiper_pending_image_source": image_source,
            "hiper_image_sync_state": "queued",
            "hiper_image_sync_note": False,
            "hiper_image_sync_updated_at": fields.Datetime.now(),
        }
        if image_source != self.hiper_pending_image_source:
            values["hiper_image_sync_retry_count"] = 0
        self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(values)
        return True

    def queue_pg_hiper_media_sync(self, media_items):
        self.ensure_one()
        if self.hiper_lock_images:
            return False
        normalized_media = []
        for item in media_items or []:
            if not isinstance(item, dict):
                continue
            media_type = (item.get("type") or "image").strip().lower()
            media_url = (item.get("url") or "").strip()
            if not media_url:
                continue
            normalized_media.append({"type": media_type, "url": media_url})
        if not normalized_media:
            return False
        serialized = json.dumps(normalized_media, ensure_ascii=False, sort_keys=True)
        fingerprint = hashlib.sha1(serialized.encode("utf-8")).hexdigest()
        if (
            fingerprint == self.pg_hiper_last_media_fingerprint
            and self.hiper_image_sync_state == "done"
            and not self.pg_hiper_pending_media_json
        ):
            return False
        if self.pg_hiper_pending_media_json == serialized and self.hiper_image_sync_state == "queued":
            return False
        self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(
            {
                "pg_hiper_pending_media_json": serialized,
                "hiper_image_sync_state": "queued",
                "hiper_image_sync_note": False,
                "hiper_image_sync_updated_at": fields.Datetime.now(),
            }
        )
        return True

    @api.model
    def _trigger_hiper_image_worker(self):
        cron = self.env.ref("hiper_sync.ir_cron_hiper_pending_images", raise_if_not_found=False)
        if not cron:
            _logger.error("Queue cron record hiper_sync.ir_cron_hiper_pending_images was not found.")
            return
        try:
            cron.sudo().write(
                {
                    "active": True,
                    "nextcall": fields.Datetime.now(),
                }
            )
            self.env.cr.commit()
        except UserError as exc:
            if "currently being executed" in str(exc):
                _logger.info(
                    "Pending-image cron id=%s is already executing; leaving remaining images for the next scheduled pass.",
                    cron.id,
                )
                return
            raise
        if hasattr(cron, "_trigger"):
            try:
                cron._trigger()
            except Exception:
                _logger.exception("Failed to trigger pending-image cron id=%s", cron.id)

    @api.model
    def cron_process_pending_hiper_images(self):
        """Cron worker das imagens pendentes (``ir_cron_hiper_pending_images``).

        Processa em ordem cronologica (``hiper_image_sync_updated_at asc``) ate
        ``_hiper_image_batch_size`` templates ou ``_hiper_image_max_seconds``
        segundos, o que ocorrer primeiro. Se ainda restarem itens depois do
        passe, re-arma o cron para correr de novo de seguida (ver
        ``_trigger_hiper_image_worker``).
        """
        start_time = time.time()
        domain = [
            ("hiper_image_sync_state", "=", "queued"),
            "|",
            ("hiper_pending_image_source", "!=", False),
            ("pg_hiper_pending_media_json", "!=", False),
        ]
        templates = self.sudo().search(
            domain,
            order="hiper_image_sync_updated_at asc, id asc",
            limit=self._hiper_image_batch_size,
        )
        if not templates:
            _logger.info("Hiper pending-image cron found no queued images.")
            return True
        _logger.info("Hiper pending-image cron picked templates=%s", templates.ids)
        processed = 0
        for template in templates:
            if processed and time.time() - start_time >= self._hiper_image_max_seconds:
                break
            template._process_hiper_image_queue_item()
            processed += 1
        remaining = self.sudo().search_count(domain)
        _logger.info(
            "Hiper pending-image cron processed=%s remaining=%s",
            processed,
            remaining,
        )
        if remaining:
            self._trigger_hiper_image_worker()
        return True

    def _process_hiper_image_queue_item(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.hiper_lock_images or not self.hiper_pending_image_source:
            if not self.pg_hiper_pending_media_json:
                self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(
                    {
                        "hiper_pending_image_source": False,
                        "hiper_image_sync_state": "idle",
                        "hiper_image_sync_note": False,
                        "hiper_image_sync_updated_at": now,
                    }
                )
                self.env.cr.commit()
                return
        if self.hiper_lock_images:
            self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(
                {
                    "hiper_pending_image_source": False,
                    "pg_hiper_pending_media_json": False,
                    "hiper_image_sync_state": "idle",
                    "hiper_image_sync_note": False,
                    "hiper_image_sync_updated_at": now,
                }
            )
            self.env.cr.commit()
            return
        try:
            media_items = []
            media_json = self.pg_hiper_pending_media_json
            if media_json:
                media_items = json.loads(media_json)
            values = {
                "hiper_image_sync_state": "done",
                "hiper_image_sync_note": False,
                "hiper_image_sync_updated_at": now,
            }
            source = self.hiper_pending_image_source
            main_candidates = []
            if source:
                main_candidates.append(source)
            main_candidates.extend(
                [
                    str(item.get("url")).strip()
                    for item in media_items
                    if isinstance(item, dict)
                    and (item.get("type") or "image").strip().lower() == "image"
                    and item.get("url")
                ]
            )
            image_data, applied_source, main_errors = self._load_pg_hiper_first_image(main_candidates)
            if source:
                values["hiper_pending_image_source"] = False
            if image_data and applied_source:
                values.update(
                    {
                        "image_1920": image_data,
                        "hiper_last_image_source": applied_source,
                    }
                )
            notes = []
            if main_errors and not applied_source:
                notes.append(f"Main image failed: {main_errors[0]}")
            if media_json:
                if applied_source:
                    media_items = [
                        item
                        for item in media_items
                        if not (
                            isinstance(item, dict)
                            and (item.get("url") or "").strip() == applied_source
                        )
                    ]
                media_errors = self._apply_pg_hiper_extra_media(media_items)
                values["pg_hiper_pending_media_json"] = False
                values["pg_hiper_last_media_fingerprint"] = hashlib.sha1(
                    json.dumps(media_items, ensure_ascii=False, sort_keys=True).encode("utf-8")
                ).hexdigest()
                if media_errors:
                    notes.append(f"Skipped extra media: {', '.join(media_errors[:2])}")
            if notes:
                values["hiper_image_sync_note"] = " | ".join(notes)[:255]
            self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(values)
        except Exception as exc:
            self.sudo().with_context(tracking_disable=True, mail_notrack=True).write(
                {
                    "hiper_image_sync_state": "error",
                    "hiper_image_sync_note": str(exc),
                    "hiper_image_sync_retry_count": self.hiper_image_sync_retry_count + 1,
                    "hiper_image_sync_updated_at": now,
                }
            )
            _logger.warning(
                "Template id=%s image sync failed for source=%s: %s",
                self.id,
                self.hiper_pending_image_source or self.pg_hiper_pending_media_json,
                exc,
            )
        self.env.cr.commit()

    def _apply_pg_hiper_extra_media(self, media_items):
        self.ensure_one()
        ProductImage = self.env["product.image"].sudo()
        desired_urls = [str(item.get("url")).strip() for item in media_items if item.get("url")]
        existing_items = ProductImage.search(
            [
                ("product_tmpl_id", "=", self.id),
                ("pg_source_url", "!=", False),
            ]
        )
        stale_items = existing_items.filtered(lambda media: media.pg_source_url not in desired_urls)
        if stale_items:
            stale_items.unlink()
        existing_by_url = {media.pg_source_url: media for media in existing_items}
        errors = []
        for sequence, item in enumerate(media_items, start=1):
            media_url = (item.get("url") or "").strip()
            if not media_url:
                continue
            media_type = (item.get("type") or "image").strip().lower()
            existing = existing_by_url.get(media_url)
            values = {
                "name": os.path.basename(media_url.split("?", 1)[0]) or f"Media {sequence}",
                "sequence": sequence * 10,
                "product_tmpl_id": self.id,
                "pg_source_url": media_url,
            }
            try:
                if media_type in {"video", "embed"}:
                    values["video_url"] = media_url
                    values["image_1920"] = False
                else:
                    values["image_1920"] = self._load_hiper_image_data(media_url)
                    values["video_url"] = False
                if existing:
                    existing.write(values)
                else:
                    ProductImage.create(values)
            except Exception as exc:
                _logger.warning(
                    "Skipping extra media sync for template=%s url=%s due to error: %s",
                    self.id,
                    media_url,
                    exc,
                )
                errors.append(f"{media_type}:{media_url}")
        return errors

    def _load_pg_hiper_first_image(self, sources):
        errors = []
        seen_sources = set()
        for source in sources:
            source = (source or "").strip()
            if not source or source in seen_sources:
                continue
            seen_sources.add(source)
            try:
                return self._load_hiper_image_data(source), source, errors
            except Exception as exc:
                _logger.warning("Main image fetch failed for template=%s url=%s error=%s", self.id, source, exc)
                errors.append(f"{source} ({exc})")
        return False, False, errors

    @api.model
    def _load_hiper_image_data(self, source):
        if source.startswith(("http://", "https://")):
            headers = self._get_pg_hiper_remote_headers(source)
            response = requests.get(source, headers=headers, timeout=(5, 10))
            response.raise_for_status()
            return base64.b64encode(response.content)
        local_path = source
        if local_path and not os.path.isabs(local_path):
            local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", local_path))
        if not local_path or not os.path.isfile(local_path):
            raise FileNotFoundError("Image source not found: %s" % source)
        with open(local_path, "rb") as handle:
            return base64.b64encode(handle.read())

    @api.model
    def _get_pg_hiper_remote_headers(self, source):
        """Constroi headers HTTP "browser-like" para descarregar imagens.

        Alguns sites de fornecedores bloqueiam User-Agent generico (Python /
        urllib) ou exigem Referer da propria origem; estes headers minimizam
        recusas 403/4xx por deteccao de bot.
        """
        parsed = urlsplit(source)
        referer = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else False
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if referer:
            headers["Referer"] = referer
        return headers
