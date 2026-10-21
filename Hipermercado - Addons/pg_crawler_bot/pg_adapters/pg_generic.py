from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..pg_base import PgBaseCrawler


PG_GENERIC_PRODUCT_URL_RE = re.compile(r"(/product/|/produto/|/producto/|/prod/|-\d{5,}/?$)", re.IGNORECASE)
PG_GENERIC_REF_VALUE_RE = re.compile(
    r"(?:Ref(?:erence)?|SKU|EAN)\s*[:\-]\s*(?P<value>[A-Za-z0-9\-]+)",
    re.IGNORECASE,
)


class PgGenericCrawler(PgBaseCrawler):
    adapter_key = "pg_generic"
    adapter_label = "Generic Product Crawler"

    def is_product_page(self, url: str, soup: BeautifulSoup) -> bool:
        path = urlparse(url).path
        text = soup.get_text(" ", strip=True).lower()
        if self._extract_json_ld_product(soup):
            return True
        if PG_GENERIC_PRODUCT_URL_RE.search(path):
            return True
        return any(marker in text for marker in ("sku", "ean", "gtin", "add to cart", "comprar"))

    def extract_product(self, url: str, soup: BeautifulSoup) -> dict[str, Any] | None:
        ld_product = self._extract_json_ld_product(soup)
        breadcrumbs = self._extract_breadcrumbs(soup)
        images = self._extract_images(soup, ld_product)
        specs = self._extract_specs(soup)
        name = (
            ld_product.get("name")
            or self._first_text(soup.select_one("h1"))
            or self._meta_content(soup, "meta[property='og:title']")
        )
        price = self._extract_price(soup, ld_product)
        availability_text = self._extract_availability_text(soup, ld_product)
        quantity = self.quantity_instock if self._is_in_stock(availability_text, ld_product) else self.quantity_outofstock
        brand = self._extract_brand_from_json_ld(ld_product)
        category = breadcrumbs[-2] if len(breadcrumbs) >= 2 else (breadcrumbs[-1] if breadcrumbs else "")
        sub_category = breadcrumbs[-1] if breadcrumbs else ""
        description = (
            ld_product.get("description")
            or self._extract_description_from_heading(soup, ("DESCRIPTION", "DESCRICAO", "DESCRIPCION"))
            or self._meta_content(soup, "meta[name='description']")
        )
        description_short = self._meta_content(soup, "meta[name='description']") or description[:240]
        reference = self._extract_reference(soup, ld_product)
        ean13 = self._extract_gtin(ld_product) or self._extract_ean_from_text(soup)

        if not name or not (price or reference or ean13 or ld_product):
            return None

        return {
            "source_url": url,
            "name": name,
            "reference": reference,
            "ean13": ean13,
            "brand": brand or "",
            "category": category or "",
            "sub_category": sub_category or "",
            "unit_price": price,
            "quantity": quantity,
            "availability_text": availability_text or "",
            "image_url": images[0] if images else "",
            "images": images,
            "description": description or "",
            "description_short": description_short or "",
            "features_json": specs,
        }

    def _extract_reference(self, soup: BeautifulSoup, ld_product: dict[str, Any]) -> str:
        if ld_product.get("sku"):
            return str(ld_product.get("sku")).strip()
        text = soup.get_text(" ", strip=True)
        match = PG_GENERIC_REF_VALUE_RE.search(text)
        return match.group("value").strip() if match else ""

    def _extract_ean_from_text(self, soup: BeautifulSoup) -> str:
        text = soup.get_text(" ", strip=True)
        match = re.search(r"\b\d{8,14}\b", text)
        return match.group(0) if match else ""
