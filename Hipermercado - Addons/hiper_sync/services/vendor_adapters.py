"""Adapters concretos de fornecedores + factory ``get_adapter(vendor)``.

Cada fornecedor real (Eldisser, Sorefoz, etc.) tem aqui uma subclasse de
``SharedSupplierAdapter`` que sabe parsear o seu feed especifico (campos,
formatos de preco, EAN, imagens, features). A factory escolhe a classe
certa a partir de:

* ``vendor.pg_adapter_mode == 'generic'`` -> ``GenericMappingAdapter`` com o
  JSON em ``vendor.pg_mapping_json``;
* ``vendor.code`` -> adapter Python registado (via dicionario ``ADAPTERS``).

Adicionar um adapter novo:

1. Criar subclasse de ``SharedSupplierAdapter``.
2. Implementar ``fetch_rows()`` (ou ``fetch_with_diagnostics()``) e
   ``normalize_row(raw)`` devolvendo um ``dict`` com as chaves
   normalizadas (``reference``, ``ean13``, ``name``, ``unit_price``,
   ``quantity``, ``category``, ``sub_category``, ``brand``, ``description``,
   ``images``, ``features``, ...).
3. Registar a classe em ``ADAPTERS`` com a chave igual ao ``code`` do
   fornecedor.
"""

from collections import OrderedDict

import json
import os
import re
import requests
from urllib.parse import urlsplit

from odoo import _
from odoo.exceptions import UserError

from .adapter_base import BaseAdapter
from .utils import clean_html_text, decode_html_entities, ensure_list, is_valid_ean13, parse_float, parse_int, parse_json


def _pg_media_identity(media_url):
    # Reduz uma URL de media ao seu basename minusculo, usado para deduplicar
    # imagens entre re-runs (o CDN pode mudar querystring/host mantendo o
    # mesmo ficheiro).
    media_url = str(media_url or "").strip()
    if not media_url:
        return ""
    path = urlsplit(media_url).path
    basename = os.path.basename(path).strip().lower()
    return basename or media_url.lower()


class SharedSupplierAdapter(BaseAdapter):
    def apply_common(self, row):
        row.setdefault("images", [])
        row.setdefault("features", [])
        row.setdefault("tags", False)
        row.setdefault("qty_min", 1)
        row.setdefault("meta_title", False)
        row.setdefault("meta_description", False)
        row.setdefault("info_manual", False)
        row.setdefault("weight", 0.0)
        row.setdefault("volume", 0.0)
        if row.get("images") and not isinstance(row["images"], list):
            row["images"] = ensure_list(row["images"])
        if row.get("ean13"):
            row["ean13"] = str(row["ean13"]).strip()
        if row.get("reference"):
            row["reference"] = str(row["reference"]).strip()
        for field_name in ("name_pt", "name", "brand", "category", "sub_category", "description_short_pt", "description_short"):
            if row.get(field_name):
                row[field_name] = decode_html_entities(row[field_name])
        for field_name in ("description_pt", "description"):
            if row.get(field_name):
                row[field_name] = decode_html_entities(row[field_name])
        category_name = clean_html_text(row.get("category") or "")
        sub_category_name = clean_html_text(row.get("sub_category") or "")
        if category_name and sub_category_name and category_name.casefold() == sub_category_name.casefold():
            row["sub_category"] = False
        if row.get("name_pt"):
            row["name"] = row["name_pt"]
        if row.get("description_pt"):
            row["description"] = row["description_pt"]
        if row.get("description_short_pt"):
            row["description_short"] = row["description_short_pt"]
        if not row.get("wholesale_price"):
            row["wholesale_price"] = row.get("unit_price", 0.0)
        return row if row.get("name_pt") or row.get("reference") else False


class IntSorefozAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.ftp_user:
            missing.append("ftp_user")
        if not self.vendor.ftp_password:
            missing.append("ftp_password")
        return missing

    def fetch_rows(self):
        return self.fetch_csv_from_ftp(
            self.vendor.ftp_host,
            self.vendor.ftp_port,
            self.vendor.ftp_user,
            self.vendor.ftp_password,
            self.vendor.remote_filename,
            delimiter=";",
        )

    def normalize_row(self, row):
        qty = 5 if str(row.get("QtdLinear", "")).strip().lower() == "sim" else 0
        images = []
        if row.get("LinkImagem"):
            images.append(row.get("LinkImagem"))
        if row.get("OutrasFotos"):
            images.extend([part.strip() for part in str(row.get("OutrasFotos")).split(",") if part.strip()])
        values = {
            "name_pt": row.get("NOME_PRODUTO"),
            "category": row.get("NOME_FAMILIA"),
            "sub_category": row.get("NOME_SUBFAMILIA"),
            "reference": row.get("Referencia"),
            "ean13": row.get("EAN"),
            "unit_price": parse_float(row.get("PR_LIQUIDO")),
            "wholesale_price": parse_float(row.get("PR_LIQUIDO")),
            "quantity": qty,
            "brand": row.get("NOME_MARCA"),
            "description_pt": row.get("Caracteristicas_Completa"),
            "description_short_pt": row.get("Caracteristicas_Resumo"),
            "images": images,
            "weight": parse_float(row.get("Peso(kg)")),
            "volume": parse_float(row.get("Volume(dm3)")),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntDmiAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.username:
            missing.append("username")
        if not self.vendor.password:
            missing.append("password")
        return missing

    def fetch_rows(self):
        return self.fetch_csv_from_url(self.build_template_url(), delimiter=";")

    def normalize_row(self, row):
        ean_value = (
            row.get("EAN")
            or row.get("EAN13")
            or row.get("CODBARRAS")
            or row.get("COD_BARRAS")
            or row.get("CODIGO_BARRAS")
        )
        values = {
            "name_pt": row.get("NOMBRE") or row.get("DENOMINA"),
            "category": row.get("FAMILIA"),
            "reference": row.get("REFERENCIA") or row.get("ARTICULO"),
            "ean13": ean_value,
            "unit_price": parse_float(row.get("COMPRA") or row.get("PRECIOCANO")),
            "wholesale_price": parse_float(row.get("COMPRA") or row.get("PRECIOCANO")),
            "quantity": parse_int(row.get("STOCK") or row.get("CANTIDAD") or row.get("DISPONIBLE")),
            "brand": row.get("MARCA"),
            "description_pt": row.get("DESCRIPCION") or row.get("DENOMINA"),
            "images": [row.get("IMAGEN") or row.get("URL")] if (row.get("IMAGEN") or row.get("URL")) else [],
        }
        normalized = self.apply_common(values)
        if not normalized:
            return False
        if values["ean13"] and not is_valid_ean13(values["ean13"]):
            normalized["ean13"] = False
        return normalized


class IntAufermaAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.ftp_user:
            missing.append("ftp_user")
        if not self.vendor.ftp_password:
            missing.append("ftp_password")
        return missing

    def fetch_rows(self):
        return self.fetch_csv_from_ftp(
            self.vendor.ftp_host,
            self.vendor.ftp_port,
            self.vendor.ftp_user,
            self.vendor.ftp_password,
            self.vendor.remote_filename,
            delimiter=";",
        )

    def normalize_row(self, row):
        values = {
            "name_pt": row.get("dbo_Produtos_Nome"),
            "category": row.get("Familias_Nome"),
            "reference": row.get("Refer"),
            "ean13": row.get("CodBarras"),
            "unit_price": parse_float(row.get("PVPBase")),
            "wholesale_price": parse_float(row.get("PVPBase")),
            "quantity": parse_int(row.get("QtStock")),
            "brand": row.get("Marca"),
            "description_short_pt": row.get("NomeXtra"),
            "images": [],
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntDepauAdapter(SharedSupplierAdapter):
    def fetch_rows(self):
        return self.fetch_csv_from_url(self.vendor.feed_url, delimiter=";")

    def normalize_row(self, row):
        values = {
            "name_pt": row.get("Nombre"),
            "reference": row.get("Referencia n"),
            "category": row.get("Familia"),
            "sub_category": row.get("Subfamilia"),
            "ean13": row.get("EAN13"),
            "brand": row.get("Fabricante"),
            "weight": parse_float(row.get("Peso")),
            "quantity": parse_int(row.get("Cantidad")),
            "description_pt": row.get("Descripcion"),
            "images": [row.get("URL_IMG")] if row.get("URL_IMG") else [],
            "unit_price": parse_float(row.get("PVD (Sin IVA)")),
            "wholesale_price": parse_float(row.get("PVD (Sin IVA)")),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntOciostockAdapter(SharedSupplierAdapter):
    def fetch_rows(self):
        return self.fetch_csv_from_url(self.vendor.feed_url, delimiter=";")

    def normalize_row(self, row):
        values = {
            "name_pt": row.get("nombre"),
            "reference": row.get("referencia"),
            "category": row.get("categoria_principal"),
            "ean13": row.get("ean"),
            "brand": row.get("marca"),
            "quantity": parse_int(row.get("stock_disponible")),
            "description_pt": row.get("descripcion_html"),
            "images": [row.get("url_imagen_principal_grande")] if row.get("url_imagen_principal_grande") else [],
            "unit_price": parse_float(row.get("precio_distribuidores")),
            "wholesale_price": parse_float(row.get("precio_distribuidores")),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntOrimaAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.username_id:
            missing.append("username_id")
        if not self.vendor.username:
            missing.append("username")
        if not self.vendor.password:
            missing.append("password")
        return missing

    def fetch_rows(self):
        data = self.fetch_json_from_url(self.build_template_url())
        products = data.get("products", [])
        if isinstance(products, dict):
            products = products.get("product", [])
        products = ensure_list(products)
        normalized_products = []
        for item in products:
            if isinstance(item, dict) and isinstance(item.get("product"), dict):
                normalized_products.append(item["product"])
            else:
                normalized_products.append(item)
        products = normalized_products
        if products:
            return products
        if isinstance(data, dict):
            top_keys = ", ".join(sorted(data.keys())[:10]) or _("none")
            message_parts = []
            for key in ("message", "error", "errors", "status", "detail", "details"):
                value = data.get(key)
                if value:
                    message_parts.append("%s=%s" % (key, value))
            extra = " | ".join(message_parts)
            raise UserError(
                _("Orima returned no products. Top-level keys: %s%s")
                % (top_keys, (". %s" % extra) if extra else "")
            )
        raise UserError(_("Orima returned no products and an unexpected response shape."))

    def normalize_row(self, row):
        stock_status = str(row.get("stock_status") or row.get("Stock") or "").strip()
        quantity_map = {"0": 0, "1": 2, "2": 5, "E": 0}
        values = {
            "name_pt": row.get("description") or row.get("Description"),
            "reference": row.get("reference") or row.get("Reference"),
            "ean13": row.get("ean13") or row.get("EAN13"),
            "brand": row.get("brand") or row.get("Brand"),
            "category": row.get("gamma") or row.get("family") or row.get("category"),
            "sub_category": row.get("family") or row.get("category"),
            "description_pt": row.get("details") or row.get("Details"),
            "images": ensure_list(row.get("image") or row.get("images")),
            "unit_price": parse_float(row.get("wholesale_price") or row.get("unit_price")),
            "wholesale_price": parse_float(row.get("wholesale_price") or row.get("unit_price")),
            "quantity": quantity_map.get(stock_status, 0),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntExperteletroAdapter(SharedSupplierAdapter):
    def fetch_rows(self):
        return self.fetch_csv_from_url(self.vendor.feed_url, delimiter=";")

    def normalize_row(self, row):
        availability = str(row.get("disponibilidade", "")).strip().lower()
        if availability in ("limitado", "limitada", "baixo stock", "baixo estoque"):
            quantity = 2
        elif availability in ("disponivel", "em stock", "em estoque"):
            quantity = 5
        else:
            quantity = parse_int(row.get("stock") or row.get("quantidade"))
        if not quantity and str(row.get("precor", "")).strip():
            # Some supplier exports expose the commercial price field on rows
            # that are effectively sellable even when no explicit availability
            # label is present.
            quantity = 5
        category = row.get("familia") or ""
        normalized_category = str(category).replace("=>", "->").replace(">", "->")
        parts = [part.strip() for part in normalized_category.split("->") if part.strip()]
        images = []
        for field_name in ("galeria", "imagem", "image", "linkimagem"):
            field_value = row.get(field_name)
            if not field_value:
                continue
            images.extend([part.strip() for part in str(field_value).split(",") if part.strip()])
        values = {
            "name_pt": row.get("nome"),
            "reference": row.get("referencia") or row.get("partnumber"),
            "category": parts[0] if parts else False,
            "sub_category": parts[-1] if len(parts) > 1 else False,
            "ean13": row.get("ean"),
            "brand": row.get("marcas"),
            "description_pt": row.get("caracteristicas"),
            "description_short_pt": row.get("resumo"),
            "images": images,
            "unit_price": parse_float(row.get("preco")),
            "wholesale_price": parse_float(row.get("preco") or row.get("precor")),
            "quantity": quantity,
        }
        normalized = self.apply_common(values)
        if not normalized:
            return False
        if values["ean13"] and not is_valid_ean13(values["ean13"]):
            normalized["ean13"] = False
        return normalized


class PgGenericSupplierAdapter(SharedSupplierAdapter):
    PG_MISSING = object()
    PG_FLOAT_FIELDS = {"unit_price", "wholesale_price", "weight", "volume", "shipping"}
    PG_INT_FIELDS = {"quantity", "qty_min"}
    PG_LIST_FIELDS = {"images", "tags"}

    def validate_configuration(self):
        missing = []
        remote_crawler_ready = bool(self.vendor.source_kind == "csv_url" and self.vendor.remote_crawler_trigger_url)
        if self.vendor.source_kind == "ftp_csv":
            for field_name in ("ftp_host", "ftp_user", "ftp_password", "remote_filename"):
                if not getattr(self.vendor, field_name):
                    missing.append(field_name)
        elif self.vendor.source_kind == "csv_url" and not remote_crawler_ready and not (
            self.vendor.feed_url or self.vendor.api_url_template
        ):
            missing.append("feed_url/api_url_template")
        elif self.vendor.source_kind == "json_url" and not (self.vendor.feed_url or self.vendor.api_url_template):
            missing.append("feed_url/api_url_template")
        elif self.vendor.source_kind == "local_csv" and not (self.vendor.crawler_output_path or self.vendor.feed_url):
            missing.append("crawler_output_path/feed_url")
        elif self.vendor.source_kind == "crawler_csv" and not (self.vendor.crawler_output_path or self.vendor.feed_url):
            missing.append("crawler_output_path/feed_url")

        config = self._pg_mapping_config()
        field_map = config.get("field_map") if isinstance(config, dict) else {}
        if not isinstance(field_map, dict) or not field_map:
            missing.append("pg_mapping_json.field_map")
        elif not any(field_map.get(key) for key in ("name_pt", "reference")):
            missing.append("pg_mapping_json.field_map.name_pt/reference")
        return missing

    def fetch_rows(self):
        source_kind = self.vendor.source_kind
        delimiter = self._pg_csv_delimiter()
        if source_kind == "ftp_csv":
            return self.fetch_csv_from_ftp(
                self.vendor.ftp_host,
                self.vendor.ftp_port,
                self.vendor.ftp_user,
                self.vendor.ftp_password,
                self.vendor.remote_filename,
                delimiter=delimiter,
            )
        if source_kind == "csv_url":
            url = self.build_template_url() if self.vendor.api_url_template else self.vendor.feed_url
            return self.fetch_csv_from_url(url, delimiter=delimiter)
        if source_kind == "local_csv":
            local_path = self.vendor.crawler_output_path or self.vendor.feed_url
            return self.fetch_csv_from_local_file(local_path, delimiter=delimiter)
        if source_kind == "crawler_csv":
            if self.vendor.crawler_command:
                self.run_crawler_command()
            local_path = self.vendor.crawler_output_path or self.vendor.feed_url
            return self.fetch_csv_from_local_file(local_path, delimiter=delimiter)
        if source_kind == "json_url":
            url = self.build_template_url() if self.vendor.api_url_template else self.vendor.feed_url
            payload = self.fetch_json_from_url(url)
            rows = self._pg_extract_json_rows(payload)
            if rows:
                return rows
            raise UserError(self._pg_build_empty_payload_message(payload))
        raise UserError(_("Unsupported source kind for generic supplier: %s") % source_kind)

    def normalize_row(self, row):
        config = self._pg_mapping_config()
        field_map = config.get("field_map") if isinstance(config, dict) else {}
        values = {}
        for target, spec in field_map.items():
            values[target] = self._pg_normalize_target_value(target, spec, row)
        normalized = self.apply_common(values)
        if not normalized:
            return False
        if normalized.get("ean13") and not is_valid_ean13(normalized["ean13"]):
            normalized["ean13"] = False
        return normalized

    def _pg_mapping_config(self):
        config = parse_json(getattr(self.vendor, "pg_mapping_json", False), default={})
        return config if isinstance(config, dict) else {}

    def _pg_csv_delimiter(self):
        config = self._pg_mapping_config()
        return config.get("delimiter") or self.vendor.delimiter or ";"

    def _pg_normalize_target_value(self, target, spec, row):
        raw = self._pg_resolve_spec(row, spec)
        if target == "features":
            return self._pg_normalize_features(raw, spec)
        if target in self.PG_LIST_FIELDS:
            return self._pg_normalize_list(raw, spec)
        if self._pg_is_missing(raw):
            return [] if target in self.PG_LIST_FIELDS or target == "features" else False
        if target in self.PG_FLOAT_FIELDS:
            return parse_float(raw)
        if target in self.PG_INT_FIELDS:
            return parse_int(raw)
        return str(raw).strip() if isinstance(raw, str) else raw

    def _pg_resolve_spec(self, container, spec):
        if spec in (None, False):
            return False
        if isinstance(spec, dict):
            if "value" in spec and not any(key in spec for key in ("path", "paths", "source", "sources")):
                raw = spec.get("value")
            else:
                raw = self._pg_resolve_candidates(
                    container,
                    spec.get("path") or spec.get("paths") or spec.get("source") or spec.get("sources"),
                )
            if self._pg_is_missing(raw) and "default" in spec:
                raw = spec.get("default")
            raw = self._pg_apply_value_map(raw, spec.get("map"))
            if isinstance(raw, str) and spec.get("strip", True):
                raw = raw.strip()
            return raw
        raw = self._pg_resolve_candidates(container, spec)
        return raw.strip() if isinstance(raw, str) else raw

    def _pg_resolve_candidates(self, container, candidates):
        if candidates in (None, False):
            return False
        if isinstance(candidates, dict):
            return self._pg_resolve_spec(container, candidates)
        if isinstance(candidates, (list, tuple)):
            for candidate in candidates:
                value = self._pg_resolve_candidates(container, candidate)
                if not self._pg_is_missing(value):
                    return value
            return False
        if isinstance(candidates, str):
            return self._pg_resolve_path(container, candidates)
        return candidates

    def _pg_resolve_path(self, container, path):
        if path in ("$", ".", "@"):
            return container
        if not isinstance(path, str):
            return path
        current = container
        for part in [item for item in path.split(".") if item not in ("", "$")]:
            if isinstance(current, list):
                if not part.isdigit():
                    return False
                index = int(part)
                if index >= len(current):
                    return False
                current = current[index]
                continue
            if not isinstance(current, dict):
                return False
            if part in current:
                current = current.get(part)
                continue
            lowered = part.strip().lower()
            matched_key = next(
                (key for key in current.keys() if str(key).strip().lower() == lowered),
                self.PG_MISSING,
            )
            if matched_key is self.PG_MISSING:
                return False
            current = current.get(matched_key)
        return current

    def _pg_apply_value_map(self, raw, value_map):
        if not value_map or self._pg_is_missing(raw):
            return raw
        raw_text = str(raw).strip()
        if raw_text in value_map:
            return value_map[raw_text]
        lowered = raw_text.lower()
        for key, value in value_map.items():
            if str(key).strip().lower() == lowered:
                return value
        return raw

    def _pg_normalize_list(self, raw, spec):
        if self._pg_is_missing(raw):
            return []
        if isinstance(raw, list):
            values = raw
        elif isinstance(raw, tuple):
            values = list(raw)
        elif isinstance(raw, str):
            split_spec = spec.get("split") if isinstance(spec, dict) else False
            if split_spec:
                if isinstance(split_spec, str):
                    parts = re.split(split_spec, raw)
                else:
                    pattern = "|".join(re.escape(str(item)) for item in ensure_list(split_spec))
                    parts = re.split(pattern, raw)
                values = parts
            else:
                values = [raw]
        else:
            values = ensure_list(raw)
        normalized = []
        for value in values:
            if self._pg_is_missing(value):
                continue
            normalized.append(str(value).strip() if isinstance(value, str) else value)
        return [value for value in normalized if not self._pg_is_missing(value)]

    def _pg_normalize_features(self, raw, spec):
        if self._pg_is_missing(raw):
            return []
        feature_spec = spec if isinstance(spec, dict) else {}
        if feature_spec.get("item_path"):
            raw = self._pg_resolve_candidates(raw, feature_spec.get("item_path"))
        name_key = feature_spec.get("name_key", "name")
        value_key = feature_spec.get("value_key", "value")
        pair_separator = feature_spec.get("pair_separator", ":")
        items = ensure_list(raw)
        features = []
        for item in items:
            if self._pg_is_missing(item):
                continue
            if isinstance(item, dict):
                name = self._pg_resolve_candidates(item, name_key)
                value = self._pg_resolve_candidates(item, value_key)
            elif isinstance(item, str) and pair_separator in item:
                name, value = item.split(pair_separator, 1)
            else:
                continue
            if self._pg_is_missing(name) or self._pg_is_missing(value):
                continue
            features.append({"name": str(name).strip(), "value": str(value).strip()})
        return features

    def _pg_extract_json_rows(self, payload):
        config = self._pg_mapping_config()
        row_path = config.get("row_path") or config.get("rows_path") or ["Produtos", "produtos", "products", "items"]
        rows = self._pg_resolve_candidates(payload, row_path)
        if self._pg_is_missing(rows):
            rows = payload
        rows = ensure_list(rows)
        item_path = config.get("row_item_path")
        normalized_rows = []
        for item in rows:
            current = item
            if item_path:
                extracted = self._pg_resolve_candidates(item, item_path)
                if not self._pg_is_missing(extracted):
                    current = extracted
            elif isinstance(item, dict):
                for wrapper in ("Produto", "product", "item"):
                    if isinstance(item.get(wrapper), dict):
                        current = item.get(wrapper)
                        break
            if isinstance(current, dict):
                normalized_rows.append(current)
        return normalized_rows

    def _pg_build_empty_payload_message(self, payload):
        if isinstance(payload, dict):
            top_keys = ", ".join(str(key) for key in list(payload.keys())[:10]) or _("none")
            return _("Generic supplier returned no usable rows. Top-level keys: %s") % top_keys
        if isinstance(payload, list):
            return _("Generic supplier returned a list payload but no usable rows were found. items=%s") % len(payload)
        return _("Generic supplier returned an unexpected payload shape: %s") % type(payload).__name__

    def _pg_is_missing(self, value):
        return value is None or value is False or value == "" or value == [] or value == {}


class IntMacorluxAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if not self.vendor.api_key:
            missing.append("api_key")
        if not self.vendor.username:
            missing.append("username")
        if not self.vendor.password:
            missing.append("password")
        return missing

    def fetch_rows(self):
        attempts = self._build_macorlux_attempts()
        last_payload = False
        attempt_labels = []
        for label, url, method, headers in attempts:
            attempt_labels.append(label)
            payload = self._fetch_macorlux_payload(url, method=method, headers=headers, label=label)
            rows = self._extract_product_rows(payload)
            if rows:
                return rows
            last_payload = payload
        if isinstance(last_payload, dict):
            last_payload = dict(last_payload)
            last_payload["_hiper_attempts"] = attempt_labels
        raise UserError(self._build_empty_payload_message(last_payload or {}))

    def _build_macorlux_attempts(self):
        raw_urls = self._build_macorlux_candidate_urls(self._build_macorlux_url())
        encoded_urls = self._build_macorlux_candidate_urls(self.build_template_url())
        legacy_headers = {"Content-Type": "application/json"}
        browser_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.macorlux.pt",
            "Referer": "https://www.macorlux.pt/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
        }
        attempts = []
        for url_label, raw_url in raw_urls:
            attempts.extend(
                [
                    (f"raw-post-legacy{url_label}", raw_url, "POST", legacy_headers),
                    (f"raw-post-browser{url_label}", raw_url, "POST", browser_headers),
                ]
            )
        if not self.get_extra_config().get("json_http_method"):
            for url_label, raw_url in raw_urls:
                attempts.extend(
                    [
                        (f"raw-get-legacy{url_label}", raw_url, "GET", legacy_headers),
                        (f"raw-get-browser{url_label}", raw_url, "GET", browser_headers),
                    ]
                )
            seen_urls = {url for _, url in raw_urls}
            for url_label, encoded_url in encoded_urls:
                if encoded_url in seen_urls:
                    continue
                attempts.extend(
                    [
                        (f"encoded-post-legacy{url_label}", encoded_url, "POST", legacy_headers),
                        (f"encoded-post-browser{url_label}", encoded_url, "POST", browser_headers),
                        (f"encoded-get-legacy{url_label}", encoded_url, "GET", legacy_headers),
                        (f"encoded-get-browser{url_label}", encoded_url, "GET", browser_headers),
                    ]
                )
        return attempts

    def _build_macorlux_candidate_urls(self, url):
        urls = [("", url)]
        call_type = str(self.vendor.request_call_type or "").strip()
        if call_type:
            alternate_url = self._with_macorlux_method(url, call_type)
            if alternate_url != url:
                urls.append(("-call-type", alternate_url))
        return urls

    def _with_macorlux_method(self, url, method_name):
        if not url or not method_name:
            return url
        if re.search(r"([?&])method=", url, flags=re.IGNORECASE):
            return re.sub(
                r"([?&]method=)[^&]*",
                lambda match: f"{match.group(1)}{method_name}",
                url,
                count=1,
                flags=re.IGNORECASE,
            )
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}method={method_name}"

    def _build_macorlux_url(self):
        template = self.vendor.api_url_template or self.vendor.feed_url or ""
        replacements = {
            "{_apikey_}": str(self.vendor.api_key or "").strip(),
            "{_user_}": str(self.vendor.username or "").strip(),
            "{_pass_}": str(self.vendor.password or "").strip(),
            "{_userid_}": str(self.vendor.username_id or "").strip(),
            "{_call_type_}": str(self.vendor.request_call_type or "normal").strip(),
            "{_type_}": "json",
        }
        for source, target in replacements.items():
            template = template.replace(source, str(target))
        return template

    def _fetch_macorlux_payload(self, url, method="POST", headers=False, label=False):
        response = requests.request(
            method,
            url,
            headers=headers or {"Content-Type": "application/json"},
            data="" if method == "POST" else None,
            timeout=180,
        )
        response.raise_for_status()
        content = self.decode_text_bytes(response.content)
        content = content.replace("\ufeff", "")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return {
                "_hiper_attempt_label": label,
                "_hiper_content_type": response.headers.get("Content-Type") or False,
                "_hiper_http_status": response.status_code,
                "_hiper_raw_text": content[:500],
            }
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_hiper_attempt_label"] = label
            payload["_hiper_content_type"] = response.headers.get("Content-Type") or False
            payload["_hiper_http_status"] = response.status_code
        return payload


    def _extract_product_rows(self, data):
        payload = data
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = (
                payload.get("Produtos")
                or payload.get("produtos")
                or payload.get("products")
                or payload.get("items")
                or payload
            )
            if isinstance(rows, dict):
                rows = (
                    rows.get("Produto")
                    or rows.get("Produtos")
                    or rows.get("produto")
                    or rows.get("products")
                    or rows.get("items")
                    or rows
                )
        else:
            rows = []
        rows = ensure_list(rows)
        normalized_rows = []
        for item in rows:
            if isinstance(item, dict) and isinstance(item.get("Produto"), dict):
                normalized_rows.append(item["Produto"])
            elif isinstance(item, dict) and any(
                item.get(key)
                for key in ("Nome", "Referencia", "EAN", "Preco", "Marca", "Familia")
            ):
                normalized_rows.append(item)
        return normalized_rows

    def _build_empty_payload_message(self, data):
        if isinstance(data, dict):
            visible_keys = [str(key) for key in sorted(data.keys()) if not str(key).startswith("_hiper_")]
            top_keys = ", ".join(visible_keys[:10]) or _("none")
            nested_keys = []
            for key in ("Produtos", "produtos", "products", "items"):
                value = data.get(key)
                if isinstance(value, dict):
                    nested_keys = [str(item) for item in list(value.keys())[:10]]
                    break
            extra = []
            if nested_keys:
                extra.append(_("nested keys=%s") % ", ".join(nested_keys))
            for key in ("Erro", "erro", "Mensagem", "mensagem", "message", "detail", "details"):
                value = data.get(key)
                if value:
                    extra.append("%s=%s" % (key, value))
            if data.get("_hiper_attempt_label"):
                extra.append(_("last attempt=%s") % data.get("_hiper_attempt_label"))
            if data.get("_hiper_http_status"):
                extra.append(_("http status=%s") % data.get("_hiper_http_status"))
            if data.get("_hiper_content_type"):
                extra.append(_("content type=%s") % data.get("_hiper_content_type"))
            if data.get("_hiper_raw_text"):
                extra.append(_("raw=%s") % data.get("_hiper_raw_text"))
            attempts = data.get("_hiper_attempts")
            if attempts:
                extra.append(_("attempts=%s") % ", ".join(attempts))
            method = self.get_extra_config().get("json_http_method") or "POST (default), GET fallback"
            extra.append(_("method=%s") % method)
            return _("Macorlux returned no usable products. Top-level keys: %s%s") % (
                top_keys,
                (". %s" % " | ".join(extra)) if extra else "",
            )
        if isinstance(data, list):
            return _("Macorlux returned a list payload but no usable product rows were found. items=%s") % len(data)
        return _("Macorlux returned an unexpected payload shape: %s") % type(data).__name__

    def normalize_row(self, row):
        features = []
        for feature in ensure_list(row.get("Caracteristicas")):
            if isinstance(feature, dict):
                features.append({"name": feature.get("Categoria"), "value": feature.get("Valor")})
        category = row.get("Familia", {})
        sub_category = row.get("SubFamilia", {})
        brand = row.get("Marca", {})
        reference = str(row.get("Referencia") or "")
        if "." in reference:
            reference = reference.split(".")[-1]
        values = {
            "name_pt": row.get("Nome"),
            "reference": reference,
            "category": category.get("Valor") if isinstance(category, dict) else category,
            "sub_category": sub_category.get("Valor") if isinstance(sub_category, dict) else sub_category,
            "ean13": row.get("EAN"),
            "brand": brand.get("Valor") if isinstance(brand, dict) else brand,
            "description_pt": row.get("Descricao"),
            "description_short_pt": row.get("Resumo"),
            "images": ensure_list(row.get("Imagem")),
            "unit_price": parse_float(row.get("Preco")),
            "wholesale_price": parse_float(row.get("Preco")),
            "quantity": parse_int(row.get("Stock")),
            "shipping": parse_float(row.get("Portes")),
            "weight": parse_float(row.get("PesoBruto")),
            "features": features,
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


class IntEldisserAdapter(SharedSupplierAdapter):
    def validate_configuration(self):
        missing = []
        if self.vendor.source_kind == "csv_url" and not (self.vendor.feed_url or self.vendor.remote_crawler_trigger_url):
            missing.append("feed_url")
        elif self.vendor.source_kind in ("crawler_csv", "local_csv") and not (
            self.vendor.crawler_output_path or self.vendor.feed_url
        ):
            missing.append("crawler_output_path")
        return missing

    def fetch_rows(self):
        if self.vendor.source_kind == "csv_url":
            return self.fetch_csv_from_url(self.vendor.feed_url, delimiter=",")
        if self.vendor.source_kind == "local_csv":
            local_path = self.vendor.crawler_output_path or self.vendor.feed_url
            return self.fetch_csv_from_local_file(local_path, delimiter=",")
        if self.vendor.crawler_command:
            self.run_crawler_command()
        return self.fetch_csv_from_local_file(self.vendor.crawler_output_path, delimiter=",")

    def _normalize_remote_crawler_features(self, raw_value):
        payload = parse_json(raw_value, default=False)
        if not payload:
            return []
        features = []
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and item.get("name") and item.get("value"):
                    features.append({"name": str(item["name"]).strip(), "value": str(item["value"]).strip()})
            return features
        if not isinstance(payload, dict):
            return []
        for section_name, section_values in payload.items():
            if isinstance(section_values, dict):
                for key, value in section_values.items():
                    if key and value not in (None, False, ""):
                        label = "%s - %s" % (section_name, key) if section_name else str(key)
                        features.append({"name": str(label).strip(), "value": str(value).strip()})
            elif section_name and section_values not in (None, False, ""):
                features.append({"name": str(section_name).strip(), "value": str(section_values).strip()})
        return features

    def _normalize_remote_crawler_row(self, row):
        primary_images = []
        primary_keys = set()
        for key in ("image_url", "thumbnail_url"):
            media_url = str(row.get(key) or "").strip()
            media_key = _pg_media_identity(media_url)
            if not media_url or not media_key or media_key in primary_keys:
                continue
            primary_images.append(media_url)
            primary_keys.add(media_key)
        gallery_urls = []
        extra_images = row.get("images")
        if extra_images:
            gallery_urls.extend([part.strip() for part in str(extra_images).split(",") if part.strip()])
        unique_primary_images = primary_images
        if not unique_primary_images and gallery_urls:
            fallback_primary = gallery_urls[0]
            fallback_key = _pg_media_identity(fallback_primary)
            if fallback_primary and fallback_key:
                unique_primary_images = [fallback_primary]
                primary_keys.add(fallback_key)
            gallery_urls = gallery_urls[1:]
        extra_media = []
        seen_media = set()
        for item in parse_json(row.get("extra_media_json"), default=[]):
            if not isinstance(item, dict):
                continue
            media_url = str(item.get("url") or "").strip()
            media_type = (item.get("type") or "image").strip().lower()
            media_key = _pg_media_identity(media_url)
            if (
                not media_url
                or not media_key
                or media_key in primary_keys
                or (media_type, media_key) in seen_media
            ):
                continue
            seen_media.add((media_type, media_key))
            extra_media.append({"type": media_type, "url": media_url})
        for media_url in gallery_urls:
            media_key = _pg_media_identity(media_url)
            if (
                not media_url
                or not media_key
                or media_key in primary_keys
                or ("image", media_key) in seen_media
            ):
                continue
            seen_media.add(("image", media_key))
            extra_media.append({"type": "image", "url": media_url})
        values = {
            "name_pt": row.get("name"),
            "category": row.get("category"),
            "sub_category": row.get("sub_category"),
            "reference": row.get("reference"),
            "ean13": row.get("ean13"),
            "unit_price": parse_float(row.get("unit_price")),
            "wholesale_price": parse_float(row.get("wholesale_price") or row.get("unit_price")),
            "quantity": parse_int(row.get("quantity")),
            "brand": row.get("brand"),
            "description_pt": row.get("description"),
            "description_short_pt": row.get("description_short"),
            "images": unique_primary_images,
            "features": self._normalize_remote_crawler_features(row.get("features_json")),
            "extra_media_json": extra_media,
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False

    def normalize_row(self, row):
        if row.get("source_url") and row.get("reference") and row.get("ean13"):
            return self._normalize_remote_crawler_row(row)
        images = []
        if row.get("LinkImagem"):
            images.append(row.get("LinkImagem"))
        extra = row.get("OutrasFotos")
        if extra:
            images.extend([part.strip() for part in str(extra).split(",") if part.strip()])
        values = {
            "name_pt": row.get("NOME_PRODUTO"),
            "category": row.get("NOME_FAMILIA"),
            "reference": row.get("EAN"),
            "ean13": row.get("EAN"),
            "unit_price": parse_float(row.get("PR_LIQUIDO")),
            "wholesale_price": parse_float(row.get("PR_LIQUIDO")),
            "quantity": parse_int(row.get("QtdLinear") or row.get("Stock")),
            "brand": row.get("NOME_MARCA"),
            "description_pt": row.get("Caracteristicas_Completa"),
            "description_short_pt": row.get("Caracteristicas_Resumo"),
            "images": images,
            "weight": parse_float(row.get("Peso_kg")),
        }
        return self.apply_common(values) if is_valid_ean13(values["ean13"]) else False


ADAPTERS = OrderedDict(
    [
        ("intsorefoz", IntSorefozAdapter),
        ("intdmi", IntDmiAdapter),
        ("intauferma", IntAufermaAdapter),
        ("intdepau", IntDepauAdapter),
        ("intociostock", IntOciostockAdapter),
        ("intorima", IntOrimaAdapter),
        ("intexperteletro", IntExperteletroAdapter),
        ("intmacorlux", IntMacorluxAdapter),
        ("inteldisser", IntEldisserAdapter),
    ]
)


def get_adapter(vendor):
    if getattr(vendor, "pg_adapter_mode", "code") == "generic":
        return PgGenericSupplierAdapter(vendor)
    adapter_class = ADAPTERS.get(vendor.code)
    if not adapter_class and getattr(vendor, "pg_mapping_json", False):
        return PgGenericSupplierAdapter(vendor)
    if not adapter_class:
        raise UserError(
            _("Unsupported supplier adapter %s. Switch Adapter Mode to Generic Mapping or add a code adapter.")
            % vendor.code
        )
    return adapter_class(vendor)
