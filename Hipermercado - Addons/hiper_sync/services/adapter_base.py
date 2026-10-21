"""Classe base de todos os adapters de fornecedor.

Cada adapter especifico (FTP, CSV URL, JSON URL, crawler local, CSV local,
ou adapter Python custom registado por ``code``) deriva de
``BaseAdapter`` / ``SharedSupplierAdapter`` e implementa, no minimo,
``fetch_rows()`` + ``normalize_row(raw)``.

``fetch_with_diagnostics()`` e o ponto de entrada usado pelas vistas: alem
das linhas normalizadas, devolve estatisticas (raw_count, dropped,
invalid_ean_count, missing_identity_count, sample_keys) que aparecem em
``hiper.sync.vendor.last_sync_message``.
"""

import csv
import io
import json
import os
import re
import subprocess
import time
from ftplib import FTP
from urllib.parse import quote_plus

import requests

from odoo import _
from odoo.exceptions import UserError

from .utils import ensure_list, parse_json


class BaseAdapter:
    """Contrato comum a todos os adapters de fornecedor."""

    def __init__(self, vendor):
        self.vendor = vendor
        # Diretorio raiz do modulo (resolvido a partir do path deste ficheiro)
        # usado por adapters de ficheiro local para resolver paths relativos.
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def validate_configuration(self):
        """Devolve lista de mensagens de configuracao em falta (vazio = OK)."""
        return []

    def fetch(self):
        """Fluxo simples: linhas raw -> linhas normalizadas (filtrando vazias)."""
        raw_rows = self.fetch_rows()
        return [row for row in (self.normalize_row(raw) for raw in raw_rows) if row]

    def fetch_with_diagnostics(self):
        """Igual a ``fetch()`` mas devolve estatisticas para reportar na UI."""
        raw_rows = ensure_list(self.fetch_rows())
        normalized_rows = []
        invalid_ean_count = 0
        missing_identity_count = 0

        for raw in raw_rows:
            normalized = self.normalize_row(raw)
            if normalized:
                normalized_rows.append(normalized)
                continue
            ean_value = self._guess_raw_value(
                raw,
                ["ean13", "ean", "codbarras", "barcode", "cod_barras"],
            )
            if ean_value:
                digits = re.sub(r"\D", "", str(ean_value))
                if len(digits) != 13:
                    invalid_ean_count += 1
            else:
                invalid_ean_count += 1

            name_value = self._guess_raw_value(
                raw,
                ["name_pt", "name", "description", "dbo_produtos_nome", "nome_produto", "description"],
            )
            reference_value = self._guess_raw_value(raw, ["reference", "refer", "referencia", "partnr"])
            if not name_value and not reference_value:
                missing_identity_count += 1

        return {
            "rows": normalized_rows,
            "raw_count": len(raw_rows),
            "normalized_count": len(normalized_rows),
            "dropped_count": max(len(raw_rows) - len(normalized_rows), 0),
            "invalid_ean_count": invalid_ean_count,
            "missing_identity_count": missing_identity_count,
            "sample_keys": self._sample_keys(raw_rows),
            "first_row_preview": self._first_row_preview(raw_rows),
        }

    def fetch_rows(self):
        raise NotImplementedError()

    def normalize_row(self, row):
        raise NotImplementedError()

    def get_extra_config(self):
        return parse_json(self.vendor.extra_config_json, default={})

    def decode_text_bytes(self, data):
        # Supplier feeds are not consistently UTF-8. Try common legacy encodings
        # used by the original Prestashop integrations before falling back.
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    def fetch_csv_from_url(self, url, delimiter=";"):
        response = requests.get(url, timeout=180)
        response.raise_for_status()
        content = self.decode_text_bytes(response.content)
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        return list(reader)

    def fetch_json_from_url(self, url, method=False):
        extra_config = self.get_extra_config()
        method = (method or extra_config.get("json_http_method") or "").upper()
        if not method:
            method = "POST" if self.vendor.source_kind == "json_url" else "GET"
        response = requests.request(method, url, timeout=180)
        response.raise_for_status()
        content = self.decode_text_bytes(response.content)
        content = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\xFF]", "", content)
        return json.loads(content)

    def fetch_csv_from_ftp(self, host, port, username, password, remote_filename, delimiter=";"):
        with FTP() as ftp:
            ftp.connect(host=host, port=port, timeout=180)
            ftp.login(user=username, passwd=password)
            ftp.set_pasv(True)
            output = io.BytesIO()
            ftp.retrbinary(f"RETR {remote_filename}", output.write)
            content = self.decode_text_bytes(output.getvalue())
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        return list(reader)

    def run_crawler_command(self):
        command = self.vendor.crawler_command
        if not command:
            return
        output_path = self.resolve_path(self.vendor.crawler_output_path)
        extra_config = self.get_extra_config()
        max_age_minutes = int(extra_config.get("crawler_max_age_minutes", 0) or 0)
        allow_existing_output_on_failure = bool(extra_config.get("allow_existing_output_on_failure", True))
        if output_path and max_age_minutes > 0 and os.path.isfile(output_path):
            age_seconds = time.time() - os.path.getmtime(output_path)
            if age_seconds <= max_age_minutes * 60:
                return
        env = os.environ.copy()
        extra_env = parse_json(self.vendor.crawler_env_text, default={})
        env.update({str(key): str(value) for key, value in extra_env.items()})
        workdir = self.resolve_path(self.vendor.crawler_workdir)
        completed = subprocess.run(
            command,
            cwd=workdir or None,
            env=env,
            shell=True,
            capture_output=True,
            text=True,
            timeout=1800,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr or ""
            stdout = completed.stdout or ""
            command_missing = any(
                token in "%s\n%s" % (stdout, stderr)
                for token in ("not found", "No such file or directory", "is not recognized")
            )
            if allow_existing_output_on_failure and output_path and os.path.isfile(output_path) and command_missing:
                return
            raise UserError(
                _("Crawler failed for %s:\n%s\n%s")
                % (self.vendor.name, stdout, stderr)
            )

    def fetch_csv_from_local_file(self, path, delimiter=";"):
        with open(self.resolve_path(path), "rb") as handle:
            content = self.decode_text_bytes(handle.read())
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            return list(reader)

    def build_template_url(self):
        template = self.vendor.api_url_template or self.vendor.feed_url or ""
        replacements = {
            "{_apikey_}": quote_plus(self.vendor.api_key or ""),
            "{_user_}": quote_plus(self.vendor.username or ""),
            "{_pass_}": quote_plus(self.vendor.password or ""),
            "{_userid_}": quote_plus(self.vendor.username_id or ""),
            "{_call_type_}": quote_plus(self.vendor.request_call_type or ""),
            "{_type_}": "json",
        }
        for source, target in replacements.items():
            template = template.replace(source, target)
        return template

    def first(self, value):
        return ensure_list(value)[0] if ensure_list(value) else False

    def resolve_path(self, path):
        if not path:
            return False
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.repo_root, path))

    def _guess_raw_value(self, raw, candidates):
        if not isinstance(raw, dict):
            return False
        normalized_map = {str(key).strip().lower(): value for key, value in raw.items()}
        for candidate in candidates:
            if candidate in normalized_map:
                return normalized_map[candidate]
        return False

    def _sample_keys(self, raw_rows):
        first = raw_rows[0] if raw_rows else {}
        if not isinstance(first, dict):
            return []
        sample_keys = []
        for key in list(first.keys())[:12]:
            if key in (None, False):
                sample_keys.append("<extra_column>")
            else:
                sample_keys.append(str(key))
        return sample_keys

    def _first_row_preview(self, raw_rows):
        first = raw_rows[0] if raw_rows else {}
        if not isinstance(first, dict):
            return str(first)[:300] if first else False
        preview = {}
        for key in list(first.keys())[:6]:
            preview[key] = first.get(key)
        return json.dumps(preview, ensure_ascii=False)[:300]
