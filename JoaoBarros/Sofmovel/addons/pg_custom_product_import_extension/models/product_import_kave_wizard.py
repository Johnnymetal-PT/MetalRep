# -*- coding: utf-8 -*-
import logging
import base64
import time
import pandas as pd
import tempfile
import re

from odoo import _, models, fields, api
from odoo.exceptions import UserError, ValidationError
from psycopg2 import OperationalError

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_studio_largura = fields.Float(
        string="Largura",
        help="Largura do item (em cm, mm, etc.)"
    )
    x_studio_comprimento = fields.Float(
        string="Comprimento",
        help="Comprimento do item"
    )


class ProductImportKaveWizard(models.TransientModel):
    _name = 'product.import.kave.wizard'
    _description = 'Import Products with Kave Tag'

    file = fields.Binary('Excel File', required=True)
    filename = fields.Char('Filename')

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _set_db_timeouts(self, lock_timeout="5s", statement_timeout="120s"):
        """Apply short DB timeouts so the wizard fails fast instead of hanging."""
        try:
            self.env.cr.execute("SET LOCAL lock_timeout = %s", (lock_timeout,))
            self.env.cr.execute("SET LOCAL statement_timeout = %s", (statement_timeout,))
        except Exception as timeout_error:
            _logger.warning(
                "Unable to set PostgreSQL timeouts for import",
                extra={"error": str(timeout_error)},
            )

    def send_success_email(self, processed_rows, failed_rows):
        """Send import summary to current user."""
        email_to = self.env.user.email
        if not email_to:
            _logger.error("Cannot send success email because the user has no email set.")
            return

        skipped_rows_section = "<p>No rows were skipped.</p>"
        if failed_rows:
            header = "<tr><th>Row</th><th>Code</th><th>EAN</th><th>Program</th><th>Error</th></tr>"
            rows = "".join(
                f"<tr><td>{row.get('row_index')}</td><td>{row.get('code') or ''}</td>"
                f"<td>{row.get('ean') or ''}</td><td>{row.get('program') or ''}</td>"
                f"<td>{row.get('error') or ''}</td></tr>"
                for row in failed_rows
            )
            skipped_rows_section = (
                f"<p>Skipped rows:</p>"
                f"<table border='1' cellpadding='4' cellspacing='0'>{header}{rows}</table>"
            )

        body_html = (
            "<p>The Kave import process has finished.</p>"
            f"<p>Processed rows: <strong>{processed_rows}</strong></p>"
            f"<p>Skipped rows: <strong>{len(failed_rows)}</strong></p>"
            f"{skipped_rows_section}"
        )

        mail_values = {
            "email_to": email_to,
            "subject": "Kave import completed",
            "body_html": body_html,
        }

        try:
            self.env["mail.mail"].sudo().create(mail_values).send()
            _logger.info("Kave import summary email sent", extra={"email_to": email_to})
        except Exception as email_error:
            _logger.error(
                "Error sending Kave import summary email",
                extra={"error": str(email_error), "email_to": email_to},
            )

    def _normalize_value(self, value):
        """Normalize prices/discounts coming from PT formatted Excel."""
        if pd.isna(value):
            return 0.0
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')
        try:
            if isinstance(value, float) or isinstance(value, str):
                match = re.search(r'\.\d+', str(value))
                if match:
                    decimal_digits = len(match.group(0)) - 1
                    if decimal_digits >= 3:
                        return float(str(value).replace('.', ''))
            return float(value)
        except ValueError:
            raise UserError(f"Invalid number format: {value}")

    def _convert_to_number(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _find_barcode_conflict(self, company_env, barcode, current_template):
        """
        Find any OTHER product that already uses this barcode.
        If found, we skip barcode update to avoid import abort.
        """
        if not barcode:
            return None
        return company_env['product.product'].sudo().search([
            ('barcode', '=', barcode),
            ('product_tmpl_id', '!=', current_template.id),
            ('active', 'in', [True, False]),
        ], limit=1)

    def _ensure_kave_only(self, product_template, kave_tag, row_index, code_value):
        """Hard safety check: never write to non-Kave products."""
        if product_template and kave_tag not in product_template.product_tag_ids:
            raise UserError(
                f"[Row {row_index}] Safety stop: matched non-Kave product "
                f"(ID {product_template.id}) for code {code_value}: {product_template.display_name}"
            )

    # -------------------------------------------------------------------------
    # Main import
    # -------------------------------------------------------------------------
    def action_import(self):
        start_ts = time.monotonic()
        _logger.info("Starting Kave product import process...")

        # speed-focused context
        self = self.with_context(
            tracking_disable=True,
            mail_notrack=True,
            mail_create_nosubscribe=True,
            mail_auto_subscribe_no_notify=True,
            prefetch_fields=False,
        )
        self._set_db_timeouts()

        if not self.file:
            raise UserError("Please upload an Excel file.")

        # ---------------------------------------------------------------------
        # Read Excel
        # ---------------------------------------------------------------------
        try:
            file_data = base64.b64decode(self.file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(file_data)
                tmp_file_path = tmp_file.name

            df = pd.read_excel(tmp_file_path)

            # EAN -> string without decimals
            if 'EAN Code' in df.columns:
                df['EAN Code'] = df['EAN Code'].apply(
                    lambda x: str(int(x)) if pd.notna(x) else ''
                )

        except Exception as e:
            _logger.error("Error reading Excel file: %s", str(e))
            raise UserError(f"Error processing Excel file: {str(e)}")

        required_columns = [
            'Code', 'EAN Code', 'Program', 'Description', 'Stock',
            'Purchase Price', 'Discount', 'Nett Purchase Price',
            'Recommended Retail Price', 'Suggested Retail Price',
            'Weight Package', 'Stock Blue', 'Stock Red', 'Stock Grey',
            'Estimated Date (dd/mm/yyyy)'
        ]
        for col in required_columns:
            if col not in df.columns:
                raise UserError(f"Missing required column: {col}")

        # normalize numeric columns
        for c in [
            'Purchase Price', 'Recommended Retail Price', 'Suggested Retail Price',
            'Nett Purchase Price', 'Discount'
        ]:
            df[c] = df[c].apply(self._normalize_value)

        total_rows = len(df)
        _logger.info("Excel loaded", extra={"total_rows": total_rows})

        # ---------------------------------------------------------------------
        # Static/cached env + references
        # ---------------------------------------------------------------------
        target_company_id = 2
        target_company = self.env['res.company'].sudo().browse(target_company_id)
        if not target_company:
            raise UserError(f"Target company with ID {target_company_id} not found.")

        company_env = self.with_company(target_company).sudo().env

        # Tag (must exist, but we will NEVER add it to non-Kave products here)
        kave_tag = self.env['product.tag'].sudo().search([('name', '=', 'Kave')], limit=1)
        if not kave_tag:
            kave_tag = self.env['product.tag'].sudo().create({'name': 'Kave'})

        # Categories
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

        # VAT tax
        default_vat_tax = self.env['account.tax'].sudo().search([
            ('id', '=', 1567),
            ('type_tax_use', '=', 'sale')
        ], limit=1)

        # Vendor
        kave_home_vendor = self.env['res.partner'].sudo().search([('name', '=', 'Kave Home')], limit=1)
        if not kave_home_vendor:
            raise UserError("Vendor 'Kave Home' not found. Please create this vendor.")

        # Routes
        buy_route = self.env['stock.route'].sudo().search([('name', '=', 'Comprar')], limit=1)
        if not buy_route:
            raise UserError('Buy Route not found')

        supply_route_1 = self.env['stock.route'].sudo().search([('name', '=', 'BRAGA: Supply Product from FREAMUNDE')], limit=1)
        supply_route_2 = self.env['stock.route'].sudo().search([('name', '=', 'SEIXAL: Supply Product from FREAMUNDE')], limit=1)
        if not supply_route_1 or not supply_route_2:
            raise UserError('Supply Route not found')

        valid_locations = {
            "FRE/Stock": {"parent": "FREAMUNDE", "route": buy_route},
            "BRA/Stock": {"parent": "BRAGA", "route": supply_route_1},
            "SEI/Stock": {"parent": "SEIXAL", "route": supply_route_2}
        }

        # ---------------------------------------------------------------------
        # Preload products + maps (KAVE ONLY!)
        # ---------------------------------------------------------------------
        imported_codes = [c for c in df['Code'].tolist() if c]
        imported_barcodes = [b for b in df['EAN Code'].tolist() if b]

        # IMPORTANT CHANGE:
        # Preload ONLY products that ALREADY HAVE the Kave tag.
        preload_domain = [
            '&',
                ('product_tag_ids', 'in', [kave_tag.id]),
                '|',
                    ('x_studio_referncia_interna', 'in', imported_codes),
                    ('x_studio_cdigo_de_barras', 'in', imported_barcodes),
        ]
        preload_products = company_env['product.template'].sudo().search(preload_domain)

        products_by_code = {p.x_studio_referncia_interna: p for p in preload_products if p.x_studio_referncia_interna}
        products_by_barcode = {p.x_studio_cdigo_de_barras: p for p in preload_products if p.x_studio_cdigo_de_barras}

        # Supplierinfo preload (Kave-only templates)
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

        # Existing orderpoints preload (Kave-only templates)
        existing_orderpoints = company_env['stock.warehouse.orderpoint'].sudo().search([
            ('product_id.product_tmpl_id', 'in', preload_products.ids),
            ('location_id', 'in', [l.id for l in location_cache.values()]),
        ])
        orderpoint_keyset = set(
            (op.product_id.id, op.location_id.id, op.company_id.id) for op in existing_orderpoints
        )

        # Quants preload for KAV/Stock (Kave-only templates)
        existing_quants = company_env['stock.quant'].sudo().search([
            ('product_id.product_tmpl_id', 'in', preload_products.ids),
            ('location_id', '=', 54),
            ('company_id', '=', target_company_id),
        ])
        quant_by_product = {q.product_id.id: q for q in existing_quants}

        # ---------------------------------------------------------------------
        # Import loop (Kave-only updates; creates allowed; no hard stop)
        # ---------------------------------------------------------------------
        processed_rows = 0
        failed_rows = []

        with self.env.norecompute():
            for row_index, (_, row) in enumerate(df.iterrows(), start=1):
                self._set_db_timeouts()

                code_value = row.get('Code')
                ean_value = row.get('EAN Code') or ''
                program = row.get('Program') or ''

                if not code_value:
                    failed_rows.append({
                        "row_index": row_index,
                        "code": '',
                        "ean": ean_value,
                        "program": program,
                        "error": "Missing Code",
                    })
                    continue

                try:
                    with self.env.cr.savepoint():
                        # -----------------------------------------------------
                        # Find product (STRICTLY from Kave-only caches)
                        # -----------------------------------------------------
                        product_template = products_by_code.get(code_value)

                        if not product_template:
                            product_template = products_by_barcode.get(ean_value)

                        # Hard safety: if somehow we matched non-Kave, stop that row.
                        self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                        # -----------------------------------------------------
                        # Unarchive archived Kave products (KAVE ONLY!)
                        # -----------------------------------------------------
                        if not product_template:
                            archived_candidate = company_env['product.template'].sudo().search(
                                [
                                    '|',
                                    ('x_studio_referncia_interna', '=', code_value),
                                    ('x_studio_cdigo_de_barras', '=', ean_value),
                                    ('product_tag_ids', 'in', [kave_tag.id]),
                                    ('active', '=', False),
                                ],
                                order='create_date desc',
                                limit=1,
                            )
                            if archived_candidate:
                                product_template = archived_candidate
                                self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                                product_template.sudo().write({
                                    'active': True,
                                    'website_published': True,
                                    # NOTE: We do NOT add Kave tag here because it must already be Kave.
                                    # Still, keeping tag write is harmless; but we keep it minimal:
                                })
                                if default_vat_tax and (
                                    not product_template.taxes_id
                                    or not product_template.taxes_id.filtered(lambda t: t.type_tax_use == 'sale')
                                ):
                                    product_template.sudo().write({
                                        'taxes_id': [(6, 0, [default_vat_tax.id])]
                                    })

                                products_by_code[code_value] = product_template
                                if ean_value:
                                    products_by_barcode[ean_value] = product_template

                        # -----------------------------------------------------
                        # Parse weights
                        # -----------------------------------------------------
                        weight_package = str(row.get('Weight Package') or '0')
                        if '#' in weight_package:
                            weights = [float(w.replace(',', '.')) for w in weight_package.split('#')]
                            total_weight = sum(weights)
                            volume_qty = len(weights)
                            peso_cada_volume = ' / '.join(weight_package.split('#'))
                        else:
                            total_weight = float(weight_package.replace(',', '.')) if weight_package else 0.0
                            volume_qty = 1
                            peso_cada_volume = weight_package or '0'

                        purchase_price = row.get('Nett Purchase Price') or 0.0

                        # -----------------------------------------------------
                        # Base vals
                        # -----------------------------------------------------
                        base_vals = {
                            'name': program,
                            'x_studio_referncia_interna': code_value,
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
                            'default_code': code_value,
                            'sale_delay': 30,
                            'type': 'product',
                            'available_in_pos': True,
                            'allow_out_of_stock_order': True,
                            # IMPORTANT: for EXISTING products, this is fine (keeps tag). For NEW creates, it's how they become Kave.
                            'product_tag_ids': [(4, kave_tag.id)],
                            'company_id': target_company_id,
                            'website_published': True,
                            'categ_id': kave_category.id,
                            'public_categ_ids': [(6, 0, [kave_public_category.id])],
                            'pos_categ_ids': [(6, 0, [pos_category.id])],
                        }

                        # compare price nulling
                        if base_vals['compare_list_price'] == base_vals['list_price']:
                            base_vals['compare_list_price'] = None

                        # -----------------------------------------------------
                        # Create or update
                        # -----------------------------------------------------
                        if not product_template:
                            # CREATE is allowed (new product will be Kave by definition)
                            base_vals.update({
                                'barcode': ean_value,
                                'x_studio_cdigo_de_barras': ean_value,
                            })
                            if default_vat_tax:
                                base_vals['taxes_id'] = [(6, 0, [default_vat_tax.id])]

                            product_template = company_env['product.template'].sudo().create(base_vals)

                            # cache it (it is Kave now)
                            products_by_code[code_value] = product_template
                            if ean_value:
                                products_by_barcode[ean_value] = product_template

                        else:
                            # UPDATE only Kave products
                            self._ensure_kave_only(product_template, kave_tag, row_index, code_value)

                            # Ensure VAT tax on existing
                            if default_vat_tax and (
                                not product_template.taxes_id
                                or not product_template.taxes_id.filtered(lambda t: t.type_tax_use == 'sale')
                            ):
                                product_template.sudo().write({'taxes_id': [(6, 0, [default_vat_tax.id])]})

                            update_vals = dict(base_vals)

                            # BARCODE CONFLICT SAFE UPDATE
                            if ean_value:
                                conflict = self._find_barcode_conflict(company_env, ean_value, product_template)
                                if conflict:
                                    failed_rows.append({
                                        "row_index": row_index,
                                        "code": code_value,
                                        "ean": ean_value,
                                        "program": program,
                                        "error": f"Barcode already used by {conflict.display_name}. Barcode not updated.",
                                    })
                                    update_vals.pop('barcode', None)
                                    update_vals.pop('x_studio_cdigo_de_barras', None)
                                else:
                                    update_vals['barcode'] = ean_value
                                    update_vals['x_studio_cdigo_de_barras'] = ean_value

                            product_template.sudo().write(update_vals)

                        variant = product_template.product_variant_id

                        # -----------------------------------------------------
                        # Accessory products by Program
                        # -----------------------------------------------------
                        if program:
                            try:
                                similar_products = company_env['product.template'].sudo().search([('name', '=', program)])
                                accessory_product_ids = []
                                for prod in similar_products:
                                    if (
                                        prod.product_variant_id
                                        and prod.product_variant_id.active
                                        and prod.product_variant_id.id != variant.id
                                    ):
                                        accessory_product_ids.append(prod.product_variant_id.id)

                                if accessory_product_ids:
                                    product_template.sudo().write({
                                        'accessory_product_ids': [(4, pid) for pid in accessory_product_ids]
                                    })
                            except Exception as acc_exc:
                                failed_rows.append({
                                    "row_index": row_index,
                                    "code": code_value,
                                    "ean": ean_value,
                                    "program": program,
                                    "error": f"Accessory link error: {str(acc_exc)}",
                                })

                        # -----------------------------------------------------
                        # Supplierinfo (upsert cached)
                        # -----------------------------------------------------
                        si = supplierinfo_by_tmpl.get(product_template.id)
                        si_vals = {
                            'price': row.get('Purchase Price') or 0.0,
                            'discount': row.get('Discount') or 0.0,
                            'currency_id': self.env.ref('base.EUR').id,
                            'partner_id': kave_home_vendor.id,
                            'product_tmpl_id': product_template.id,
                        }
                        if si:
                            si.sudo().write(si_vals)
                        else:
                            si = company_env['product.supplierinfo'].sudo().create(si_vals)
                            supplierinfo_by_tmpl[product_template.id] = si

                        # -----------------------------------------------------
                        # Stock quant at KAV/Stock (location 54)
                        # -----------------------------------------------------
                        qty_stock = row.get('Stock') or 0.0
                        q = quant_by_product.get(variant.id)
                        if q:
                            q.sudo().write({'quantity': qty_stock, 'company_id': target_company_id})
                        else:
                            q = company_env['stock.quant'].sudo().create({
                                'product_id': variant.id,
                                'location_id': 54,
                                'company_id': target_company_id,
                                'quantity': qty_stock,
                            })
                            quant_by_product[variant.id] = q

                        product_template.sudo().write({'x_studio_quantidade_em_stock': str(qty_stock)})

                        # -----------------------------------------------------
                        # Estimated delivery date + sale_delay
                        # -----------------------------------------------------
                        est = row.get('Estimated Date (dd/mm/yyyy)')
                        if pd.notna(est):
                            try:
                                estimated_date = pd.to_datetime(est, format='%d/%m/%Y')
                                product_template.sudo().write({'x_studio_data_estimada_de_entrega': estimated_date})
                            except Exception:
                                failed_rows.append({
                                    "row_index": row_index,
                                    "code": code_value,
                                    "ean": ean_value,
                                    "program": program,
                                    "error": f"Invalid estimated date: {est}",
                                })

                        data_estimada = product_template.x_studio_data_estimada_de_entrega
                        quantidade_em_stock = self._convert_to_number(product_template.x_studio_quantidade_em_stock) or 0.0
                        stock_7 = self._convert_to_number(product_template.x_studio_stock_em_7_dias) or 0.0
                        stock_15 = self._convert_to_number(product_template.x_studio_stock_em_15_dias) or 0.0
                        stock_30 = self._convert_to_number(product_template.x_studio_stock_em_30_dias) or 0.0

                        if data_estimada:
                            sale_delay_days = (data_estimada.date() - fields.Date.context_today(self)).days
                            product_template.sudo().write({'sale_delay': max(sale_delay_days, 0)})
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
                            product_template.sudo().write({'sale_delay': sd})

                        # -----------------------------------------------------
                        # Reordering rules (cached existence)
                        # -----------------------------------------------------
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
                                company_env['stock.warehouse.orderpoint'].sudo().create({
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
                            except OperationalError as oe:
                                failed_rows.append({
                                    "row_index": row_index,
                                    "code": code_value,
                                    "ean": ean_value,
                                    "program": program,
                                    "error": f"Orderpoint timeout: {str(oe)}",
                                })

                        processed_rows += 1

                except (ValidationError, UserError, OperationalError) as exc:
                    failed_rows.append({
                        "row_index": row_index,
                        "code": code_value,
                        "ean": ean_value,
                        "program": program,
                        "error": str(exc),
                    })
                    continue
                except Exception as exc:
                    failed_rows.append({
                        "row_index": row_index,
                        "code": code_value,
                        "ean": ean_value,
                        "program": program,
                        "error": f"Unhandled row error: {str(exc)}",
                    })
                    continue

        # recompute once after batch
        self.env.recompute()

        elapsed = time.monotonic() - start_ts
        _logger.info(
            "Kave import finished",
            extra={
                "processed_rows": processed_rows,
                "failed_rows": len(failed_rows),
                "total_rows": total_rows,
                "elapsed_s": round(elapsed, 2),
            },
        )

        if failed_rows:
            _logger.warning(
                "Kave product import completed with row errors",
                extra={"failed_rows_count": len(failed_rows)},
            )
        else:
            _logger.info("Kave product import completed with no row errors.")

        self.send_success_email(processed_rows, failed_rows)
        return {
            'type': 'ir.actions.act_window_close',
            'processed': processed_rows,
        }
