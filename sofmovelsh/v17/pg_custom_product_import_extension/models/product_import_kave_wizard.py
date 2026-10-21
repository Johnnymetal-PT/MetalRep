# -*- coding: utf-8 -*-
"""Wizard de importacao de produtos Kave Home a partir de Excel.

Pertence ao modulo `pg_custom_product_import_extension`. Le um XLSX da Kave,
faz CREATE/UPDATE/REATIVAR/ARQUIVAR no catalogo Odoo com:
- barreira "so produtos Kave" (`_ensure_kave_only`) para nao tocar em outros;
- caches por default_code/barcode/supplierinfo/orderpoints/quants para evitar
  N+1 querys em datasets grandes;
- writes em savepoint com retries em deadlocks/lock-timeouts via
  `_write_with_retries`;
- publicacao best-effort (downgrade de erros conhecidos a warning);
- email HTML de resumo no fim com tabelas de erros e warnings por linha.

Empresa alvo: ID 2 (hardcoded). Localizacao para quants iniciais: ID 54
(KAV/Stock). Sale tax fallback: id 1567.
"""
import logging
import base64
import time
import pandas as pd
import tempfile
import re
import datetime

import psycopg2
from psycopg2 import errors as pg_errors  # noqa: F401  (kept for possible future use)
from psycopg2 import OperationalError

from odoo import models, fields
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Extra fields on PO lines (declarados aqui para reaproveitamento em PO geradas
# a partir de SO de carpetes; nao confundir com [[pg_buy_and_sell_by_m2]] que
# declara campos com o mesmo nome).
# -------------------------------------------------------------------------
class PurchaseOrderLine(models.Model):
    """Extende `purchase.order.line` com largura/comprimento (campos Studio)."""

    _inherit = 'purchase.order.line'

    x_studio_largura = fields.Float(string="Largura", help="Largura do item (em cm, mm, etc.)")
    x_studio_comprimento = fields.Float(string="Comprimento", help="Comprimento do item")


# -------------------------------------------------------------------------
# Wizard de importacao
# -------------------------------------------------------------------------
class ProductImportKaveWizard(models.TransientModel):
    """Wizard transitorio que orquestra a importacao XLSX da Kave Home."""

    _name = 'product.import.kave.wizard'
    _description = 'Import Products with Kave Tag'

    file = fields.Binary('Excel File', required=True)
    filename = fields.Char('Filename')

    # Context flags to avoid heavy / deadlock-prone automations during mass writes
    CTX_SKIP_PRODUCT_LOG = "skip_product_log"
    CTX_SKIP_SUPPLIER_TAX = "skip_supplier_tax_update"
    CTX_SKIP_TRACKING = "tracking_disable"

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _set_db_timeouts(self, lock_timeout="1s", statement_timeout="120s"):
        """Aplicar timeouts curtos para falhar rápido em locks/queries lentas."""
        try:
            self.env.cr.execute("SET LOCAL lock_timeout = %s", (lock_timeout,))
            self.env.cr.execute("SET LOCAL statement_timeout = %s", (statement_timeout,))
        except Exception as timeout_error:
            _logger.warning("Não foi possível aplicar timeouts no DB", extra={"error": str(timeout_error)})

    def _normalize_value(self, value):
        """Normaliza valores PT (1.234,56) → float."""
        if pd.isna(value):
            return 0.0
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        try:
            match = re.search(r'\.\d+', str(value))
            if match:
                decimal_digits = len(match.group(0)) - 1
                if decimal_digits >= 3:
                    return float(str(value).replace('.', ''))
            return float(value)
        except ValueError:
            raise UserError(f"Formato numérico inválido: {value}")

    def _convert_to_number(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _find_barcode_conflict(self, company_env, barcode, current_template):
        """Procura outro produto (product.product) com o mesmo barcode."""
        if not barcode:
            return None
        return company_env['product.product'].sudo().search([
            ('barcode', '=', barcode),
            ('product_tmpl_id', '!=', current_template.id),
            ('active', 'in', [True, False]),
        ], limit=1)

    def _ensure_kave_only(self, product_template, kave_tag, row_index, code_value):
        """Barreira dura: nunca escrever em produtos nao-Kave.

        Critica para evitar que um conflito de `default_code` ou de barcode
        com um produto de outra marca leve a importacao Kave a sobrescrever
        produtos doutras tags. Rebenta com UserError caso o match dado nao
        tenha a tag Kave.
        """
        if product_template and kave_tag not in product_template.product_tag_ids:
            raise UserError(
                f"[Linha {row_index}] Segurança: foi feito match com produto NÃO-Kave "
                f"(ID {product_template.id}) para Code={code_value}: {product_template.display_name}"
            )

    def _pg_exc_payload(self, exc):
        """Extract useful diagnostics from psycopg2 exceptions (SQLSTATE, constraint, etc.)"""
        payload = {
            "exc_type": type(exc).__name__,
            "exc": str(exc),
        }
        try:
            payload["pgcode"] = getattr(exc, "pgcode", None)
            payload["pgerror"] = getattr(exc, "pgerror", None)
            diag = getattr(exc, "diag", None)
            if diag:
                payload.update({
                    "diag_severity": getattr(diag, "severity", None),
                    "diag_sqlstate": getattr(diag, "sqlstate", None),
                    "diag_message_primary": getattr(diag, "message_primary", None),
                    "diag_message_detail": getattr(diag, "message_detail", None),
                    "diag_message_hint": getattr(diag, "message_hint", None),
                    "diag_constraint_name": getattr(diag, "constraint_name", None),
                    "diag_table_name": getattr(diag, "table_name", None),
                    "diag_column_name": getattr(diag, "column_name", None),
                    "diag_schema_name": getattr(diag, "schema_name", None),
                })
        except Exception:
            pass
        return payload

    def _log_extra_safe(self, extra):
        """
        Prevent LogRecord collisions (e.g. 'name', 'msg', 'levelname', etc.).
        If collisions are present, rename them.
        """
        if not extra:
            return extra
        reserved = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename', 'module',
            'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName', 'created', 'msecs',
            'relativeCreated', 'thread', 'threadName', 'processName', 'process', 'message'
        }
        safe = {}
        for k, v in extra.items():
            if k in reserved:
                safe[f"x_{k}"] = v
            else:
                safe[k] = v
        return safe

    def _is_transient_lock_error(self, err):
        msg = (str(err) or "").lower()
        return (
            ("deadlock detected" in msg) or
            ("could not obtain lock" in msg) or
            ("lock timeout" in msg) or
            ("could not serialize access" in msg) or
            ("serialization failure" in msg)
        )

    def _write_with_retries(self, recordset, vals, retries=4, base_sleep=0.35, row_index=None, code=None, phase="write"):
        """Faz write com retries em deadlock / lock-timeout / serialization.

        Usa savepoint dedicado para que uma falha nao aborte a transacao da
        importacao inteira. So faz retry em erros transientes (`_is_transient_lock_error`);
        outros DB errors sao logados em ERROR e re-raised.
        """
        ctx = {
            self.CTX_SKIP_PRODUCT_LOG: True,
            self.CTX_SKIP_SUPPLIER_TAX: True,
            self.CTX_SKIP_TRACKING: True,
            "mail_notrack": True,
            "mail_create_nosubscribe": True,
            "mail_auto_subscribe_no_notify": True,
        }

        last_err = None
        for attempt in range(1, retries + 1):
            try:
                self._set_db_timeouts(lock_timeout="1s", statement_timeout="120s")
                with self.env.cr.savepoint():
                    recordset.with_context(**ctx).sudo().write(vals)
                return True

            except (OperationalError, psycopg2.Error) as e:
                last_err = e
                payload = self._pg_exc_payload(e)

                if self._is_transient_lock_error(e):
                    sleep_s = base_sleep * attempt
                    _logger.warning(
                        "Lock/deadlock ao escrever (retry)",
                        extra=self._log_extra_safe({
                            "phase": phase,
                            "attempt": attempt,
                            "retries": retries,
                            "sleep_s": sleep_s,
                            "row_index": row_index,
                            "code": code,
                            "record_ids": getattr(recordset, "ids", None),
                            **payload,
                        }),
                    )
                    time.sleep(sleep_s)
                    continue

                _logger.error(
                    "DB erro não-retryable no write (vai re-raise)",
                    extra=self._log_extra_safe({
                        "phase": phase,
                        "row_index": row_index,
                        "code": code,
                        "record_ids": getattr(recordset, "ids", None),
                        **payload,
                    }),
                )
                raise

            except Exception as e:
                last_err = e
                _logger.warning(
                    "Falha ao escrever (sem retry)",
                    extra=self._log_extra_safe({
                        "phase": phase,
                        "row_index": row_index,
                        "code": code,
                        "record_ids": getattr(recordset, "ids", None),
                        "exc_type": type(e).__name__,
                        "error": str(e),
                    }),
                )
                break

        _logger.warning(
            "Write falhou após retries (ignorado)",
            extra=self._log_extra_safe({
                "phase": phase,
                "row_index": row_index,
                "code": code,
                "record_ids": getattr(recordset, "ids", None),
                "error": str(last_err) if last_err else "unknown",
            }),
        )
        return False

    def _add_issue(self, bucket, row_index, code, ean, program, message):
        """
        bucket: dict[row_index] -> issue dict
        Agrega mensagens por linha para não inflacionar o email.
        """
        if row_index not in bucket:
            bucket[row_index] = {
                "row_index": row_index,
                "code": code or "",
                "ean": ean or "",
                "program": program or "",
                "error": message or "",
            }
        else:
            prev = bucket[row_index].get("error") or ""
            if message and message not in prev:
                bucket[row_index]["error"] = (prev + " | " + message) if prev else message

    # -------------------------------------------------------------------------
    # VAT / publishing helpers
    # -------------------------------------------------------------------------
    def _find_default_sale_tax(self, company_env, target_company_id):
        """Resolve uma sale tax default em 3 niveis (id 1567 -> empresa -> shared).

        IMPORTANTE: id 1567 e o IVA standard da empresa Sofmovel nesta BD;
        hardcoded por simplicidade. Migracoes precisam atualizar este ID.
        """
        tax = self.env['account.tax'].sudo().search([
            ('id', '=', 1567),
            ('type_tax_use', '=', 'sale')
        ], limit=1)
        if tax:
            return tax

        # Prefer taxes for the target company
        tax = company_env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', target_company_id),
            ('active', 'in', [True, False]),
        ], order="sequence asc, id asc", limit=1)
        if tax:
            return tax

        # Final fallback (shared taxes / no company)
        tax = company_env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', False),
            ('active', 'in', [True, False]),
        ], order="sequence asc, id asc", limit=1)
        return tax

    def _should_downgrade_publish_error(self, msg):
        """
        Business/validation cases we want to downgrade to warning and unpublish:
        - Unique products with no stock cannot be sold anymore
        - No VAT sale tax defined (or similar)
        """
        m = (msg or "").lower()
        return (
            ("produtos únicos" in m and "sem stock" in m) or
            ("no vat sale tax" in m) or
            ("no vat" in m and "tax" in m) or
            ("no sale tax" in m)
        )

    def _apply_publish_best_effort(self, record, publish, row_index=None, code=None, program=None, bucket=None, reason_prefix=""):
        """Tenta publicar e tolera erros de negocio conhecidos.

        Se a validacao for "Unique products with no stock cannot be sold anymore"
        ou "No VAT sale tax", regista warning, forca `website_published=False`
        e devolve False. Outras ValidationError/UserError continuam a propagar
        para que a linha seja marcada como erro.
        """
        vals = {'website_published': bool(publish)}
        try:
            with self.env.cr.savepoint():
                record.sudo().write(vals)
            return True
        except (ValidationError, UserError) as e:
            msg = str(e)
            if publish and self._should_downgrade_publish_error(msg):
                if bucket is not None:
                    self._add_issue(bucket, row_index, code, "", program, f"{reason_prefix}{msg} (produto NÃO publicado)")
                try:
                    with self.env.cr.savepoint():
                        record.sudo().write({'website_published': False})
                except Exception:
                    # ignore: publishing already failed; we tried to force False
                    pass
                return False
            raise  # other validations should still fail the row
        except (OperationalError, psycopg2.Error):
            raise  # DB errors must be handled by outer savepoint

    # -------------------------------------------------------------------------
    # Promotions detach (best-effort) -- só usar quando necessário
    # -------------------------------------------------------------------------
    def _detach_product_from_promotions_best_effort(self, company_env, product_template):
        """
        Best-effort: tenta descolar o template de modelos de loyalty/promoção
        para reduzir risco de falhas ao arquivar. Nunca rebenta o wizard.
        """
        try:
            fields_obj = self.env['ir.model.fields'].sudo()

            promo_fields = fields_obj.search([
                ('relation', '=', 'product.template'),
                ('ttype', 'in', ['many2many', 'many2one']),
                ('model_id.model', 'in', ['loyalty.program', 'loyalty.rule', 'loyalty.reward']),
            ])

            promo_fields |= fields_obj.search([
                ('relation', '=', 'product.template'),
                ('ttype', 'in', ['many2many', 'many2one']),
                ('model_id.model', 'ilike', '%promotion%'),
            ])

            ctx = {
                self.CTX_SKIP_PRODUCT_LOG: True,
                self.CTX_SKIP_SUPPLIER_TAX: True,
                self.CTX_SKIP_TRACKING: True,
                "mail_notrack": True,
                "mail_create_nosubscribe": True,
                "mail_auto_subscribe_no_notify": True,
            }

            seen = set()
            for f in promo_fields:
                key = (f.model_id.model, f.name)
                if key in seen:
                    continue
                seen.add(key)

                model = company_env[f.model_id.model].sudo()
                try:
                    if f.ttype == 'many2many':
                        recs = model.search([(f.name, 'in', product_template.id)])
                        if recs:
                            recs.with_context(**ctx).write({f.name: [(3, product_template.id)]})
                    else:  # many2one
                        recs = model.search([(f.name, '=', product_template.id)])
                        if recs:
                            recs.with_context(**ctx).write({f.name: False})
                except Exception as e:
                    _logger.warning(
                        "Best-effort detach falhou (ignorado)",
                        extra=self._log_extra_safe({
                            "model": f.model_id.model,
                            "field": f.name,
                            "tmpl_id": product_template.id,
                            "error": str(e),
                        })
                    )
        except Exception as e:
            _logger.warning(
                "Best-effort detach global falhou (ignorado)",
                extra=self._log_extra_safe({"tmpl_id": product_template.id, "error": str(e)})
            )

    # -------------------------------------------------------------------------
    # Archive pass (logs detalhados + detach só quando falha)
    # -------------------------------------------------------------------------
    def _archive_missing_kave_products(self, company_env, kave_tag, imported_codes):
        """Arquiva templates Kave ativos cujo default_code nao consta do Excel.

        Estrategia em dois passos:
        1) tenta arquivar (active=False, website_published=False) sem detach;
        2) se falhar, faz `_detach_product_from_promotions_best_effort` para
           soltar de loyalty/promocoes e tenta novamente.

        Devolve dicionario com estatisticas para o email final
        (`to_archive`, `archived`, `failed_to_archive`, `failed_sample`).
        """
        imported_codes = set([(c or "").strip() for c in imported_codes if c])

        kave_active = company_env['product.template'].sudo().search([
            ('active', '=', True),
            ('product_tag_ids', 'in', [kave_tag.id]),
        ])

        to_archive = kave_active.filtered(lambda t: (t.default_code or '').strip() not in imported_codes)

        _logger.warning(
            "Kave archive pass",
            extra=self._log_extra_safe({
                "kave_active_total": len(kave_active),
                "excel_codes_total": len(imported_codes),
                "to_archive": len(to_archive),
            })
        )

        sample = [(t.id, t.display_name, t.default_code) for t in to_archive[:30]]
        if sample:
            _logger.warning("Amostra de produtos Kave a arquivar", extra=self._log_extra_safe({"sample": sample}))

        archived_count = 0
        failed_count = 0
        failed_details = []  # sample (até 60) para email

        ordered = to_archive.sorted(key=lambda r: r.id)

        for idx, t in enumerate(ordered, start=1):
            code = (t.default_code or "").strip() or None

            _logger.info(
                "Archive attempt",
                extra=self._log_extra_safe({
                    "idx": idx,
                    "total": len(ordered),
                    "tmpl_id": t.id,
                    "code": code,
                    "tmpl_name": t.display_name,
                })
            )

            # 1) tenta arquivar SEM detach
            try:
                ok = self._write_with_retries(
                    t,
                    {'active': False, 'website_published': False},
                    retries=4,
                    base_sleep=0.35,
                    code=code,
                    phase="archive_product_no_detach",
                )
                if ok:
                    archived_count += 1
                    continue
            except (OperationalError, psycopg2.Error) as db_exc:
                _logger.error(
                    "Archive DB error (no detach) — will try detach+retry",
                    extra=self._log_extra_safe({"tmpl_id": t.id, "code": code, **self._pg_exc_payload(db_exc)}),
                )
            except Exception as exc:
                _logger.error(
                    "Archive non-DB error (no detach) — will try detach+retry",
                    extra=self._log_extra_safe({"tmpl_id": t.id, "code": code, "exc_type": type(exc).__name__, "exc": str(exc)}),
                )

            # 2) só agora faz detach e tenta novamente
            try:
                _logger.warning(
                    "Archive retry WITH detach promotions",
                    extra=self._log_extra_safe({"tmpl_id": t.id, "code": code})
                )

                self._detach_product_from_promotions_best_effort(company_env, t)

                ok2 = self._write_with_retries(
                    t,
                    {'active': False, 'website_published': False},
                    retries=4,
                    base_sleep=0.50,
                    code=code,
                    phase="archive_product_with_detach",
                )
                if ok2:
                    archived_count += 1
                    continue

                failed_count += 1
                _logger.error("Archive FAILED after detach+retries", extra=self._log_extra_safe({"tmpl_id": t.id, "code": code}))
                if len(failed_details) < 60:
                    failed_details.append({
                        "tmpl_id": t.id,
                        "code": code,
                        "name": t.display_name,
                        "error": "write_with_retries returned False",
                    })

            except (OperationalError, psycopg2.Error) as db_exc2:
                failed_count += 1
                _logger.error(
                    "Archive DB FAILED after detach+retries",
                    extra=self._log_extra_safe({"tmpl_id": t.id, "code": code, **self._pg_exc_payload(db_exc2)}),
                )
                if len(failed_details) < 60:
                    failed_details.append({"tmpl_id": t.id, "code": code, "name": t.display_name, "error": str(db_exc2)})

            except Exception as exc2:
                failed_count += 1
                _logger.error(
                    "Archive non-DB FAILED after detach+retries",
                    extra=self._log_extra_safe({"tmpl_id": t.id, "code": code, "exc_type": type(exc2).__name__, "exc": str(exc2)}),
                )
                if len(failed_details) < 60:
                    failed_details.append({"tmpl_id": t.id, "code": code, "name": t.display_name, "error": str(exc2)})

        _logger.warning(
            "Archive pass concluído",
            extra=self._log_extra_safe({
                "archived_count": archived_count,
                "failed_count": failed_count,
                "failed_sample": failed_details[:25],
            })
        )

        return {
            "to_archive": len(to_archive),
            "archived": archived_count,
            "failed_to_archive": max(0, len(to_archive) - archived_count),
            "failed_sample": failed_details,
        }

    # -------------------------------------------------------------------------
    # Email
    # -------------------------------------------------------------------------
    def send_success_email(self, processed_rows, errors_by_row, warnings_by_row, archive_stats, total_rows=0, elapsed_s=0.0):
        """Envia resumo ao utilizador atual (best-effort)."""
        email_to = self.env.user.email
        if not email_to:
            _logger.error("Não foi possível enviar email: utilizador sem email configurado.")
            return

        def _table_from_dict(d, title):
            if not d:
                return f"<p><strong>{title}:</strong> Não houve.</p>"
            header = "<tr><th>Linha</th><th>Code</th><th>EAN</th><th>Program</th><th>Detalhe</th></tr>"
            rows = "".join(
                f"<tr><td>{v.get('row_index')}</td><td>{v.get('code') or ''}</td>"
                f"<td>{v.get('ean') or ''}</td><td>{v.get('program') or ''}</td>"
                f"<td>{(v.get('error') or '')}</td></tr>"
                for _, v in sorted(d.items(), key=lambda kv: kv[0])
            )
            return f"<p><strong>{title}:</strong></p><table border='1' cellpadding='4' cellspacing='0'>{header}{rows}</table>"

        failed_sample_html = ""
        if archive_stats and archive_stats.get("failed_sample"):
            header = "<tr><th>Template ID</th><th>Code</th><th>Nome</th><th>Erro</th></tr>"
            rows = "".join(
                f"<tr><td>{x.get('tmpl_id')}</td><td>{x.get('code') or ''}</td><td>{x.get('name') or ''}</td><td>{x.get('error') or ''}</td></tr>"
                for x in archive_stats.get("failed_sample")
            )
            failed_sample_html = (
                "<p><strong>Amostra de falhas ao arquivar (até 60):</strong></p>"
                f"<table border='1' cellpadding='4' cellspacing='0'>{header}{rows}</table>"
            )

        body_html = (
            "<p>O processo de importação Kave terminou.</p>"
            f"<p>Total no Excel: <strong>{total_rows}</strong></p>"
            f"<p>Linhas processadas (sucesso): <strong>{processed_rows}</strong></p>"
            f"<p>Linhas com ERRO: <strong>{len(errors_by_row)}</strong></p>"
            f"<p>Linhas com WARNING: <strong>{len(warnings_by_row)}</strong></p>"
            "<hr/>"
            "<p><strong>Arquivação (Kave ativos que não estão no Excel):</strong></p>"
            f"<p>Para arquivar: <strong>{archive_stats.get('to_archive', 0)}</strong> | "
            f"Arquivados: <strong>{archive_stats.get('archived', 0)}</strong> | "
            f"Falharam: <strong>{archive_stats.get('failed_to_archive', 0)}</strong></p>"
            f"<p>Duração: <strong>{round(elapsed_s, 2)}s</strong></p>"
            "<hr/>"
            f"{_table_from_dict(errors_by_row, 'ERROS por linha')}"
            f"{_table_from_dict(warnings_by_row, 'WARNINGS por linha')}"
            f"{failed_sample_html}"
        )

        mail_values = {
            "email_to": email_to,
            "subject": "Importação Kave concluída",
            "body_html": body_html,
        }

        try:
            self.env["mail.mail"].sudo().create(mail_values).send()
            _logger.info("Email de resumo enviado", extra=self._log_extra_safe({"email_to": email_to}))
        except Exception as email_error:
            _logger.error("Erro a enviar email de resumo", extra=self._log_extra_safe({"error": str(email_error), "email_to": email_to}))

    # -------------------------------------------------------------------------
    # Main
    # -------------------------------------------------------------------------
    def action_import(self):
        start_ts = time.monotonic()
        _logger.info("Starting Kave product import process...")

        # contexto mais leve (e já inclui skips para automações pesadas)
        self = self.with_context(
            tracking_disable=True,
            mail_notrack=True,
            mail_create_nosubscribe=True,
            mail_auto_subscribe_no_notify=True,
            prefetch_fields=False,
            **{
                self.CTX_SKIP_PRODUCT_LOG: True,
                self.CTX_SKIP_SUPPLIER_TAX: True,
            }
        )

        self._set_db_timeouts()

        if not self.file:
            raise UserError("Por favor carregue um ficheiro Excel.")

        # ---------------------------------------------------------------------
        # Read Excel
        # ---------------------------------------------------------------------
        try:
            file_data = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_data)
                tmp_file_path = tmp_file.name

            df = pd.read_excel(tmp_file_path)

            # EAN -> string sem decimais
            if 'EAN Code' in df.columns:
                df['EAN Code'] = df['EAN Code'].apply(lambda x: str(int(x)) if pd.notna(x) else '')
        except Exception as e:
            _logger.error("Erro a ler Excel: %s", str(e))
            raise UserError(f"Erro a processar Excel: {str(e)}")

        required_columns = [
            'Code', 'EAN Code', 'Program', 'Description', 'Stock',
            'Purchase Price', 'Discount', 'Nett Purchase Price',
            'Recommended Retail Price', 'Suggested Retail Price',
            'Weight Package', 'Stock Blue', 'Stock Red', 'Stock Grey',
            'Estimated Date (dd/mm/yyyy)'
        ]
        for col in required_columns:
            if col not in df.columns:
                raise UserError(f"Coluna obrigatória em falta: {col}")

        # normalizar numéricos
        for c in ['Purchase Price', 'Recommended Retail Price', 'Suggested Retail Price', 'Nett Purchase Price', 'Discount']:
            df[c] = df[c].apply(self._normalize_value)

        total_rows = len(df)
        _logger.info("Excel loaded", extra=self._log_extra_safe({"total_rows": total_rows}))

        imported_codes = [c for c in df['Code'].tolist() if c]
        imported_barcodes = [b for b in df['EAN Code'].tolist() if b]

        # ---------------------------------------------------------------------
        # Static env + refs
        # IMPORTANTE: a empresa alvo esta hardcoded (id=2 = Sofmovel nesta BD).
        # Em qualquer outro ambiente este valor tem de ser ajustado.
        # ---------------------------------------------------------------------
        target_company_id = 2
        target_company = self.env['res.company'].sudo().browse(target_company_id)
        if not target_company:
            raise UserError(f"Empresa alvo com ID {target_company_id} não encontrada.")

        company_env = self.with_company(target_company).sudo().env

        # Tag Kave
        kave_tag = self.env['product.tag'].sudo().search([('name', '=', 'Kave')], limit=1)
        if not kave_tag:
            kave_tag = self.env['product.tag'].sudo().create({'name': 'Kave'})

        # Categorias
        kave_category = self.env['product.category'].sudo().search([('name', '=', 'Produtos Kave')], limit=1)
        if not kave_category:
            all_category = self.env['product.category'].sudo().search([('name', '=', 'All')], limit=1)
            kave_category = self.env['product.category'].sudo().create({
                'name': 'Produtos Kave',
                'parent_id': all_category.id if all_category else False
            })

        kave_public_category = self.env['product.public.category'].sudo().search([('name', '=', 'Produtos Kave')], limit=1)
        if not kave_public_category:
            todas_category = self.env['product.public.category'].sudo().search([('name', '=', 'Todas')], limit=1)
            kave_public_category = self.env['product.public.category'].sudo().create({
                'name': 'Produtos Kave',
                'parent_id': todas_category.id if todas_category else False
            })

        pos_category = self.env['pos.category'].sudo().search([('name', '=', 'Produtos Kave')], limit=1)
        if not pos_category:
            pos_category = self.env['pos.category'].sudo().create({'name': 'Produtos Kave'})

        # IVA (venda) - robust
        default_vat_tax = self._find_default_sale_tax(company_env, target_company_id)
        if not default_vat_tax:
            _logger.warning(
                "Não foi encontrado IVA de venda (sale tax). Produtos podem ficar não publicados.",
                extra=self._log_extra_safe({"company_id": target_company_id}),
            )

        # Fornecedor
        kave_home_vendor = self.env['res.partner'].sudo().search([('name', '=', 'Kave Home')], limit=1)
        if not kave_home_vendor:
            raise UserError("Fornecedor 'Kave Home' não encontrado. Crie-o primeiro.")

        # Rotas
        buy_route = self.env['stock.route'].sudo().search([('name', '=', 'Comprar')], limit=1)
        if not buy_route:
            raise UserError('Rota "Comprar" não encontrada')

        supply_route_1 = self.env['stock.route'].sudo().search([('name', '=', 'BRAGA: Supply Product from FREAMUNDE')], limit=1)
        supply_route_2 = self.env['stock.route'].sudo().search([('name', '=', 'SEIXAL: Supply Product from FREAMUNDE')], limit=1)
        if not supply_route_1 or not supply_route_2:
            raise UserError('Rotas de supply não encontradas')

        valid_locations = {
            "FRE/Stock": {"parent": "FREAMUNDE", "route": buy_route},
            "BRA/Stock": {"parent": "BRAGA", "route": supply_route_1},
            "SEI/Stock": {"parent": "SEIXAL", "route": supply_route_2}
        }

        # ---------------------------------------------------------------------
        # Preload: APENAS KAVE
        # ---------------------------------------------------------------------
        preload_domain = [
            '&',
                ('product_tag_ids', 'in', [kave_tag.id]),
                '|',
                    ('default_code', 'in', imported_codes),
                    ('x_studio_cdigo_de_barras', 'in', imported_barcodes),
        ]
        preload_products = company_env['product.template'].sudo().search(preload_domain)

        products_by_code = {p.default_code: p for p in preload_products if p.default_code}
        products_by_barcode = {p.x_studio_cdigo_de_barras: p for p in preload_products if p.x_studio_cdigo_de_barras}

        # Supplierinfo preload (só templates Kave)
        supplierinfos = company_env['product.supplierinfo'].sudo().search([
            ('partner_id', '=', kave_home_vendor.id),
            ('product_tmpl_id', 'in', preload_products.ids)
        ])
        supplierinfo_by_tmpl = {si.product_tmpl_id.id: si for si in supplierinfos}

        # Locations cache
        location_cache = {}
        for loc_name, data in valid_locations.items():
            loc = company_env['stock.location'].sudo().search([
                ('complete_name', '=', loc_name),
                ('company_id', '=', target_company_id),
            ], limit=1)
            if not loc:
                loc = company_env['stock.location'].sudo().search([
                    ('name', '=', 'Stock'),
                    ('location_id.name', '=', data["parent"]),
                    ('company_id', '=', target_company_id),
                ], limit=1)
            if loc:
                location_cache[loc_name] = loc

        # Orderpoints preload
        existing_orderpoints = company_env['stock.warehouse.orderpoint'].sudo().search([
            ('product_id.product_tmpl_id', 'in', preload_products.ids),
            ('location_id', 'in', [l.id for l in location_cache.values()]),
        ])
        orderpoint_keyset = set((op.product_id.id, op.location_id.id, op.company_id.id) for op in existing_orderpoints)

        # Quants preload. ID 54 corresponde a KAV/Stock nesta BD (hardcoded).
        existing_quants = company_env['stock.quant'].sudo().search([
            ('product_id.product_tmpl_id', 'in', preload_products.ids),
            ('location_id', '=', 54),
            ('company_id', '=', target_company_id),
        ])
        quant_by_product = {q.product_id.id: q for q in existing_quants}

        # ---------------------------------------------------------------------
        # Import loop
        # ---------------------------------------------------------------------
        processed_rows = 0

        errors_by_row = {}
        warnings_by_row = {}

        # progress logs
        progress_every_rows = 50
        progress_every_seconds = 30
        last_progress_log_ts = time.monotonic()

        # Context para writes dentro do loop
        write_ctx = {
            self.CTX_SKIP_PRODUCT_LOG: True,
            self.CTX_SKIP_SUPPLIER_TAX: True,
            self.CTX_SKIP_TRACKING: True,
            "mail_notrack": True,
            "mail_create_nosubscribe": True,
            "mail_auto_subscribe_no_notify": True,
        }

        for row_index, (_, row) in enumerate(df.iterrows(), start=1):
            self._set_db_timeouts(lock_timeout="1s", statement_timeout="120s")

            # heartbeat
            now = time.monotonic()
            if row_index == 1 or (row_index % progress_every_rows == 0) or ((now - last_progress_log_ts) >= progress_every_seconds):
                _logger.info(
                    "Kave import progresso",
                    extra=self._log_extra_safe({
                        "row": row_index,
                        "total": total_rows,
                        "processed": processed_rows,
                        "errors": len(errors_by_row),
                        "warnings": len(warnings_by_row),
                        "elapsed_s": round(now - start_ts, 1),
                    }),
                )
                last_progress_log_ts = now

            code_value = (row.get('Code') or '').strip()
            ean_value = (row.get('EAN Code') or '').strip()
            program = (row.get('Program') or '').strip()

            if not code_value:
                self._add_issue(errors_by_row, row_index, "", ean_value, program, "Code em falta")
                continue

            try:
                with self.env.cr.savepoint():
                    # ---------------------------------------------------------
                    # Match EXISTENTE: apenas caches Kave
                    # ---------------------------------------------------------
                    product_template = products_by_code.get(code_value) or products_by_barcode.get(ean_value)
                    self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                    # ---------------------------------------------------------
                    # Reativar apenas se for Kave e arquivado (match por Code)
                    # ---------------------------------------------------------
                    if not product_template:
                        archived_kave = company_env['product.template'].sudo().search([
                            ('active', '=', False),
                            ('product_tag_ids', 'in', [kave_tag.id]),
                            ('default_code', '=', code_value),
                        ], order='create_date desc', limit=1)

                        if archived_kave:
                            product_template = archived_kave
                            self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                            # Reactivate: if publish fails (tax/unique-stock rules), downgrade to warning and keep active.
                            self._write_with_retries(
                                product_template,
                                {'active': True},
                                retries=3,
                                base_sleep=0.25,
                                row_index=row_index,
                                code=code_value,
                                phase="reactivate_kave_active_only",
                            )
                            self._apply_publish_best_effort(
                                product_template,
                                True,
                                row_index=row_index,
                                code=code_value,
                                program=program,
                                bucket=warnings_by_row,
                                reason_prefix="Reativação: ",
                            )

                            products_by_code[code_value] = product_template
                            if ean_value:
                                products_by_barcode[ean_value] = product_template

                    # ---------------------------------------------------------
                    # Pesos
                    # ---------------------------------------------------------
                    weight_package = str(row.get('Weight Package') or '0')
                    if '#' in weight_package:
                        weights = [float(w.replace(',', '.')) for w in weight_package.split('#') if w]
                        total_weight = sum(weights) if weights else 0.0
                        volume_qty = len(weights) if weights else 1
                        peso_cada_volume = ' / '.join(weight_package.split('#'))
                    else:
                        total_weight = float(weight_package.replace(',', '.')) if weight_package else 0.0
                        volume_qty = 1
                        peso_cada_volume = weight_package or '0'

                    purchase_price = row.get('Nett Purchase Price') or 0.0

                    # ---------------------------------------------------------
                    # Valores base (SEM company_id aqui!)
                    # company_id só no CREATE para evitar erro "company cannot be changed"
                    # IMPORTANT: do NOT force website_published=True here anymore.
                    # We'll set publishing best-effort after ensuring VAT + validations.
                    # ---------------------------------------------------------
                    base_vals = {
                        'name': program,
                        'default_code': code_value,
                        'description_sale': row.get('Description') or '',
                        'list_price': row.get('Suggested Retail Price') or 0.0,
                        'standard_price': purchase_price,
                        'weight': total_weight,
                        'volume_qty': volume_qty,
                        'peso_cada_volume': peso_cada_volume,
                        'x_studio_stock_em_7_dias': row.get('Stock Blue') or 0.0,
                        'x_studio_stock_em_15_dias': row.get('Stock Red') or 0.0,
                        'x_studio_stock_em_30_dias': row.get('Stock Grey') or 0.0,
                        'x_studio_preo_antes_desconto': row.get('Recommended Retail Price') or 0.0,
                        'compare_list_price': row.get('Recommended Retail Price') or 0.0,
                        'x_studio_desconto_aplicado_1': row.get('Discount') or 0.0,
                        'sale_delay': 30,
                        'type': 'product',
                        'available_in_pos': True,
                        'allow_out_of_stock_order': True,
                        'categ_id': kave_category.id,
                        'public_categ_ids': [(6, 0, [kave_public_category.id])],
                        'pos_categ_ids': [(6, 0, [pos_category.id])],
                    }

                    if base_vals['compare_list_price'] == base_vals['list_price']:
                        base_vals['compare_list_price'] = None

                    # ---------------------------------------------------------
                    # CREATE ou UPDATE
                    # ---------------------------------------------------------
                    if not product_template:
                        create_vals = dict(base_vals)
                        create_vals.update({
                            'company_id': target_company_id,
                            'barcode': ean_value,
                            'x_studio_cdigo_de_barras': ean_value,
                            'product_tag_ids': [(4, kave_tag.id)],
                            # default to NOT published; we'll publish best-effort later
                            'website_published': False,
                        })
                        if default_vat_tax:
                            create_vals['taxes_id'] = [(6, 0, [default_vat_tax.id])]

                        product_template = company_env['product.template'].with_context(**write_ctx).sudo().create(create_vals)

                        products_by_code[code_value] = product_template
                        if ean_value:
                            products_by_barcode[ean_value] = product_template
                    else:
                        self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                        update_vals = dict(base_vals)

                        # -----------------------------------------------------------------
                        # IMPORTANT CHANGE: match old behavior on UPDATE for categories.
                        # Only set categories if the corresponding fields are currently empty.
                        # This prevents removing/replacing existing Backoffice/Website/POS categories.
                        # -----------------------------------------------------------------
                        if product_template.categ_id:
                            update_vals.pop('categ_id', None)
                        if product_template.public_categ_ids:
                            update_vals.pop('public_categ_ids', None)
                        if product_template.pos_categ_ids:
                            update_vals.pop('pos_categ_ids', None)
                        # -----------------------------------------------------------------

                        # barcode safe update
                        if ean_value:
                            conflict = self._find_barcode_conflict(company_env, ean_value, product_template)
                            if conflict:
                                self._add_issue(
                                    warnings_by_row, row_index, code_value, ean_value, program,
                                    f"Barcode já usado por {conflict.display_name}. Barcode não atualizado."
                                )
                            else:
                                update_vals['barcode'] = ean_value
                                update_vals['x_studio_cdigo_de_barras'] = ean_value

                        # protect update with savepoint to prevent tx abort
                        with self.env.cr.savepoint():
                            product_template.with_context(**write_ctx).sudo().write(update_vals)

                    # Ensure sale VAT tax (best effort) BEFORE publishing
                    if default_vat_tax:
                        try:
                            with self.env.cr.savepoint():
                                if (
                                    not product_template.taxes_id
                                    or not product_template.taxes_id.filtered(lambda t: t.type_tax_use == 'sale')
                                ):
                                    product_template.with_context(**write_ctx).sudo().write({
                                        'taxes_id': [(6, 0, [default_vat_tax.id])]
                                    })
                        except (OperationalError, psycopg2.Error) as db_exc:
                            _logger.error(
                                "DB erro ao garantir IVA de venda (rollback via savepoint).",
                                extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(db_exc)}),
                            )
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Erro DB a garantir IVA de venda: {str(db_exc)}"
                            )

                    # Finally: publish best-effort (downgrade known errors to warnings)
                    # If no default tax was found, do not attempt to publish.
                    if default_vat_tax:
                        self._apply_publish_best_effort(
                            product_template,
                            True,
                            row_index=row_index,
                            code=code_value,
                            program=program,
                            bucket=warnings_by_row,
                            reason_prefix="Publicação: ",
                        )
                    else:
                        # Keep not published and warn once per row
                        self._add_issue(
                            warnings_by_row, row_index, code_value, ean_value, program,
                            "Sem IVA de venda configurado no sistema — produto NÃO publicado."
                        )
                        try:
                            with self.env.cr.savepoint():
                                product_template.with_context(**write_ctx).sudo().write({'website_published': False})
                        except Exception:
                            pass

                    variant = product_template.product_variant_id

                    # ---------------------------------------------------------
                    # Acessórios por Program
                    # IMPORTANT: proteger com savepoint próprio para nunca deixar a tx abortada
                    # ---------------------------------------------------------
                    if program:
                        try:
                            with self.env.cr.savepoint():
                                similar_products = company_env['product.template'].sudo().search([('name', '=', program)])
                                accessory_ids = []
                                for prod in similar_products:
                                    if prod.product_variant_id and prod.product_variant_id.active and prod.product_variant_id.id != variant.id:
                                        accessory_ids.append(prod.product_variant_id.id)

                                if accessory_ids:
                                    product_template.with_context(**write_ctx).sudo().write({
                                        'accessory_product_ids': [(4, pid) for pid in accessory_ids]
                                    })
                        except (OperationalError, psycopg2.Error) as db_exc:
                            _logger.error(
                                "DB erro no bloco de acessórios (rollback via savepoint).",
                                extra=self._log_extra_safe({"row_index": row_index, "code": code_value, "program": program, **self._pg_exc_payload(db_exc)}),
                            )
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Erro acessórios (DB): {str(db_exc)}"
                            )
                        except Exception as acc_exc:
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Erro acessórios: {str(acc_exc)}"
                            )

                    # ---------------------------------------------------------
                    # Supplierinfo upsert (guard with savepoint)
                    # ---------------------------------------------------------
                    try:
                        with self.env.cr.savepoint():
                            si = supplierinfo_by_tmpl.get(product_template.id)
                            si_vals = {
                                'price': row.get('Purchase Price') or 0.0,
                                'discount': row.get('Discount') or 0.0,
                                'currency_id': self.env.ref('base.EUR').id,
                                'partner_id': kave_home_vendor.id,
                                'product_tmpl_id': product_template.id,
                            }
                            if si:
                                si.with_context(**write_ctx).sudo().write(si_vals)
                            else:
                                si = company_env['product.supplierinfo'].with_context(**write_ctx).sudo().create(si_vals)
                                supplierinfo_by_tmpl[product_template.id] = si
                    except (OperationalError, psycopg2.Error) as db_exc:
                        _logger.error(
                            "DB erro supplierinfo (rollback via savepoint).",
                            extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(db_exc)}),
                        )
                        self._add_issue(
                            warnings_by_row, row_index, code_value, ean_value, program,
                            f"Erro DB supplierinfo: {str(db_exc)}"
                        )

                    # ---------------------------------------------------------
                    # Stock quant KAV/Stock (54) (guard with savepoint)
                    # ---------------------------------------------------------
                    qty_stock = row.get('Stock') or 0.0
                    try:
                        with self.env.cr.savepoint():
                            q = quant_by_product.get(variant.id)
                            if q:
                                q.with_context(**write_ctx).sudo().write({'quantity': qty_stock, 'company_id': target_company_id})
                            else:
                                q = company_env['stock.quant'].with_context(**write_ctx).sudo().create({
                                    'product_id': variant.id,
                                    'location_id': 54,
                                    'company_id': target_company_id,
                                    'quantity': qty_stock,
                                })
                                quant_by_product[variant.id] = q

                            product_template.with_context(**write_ctx).sudo().write({'x_studio_quantidade_em_stock': str(qty_stock)})
                    except (OperationalError, psycopg2.Error) as db_exc:
                        _logger.error(
                            "DB erro stock quant (rollback via savepoint).",
                            extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(db_exc)}),
                        )
                        self._add_issue(
                            warnings_by_row, row_index, code_value, ean_value, program,
                            f"Erro DB stock quant: {str(db_exc)}"
                        )

                    # ---------------------------------------------------------
                    # Data estimada + sale_delay
                    # IMPORTANT: proteger writes com savepoints próprios
                    # ---------------------------------------------------------
                    est = row.get('Estimated Date (dd/mm/yyyy)')
                    if pd.notna(est):
                        try:
                            estimated_dt = pd.to_datetime(est, format='%d/%m/%Y', errors='raise')
                            try:
                                with self.env.cr.savepoint():
                                    product_template.with_context(**write_ctx).sudo().write({
                                        'x_studio_data_estimada_de_entrega': estimated_dt
                                    })
                            except (OperationalError, psycopg2.Error) as db_exc:
                                _logger.error(
                                    "DB erro ao escrever data estimada (rollback via savepoint).",
                                    extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(db_exc)}),
                                )
                                self._add_issue(
                                    warnings_by_row, row_index, code_value, ean_value, program,
                                    f"Erro DB a gravar data estimada: {str(db_exc)}"
                                )
                        except Exception:
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Data estimada inválida: {est}"
                            )

                    data_estimada = product_template.x_studio_data_estimada_de_entrega
                    quantidade_em_stock = self._convert_to_number(product_template.x_studio_quantidade_em_stock) or 0.0
                    stock_7 = self._convert_to_number(product_template.x_studio_stock_em_7_dias) or 0.0
                    stock_15 = self._convert_to_number(product_template.x_studio_stock_em_15_dias) or 0.0
                    stock_30 = self._convert_to_number(product_template.x_studio_stock_em_30_dias) or 0.0

                    try:
                        with self.env.cr.savepoint():
                            if data_estimada:
                                if isinstance(data_estimada, datetime.datetime):
                                    dt_date = data_estimada.date()
                                elif isinstance(data_estimada, datetime.date):
                                    dt_date = data_estimada
                                else:
                                    dt_date = fields.Date.context_today(self)

                                sale_delay_days = (dt_date - fields.Date.context_today(self)).days
                                product_template.with_context(**write_ctx).sudo().write({'sale_delay': max(sale_delay_days, 0)})
                            else:
                                if quantidade_em_stock > 0:
                                    sd = 30
                                elif stock_7 > 0:
                                    sd = 45
                                elif stock_15 > 0:
                                    sd = 60
                                elif stock_30 > 0:
                                    sd = 70
                                else:
                                    sd = 30
                                product_template.with_context(**write_ctx).sudo().write({'sale_delay': sd})
                    except (OperationalError, psycopg2.Error) as db_exc:
                        _logger.error(
                            "DB erro sale_delay (rollback via savepoint).",
                            extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(db_exc)}),
                        )
                        self._add_issue(
                            warnings_by_row, row_index, code_value, ean_value, program,
                            f"Erro DB sale_delay: {str(db_exc)}"
                        )

                    # ---------------------------------------------------------
                    # Orderpoints por localização (se não existir)
                    # IMPORTANT: usar savepoint por orderpoint
                    # ---------------------------------------------------------
                    for loc_name, data in valid_locations.items():
                        loc = location_cache.get(loc_name)
                        if not loc:
                            continue
                        if data["route"].company_id and data["route"].company_id.id != loc.company_id.id:
                            continue

                        key = (variant.id, loc.id, loc.company_id.id)
                        if key in orderpoint_keyset:
                            continue

                        try:
                            with self.env.cr.savepoint():
                                company_env['stock.warehouse.orderpoint'].with_context(**write_ctx).sudo().create({
                                    'product_id': variant.id,
                                    'location_id': loc.id,
                                    'company_id': loc.company_id.id,
                                    'route_id': data["route"].id,
                                    'product_min_qty': 0.0,
                                    'product_max_qty': 0.0,
                                    'qty_multiple': 1.0,
                                    'trigger': 'auto',
                                })
                            orderpoint_keyset.add(key)

                        except (OperationalError, psycopg2.Error) as oe:
                            _logger.error(
                                "DB erro a criar orderpoint (rollback via savepoint).",
                                extra=self._log_extra_safe({"row_index": row_index, "code": code_value, "loc": loc_name, **self._pg_exc_payload(oe)}),
                            )
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Erro DB orderpoint ({loc_name}): {str(oe)}"
                            )
                        except Exception as oe2:
                            self._add_issue(
                                warnings_by_row, row_index, code_value, ean_value, program,
                                f"Erro orderpoint ({loc_name}): {str(oe2)}"
                            )

                    processed_rows += 1

            except (ValidationError, UserError, OperationalError, psycopg2.Error) as exc:
                # aqui já saímos do savepoint da linha => rollback feito
                if isinstance(exc, (OperationalError, psycopg2.Error)):
                    _logger.error(
                        "DB erro na linha (rollback via savepoint da linha).",
                        extra=self._log_extra_safe({"row_index": row_index, "code": code_value, **self._pg_exc_payload(exc)}),
                    )
                self._add_issue(errors_by_row, row_index, code_value, ean_value, program, str(exc))
                continue

            except Exception as exc:
                self._add_issue(errors_by_row, row_index, code_value, ean_value, program, f"Erro inesperado: {str(exc)}")
                continue

        # ---------------------------------------------------------------------
        # Arquivar Kave ativos que NÃO estão no Excel
        # ---------------------------------------------------------------------
        _logger.warning("A iniciar archive pass (Kave ativos que não estão no Excel)...")
        archive_stats = self._archive_missing_kave_products(company_env, kave_tag, imported_codes)

        elapsed = time.monotonic() - start_ts
        _logger.info(
            "Kave import finished",
            extra=self._log_extra_safe({
                "processed_rows": processed_rows,
                "errors_rows": len(errors_by_row),
                "warnings_rows": len(warnings_by_row),
                "total_rows": total_rows,
                "archived_missing": archive_stats.get("archived", 0),
                "archive_failed": archive_stats.get("failed_to_archive", 0),
                "elapsed_s": round(elapsed, 2),
            }),
        )

        if errors_by_row:
            _logger.warning("Importação Kave terminou com erros", extra=self._log_extra_safe({"errors_rows_count": len(errors_by_row)}))

        self.send_success_email(
            processed_rows=processed_rows,
            errors_by_row=errors_by_row,
            warnings_by_row=warnings_by_row,
            archive_stats=archive_stats,
            total_rows=total_rows,
            elapsed_s=elapsed,
        )
        return {'type': 'ir.actions.act_window_close', 'processed': processed_rows}
