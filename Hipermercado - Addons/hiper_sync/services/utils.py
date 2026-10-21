"""Utilitarios partilhados pelos services e pelos models do Hiper Sync.

Inclui parsing tolerante (``parse_json``, ``parse_float``, ``parse_int``),
limpeza de HTML, normalizacao de texto, validacao EAN13 e geracao de
fingerprints estaveis. Nenhuma funcao aqui depende do ORM, por isso e seguro
re-usar em testes unitarios e fora do contexto Odoo.
"""

import hashlib
import html
import json
import re
import unicodedata


def parse_json(text, default=None):
    if not text:
        return default if default is not None else {}
    try:
        return json.loads(text)
    except Exception:
        return default if default is not None else {}


def ensure_list(value):
    if value in (None, False, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def parse_float(value, default=0.0):
    if value in (None, False, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        return float(text)
    except Exception:
        return default


def parse_int(value, default=0):
    if value in (None, False, ""):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    digits = re.sub(r"[^\d-]", "", str(value))
    if not digits:
        return default
    try:
        return int(digits)
    except Exception:
        return default


def clean_html_text(value):
    if value in (None, False):
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def decode_html_entities(value):
    if value in (None, False):
        return ""
    return html.unescape(str(value)).strip()


def text_to_basic_html(value):
    if value in (None, False, ""):
        return ""
    text = str(value)
    if "<" in text and ">" in text:
        return text
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
    if not blocks:
        cleaned = clean_html_text(text)
        return f"<p>{html.escape(cleaned)}</p>" if cleaned else ""
    html_blocks = []
    for block in blocks:
        lines = [clean_html_text(line) for line in block.split("\n") if clean_html_text(line)]
        if not lines:
            continue
        if len(lines) == 1:
            html_blocks.append(f"<p>{html.escape(lines[0])}</p>")
            continue
        if all(":" in line and len(line) <= 160 for line in lines):
            html_blocks.append(
                "<ul>%s</ul>"
                % "".join(f"<li>{html.escape(line)}</li>" for line in lines)
            )
            continue
        html_blocks.extend(f"<p>{html.escape(line)}</p>" for line in lines)
    return "".join(html_blocks)


def normalize_text(value):
    text = clean_html_text(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fingerprint_for_payload(name, description_short="", description=""):
    normalized = "||".join(
        [
            normalize_text(name),
            normalize_text(description_short),
            normalize_text(description),
        ]
    )
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest() if normalized.strip("|") else ""


def is_valid_ean13(value):
    text = re.sub(r"\D", "", str(value or ""))
    return len(text) == 13
