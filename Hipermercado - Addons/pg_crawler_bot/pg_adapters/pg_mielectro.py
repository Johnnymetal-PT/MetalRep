from __future__ import annotations

import html
import re
import unicodedata
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..pg_base import PgBaseCrawler


PG_PRODUCT_URL_RE = re.compile(r"-\d{6,}/?$")
PG_REF_EAN_RE = re.compile(
    r"Ref\.\s*:\s*(?P<reference>.+?)\s*-\s*EAN/SKU:\s*(?P<ean>[A-Za-z0-9\-]+)",
    re.IGNORECASE | re.DOTALL,
)


class PgMielectroCrawler(PgBaseCrawler):
    adapter_key = "pg_mielectro"
    adapter_label = "Mi Electro"
    supported_domains = ("mielectro.es",)
    skip_path_parts = PgBaseCrawler.skip_path_parts + (
        "/marcas",
        "/financiacion",
        "/tiendas",
        "/servicios",
    )

    def is_product_page(self, url: str, soup: BeautifulSoup) -> bool:
        if self._extract_ref_and_ean(soup).get("reference"):
            return True
        if self._has_strong_json_ld_product(soup):
            return True
        if self._looks_like_listing_page(soup):
            return False
        return False

    def extract_product(self, url: str, soup: BeautifulSoup) -> dict[str, Any] | None:
        ld_product = self._extract_json_ld_product(soup)
        ref_ean = self._extract_ref_and_ean(soup)
        if not (ref_ean.get("reference") or ref_ean.get("ean13") or self._has_strong_json_ld_product(soup)):
            return None
        breadcrumbs = self._clean_product_breadcrumbs(self._extract_breadcrumbs(soup), ld_product, soup)
        name = (
            self._first_text(soup.select_one("h1"))
            or ld_product.get("name")
            or self._meta_content(soup, "meta[property='og:title']")
        )
        description_short = self._extract_description_short(soup, ld_product, name)
        specs = self._extract_specs(soup, name, description_short)
        images = self._extract_product_images(soup, ld_product)
        extra_media = self._extract_extra_media(soup, ld_product, images)
        brand = self._extract_brand_from_json_ld(ld_product) or self._extract_brand_from_breadcrumbs(breadcrumbs)
        price = self._extract_price(soup, ld_product)
        availability_text = self._extract_availability_text(soup, ld_product)
        quantity = self.quantity_instock if self._is_in_stock(availability_text, ld_product) else self.quantity_outofstock
        category, sub_category = self._extract_category_fields(breadcrumbs, ld_product, brand)
        description = self._extract_product_description(
            soup,
            ld_product,
            name,
            brand or "",
            ref_ean.get("reference") or ld_product.get("sku") or "",
        )

        if not name:
            return None

        return {
            "source_url": url,
            "name": name,
            "reference": ref_ean.get("reference") or ld_product.get("sku") or "",
            "ean13": ref_ean.get("ean13") or self._extract_gtin(ld_product) or "",
            "brand": brand or "",
            "category": category or "",
            "sub_category": sub_category or "",
            "unit_price": price,
            "quantity": quantity,
            "availability_text": availability_text or "",
            "image_url": images[0] if images else "",
            "thumbnail_url": self._select_thumbnail_url(images, extra_media),
            "images": images,
            "extra_media_json": extra_media,
            "description": description or "",
            "description_short": description_short or "",
            "features_json": specs,
        }

    def _extract_ref_and_ean(self, soup: BeautifulSoup) -> dict[str, str]:
        text = soup.get_text(" ", strip=True)
        match = PG_REF_EAN_RE.search(text)
        if not match:
            return {"reference": "", "ean13": ""}
        return {
            "reference": match.group("reference").strip(),
            "ean13": match.group("ean").strip(),
        }

    def _extract_brand_from_breadcrumbs(self, breadcrumbs: list[str]) -> str:
        if len(breadcrumbs) >= 3:
            return breadcrumbs[-3]
        return ""

    def _extract_category_fields(
        self,
        breadcrumbs: list[str],
        ld_product: dict[str, Any],
        brand: str,
    ) -> tuple[str, str]:
        values = [self._clean_text(value) for value in breadcrumbs if self._clean_text(value)]
        generic = {
            "inicio",
            "home",
            "tecnología",
            "tecnologia",
            "mi electro",
        }
        if brand:
            generic.add(self._clean_text(brand).lower())
        values = [value for value in values if value.lower() not in generic]
        ld_category = self._clean_text(str(ld_product.get("category") or ""))
        if ld_category:
            parts = [self._clean_text(part) for part in re.split(r"[>/|]+", ld_category) if self._clean_text(part)]
            if len(parts) >= 2:
                return parts[0], parts[-1]
            if parts:
                return parts[0], parts[0]
        if len(values) >= 2:
            return values[0], values[-1]
        if values:
            return values[0], values[0]
        return "", ""

    def _link_priority(self, url: str, *, anchor_text: str, anchor: Any, current_url: str) -> int:
        path = urlparse(url).path.lower()
        text = (anchor_text or "").strip().lower()
        if "/cdn-cgi/" in path:
            return 1000
        if PG_PRODUCT_URL_RE.search(path):
            # Prefer card/product links over broad category links.
            if len(text) >= 25 and not text.isupper():
                return 0
            if any(marker in text for marker in ("€", "eur", "ref", "sku", "añadir", "anadir", "comprar")):
                return 0
            return 20
        if any(marker in text for marker in ("hemos encontrado", "filtrar", "ver todos", "ver todas")):
            return 200
        if "/blog" in path or "/marcas" in path or "/servicios" in path:
            return 300
        return 100

    def _has_strong_json_ld_product(self, soup: BeautifulSoup) -> bool:
        ld_product = self._extract_json_ld_product(soup)
        if not ld_product:
            return False
        if ld_product.get("sku") or self._extract_gtin(ld_product):
            return True
        offers = ld_product.get("offers")
        if isinstance(offers, dict) and offers.get("price") is not None:
            return True
        if isinstance(offers, list):
            for offer in offers:
                if isinstance(offer, dict) and offer.get("price") is not None:
                    return True
        return False

    def _looks_like_listing_page(self, soup: BeautifulSoup) -> bool:
        text = soup.get_text(" ", strip=True).lower()
        listing_markers = (
            "filtrar por",
            "hemos encontrado para ti",
            "ver más productos",
            "aplicar filtros",
            "quitar filtros",
            "comprueba disponibilidad",
        )
        if any(marker in text for marker in listing_markers):
            return True
        product_links = 0
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if href and PG_PRODUCT_URL_RE.search(urlparse(href).path):
                product_links += 1
                if product_links >= 6:
                    return True
        return False

    def _clean_product_breadcrumbs(
        self,
        breadcrumbs: list[str],
        ld_product: dict[str, Any],
        soup: BeautifulSoup,
    ) -> list[str]:
        cleaned = [value.strip() for value in breadcrumbs if value and value.strip()]
        product_name = (
            self._first_text(soup.select_one("h1"))
            or str(ld_product.get("name") or "").strip()
        )
        if not product_name:
            return cleaned
        normalized_name = product_name.lower()
        while cleaned and (
            cleaned[-1].lower() == normalized_name
            or normalized_name in cleaned[-1].lower()
            or cleaned[-1].lower() in normalized_name
        ):
            cleaned.pop()
        return cleaned

    def _extract_product_images(self, soup: BeautifulSoup, ld_product: dict[str, Any]) -> list[str]:
        images = []
        ld_images = ld_product.get("image")
        if isinstance(ld_images, list):
            images.extend(str(item).strip() for item in ld_images if item)
        elif isinstance(ld_images, str):
            images.append(ld_images.strip())
        og_image = self._meta_content(soup, "meta[property='og:image']")
        if og_image:
            images.append(og_image)
        for selector in (
            ".product-cover img[src]",
            ".product-images img[src]",
            ".images-container img[src]",
            ".gallery img[src]",
            ".product-thumbs img[src]",
            ".swiper-wrapper img[src]",
            "[data-fancybox] img[src]",
            "[itemprop='image'][src]",
        ):
            for image in soup.select(selector):
                src = (image.get("data-large-image") or image.get("data-src") or image.get("src") or "").strip()
                if src:
                    images.append(self._normalize_url(self._join_image_url(src)))
        filtered = []
        seen = set()
        for image in images:
            if not image or image in seen or not self._is_likely_product_image(image):
                continue
            seen.add(image)
            filtered.append(image)
        return filtered

    def _extract_extra_media(
        self,
        soup: BeautifulSoup,
        ld_product: dict[str, Any],
        product_images: list[str],
    ) -> list[dict[str, str]]:
        media: list[dict[str, str]] = []
        seen = {product_images[0]} if product_images else set()
        for image in product_images[1:]:
            if image and image not in seen:
                media.append({"type": "image", "url": image})
                seen.add(image)
        for selector in ("video source[src]", "video[src]", "iframe[src]"):
            for node in soup.select(selector):
                src = (node.get("src") or "").strip()
                if not src:
                    continue
                media_url = self._normalize_url(self._join_image_url(src))
                if not media_url or media_url in seen:
                    continue
                media_type = "video"
                if "youtube" in media_url or "vimeo" in media_url:
                    media_type = "embed"
                media.append({"type": media_type, "url": media_url})
                seen.add(media_url)
        return media

    def _select_thumbnail_url(self, images: list[str], extra_media: list[dict[str, str]]) -> str:
        if images:
            return images[0]
        for item in extra_media:
            if item.get("type") == "image" and item.get("url"):
                return str(item["url"])
        return ""

    def _extract_description_short(self, soup: BeautifulSoup, ld_product: dict[str, Any], name: str) -> str:
        candidates = [
            self._meta_content(soup, "meta[name='description']"),
            self._meta_content(soup, "meta[property='og:description']"),
            str(ld_product.get("description") or ""),
            name,
        ]
        for candidate in candidates:
            text = self._clean_text(candidate)
            if text:
                return text
        return ""

    def _extract_product_description(
        self,
        soup: BeautifulSoup,
        ld_product: dict[str, Any],
        name: str,
        brand: str,
        reference: str,
    ) -> str:
        html_description = self._extract_product_description_html(soup, name, brand, reference)
        if html_description and self._is_valid_description_text(self._clean_text(html_description), name, brand, reference):
            return html_description
        page_text = self._page_text(soup)
        short_name = self._clean_text(name).split(" - ")[0]
        section_text = self._extract_text_between_markers(
            page_text,
            start_markers=(
                f"Características {name}",
                f"Caracteristicas {name}",
                f"Características {short_name}",
                f"Caracteristicas {short_name}",
                "## Características",
            ),
            stop_markers=(
                "DESCRIPCIÓN Y CARACTERÍSTICAS ESPECIFICACIONES",
                "ESPECIFICACIONES",
                "Servicio Mi Electro",
                "ENTREGA A DOMICILIO",
                "PUESTA EN MARCHA",
                "RESOLVEMOS CUALQUIER DUDA",
                "RETIRADA DEL ANTIGUO",
                "OPINIONES DE",
                "INCLUYE ESTA PROMOCIÓN",
            ),
        )
        if self._is_valid_description_text(section_text, name, brand, reference):
            return section_text

        heading_text = self._extract_description_from_heading(soup, ("DESCRIPCION", "CARACTERÍSTICAS", "CARACTERISTICAS"))
        if self._is_valid_description_text(heading_text, name, brand, reference):
            return heading_text
        ld_description = self._clean_text(str(ld_product.get("description") or ""))
        if self._is_valid_description_text(ld_description, name, brand, reference):
            return f"<p>{html.escape(ld_description)}</p>"
        return ""

    def _extract_product_description_html(self, soup: BeautifulSoup, name: str, brand: str, reference: str) -> str:
        start_markers = (
            "TE EXPLICAMOS TODO",
            "CARACTERÍSTICAS",
            "CARACTERISTICAS",
        )
        stop_markers = (
            "ESPECIFICACIONES",
            "OPINIONES",
            "SERVICIO MI ELECTRO",
            "ENTREGA A DOMICILIO",
            "PUESTA EN MARCHA",
            "RETIRADA DEL ANTIGUO",
        )
        for root in soup.select("section, article, div, .tab-pane"):
            text = self._clean_text(root.get_text(" ", strip=True))
            upper = text.upper()
            if not any(marker in upper for marker in start_markers):
                continue
            if not self._looks_product_specific_text(text, name, brand, reference):
                continue
            parts: list[str] = []
            current_list: list[str] = []
            seen_text = set()
            started = False
            for node in root.find_all(["h2", "h3", "h4", "p", "li"]):
                node_text = self._clean_text(node.get_text(" ", strip=True))
                if not node_text:
                    continue
                upper_text = node_text.upper()
                if not started and any(marker in upper_text for marker in start_markers):
                    started = True
                if not started:
                    continue
                if any(marker in upper_text for marker in stop_markers):
                    break
                if node_text in seen_text:
                    continue
                seen_text.add(node_text)
                if not self._is_valid_description_text(node_text, name, brand, reference) and node.name == "p":
                    continue
                if node.name in {"h2", "h3", "h4"}:
                    if current_list:
                        parts.append("<ul>%s</ul>" % "".join(current_list))
                        current_list = []
                    parts.append(f"<h3>{html.escape(node_text)}</h3>")
                    continue
                if node.name == "li":
                    current_list.append(f"<li>{html.escape(node_text)}</li>")
                    continue
                if current_list:
                    parts.append("<ul>%s</ul>" % "".join(current_list))
                    current_list = []
                parts.append(f"<p>{html.escape(node_text)}</p>")
            if current_list:
                parts.append("<ul>%s</ul>" % "".join(current_list))
            candidate = "".join(parts)
            if candidate and self._is_valid_description_text(self._clean_text(candidate), name, brand, reference):
                return candidate
        return ""

    def _is_valid_description_text(self, text: str, name: str, brand: str = "", reference: str = "") -> bool:
        cleaned = self._clean_text(text)
        if not cleaned or len(cleaned) < 40:
            return False
        lowered = self._normalize_compare_text(cleaned)
        blocked_markers = (
            "habla con nuestros expertos",
            "tambien puedes escribirnos",
            "llamanos al",
            "ver todos",
            "ver todas",
            "opiniones de",
            "trustpilot",
            "frigorificos integrables",
            "frigorificos con dispensador de agua",
        )
        if any(marker in lowered for marker in blocked_markers):
            return False
        if name and lowered == self._normalize_compare_text(name):
            return False
        if not self._looks_product_specific_text(cleaned, name, brand, reference):
            return False
        return True

    def _looks_product_specific_text(self, text: str, name: str, brand: str = "", reference: str = "") -> bool:
        normalized_text = self._normalize_compare_text(text)
        if not normalized_text:
            return False
        text_tokens = self._tokenize_compare_text(normalized_text)
        normalized_reference = self._normalize_compare_text(reference)
        if normalized_reference and normalized_reference in text_tokens:
            return True
        tokens: set[str] = set()
        generic_tokens = {
            "comprar",
            "envio",
            "color",
            "negro",
            "blanco",
            "gris",
            "smart",
            "wifi",
            "aire",
            "multi",
            "frig",
            "kcal",
            "portatil",
            "split",
            "kit",
        }
        for raw in self._tokenize_compare_text(name):
            token = raw.strip()
            if len(token) < 4 or token.isdigit():
                continue
            if token in generic_tokens:
                continue
            tokens.add(token)
        for raw in self._tokenize_compare_text(brand):
            token = raw.strip()
            if len(token) >= 3:
                tokens.add(token)
        matches = sum(1 for token in tokens if token in text_tokens)
        return matches >= 1

    def _normalize_compare_text(self, value: str) -> str:
        cleaned = self._clean_text(value).lower()
        normalized = unicodedata.normalize("NFKD", cleaned)
        return "".join(char for char in normalized if not unicodedata.combining(char))

    def _tokenize_compare_text(self, value: str) -> set[str]:
        normalized = self._normalize_compare_text(value)
        return {token for token in re.split(r"[^a-z0-9]+", normalized) if token}

    def _extract_specs(self, soup: BeautifulSoup, name: str, description_short: str = "") -> dict[str, Any]:
        specs = self._extract_json_ld_specs(soup)
        sections = self._extract_specs_from_scoped_blocks(soup)
        table_sections = self._extract_specs_from_tables(soup)
        text_sections = self._extract_specs_from_text_section(soup, name)
        for section_name, section_values in sections.items():
            target = specs.setdefault(section_name, {})
            target.update(section_values)
        for section_name, section_values in table_sections.items():
            target = specs.setdefault(section_name, {})
            target.update(section_values)
        for section_name, section_values in text_sections.items():
            target = specs.setdefault(section_name, {})
            target.update(section_values)
        specs = {section_name: values for section_name, values in specs.items() if values}
        if specs:
            return specs
        fallback = self._extract_summary_specs(name, description_short)
        return {"Resumen comercial": fallback} if fallback else {}

    def _extract_json_ld_specs(self, soup: BeautifulSoup) -> dict[str, Any]:
        ld_product = self._extract_json_ld_product(soup)
        additional = ld_product.get("additionalProperty") or []
        values: dict[str, Any] = {}
        for item in additional if isinstance(additional, list) else []:
            if not isinstance(item, dict):
                continue
            name = self._clean_text(str(item.get("name") or ""))
            value = self._clean_text(str(item.get("value") or item.get("valueReference") or ""))
            if name and value:
                values[name] = value
        return {"General": values} if values else {}

    def _extract_specs_from_scoped_blocks(self, soup: BeautifulSoup) -> dict[str, Any]:
        specs: dict[str, dict[str, str]] = {}
        roots = []
        selectors = (
            ".product-features",
            ".product-specs",
            ".product-details",
            ".tab-pane",
            "[id*='spec']",
        )
        for selector in selectors:
            roots.extend(soup.select(selector))
        if not roots:
            return {}
        seen_roots = set()
        for root in roots:
            root_id = id(root)
            if root_id in seen_roots:
                continue
            seen_roots.add(root_id)
            current_section = "General"
            for element in root.select("h2, h3, h4, strong, table tr, li, dt, dd"):
                text = self._clean_text(element.get_text(" ", strip=True))
                if not text:
                    continue
                upper = text.upper()
                if any(marker in upper for marker in ("OPINIONES", "TRUSTPILOT", "HABLA CON NUESTROS EXPERTOS", "VER TODOS")):
                    continue
                if element.name in {"h2", "h3", "h4", "strong"} and len(text) < 80:
                    if any(token in upper for token in ("ESPECIFIC", "CARACTER", "MEDIDAS", "DIMENSIONES", "CONTENIDO", "DESEMPEÑO", "DESEMPENO", "EXHIBICIÓN", "EXHIBICION", "PUERTOS", "CONTROL", "PESO")):
                        current_section = text
                        specs.setdefault(current_section, {})
                    continue
                if element.name == "tr":
                    cells = [self._clean_text(cell.get_text(" ", strip=True)) for cell in element.select("th, td")]
                    if len(cells) >= 2 and self._is_valid_feature_pair(cells[0], cells[1]):
                        specs.setdefault(current_section, {})[cells[0]] = cells[1]
                    continue
                if element.name in {"dt", "dd"}:
                    continue
                if element.name == "li":
                    key, value = self._split_feature_line(text)
                    if key and value and self._is_valid_feature_pair(key, value):
                        specs.setdefault(current_section, {})[key] = value
        return specs

    def _extract_specs_from_tables(self, soup: BeautifulSoup) -> dict[str, Any]:
        specs: dict[str, dict[str, str]] = {}
        current_section = "General"
        for row in soup.select("table tr, .table tr, [class*='spec'] tr, [class*='feature'] tr, [class*='attribute'] tr"):
            cells = [self._clean_text(cell.get_text(" ", strip=True)) for cell in row.select("th, td")]
            if len(cells) >= 2 and self._is_valid_feature_pair(cells[0], cells[1]):
                specs.setdefault(current_section, {})[cells[0]] = cells[1]
        for dt in soup.select("dl dt"):
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            key = self._clean_text(dt.get_text(" ", strip=True))
            value = self._clean_text(dd.get_text(" ", strip=True))
            if self._is_valid_feature_pair(key, value):
                specs.setdefault(current_section, {})[key] = value
        return specs

    def _extract_specs_from_text_section(self, soup: BeautifulSoup, name: str) -> dict[str, Any]:
        page_text = self._page_text(soup)
        short_name = self._clean_text(name).split(" - ")[0]
        section_text = self._extract_text_between_markers(
            page_text,
            start_markers=(
                f"{name} ESPECIFICACIONES",
                f"{short_name} ESPECIFICACIONES",
                f"{name} especificaciones",
                f"{short_name} especificaciones",
                "ESPECIFICACIONES",
                "especificaciones",
            ),
            stop_markers=(
                "Servicio Mi Electro",
                "ENTREGA A DOMICILIO",
                "PUESTA EN MARCHA",
                "RESOLVEMOS CUALQUIER DUDA",
                "RETIRADA DEL ANTIGUO",
                "OPINIONES DE",
                "INCLUYE ESTA PROMOCIÓN",
            ),
        )
        if not section_text:
            return {}
        specs: dict[str, dict[str, str]] = {}
        current_section = "General"
        lines = [self._clean_text(line) for line in section_text.split("\n")]
        lines = [line for line in lines if line]
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            upper = line.upper()
            if self._is_spec_noise_line(line):
                idx += 1
                continue
            if len(line) < 50 and not any(char.isdigit() for char in line):
                current_section = line
                specs.setdefault(current_section, {})
                idx += 1
                continue
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if next_line and len(line) < 80 and self._is_valid_feature_pair(line, next_line):
                specs.setdefault(current_section, {})[line] = next_line
                idx += 2
                continue
            inline_key, inline_value = self._split_inline_spec_line(line)
            if self._is_valid_feature_pair(inline_key, inline_value):
                specs.setdefault(current_section, {})[inline_key] = inline_value
                idx += 1
                continue
            idx += 1
        return {name: values for name, values in specs.items() if values}

    def _extract_summary_specs(self, name: str, description_short: str) -> dict[str, str]:
        candidates: list[str] = []
        if " - " in self._clean_text(name):
            candidates.append(self._clean_text(name).split(" - ", 1)[1])
        short = self._clean_text(description_short)
        if short:
            short = re.sub(r"^Comprar\s+.+?\.\s*", "", short, flags=re.IGNORECASE)
            short = re.sub(r"\.?\s*Env[ií]o.*$", "", short, flags=re.IGNORECASE)
            if short:
                candidates.append(short)
        details: list[str] = []
        seen = set()
        for candidate in candidates:
            for part in re.split(r",\s*", candidate):
                value = self._clean_text(part)
                if not value or len(value) < 3:
                    continue
                if value.lower() in seen:
                    continue
                seen.add(value.lower())
                details.append(value)
        return {f"Detalle {index}": value for index, value in enumerate(details[:8], start=1)}

    def _split_feature_line(self, text: str) -> tuple[str, str]:
        if ":" in text:
            key, value = text.split(":", 1)
            key = self._clean_text(key)
            value = self._clean_text(value)
            return (key, value) if key and value else ("", "")
        if len(text) > 90 or text.isupper():
            return "", ""
        return "", ""

    def _split_inline_spec_line(self, text: str) -> tuple[str, str]:
        cleaned = self._clean_text(text)
        if not cleaned or ":" in cleaned:
            return "", ""
        patterns = (
            r"^(?P<key>.+?)(?P<value>\d[\d\s.,/-]*(?:[A-Za-zÀ-ÿ%/()\-]+.*)?)$",
            r"^(?P<key>.+?)(?P<value>Sí|No|LED|Tocar|Integrado|Vitrocerámica|Cerámico|Negro|Acero inoxidable|Vidrio y cerámica)$",
        )
        for pattern in patterns:
            match = re.match(pattern, cleaned, flags=re.IGNORECASE)
            if not match:
                continue
            key = self._clean_text(match.group("key"))
            value = self._clean_text(match.group("value"))
            if self._is_valid_feature_pair(key, value):
                return key, value
        return "", ""

    def _page_text(self, soup: BeautifulSoup) -> str:
        text = soup.get_text("\n", strip=True)
        lines = [self._clean_text(line) for line in text.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines)

    def _extract_text_between_markers(
        self,
        text: str,
        *,
        start_markers: tuple[str, ...],
        stop_markers: tuple[str, ...],
    ) -> str:
        if not text:
            return ""
        lowered = text.lower()
        start_index = -1
        matched_marker = ""
        for marker in start_markers:
            if not marker:
                continue
            idx = lowered.find(marker.lower())
            if idx != -1 and (start_index == -1 or idx < start_index):
                start_index = idx
                matched_marker = marker
        if start_index == -1:
            return ""
        start_index += len(matched_marker)
        end_index = len(text)
        sliced = text[start_index:]
        lowered_sliced = sliced.lower()
        for marker in stop_markers:
            idx = lowered_sliced.find(marker.lower())
            if idx != -1:
                end_index = min(end_index, start_index + idx)
        candidate = self._clean_text(text[start_index:end_index])
        candidate = re.sub(r"^Ref\.\s*:.*?EAN/SKU:\s*[A-Za-z0-9\-]+\s*", "", candidate, flags=re.IGNORECASE)
        return self._clean_text(candidate)

    def _is_valid_feature_pair(self, key: str, value: str) -> bool:
        key_text = self._clean_text(key)
        value_text = self._clean_text(value)
        if not key_text or not value_text:
            return False
        if not re.search(r"[A-Za-z]", key_text):
            return False
        if len(key_text) > 140 or len(value_text) > 320:
            return False
        if self._is_spec_noise_line(key_text) or self._is_spec_noise_line(value_text):
            return False
        if key_text == value_text:
            return False
        return True

    def _is_spec_noise_line(self, text: str) -> bool:
        lowered = self._clean_text(text).lower()
        blocked_markers = (
            "cuidado personal",
            "artículo en promoción",
            "articulo en promocion",
            "habla con nuestros expertos",
            "también puedes escribirnos",
            "tambien puedes escribirnos",
            "trustpilot",
            "ver todos",
            "ver todas",
            "llámanos al",
            "llamanos al",
            "servicio mi electro",
            "entrega a domicilio",
            "puesta en marcha",
            "retirada del antiguo",
        )
        return any(marker in lowered for marker in blocked_markers)

    def _join_image_url(self, src: str) -> str:
        if src.startswith("http://") or src.startswith("https://"):
            return src
        return f"{self.source_url.rstrip('/')}/{src.lstrip('/')}"

    def _is_likely_product_image(self, image_url: str) -> bool:
        lower_url = image_url.lower()
        skip_markers = (
            "/shop/img/web/logos/",
            "/shop/img/web/decorado/",
            "icono-",
            "logo-",
            "logo_",
            "quienes-somos",
        )
        return not any(marker in lower_url for marker in skip_markers)
