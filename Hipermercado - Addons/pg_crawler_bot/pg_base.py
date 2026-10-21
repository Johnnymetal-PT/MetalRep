from __future__ import annotations

import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from .pg_browser_fetcher import PgBrowserFetcher, PgBrowserResponse


PG_PRICE_RE = re.compile(r"(\d+(?:[.,]\d{1,2})?)")
_logger = logging.getLogger(__name__)


@dataclass
class PgCrawlResult:
    records: list[dict[str, Any]]
    visited_pages: int
    discovered_products: int
    meta: dict[str, Any]


class PgBaseCrawler:
    adapter_key = "pg_base"
    adapter_label = "Base Adapter"
    supported_domains: tuple[str, ...] = ()
    skip_path_parts: tuple[str, ...] = (
        "/cdn-cgi/",
        "/checkout",
        "/cart",
        "/carrito",
        "/my-account",
        "/mi-cuenta",
        "/login",
        "/favoritos",
        "/contact",
        "/contacto",
        "/blog",
        "/stores",
        "/tiendas",
        "/services",
        "/servicios",
    )

    def __init__(
        self,
        source_url: str,
        *,
        max_pages: int = 1500,
        quantity_instock: int = 1,
        quantity_outofstock: int = 0,
        timeout_seconds: int = 30,
        pg_max_runtime_minutes: int = 0,
        **kwargs,
    ):
        self.source_url = self._normalize_url(source_url)
        self.max_pages = max_pages
        self.quantity_instock = quantity_instock
        self.quantity_outofstock = quantity_outofstock
        self.timeout_seconds = timeout_seconds
        self.pg_max_runtime_minutes = max(0, int(pg_max_runtime_minutes or 0))
        self._started_monotonic = time.monotonic()
        self._deadline_monotonic = (
            self._started_monotonic + (self.pg_max_runtime_minutes * 60)
            if self.pg_max_runtime_minutes
            else None
        )
        self._time_budget_exceeded = False
        self.extra = kwargs
        self._fetcher = PgBrowserFetcher(
            timeout_seconds=timeout_seconds,
            max_retries=3,
            proxy_server=kwargs.get("proxy_server"),
            proxy_username=kwargs.get("proxy_username"),
            proxy_password=kwargs.get("proxy_password"),
            browser_channel=kwargs.get("browser_channel"),
            storage_state_path=kwargs.get("storage_state_path"),
            restart_after_pages=kwargs.get("pg_browser_restart_pages"),
            restart_after_minutes=kwargs.get("pg_browser_restart_minutes"),
            fast_mode=bool(kwargs.get("pg_fast_mode")),
            blocked_resource_types=kwargs.get("pg_block_resource_types"),
        )
        self._visited: set[str] = set()
        self._queued: set[str] = set()
        self._products: dict[str, dict[str, Any]] = {}
        self._domain = urlparse(self.source_url).netloc
        self._fetch_failures: list[str] = []
        self._last_content_type = ""
        self._last_status_code: int | None = None
        self._progress_callback = kwargs.get("progress_callback")
        self._last_progress_emitted_at = 0.0

    @classmethod
    def supports_url(cls, source_url: str) -> bool:
        domain = urlparse(source_url).netloc.lower()
        return any(domain == value or domain.endswith(f".{value}") for value in cls.supported_domains)

    def crawl(self) -> PgCrawlResult:
        try:
            queue = deque([self.source_url])
            self._queued.add(self.source_url)
            self._emit_progress(note="Starting crawl.", force=True)

            while queue and len(self._visited) < self.max_pages:
                if self._check_time_budget("Time budget exceeded. Stopping crawl."):
                    break
                current_url = queue.popleft()
                if current_url in self._visited:
                    continue
                response = self._fetch(current_url)
                self._visited.add(current_url)
                if not response:
                    continue
                content_type = self._header_value(response.headers, "content-type")
                if "html" not in content_type:
                    continue
                soup = BeautifulSoup(response.text, "html.parser")
                if self.is_product_page(current_url, soup):
                    product = self.extract_product(current_url, soup)
                    if product:
                        self._products[self._product_key(product)] = product
                    self._emit_progress()
                    continue
                for link in self._extract_links(soup, current_url):
                    if link in self._visited or link in self._queued:
                        continue
                    queue.append(link)
                    self._queued.add(link)
                self._emit_progress()

            records = sorted(
                self._products.values(),
                key=lambda item: (
                    item.get("category") or "",
                    item.get("sub_category") or "",
                    item.get("name") or "",
                    item.get("source_url") or "",
                ),
            )
            return PgCrawlResult(
                records=records,
                visited_pages=len(self._visited),
                discovered_products=len(records),
                meta={
                    "domain": self._domain,
                    "source_url": self.source_url,
                    "last_status_code": self._last_status_code,
                    "last_content_type": self._last_content_type,
                    "fetch_failures": self._fetch_failures[:10],
                    "time_budget_minutes": self.pg_max_runtime_minutes or 0,
                    "time_budget_exceeded": self._time_budget_exceeded,
                },
            )
        finally:
            self._fetcher.close()

    def _progress_visited_pages(self) -> int:
        return len(self._visited)

    def _progress_discovered_products(self) -> int:
        return len(self._products)

    def _check_time_budget(self, note: str) -> bool:
        if not self._deadline_monotonic:
            return False
        if time.monotonic() < self._deadline_monotonic:
            return False
        if not self._time_budget_exceeded:
            self._time_budget_exceeded = True
            _logger.warning("Crawler time budget exceeded after %s minutes.", self.pg_max_runtime_minutes)
            self._emit_progress(note=note, force=True)
        return True

    def _emit_progress(self, *, note: str | None = None, force: bool = False, **extra_meta: Any) -> None:
        if not self._progress_callback:
            return
        now = time.monotonic()
        if not force and now - self._last_progress_emitted_at < 1.0:
            return
        meta: dict[str, Any] = {
            "visited_pages": self._progress_visited_pages(),
            "discovered_products": self._progress_discovered_products(),
        }
        if note:
            meta["progress_note"] = note
        for key, value in extra_meta.items():
            if value is None or value == "":
                continue
            meta[key] = value
        try:
            self._progress_callback(meta)
            self._last_progress_emitted_at = now
        except Exception as exc:
            _logger.warning("Crawler progress callback failed: %s", exc)

    def is_product_page(self, url: str, soup: BeautifulSoup) -> bool:
        raise NotImplementedError

    def extract_product(self, url: str, soup: BeautifulSoup) -> dict[str, Any] | None:
        raise NotImplementedError

    async def _page_action(self, page: Any, url: str) -> None:
        return None

    def _product_key(self, product: dict[str, Any]) -> str:
        return str(product.get("ean13") or product.get("reference") or product.get("source_url") or "")

    def _fetch(self, url: str) -> PgBrowserResponse | None:
        try:
            response = self._fetcher.fetch(url, page_action=self._page_action)
            self._last_status_code = response.status_code
            self._last_content_type = self._header_value(response.headers, "content-type")
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}")
            return response
        except Exception as exc:
            message = f"{url} -> {exc}"
            self._fetch_failures.append(message)
            _logger.warning("Crawler fetch failed: %s", message)
            return None

    def _header_value(self, headers: dict[str, str], key: str) -> str:
        lower_key = key.lower()
        for header_name, value in headers.items():
            if header_name.lower() == lower_key:
                return value
        return ""

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        candidates: list[tuple[int, str]] = []
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            candidate = self._normalize_url(urljoin(current_url, href))
            if not candidate or not self._should_visit(candidate):
                continue
            rank = self._link_priority(candidate, anchor_text=self._first_text(anchor), anchor=anchor, current_url=current_url)
            candidates.append((rank, candidate))
        candidates.sort(key=lambda item: (item[0], item[1]))
        links: list[str] = []
        seen = set()
        for _rank, candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            links.append(candidate)
        return links

    def _link_priority(self, url: str, *, anchor_text: str, anchor: Any, current_url: str) -> int:
        return 100

    def _should_visit(self, url: str) -> bool:
        parsed = urlparse(url)
        lower_path = parsed.path.lower()
        if parsed.netloc != self._domain:
            return False
        if any(part in lower_path for part in self.skip_path_parts):
            return False
        if lower_path.endswith((".jpg", ".jpeg", ".png", ".gif", ".svg", ".pdf", ".webp", ".zip")):
            return False
        return True

    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        normalized = parsed._replace(fragment="")
        if normalized.path != "/" and normalized.path.endswith("/"):
            normalized = normalized._replace(path=normalized.path.rstrip("/"))
        return urlunparse(normalized)

    def _is_likely_product_image(self, image_url: str) -> bool:
        lower_url = (image_url or "").lower()
        if not lower_url:
            return False
        skip_markers = (
            "/logo",
            "logo-",
            "logo_",
            "/icon",
            "icon-",
            "icon_",
            "/icons/",
            "/favicon",
            "/banner",
            "/banners/",
            "/placeholder",
            "/placeholders/",
            "/avatar",
            "/avatars/",
            "/sprite",
            "/sprites/",
            "/decorado/",
        )
        return not any(marker in lower_url for marker in skip_markers)

    def _extract_json_ld_product(self, soup: BeautifulSoup) -> dict[str, Any]:
        for script in soup.select("script[type='application/ld+json']"):
            raw = (script.string or script.get_text() or "").strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            product = self._find_product_node(data)
            if product:
                return product
        return {}

    def _find_product_node(self, data: Any) -> dict[str, Any]:
        if isinstance(data, dict):
            node_type = data.get("@type")
            if node_type == "Product" or (isinstance(node_type, list) and "Product" in node_type):
                return data
            for value in data.values():
                product = self._find_product_node(value)
                if product:
                    return product
        elif isinstance(data, list):
            for item in data:
                product = self._find_product_node(item)
                if product:
                    return product
        return {}

    def _extract_breadcrumbs(self, soup: BeautifulSoup) -> list[str]:
        values: list[str] = []
        selectors = (
            ".breadcrumb a",
            ".breadcrumb span",
            ".breadcrumbs a",
            ".breadcrumbs span",
            "nav.breadcrumb a",
            "nav.breadcrumb span",
            "[aria-label='breadcrumb'] a",
            "[aria-label='breadcrumb'] span",
            "[itemtype*='BreadcrumbList'] a",
            "[itemtype*='BreadcrumbList'] [itemprop='name']",
        )
        for selector in selectors:
            for candidate in soup.select(selector):
                text = self._first_text(candidate)
                if not text or text.lower() in {"inicio", "home"}:
                    continue
                values.append(text)
        values.extend(self._extract_json_ld_breadcrumbs(soup))
        deduped: list[str] = []
        seen = set()
        for value in values:
            text = self._clean_text(value)
            if not text or text.lower() in {"inicio", "home"} or text.lower() in seen:
                continue
            seen.add(text.lower())
            deduped.append(text)
        return deduped

    def _extract_json_ld_breadcrumbs(self, soup: BeautifulSoup) -> list[str]:
        for script in soup.select("script[type='application/ld+json']"):
            raw = (script.string or script.get_text() or "").strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            breadcrumbs = self._find_breadcrumb_node(data)
            if breadcrumbs:
                return breadcrumbs
        return []

    def _find_breadcrumb_node(self, data: Any) -> list[str]:
        if isinstance(data, dict):
            node_type = data.get("@type")
            if node_type == "BreadcrumbList" or (isinstance(node_type, list) and "BreadcrumbList" in node_type):
                elements = data.get("itemListElement") or []
                values: list[str] = []
                for item in elements:
                    if not isinstance(item, dict):
                        continue
                    candidate = item.get("name")
                    item_node = item.get("item")
                    if not candidate and isinstance(item_node, dict):
                        candidate = item_node.get("name")
                    text = self._clean_text(str(candidate or ""))
                    if text:
                        values.append(text)
                return values
            for value in data.values():
                breadcrumbs = self._find_breadcrumb_node(value)
                if breadcrumbs:
                    return breadcrumbs
        elif isinstance(data, list):
            for item in data:
                breadcrumbs = self._find_breadcrumb_node(item)
                if breadcrumbs:
                    return breadcrumbs
        return []

    def _extract_brand_from_json_ld(self, ld_product: dict[str, Any]) -> str:
        brand = ld_product.get("brand")
        if isinstance(brand, dict):
            return str(brand.get("name") or "").strip()
        return str(brand or "").strip()

    def _extract_gtin(self, ld_product: dict[str, Any]) -> str:
        for key in ("gtin13", "gtin", "gtin14", "mpn"):
            value = ld_product.get(key)
            if value:
                return str(value).strip()
        return ""

    def _extract_price(self, soup: BeautifulSoup, ld_product: dict[str, Any]) -> str:
        offers = ld_product.get("offers")
        if isinstance(offers, dict) and offers.get("price") is not None:
            return str(offers.get("price"))
        if isinstance(offers, list):
            for offer in offers:
                if isinstance(offer, dict) and offer.get("price") is not None:
                    return str(offer.get("price"))
        price_meta = self._meta_content(soup, "meta[property='product:price:amount']")
        if price_meta:
            return price_meta
        price_candidate = self._first_text(
            soup.select_one("[itemprop='price'], .price, .precio, .product-price, [data-price]")
        )
        if not price_candidate:
            return ""
        normalized = price_candidate.replace(".", "").replace(",", ".")
        match = PG_PRICE_RE.search(normalized)
        return match.group(1) if match else ""

    def _extract_availability_text(self, soup: BeautifulSoup, ld_product: dict[str, Any]) -> str:
        offers = ld_product.get("offers")
        if isinstance(offers, dict) and offers.get("availability"):
            return str(offers.get("availability"))
        if isinstance(offers, list):
            for offer in offers:
                if isinstance(offer, dict) and offer.get("availability"):
                    return str(offer.get("availability"))
        text = soup.get_text(" ", strip=True).lower()
        for marker in ("no disponible", "instock", "comprar", "add to cart", "agotado", "outofstock"):
            if marker in text:
                return marker
        return ""

    def _is_in_stock(self, availability_text: str, ld_product: dict[str, Any]) -> bool:
        text = (availability_text or "").lower()
        if any(token in text for token in ("instock", "comprar", "add to cart", "anadir al carrito")):
            return True
        if any(token in text for token in ("no disponible", "agotado", "outofstock", "out of stock")):
            return False
        offers = ld_product.get("offers")
        if isinstance(offers, dict):
            inventory = offers.get("inventoryLevel")
            if inventory:
                try:
                    return float(inventory) > 0
                except Exception:
                    return True
        return False

    def _extract_images(self, soup: BeautifulSoup, ld_product: dict[str, Any]) -> list[str]:
        images: list[str] = []
        ld_images = ld_product.get("image")
        if isinstance(ld_images, list):
            images.extend(str(item).strip() for item in ld_images if item)
        elif isinstance(ld_images, str):
            images.append(ld_images.strip())
        og_image = self._meta_content(soup, "meta[property='og:image']")
        if og_image:
            images.append(og_image)
        for image in soup.select("img[src]"):
            src = (image.get("src") or "").strip()
            if not src:
                continue
            full_url = self._normalize_url(urljoin(self.source_url, src))
            if full_url:
                images.append(full_url)
        deduped: list[str] = []
        seen = set()
        for image in images:
            if image in seen:
                continue
            seen.add(image)
            deduped.append(image)
        return deduped

    def _extract_description_from_heading(self, soup: BeautifulSoup, heading_hints: tuple[str, ...]) -> str:
        upper_hints = tuple(hint.upper() for hint in heading_hints)
        heading = soup.find(
            lambda tag: tag.name in {"h2", "h3", "h4", "strong"} and any(
                hint in tag.get_text(" ", strip=True).upper() for hint in upper_hints
            )
        )
        if not heading:
            return ""
        texts = []
        node = heading
        for _index in range(6):
            node = node.find_next_sibling()
            if not node:
                break
            text = node.get_text(" ", strip=True)
            if not text:
                continue
            if any(stop in text.upper() for stop in ("ESPECIFICACIONES", "SPECIFICATIONS", "CARACTERÍSTICAS")):
                break
            texts.append(text)
            if len(" ".join(texts)) > 3000:
                break
        return " ".join(texts).strip()

    def _extract_specs(self, soup: BeautifulSoup) -> dict[str, Any]:
        specs: dict[str, Any] = {}
        current_section = "General"
        for element in soup.select("h2, h3, h4, strong, table tr, li"):
            text = element.get_text(" ", strip=True)
            if not text:
                continue
            if element.name in {"h2", "h3", "h4", "strong"} and len(text) < 80:
                current_section = text
                specs.setdefault(current_section, {})
                continue
            if element.name == "tr":
                cells = [cell.get_text(" ", strip=True) for cell in element.select("th, td")]
                if len(cells) >= 2:
                    specs.setdefault(current_section, {})[cells[0]] = cells[1]
            elif element.name == "li":
                parts = [part.strip() for part in text.split(":", 1)]
                if len(parts) == 2 and parts[0] and parts[1]:
                    specs.setdefault(current_section, {})[parts[0]] = parts[1]
        return specs

    def _meta_content(self, soup: BeautifulSoup, selector: str) -> str:
        tag = soup.select_one(selector)
        return (tag.get("content") or "").strip() if tag else ""

    def _first_text(self, node: Any) -> str:
        return node.get_text(" ", strip=True) if node else ""

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "")).strip()
