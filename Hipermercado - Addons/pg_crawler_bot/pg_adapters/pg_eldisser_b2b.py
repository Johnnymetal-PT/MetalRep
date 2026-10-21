from __future__ import annotations

import asyncio
from collections import deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
import logging
import re
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import Page

from ..pg_base import PgBaseCrawler, PgCrawlResult


_logger = logging.getLogger(__name__)

PG_ELDISSER_CODE_RE = re.compile(r"\b\d{5,7}\b")
PG_ELDISSER_EAN_RE = re.compile(r"\b\d{8,14}\b")
PG_ELDISSER_STOCK_RE = re.compile(r"disp:\s*(\d+)(?:\s*\((\d+)\))?", re.IGNORECASE)


class PgEldisserB2BCrawler(PgBaseCrawler):
    adapter_key = "pg_eldisser_b2b"
    adapter_label = "Eldisser B2B"
    supported_domains = ("b2b.eldisser.com",)
    skip_path_parts = PgBaseCrawler.skip_path_parts + (
        "/logout",
        "/logoff",
        "/salir",
        "/cart",
        "/carrito",
        "/pedido",
        "/encomenda",
        "/report/",
        "addtoexistingpedidopdf",
        "imprimiret",
        "imprimir",
        "etiqueta",
        "pdf",
    )

    def __init__(
        self,
        source_url: str,
        *,
        max_pages: int = 1500,
        quantity_instock: int = 1,
        quantity_outofstock: int = 0,
        timeout_seconds: int = 30,
        **kwargs,
    ):
        if "pg_fast_mode" not in kwargs:
            kwargs["pg_fast_mode"] = True
        if "pg_block_resource_types" not in kwargs:
            kwargs["pg_block_resource_types"] = ["image", "media", "font"]
        if "pg_fast_listing" not in kwargs:
            kwargs["pg_fast_listing"] = True
        super().__init__(
            source_url,
            max_pages=max_pages,
            quantity_instock=quantity_instock,
            quantity_outofstock=quantity_outofstock,
            timeout_seconds=timeout_seconds,
            **kwargs,
        )
        self.login_username = str(kwargs.get("login_username") or kwargs.get("username") or "").strip()
        self.login_password = str(kwargs.get("login_password") or kwargs.get("password") or "").strip()
        self.login_url = str(kwargs.get("login_url") or self.source_url).strip()
        self.force_tienda_view = str(kwargs.get("force_tienda_view", "true")).strip().lower() not in {
            "0",
            "false",
            "no",
        }
        self._customer_code = self._infer_customer_code(self.login_username)
        self._product_category_overrides: dict[str, tuple[str, str]] = {}
        self._listing_card_cache: dict[str, dict] = {}
        self._listing_pages_visited = 0
        self._filter_combinations = 0
        self._combo_debug: list[dict[str, Any]] = []
        self._product_debug: list[dict[str, Any]] = []
        self._pg_fast_listing = bool(kwargs.get("pg_fast_listing"))
        self._pg_resume = bool(kwargs.get("pg_resume") or False)
        self._pg_resume_save_interval = max(1, int(kwargs.get("pg_resume_save_interval") or 200))
        self._pg_resume_state_path = str(kwargs.get("pg_resume_state_path") or "").strip()
        self._pg_resume_loaded = False
        self._pg_resume_save_counter = 0
        self._pg_resume_targets: dict[str, dict[str, str]] = {}
        self._pg_detail_concurrency = max(1, int(kwargs.get("pg_detail_concurrency") or 8))
        self._pg_detail_http_timeout_seconds = max(
            10,
            int(kwargs.get("pg_detail_http_timeout_seconds") or (self.timeout_seconds or 30)),
        )
        self._pg_http_listing = str(kwargs.get("pg_http_listing", "true")).strip().lower() not in {
            "0",
            "false",
            "no",
        }
        self._pg_http_listing_timeout_seconds = max(
            10,
            int(kwargs.get("pg_http_listing_timeout_seconds") or (self.timeout_seconds or 30)),
        )
        self._pg_search_max_rounds = max(1, int(kwargs.get("pg_search_max_rounds") or 40))
        self._pg_product_debug_log_every = max(1, int(kwargs.get("pg_product_debug_log_every") or 100))
        self._pg_product_debug_max_entries = max(20, int(kwargs.get("pg_product_debug_max_entries") or 60))
        self._accepted_product_debug_count = 0
        self._http_detail_storage_state: dict[str, Any] = {}
        self._http_listing_session_cache: requests.Session | None = None
        self._http_listing_mode = "browser"
        self._http_thread_local = threading.local()
        self._http_detail_successes = 0
        self._http_detail_fallbacks = 0
        self._stream_executor: ThreadPoolExecutor | None = None
        self._stream_futures: dict[Any, tuple[str, dict[str, str]]] = {}
        self._stream_pending: deque[tuple[str, dict[str, str]]] = deque()
        self._streaming_listing_targets = False
        login_timeout = kwargs.get("pg_login_timeout_seconds")
        retry_count = kwargs.get("pg_login_retry_count")
        self._pg_login_timeout_seconds = max(
            10,
            int(login_timeout if login_timeout is not None else (self.timeout_seconds or 30)),
        )
        self._pg_login_retry_count = max(0, int(retry_count if retry_count is not None else 2))

    def crawl(self) -> PgCrawlResult:
        try:
            self._emit_progress(note="Starting Eldisser remote crawl.", force=True)
            product_targets = self._load_resume_state()
            if product_targets is None:
                product_targets = {}
                if self._pg_http_listing:
                    try:
                        self._http_listing_mode = "http"
                        self._pg_resume_targets = product_targets
                        self._start_streaming_listing_targets()
                        product_targets = self._collect_product_targets_http()
                    except Exception as exc:
                        self._stop_streaming_listing_targets()
                        self._pg_resume_targets = {}
                        self._http_listing_mode = "browser"
                        _logger.warning("Eldisser HTTP listing discovery failed, falling back to browser: %s", exc)
                if not product_targets:
                    self._http_listing_mode = "browser"
                    self._stop_streaming_listing_targets()
                    product_targets = self._fetcher.run_page_task(self._collect_product_targets_browser)
                self._pg_resume_targets = dict(product_targets)
                self._save_resume_state(product_targets)
            else:
                self._pg_resume_targets = dict(product_targets)
            self._prepare_http_detail_fetch()
            self._emit_progress(
                note="Product targets queued.",
                force=True,
                queued_product_links=len(product_targets),
            )
            if self._streaming_listing_targets:
                self._finish_streaming_listing_targets()
            else:
                self._process_product_targets(product_targets)

            records = sorted(
                self._products.values(),
                key=lambda item: (
                    item.get("category") or "",
                    item.get("sub_category") or "",
                    item.get("name") or "",
                    item.get("source_url") or "",
                ),
            )
            if not self._time_budget_exceeded:
                self._clear_resume_state()
            return PgCrawlResult(
                records=records,
                visited_pages=self._listing_pages_visited + len(self._visited),
                discovered_products=len(records),
                meta={
                    "domain": self._domain,
                    "source_url": self.source_url,
                    "catalog_url": self._catalog_url(),
                    "last_status_code": self._last_status_code,
                    "last_content_type": self._last_content_type,
                    "fetch_failures": self._fetch_failures[:10],
                    "listing_pages_visited": self._listing_pages_visited,
                    "filter_combinations": self._filter_combinations,
                    "queued_product_links": len(product_targets),
                    "combo_debug": self._combo_debug[:10],
                    "product_debug": self._product_debug[:20],
                    "listing_fetch_mode": self._http_listing_mode,
                    "detail_fetch_mode": "http_concurrent_with_browser_fallback",
                    "detail_stream_mode": "listing_and_detail_overlap" if self._streaming_listing_targets else "post_listing_only",
                    "detail_concurrency": self._pg_detail_concurrency,
                    "detail_http_successes": self._http_detail_successes,
                    "detail_http_fallbacks": self._http_detail_fallbacks,
                    "time_budget_minutes": self.pg_max_runtime_minutes or 0,
                    "time_budget_exceeded": self._time_budget_exceeded,
                },
            )
        finally:
            self._stop_streaming_listing_targets()
            self._fetcher.close()

    def _resume_state_path(self) -> Path | None:
        if not self._pg_resume_state_path:
            return None
        return Path(self._pg_resume_state_path).resolve()

    def _load_resume_state(self) -> dict[str, dict[str, str]] | None:
        if not self._pg_resume:
            return None
        path = self._resume_state_path()
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            _logger.warning("Eldisser resume state could not be read: %s", exc)
            return None
        targets_list = payload.get("targets") or []
        if not isinstance(targets_list, list) or not targets_list:
            return None
        targets: dict[str, dict[str, str]] = {}
        for item in targets_list:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url") or "").strip()
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            if url:
                targets[url] = {str(key): str(value) for key, value in meta.items()}
        if not targets:
            return None
        self._visited = set(str(value) for value in (payload.get("visited") or []) if str(value))
        products = payload.get("products") or []
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    key = self._product_key(product)
                    if key:
                        self._products[key] = product
        self._pg_resume_loaded = True
        _logger.info(
            "Eldisser resume state loaded targets=%s visited=%s products=%s",
            len(targets),
            len(self._visited),
            len(self._products),
        )
        return targets

    def _save_resume_state(self, targets: dict[str, dict[str, str]]) -> None:
        if not self._pg_resume:
            return
        path = self._resume_state_path()
        if not path:
            return
        try:
            payload = {
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "targets": [{"url": url, "meta": meta or {}} for url, meta in targets.items()],
                "visited": sorted(self._visited),
                "products": list(self._products.values()),
            }
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            _logger.warning("Eldisser resume state could not be saved: %s", exc)

    def _clear_resume_state(self) -> None:
        path = self._resume_state_path()
        if not path:
            return
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            _logger.warning("Eldisser resume state could not be cleared: %s", exc)

    def _progress_visited_pages(self) -> int:
        return self._listing_pages_visited + len(self._visited)

    def _prepare_http_detail_fetch(self) -> None:
        # Prefer a native requests-based login session: its cookies round-trip
        # cleanly through requests.Session. Playwright cookies often carry
        # Secure/SameSite/Expires attributes that don't replay correctly and
        # cause every detail POST to 302-to-login.
        http_session: requests.Session | None = None
        try:
            http_session = self._http_listing_session(force_refresh=False)
        except Exception as exc:
            _logger.warning("Eldisser HTTP login for detail session failed, will try Playwright cookies: %s", exc)

        state: dict[str, Any] = {}
        cookie_source = "none"
        if http_session is not None:
            state = {"cookies": self._requests_cookies_to_storage_state(http_session)}
            cookie_source = "http_login"
        if not state.get("cookies") and getattr(self._fetcher, "_context", None) is not None:
            state = self._fetcher.export_storage_state()
            cookie_source = "playwright"

        self._http_detail_storage_state = dict(state or {})
        cookie_count = len(self._http_detail_storage_state.get("cookies") or [])
        _logger.info(
            "Eldisser prepared direct HTTP detail fetch cookies=%s source=%s concurrency=%s timeout_seconds=%s",
            cookie_count,
            cookie_source,
            self._pg_detail_concurrency,
            self._pg_detail_http_timeout_seconds,
        )

    def _requests_cookies_to_storage_state(self, session: requests.Session) -> list[dict[str, Any]]:
        cookies: list[dict[str, Any]] = []
        jar = getattr(session, "cookies", None)
        if jar is None:
            return cookies
        for cookie in jar:
            cookies.append(
                {
                    "name": str(cookie.name or ""),
                    "value": str(cookie.value or ""),
                    "domain": str(cookie.domain or ""),
                    "path": str(cookie.path or "/"),
                }
            )
        return cookies

    def _http_detail_ready(self) -> bool:
        return bool((self._http_detail_storage_state.get("cookies") or []))

    def _http_detail_session(self) -> requests.Session:
        session = getattr(self._http_thread_local, "session", None)
        if session is not None:
            return session
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self._fetcher.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Connection": "keep-alive",
            }
        )
        for cookie in self._http_detail_storage_state.get("cookies") or []:
            name = str(cookie.get("name") or "").strip()
            if not name:
                continue
            session.cookies.set(
                name,
                str(cookie.get("value") or ""),
                domain=str(cookie.get("domain") or ""),
                path=str(cookie.get("path") or "/"),
            )
        self._http_thread_local.session = session
        return session

    def _detail_http_headers(self) -> dict[str, str]:
        parsed = urlparse(self.source_url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": base_origin,
            "Referer": self._busqueda_url(),
        }

    def _build_detail_form_payload(self, detail_item_id: str, customer_code: str) -> dict[str, str]:
        return {
            "codProductoDetalle": detail_item_id,
            "codClienteDetalle": customer_code,
            "ocultarPVD": "0",
            "AlmacenAsociadoDetalle": "0",
            "NAVEGADORITEM": self._fetcher.user_agent,
            "PLATAFORMAITEM": "Win32",
            "RESOLUCIONITEM": "Alto: 900 x Ancho: 1440",
        }

    def _fetch_product_response_worker(self, product_url: str, metadata: dict[str, str]) -> dict[str, Any]:
        if not self._http_detail_ready():
            return {"response": None, "source": "browser_required", "error": "missing_http_session"}
        response = self._fetch_product_response_http(product_url, metadata)
        if response is None:
            return {"response": None, "source": "http_failed", "error": "http_fetch_failed"}
        return {"response": response, "source": "http"}

    def _fetch_product_response_http(self, product_url: str, metadata: dict[str, str]) -> PgBrowserResponse | None:
        detail_item_id = self._extract_detail_item_id(product_url)
        if not detail_item_id:
            _logger.warning("Eldisser direct HTTP detail skipped: could not extract item id from url=%s", product_url)
            return None

        customer_code = self._clean_text(metadata.get("customer_code") or self._customer_code)
        if not customer_code:
            _logger.warning("Eldisser direct HTTP detail skipped: missing customer_code url=%s", product_url)
            return None

        try:
            started_at = time.perf_counter()
            session = self._http_detail_session()
            response = session.post(
                self._detail_view_url(),
                data=self._build_detail_form_payload(detail_item_id, customer_code),
                headers=self._detail_http_headers(),
                timeout=(10, self._pg_detail_http_timeout_seconds),
                allow_redirects=True,
            )
            elapsed = time.perf_counter() - started_at
            if elapsed >= 2.5:
                _logger.info(
                    "Eldisser direct HTTP detail was slow item_id=%s elapsed=%.2fs status_code=%s content_length=%s",
                    detail_item_id,
                    elapsed,
                    response.status_code,
                    len(response.text or ""),
                )
            if response.status_code >= 400:
                _logger.warning(
                    "Eldisser direct HTTP detail HTTP error item_id=%s status_code=%s final_url=%s",
                    detail_item_id,
                    response.status_code,
                    response.url,
                )
                return None
            # Detect soft-fail: landed on login page (session expired) or redirect to user/login
            final_url = str(response.url or "").lower()
            text_head = (response.text or "")[:4000].lower()
            if "/user/login" in final_url or ('action="/user/login"' in text_head and 'type="password"' in text_head):
                _logger.warning(
                    "Eldisser direct HTTP detail bounced to login item_id=%s final_url=%s — re-authenticating and retrying once",
                    detail_item_id,
                    response.url,
                )
                # Re-login the shared listing session and rebuild the thread-local cookies, then retry once.
                try:
                    refreshed = self._http_listing_session(force_refresh=True)
                    self._http_detail_storage_state = {"cookies": self._requests_cookies_to_storage_state(refreshed)}
                    if hasattr(self._http_thread_local, "session"):
                        del self._http_thread_local.session
                    session = self._http_detail_session()
                    response = session.post(
                        self._detail_view_url(),
                        data=self._build_detail_form_payload(detail_item_id, customer_code),
                        headers=self._detail_http_headers(),
                        timeout=(10, self._pg_detail_http_timeout_seconds),
                        allow_redirects=True,
                    )
                    if response.status_code >= 400:
                        return None
                except Exception as retry_exc:
                    _logger.warning("Eldisser direct HTTP detail re-auth failed item_id=%s error=%s", detail_item_id, retry_exc)
                    return None
            return PgBrowserResponse(
                url=str(response.url or product_url),
                status_code=int(response.status_code or 0),
                text=str(response.text or ""),
                headers={str(key): str(value) for key, value in dict(response.headers or {}).items()},
            )
        except Exception as exc:
            _logger.warning("Eldisser direct HTTP detail failed url=%s error=%s", product_url, exc)
            return None

    def _fetch_product_response_browser(self, product_url: str, metadata: dict[str, str]) -> Any | None:
        detail_item_id = self._extract_detail_item_id(product_url)
        if not detail_item_id:
            return self._fetch(product_url)
        customer_code = self._clean_text(metadata.get("customer_code") or self._customer_code)
        if not customer_code:
            message = f"{product_url} -> missing customer_code for Eldisser detail POST"
            self._fetch_failures.append(message)
            _logger.warning("Crawler fetch failed: %s", message)
            return None
        try:
            response = self._fetcher.submit_form(
                origin_url=self._catalog_url(),
                submit_url=self._detail_view_url(),
                form_body=self._build_detail_form_body(detail_item_id, customer_code),
                page_action=self._page_action,
                headers={"X-Requested-With": "XMLHttpRequest"},
                referrer=self._busqueda_url(),
            )
            self._last_status_code = response.status_code
            self._last_content_type = self._header_value(response.headers, "content-type")
            if response.status_code >= 400:
                body_sample = self._clean_text(response.text)[:240]
                _logger.warning(
                    "Eldisser browser detail POST failed item_id=%s customer_code=%s status_code=%s response_url=%s body_sample=%s",
                    detail_item_id,
                    customer_code,
                    response.status_code,
                    response.url,
                    body_sample,
                )
                raise RuntimeError(f"HTTP {response.status_code}")
            return response
        except Exception as exc:
            message = f"{product_url} -> {exc}"
            self._fetch_failures.append(message)
            _logger.warning("Crawler fetch failed: %s", message)
            return None

    def _response_requires_browser_fallback(self, product_url: str, response: PgBrowserResponse | None) -> bool:
        if not response:
            return True
        content_type = self._header_value(response.headers, "content-type")
        if "html" not in content_type:
            return True
        lowered_url = str(response.url or product_url).lower()
        lowered_text = response.text.lower()
        if "login" in lowered_url or "acceder" in lowered_text or "iniciar sesion" in lowered_text:
            return True
        if self._fetcher._is_interstitial(response.text) or self._fetcher._is_incomplete_dom(response.text):
            return True
        return False

    def _process_product_targets(self, product_targets: dict[str, dict[str, str]]) -> None:
        pending_items = iter(product_targets.items())
        max_workers = max(1, min(self._pg_detail_concurrency, max(len(product_targets), 1)))
        futures: dict[Any, tuple[str, dict[str, str]]] = {}

        def _submit_more(executor: ThreadPoolExecutor) -> None:
            while len(futures) < max_workers and len(self._visited) < self.max_pages:
                if self._check_time_budget("Time budget exceeded. Stopping product fetch loop."):
                    return
                try:
                    product_url, metadata = next(pending_items)
                except StopIteration:
                    return
                if product_url in self._visited:
                    continue
                self._product_category_overrides[product_url] = (
                    metadata.get("category") or "",
                    metadata.get("sub_category") or "",
                )
                futures[executor.submit(self._fetch_product_response_worker, product_url, metadata)] = (product_url, metadata)

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="pgeldisser") as executor:
            _submit_more(executor)
            while futures:
                done, _pending = wait(list(futures.keys()), return_when=FIRST_COMPLETED)
                for future in done:
                    product_url, metadata = futures.pop(future)
                    try:
                        result = future.result()
                    except Exception as exc:
                        result = {"response": None, "source": "http_failed", "error": str(exc)}
                    self._handle_product_target_result(product_url, metadata, result)
                _submit_more(executor)
                if self._check_time_budget("Time budget exceeded. Stopping product fetch loop.") and not futures:
                    self._save_resume_state(product_targets)
                    break

    def _start_streaming_listing_targets(self) -> None:
        self._stream_pending.clear()
        self._stream_futures.clear()
        self._stream_executor = ThreadPoolExecutor(
            max_workers=max(1, self._pg_detail_concurrency),
            thread_name_prefix="pgeldisserstream",
        )
        self._streaming_listing_targets = True

    def _stop_streaming_listing_targets(self) -> None:
        executor = self._stream_executor
        self._stream_executor = None
        self._stream_futures.clear()
        self._stream_pending.clear()
        self._streaming_listing_targets = False
        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=False)

    def _register_product_target(
        self,
        targets: dict[str, dict[str, str]],
        product_url: str,
        metadata: dict[str, str],
    ) -> bool:
        if product_url in targets:
            return False
        normalized_metadata = {
            "category": str(metadata.get("category") or ""),
            "sub_category": str(metadata.get("sub_category") or ""),
            "customer_code": str(metadata.get("customer_code") or ""),
        }
        targets[product_url] = normalized_metadata
        if self._streaming_listing_targets and product_url not in self._visited:
            if not self._http_detail_ready():
                try:
                    self._prepare_http_detail_fetch()
                except Exception as exc:
                    _logger.warning("Eldisser could not prepare streamed detail fetch yet: %s", exc)
            self._stream_pending.append((product_url, normalized_metadata))
            self._submit_stream_pending_targets()
        return True

    def _submit_stream_pending_targets(self) -> None:
        if not self._stream_executor:
            return
        if self._check_time_budget("Time budget exceeded. Stopping streamed product fetch scheduling."):
            return
        while self._stream_pending and len(self._stream_futures) < self._pg_detail_concurrency:
            product_url, metadata = self._stream_pending.popleft()
            if product_url in self._visited:
                continue
            self._product_category_overrides[product_url] = (
                metadata.get("category") or "",
                metadata.get("sub_category") or "",
            )
            future = self._stream_executor.submit(self._fetch_product_response_worker, product_url, metadata)
            self._stream_futures[future] = (product_url, metadata)

    def _drain_stream_futures(self, *, block: bool) -> None:
        while self._stream_futures:
            timeout = None if block else 0
            done, _pending = wait(list(self._stream_futures.keys()), timeout=timeout, return_when=FIRST_COMPLETED)
            if not done:
                break
            for future in done:
                product_url, metadata = self._stream_futures.pop(future)
                try:
                    result = future.result()
                except Exception as exc:
                    result = {"response": None, "source": "http_failed", "error": str(exc)}
                self._handle_product_target_result(product_url, metadata, result)
            self._submit_stream_pending_targets()
            if not block:
                break

    def _finish_streaming_listing_targets(self) -> None:
        self._submit_stream_pending_targets()
        while self._stream_futures or self._stream_pending:
            if self._check_time_budget("Time budget exceeded. Stopping streamed product fetch loop.") and not self._stream_futures:
                break
            self._drain_stream_futures(block=True)
            self._submit_stream_pending_targets()
        self._save_resume_state(self._pg_resume_targets)

    def _handle_product_target_result(self, product_url: str, metadata: dict[str, str], result: dict[str, Any]) -> None:
        response = result.get("response")
        source = str(result.get("source") or "")
        if self._response_requires_browser_fallback(product_url, response):
            if source != "browser":
                self._http_detail_fallbacks += 1
            response = self._fetch_product_response_browser(product_url, metadata)
            source = "browser"
        elif source == "http":
            self._http_detail_successes += 1

        self._visited.add(product_url)
        if not response:
            self._emit_progress(
                current_category=metadata.get("category") or "",
                current_sub_category=metadata.get("sub_category") or "",
                queued_product_links=len(self._visited),
            )
            self._record_product_debug(
                {
                    "requested_url": product_url,
                    "category": metadata.get("category") or "",
                    "sub_category": metadata.get("sub_category") or "",
                    "status": "fetch_failed",
                    "source": source or "none",
                }
            )
            self._mark_product_processed_for_resume()
            return

        self._last_status_code = response.status_code
        self._last_content_type = self._header_value(response.headers, "content-type")
        content_type = self._header_value(response.headers, "content-type")
        if "html" not in content_type:
            self._emit_progress(
                current_category=metadata.get("category") or "",
                current_sub_category=metadata.get("sub_category") or "",
                queued_product_links=len(self._visited),
            )
            self._record_product_debug(
                {
                    "requested_url": product_url,
                    "final_url": response.url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "status": "non_html",
                    "source": source,
                }
            )
            self._mark_product_processed_for_resume()
            return

        soup = BeautifulSoup(response.text, "html.parser")
        final_url = product_url if self._extract_detail_item_id(product_url) else (response.url or product_url)
        is_product = self.is_product_page(final_url, soup)
        if not is_product and source != "browser":
            self._http_detail_fallbacks += 1
            browser_response = self._fetch_product_response_browser(product_url, metadata)
            if browser_response:
                response = browser_response
                source = "browser"
                self._last_status_code = response.status_code
                self._last_content_type = self._header_value(response.headers, "content-type")
                content_type = self._header_value(response.headers, "content-type")
                soup = BeautifulSoup(response.text, "html.parser")
                final_url = product_url if self._extract_detail_item_id(product_url) else (response.url or product_url)
                is_product = self.is_product_page(final_url, soup)

        if not is_product:
            self._emit_progress(
                current_category=metadata.get("category") or "",
                current_sub_category=metadata.get("sub_category") or "",
                queued_product_links=len(self._visited),
            )
            self._record_product_debug(
                {
                    "requested_url": product_url,
                    "final_url": final_url,
                    "response_url": response.url,
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "status": "not_product_page",
                    "source": source,
                    "name": self._extract_product_name(soup),
                    "reference": self._extract_reference(soup),
                    "ean13": self._extract_ean(soup),
                    "pvp": self._extract_named_price(response.text, "PVP"),
                    "precio": self._extract_named_price(response.text, "PRECIO"),
                    "catalog_listing": self._is_catalog_listing_page(
                        final_url,
                        self._normalize_label_text(soup.get_text(" ", strip=True)),
                    ),
                }
            )
            self._mark_product_processed_for_resume()
            return

        product = self.extract_product(final_url, soup)
        if product:
            self._products[self._product_key(product)] = product
            self._emit_progress(
                note="Extracting product details.",
                current_category=product.get("category") or metadata.get("category") or "",
                current_sub_category=product.get("sub_category") or metadata.get("sub_category") or "",
                queued_product_links=len(self._visited),
            )
            self._record_product_debug(
                {
                    "requested_url": product_url,
                    "final_url": final_url,
                    "response_url": response.url,
                    "status_code": response.status_code,
                    "status": "accepted_product",
                    "source": source,
                    "name": product.get("name") or "",
                    "reference": product.get("reference") or "",
                    "ean13": product.get("ean13") or "",
                    "category": product.get("category") or "",
                    "sub_category": product.get("sub_category") or "",
                }
            )
        else:
            self._emit_progress(
                current_category=metadata.get("category") or "",
                current_sub_category=metadata.get("sub_category") or "",
                queued_product_links=len(self._visited),
            )
            features = self._extract_specifications(soup)
            self._record_product_debug(
                {
                    "requested_url": product_url,
                    "final_url": final_url,
                    "response_url": response.url,
                    "status_code": response.status_code,
                    "status": "extract_returned_none",
                    "source": source,
                    "name": self._extract_product_name(soup),
                    "reference": self._extract_reference(soup),
                    "ean13": self._extract_ean(soup),
                    "pvp": self._extract_named_price(response.text, "PVP"),
                    "precio": self._extract_named_price(response.text, "PRECIO"),
                    "spec_sections": list(features.keys())[:5],
                }
            )
        self._mark_product_processed_for_resume()

    def _mark_product_processed_for_resume(self) -> None:
        self._pg_resume_save_counter += 1
        if self._pg_resume_save_counter >= self._pg_resume_save_interval:
            self._pg_resume_save_counter = 0
            self._save_resume_state(self._pg_resume_targets)

    def _extract_detail_item_id(self, value: str) -> str:
        if not value:
            return ""
        match = re.search(r"""DetalleItem\(\s*['"]?(\d{4,10})['"]?\s*\)|[?&]id=(\d{4,10})""", value, re.IGNORECASE)
        if not match:
            return ""
        return match.group(1) or match.group(2) or ""

    def _detail_view_url(self) -> str:
        return self._normalize_url(urljoin(self.source_url, "/Item/DetalleItemVista"))

    def _busqueda_url(self) -> str:
        return self._normalize_url(urljoin(self.source_url, "/Item/Busqueda"))

    def _build_detail_form_body(self, detail_item_id: str, customer_code: str) -> str:
        return urlencode(self._build_detail_form_payload(detail_item_id, customer_code))

    def _infer_customer_code(self, value: str) -> str:
        groups = re.findall(r"\d+", value or "")
        if not groups:
            return ""
        inferred = groups[-1]
        if len(inferred) < 6:
            inferred = inferred.zfill(6)
        return inferred

    def _http_listing_session(self, *, force_refresh: bool = False) -> requests.Session:
        if not force_refresh and self._http_listing_session_cache is not None:
            return self._http_listing_session_cache
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self._fetcher.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )
        self._http_login(session)
        self._http_listing_session_cache = session
        return session

    def _http_login(self, session: requests.Session) -> None:
        if not (self.login_username and self.login_password):
            raise RuntimeError("Eldisser B2B login required but login_username/login_password were not provided.")
        login_url = self.login_url or self._normalize_url(urljoin(self.source_url, "/user/login"))
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                get_response = session.get(login_url, timeout=self._pg_http_listing_timeout_seconds, allow_redirects=True)
                get_response.raise_for_status()
                payload = self._http_build_login_payload(get_response.text)
                post_response = session.post(
                    login_url,
                    data=payload,
                    timeout=self._pg_http_listing_timeout_seconds,
                    allow_redirects=True,
                    headers={"Referer": str(get_response.url or login_url)},
                )
                post_response.raise_for_status()
                if self._http_is_login_page(post_response.text, str(post_response.url or login_url)):
                    raise RuntimeError("Eldisser HTTP login failed or session was not established.")
                return
            except requests.HTTPError as exc:
                last_error = exc
                status = getattr(exc.response, "status_code", 0)
                if status in (403, 429, 502, 503, 504) and attempt < 2:
                    _logger.warning("Eldisser HTTP login attempt %s got status=%s, retrying.", attempt + 1, status)
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
            except requests.RequestException as exc:
                last_error = exc
                if attempt < 2:
                    _logger.warning("Eldisser HTTP login attempt %s failed: %s, retrying.", attempt + 1, exc)
                    time.sleep(2 * (attempt + 1))
                    continue
                raise
        if last_error is not None:
            raise last_error

    def _http_build_login_payload(self, login_html: str) -> dict[str, str]:
        payload: dict[str, str] = {
            "ReturnUrl": "",
            "dominio": "ELDISSER.NAV",
        }
        try:
            soup = BeautifulSoup(login_html or "", "html.parser")
            form = soup.select_one("form[action*='/user/login' i]") or soup.find("form")
            if form:
                for inp in form.find_all("input"):
                    name = str(inp.get("name") or "").strip()
                    if not name:
                        continue
                    input_type = str(inp.get("type") or "text").lower()
                    if input_type in {"submit", "button", "reset", "file", "image"}:
                        continue
                    if name in {"login", "password"}:
                        continue
                    payload[name] = str(inp.get("value") or "")
        except Exception as exc:
            _logger.warning("Eldisser login form parse failed, using defaults: %s", exc)
        payload["login"] = self.login_username
        payload["password"] = self.login_password
        return payload

    def _http_is_login_page(self, html: str, url: str) -> bool:
        lowered_url = str(url or "").lower()
        lowered_html = (html or "").lower()
        return (
            "login - extranet eldisser" in lowered_html
            or "/user/login" in lowered_url
            or 'action="/user/login"' in lowered_html
            or 'type="password"' in lowered_html and "bienvenido" in lowered_html
        )

    def _http_is_runtime_error(self, html: str) -> bool:
        lowered = (html or "").lower()
        return "error en runtime" in lowered or "error de servidor en la aplicación" in lowered

    def _http_catalog_html(self, session: requests.Session) -> str:
        response = session.get(self._catalog_url(), timeout=self._pg_http_listing_timeout_seconds, allow_redirects=True)
        response.raise_for_status()
        html = str(response.text or "")
        if self._http_is_login_page(html, str(response.url or self._catalog_url())):
            self._http_login(session)
            response = session.get(self._catalog_url(), timeout=self._pg_http_listing_timeout_seconds, allow_redirects=True)
            response.raise_for_status()
            html = str(response.text or "")
        if self._http_is_login_page(html, str(response.url or self._catalog_url())):
            raise RuntimeError("Eldisser catalog HTML still points to login after HTTP authentication.")
        return html

    def _http_extract_form(self, html: str) -> Any:
        soup = BeautifulSoup(html, "html.parser")
        form = soup.select_one("form#FrmFiltros")
        if not form:
            raise RuntimeError("Eldisser filter form FrmFiltros was not found in catalog HTML.")
        return form

    def _http_select_from_form(self, form: Any, label: str):
        normalized = self._normalize_label_text(label)
        if "GAMA" in normalized:
            return form.select_one("select[data-search-name_gama]") or form.select_one("select[id*='gama' i]") or form.select_one("select[name*='gama' i]")
        if "FAMILIA" in normalized and "SUB" not in normalized:
            return form.select_one("select#Product_Group_Code_Text_eq_Filter") or form.select_one("select[name='Product_Group_Code_Text_eq_Filter']") or form.select_one("select[name*='product_group' i]")
        if "SUBFAMILIA" in normalized:
            return form.select_one("select#Subfamilia_Text_eq_Filter") or form.select_one("select[name='Subfamilia_Text_eq_Filter']") or form.select_one("select[name*='subfamilia' i]")
        return None

    def _http_extract_options_from_select(self, select: Any) -> list[dict[str, str]]:
        if not select:
            return []
        cleaned: list[dict[str, str]] = []
        seen = set()
        for option in select.select("option"):
            text = self._clean_text(option.get_text(" ", strip=True))
            value = self._clean_text(str(option.get("value") or ""))
            normalized = self._normalize_label_text(text)
            normalized_value = self._normalize_label_text(value)
            if not text or normalized in {"SELECCIONAR", "TODOS", "TODAS", "BORRAR FILTRO", "BORRAR FILTROS"}:
                continue
            if normalized_value == "___BLANK___":
                continue
            key = (value or text, normalized)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append({"value": value or text, "text": text})
        return cleaned

    def _http_extract_catalog_options(self, html: str, label: str) -> list[dict[str, str]]:
        form = self._http_extract_form(html)
        return self._http_extract_options_from_select(self._http_select_from_form(form, label))

    def _http_fetch_family_options(self, session: requests.Session, gama_value: str) -> list[dict[str, str]]:
        response = session.post(
            self._normalize_url(urljoin(self.source_url, "/ProductGroup/Index")),
            data={"itemcategory": gama_value},
            timeout=self._pg_http_listing_timeout_seconds,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self._catalog_url(),
            },
        )
        response.raise_for_status()
        return self._http_extract_options_from_select(BeautifulSoup(f"<select>{response.text}</select>", "html.parser").select_one("select"))

    def _http_fetch_subfamilia_options(self, session: requests.Session, gama_value: str, familia_value: str) -> list[dict[str, str]]:
        response = session.post(
            self._normalize_url(urljoin(self.source_url, "/Subfamilia/FiltroSubFamilia")),
            data={"productgroup": familia_value, "itemcategorycode": gama_value},
            timeout=self._pg_http_listing_timeout_seconds,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self._catalog_url(),
            },
        )
        response.raise_for_status()
        return self._http_extract_options_from_select(BeautifulSoup(f"<select>{response.text}</select>", "html.parser").select_one("select"))

    def _http_customer_code_from_catalog(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        candidates = [
            soup.select_one("input[name='customerno']"),
            soup.select_one("input#customerno"),
            soup.select_one("input[name='codClienteDetalle']"),
            soup.select_one("input#codClienteDetalle"),
            soup.select_one("input#idcliente"),
        ]
        for candidate in candidates:
            value = self._clean_text(str(candidate.get("value") or "")) if candidate else ""
            digits = re.sub(r"\D+", "", value)
            if digits:
                resolved = digits.zfill(6) if len(digits) < 6 else digits
                self._customer_code = resolved
                return resolved
        return self._customer_code

    def _http_form_payload_from_catalog_html(
        self,
        html: str,
        combo: dict[str, dict[str, str]],
    ) -> list[tuple[str, str]]:
        form = self._http_extract_form(html)
        payload: list[tuple[str, str]] = []
        for element in form.select("input, select, textarea"):
            name = self._clean_text(str(element.get("name") or ""))
            if not name:
                continue
            tag = str(element.name or "").lower()
            if tag == "input":
                input_type = str(element.get("type") or "text").lower()
                if input_type in {"button", "submit", "reset", "file"}:
                    continue
                if input_type in {"checkbox", "radio"}:
                    if element.has_attr("checked"):
                        payload.append((name, str(element.get("value") or "on")))
                    continue
                payload.append((name, str(element.get("value") or "")))
                continue
            if tag == "select":
                selected_option = element.select_one("option[selected]") or element.select_one("option")
                payload.append((name, self._clean_text(str(selected_option.get("value") or "")) if selected_option else ""))
                continue
            if tag == "textarea":
                payload.append((name, self._clean_text(element.get_text(" ", strip=True))))

        gama_select = self._http_select_from_form(form, "GAMA")
        familia_select = self._http_select_from_form(form, "FAMILIA")
        subfamilia_select = self._http_select_from_form(form, "SUBFAMILIA")
        if gama_select:
            self._set_http_payload_value(payload, str(gama_select.get("name") or ""), str((combo.get("gama") or {}).get("value") or ""))
        if familia_select:
            self._set_http_payload_value(payload, str(familia_select.get("name") or ""), str((combo.get("familia") or {}).get("value") or ""))
        if subfamilia_select:
            self._set_http_payload_value(payload, str(subfamilia_select.get("name") or ""), str((combo.get("subfamilia") or {}).get("value") or ""))

        self._set_http_payload_value(payload, "customerno", self._customer_code)
        self._set_http_payload_value(payload, "NAVEGADOR", self._fetcher.user_agent)
        self._set_http_payload_value(payload, "PLATAFORMA", "Win32")
        self._set_http_payload_value(payload, "RESOLUCION", "Alto: 900 x Ancho: 1440")
        self._set_http_payload_value(payload, "ANCHOPANTALLA", "1440")
        self._set_http_payload_value(payload, "keynav", "0")
        self._set_http_payload_value(payload, "ispost", "1")
        self._set_http_payload_value(payload, "VistaCalendario", "0")
        self._set_http_payload_value(payload, "centroLogisticoCercano", "0")
        self._set_http_payload_value(payload, "AlmacenAsociado", "0")
        self._set_http_payload_value(payload, "attributos_gama", str((combo.get("gama") or {}).get("value") or ""))
        self._set_http_payload_value(payload, "attributos_familia", str((combo.get("familia") or {}).get("value") or ""))
        return payload

    def _set_http_payload_value(self, payload: list[tuple[str, str]], name: str, value: str) -> None:
        if not name:
            return
        updated = False
        new_payload: list[tuple[str, str]] = []
        for current_name, current_value in payload:
            if current_name != name:
                new_payload.append((current_name, current_value))
                continue
            if not updated:
                new_payload.append((current_name, value))
                updated = True
        if not updated:
            new_payload.append((name, value))
        payload[:] = new_payload

    def _http_extract_html_payload(self, response: requests.Response) -> str:
        raw_text = str(response.text or "")
        content_type = str(response.headers.get("content-type") or "").lower()
        if "json" not in content_type and not raw_text.lstrip().startswith(("{", "[")):
            return raw_text
        try:
            payload = response.json()
        except Exception:
            return raw_text
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            for key in ("html", "Html", "contenido", "Contenido", "content", "Content", "result", "Result"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return raw_text

    def _http_search_response(self, session: requests.Session, payload: list[tuple[str, str]]) -> str:
        response = session.post(
            self._busqueda_url(),
            data=payload,
            timeout=self._pg_http_listing_timeout_seconds,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self._catalog_url(),
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
        )
        response.raise_for_status()
        html = self._http_extract_html_payload(response)
        if self._http_is_runtime_error(html):
            raise RuntimeError("Eldisser Item/Busqueda returned a runtime error page.")
        if self._http_is_login_page(html, str(response.url or self._busqueda_url())):
            raise RuntimeError("Eldisser Item/Busqueda redirected back to login.")
        return html

    def _http_fetch_combo_listing_links(
        self,
        session: requests.Session,
        combo: dict[str, dict[str, str]],
    ) -> tuple[list[str], str, int]:
        catalog_html = self._http_catalog_html(session)
        customer_code = self._http_customer_code_from_catalog(catalog_html)
        payload = self._http_form_payload_from_catalog_html(catalog_html, combo)
        links: list[str] = []
        seen = set()
        previous_signature = ""
        rounds = 0
        # keynav=0 and keynav=1 return the same first batch; next VER MAS batch starts at keynav=2
        next_keynav = 2

        for _round in range(self._pg_search_max_rounds):
            if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                break
            html = self._http_search_response(session, payload)
            rounds += 1
            soup = BeautifulSoup(html, "html.parser")
            round_links = self._extract_listing_product_links(soup, self._busqueda_url())
            new_links = [candidate for candidate in round_links if candidate not in seen]
            for candidate in new_links:
                seen.add(candidate)
                links.append(candidate)
            current_signature = "|".join(round_links[:20])
            normalized_text = self._normalize_label_text(soup.get_text(" ", strip=True))
            has_more = bool(soup.select(".linkSiguiente")) or "VER MAS" in normalized_text
            if has_more and not new_links and previous_signature == current_signature:
                raise RuntimeError("Eldisser HTTP listing pagination did not advance.")
            previous_signature = current_signature
            if not has_more or not new_links:
                break
            self._set_http_payload_value(payload, "keynav", str(next_keynav))
            next_keynav += 1

        return links, customer_code, rounds

    def _http_queue_combo_targets(
        self,
        session: requests.Session,
        targets: dict[str, dict[str, str]],
        combo: dict[str, dict[str, str]],
    ) -> None:
        if self._check_time_budget("Time budget exceeded. Skipping remaining combos."):
            return
        self._filter_combinations += 1
        category = self._combo_category(combo)
        sub_category = self._combo_sub_category(combo)
        combo_links, customer_code, round_count = self._http_fetch_combo_listing_links(session, combo)
        self._listing_pages_visited += max(round_count, 1)

        for product_url in combo_links:
            self._register_product_target(
                targets,
                product_url,
                {
                    "category": category,
                    "sub_category": sub_category,
                    "customer_code": customer_code,
                },
            )
            if len(targets) >= self.max_pages:
                break

        combo_debug_entry = {
            "category": category,
            "sub_category": sub_category,
            "catalog_url": self._catalog_url(),
            "customer_code": customer_code,
            "links_found": len(combo_links),
            "sample_links": combo_links[:5],
            "listing_rounds": round_count,
            "transport": "http",
        }
        self._combo_debug.append(combo_debug_entry)
        _logger.info(
            "Eldisser HTTP combo fetched category=%s sub_category=%s customer_code=%s links_found=%s listing_rounds=%s queued_links=%s sample_links=%s",
            category,
            sub_category,
            customer_code,
            len(combo_links),
            round_count,
            len(targets),
            combo_links[:3],
        )
        self._emit_progress(
            note="Scanning category listings.",
            current_category=category,
            current_sub_category=sub_category,
            queued_product_links=len(targets),
        )
        self._drain_stream_futures(block=False)

    def _collect_product_targets_http(self) -> dict[str, dict[str, str]]:
        session = self._http_listing_session(force_refresh=True)
        catalog_html = self._http_catalog_html(session)
        targets = self._pg_resume_targets
        gama_options = self._http_extract_catalog_options(catalog_html, "GAMA")
        if not gama_options:
            raise RuntimeError("Eldisser HTTP catalog exposed no GAMA options.")

        _logger.info("Eldisser HTTP catalog loaded %s GAMA options.", len(gama_options))
        for gama in gama_options:
            if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                break
            if len(targets) >= self.max_pages:
                break

            familia_options = self._http_fetch_family_options(session, gama["value"])
            if not familia_options:
                _logger.warning(
                    "Eldisser HTTP GAMA text=%s value=%s exposed no FAMILIA options after selection.",
                    gama.get("text"),
                    gama.get("value"),
                )
                self._http_queue_combo_targets(session, targets, {"gama": gama})
                continue

            _logger.info(
                "Eldisser HTTP GAMA text=%s value=%s exposed %s FAMILIA options.",
                gama.get("text"),
                gama.get("value"),
                len(familia_options),
            )

            for familia in familia_options:
                if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                    break
                if len(targets) >= self.max_pages:
                    break

                subfamilia_options = self._http_fetch_subfamilia_options(session, gama["value"], familia["value"])
                if not subfamilia_options:
                    _logger.warning(
                        "Eldisser HTTP combo gama=%s familia=%s exposed no SUBFAMILIA options after selection.",
                        gama.get("text"),
                        familia.get("text"),
                    )
                    self._http_queue_combo_targets(session, targets, {"gama": gama, "familia": familia})
                    continue

                _logger.info(
                    "Eldisser HTTP combo gama=%s familia=%s exposed %s SUBFAMILIA options.",
                    gama.get("text"),
                    familia.get("text"),
                    len(subfamilia_options),
                )

                for subfamilia in subfamilia_options:
                    if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                        break
                    if len(targets) >= self.max_pages:
                        break
                    self._http_queue_combo_targets(
                        session,
                        targets,
                        {"gama": gama, "familia": familia, "subfamilia": subfamilia},
                    )

        return targets

    async def _page_action(self, page: Page, url: str) -> None:
        await self._ensure_logged_in(page, url)
        if self.force_tienda_view:
            await self._ensure_tienda_view(page)

    def is_product_page(self, url: str, soup: BeautifulSoup) -> bool:
        text = self._normalize_label_text(soup.get_text(" ", strip=True))
        if self._is_catalog_listing_page(url, text):
            return False
        if "CARACTERISTICAS PRINCIPALES" in text:
            return True
        if "ESPECIFICACIONES" in text and "PRECIO" in text and "PVP" in text:
            return True
        if "DISP:" in text and "PRECIO" in text and "PVD" in text:
            return True
        return bool(self._extract_product_name(soup) and PG_ELDISSER_CODE_RE.search(text) and ("PVP" in text or "PRECIO" in text))

    def extract_product(self, url: str, soup: BeautifulSoup) -> dict[str, Any] | None:
        text = soup.get_text(" ", strip=True)
        card = self._listing_card_cache.get(url, {})
        features = self._extract_specifications(soup)
        name = self._extract_product_name(soup) or card.get("name", "")
        reference = self._extract_reference(soup)
        ean13 = self._extract_ean(soup, features) or card.get("ean13", "")
        brand = self._extract_brand(soup) or card.get("brand", "")
        pvp = self._extract_named_price(text, "PVP")
        supplier_price = self._extract_named_price(text, "PRECIO")
        stock_info = self._extract_stock_info(text)
        availability_text = stock_info["text"]
        quantity = stock_info["total_quantity"]
        category, sub_category = self._product_category_overrides.get(url) or self._extract_category_fields(soup)
        images = self._extract_product_images(soup)
        if not images and card.get("image_url"):
            images = [card["image_url"]]
        self._add_stock_features(features, stock_info)
        principales = self._extract_caracteristicas_principales(soup)

        if not (name and (reference or ean13 or pvp or supplier_price)):
            return None

        return {
            "source_url": url,
            "name": name,
            "reference": reference,
            "ean13": ean13,
            "brand": brand,
            "category": category,
            "sub_category": sub_category,
            "unit_price": supplier_price or pvp,
            "wholesale_price": supplier_price or pvp,
            "quantity": quantity,
            "availability_text": availability_text,
            "image_url": images[0] if images else "",
            "thumbnail_url": images[0] if images else "",
            "images": images,
            "extra_media_json": [{"type": "image", "url": image} for image in images[1:]],
            "description": self._specs_to_text(features),
            "description_short": self._principales_to_text(principales),
            "features_json": features,
        }

    async def _collect_product_targets_browser(self, page: Page) -> dict[str, dict[str, str]]:
        targets = self._pg_resume_targets

        await self._open_catalog(page)
        gama_options = await self._wait_for_select_options(page, ("GAMA",))
        if not gama_options:
            _logger.warning(
                "Eldisser catalog exposed no GAMA options, falling back to unfiltered search. filter_debug=%s",
                await self._debug_filter_controls(page),
            )
            await self._queue_combo_targets(page, targets, {})
            return targets

        _logger.info("Eldisser catalog loaded %s GAMA options.", len(gama_options))

        for gama in gama_options:
            if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                break
            if len(targets) >= self.max_pages:
                break

            if not await self._apply_combo(page, {"gama": gama}):
                _logger.warning("Eldisser failed to apply GAMA option text=%s value=%s", gama.get("text"), gama.get("value"))
                continue

            familia_options = await self._wait_for_select_options(page, ("FAMILIA",))
            if not familia_options:
                _logger.warning(
                    "Eldisser GAMA text=%s value=%s exposed no FAMILIA options after selection.",
                    gama.get("text"),
                    gama.get("value"),
                )
                await self._queue_combo_targets(page, targets, {"gama": gama})
                continue

            _logger.info(
                "Eldisser GAMA text=%s value=%s exposed %s FAMILIA options.",
                gama.get("text"),
                gama.get("value"),
                len(familia_options),
            )

            for familia in familia_options:
                if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                    break
                if len(targets) >= self.max_pages:
                    break

                if not await self._apply_combo(page, {"gama": gama, "familia": familia}):
                    _logger.warning(
                        "Eldisser failed to apply GAMA/FAMILIA combo gama=%s familia=%s",
                        gama.get("text"),
                        familia.get("text"),
                    )
                    continue

                subfamilia_options = await self._wait_for_select_options(page, ("SUBFAMILIA",))
                if not subfamilia_options:
                    _logger.warning(
                        "Eldisser combo gama=%s familia=%s exposed no SUBFAMILIA options after selection.",
                        gama.get("text"),
                        familia.get("text"),
                    )
                    await self._queue_combo_targets(page, targets, {"gama": gama, "familia": familia})
                    continue

                _logger.info(
                    "Eldisser combo gama=%s familia=%s exposed %s SUBFAMILIA options.",
                    gama.get("text"),
                    familia.get("text"),
                    len(subfamilia_options),
                )

                for subfamilia in subfamilia_options:
                    if self._check_time_budget("Time budget exceeded. Stopping category scan."):
                        break
                    if len(targets) >= self.max_pages:
                        break
                    await self._queue_combo_targets(
                        page,
                        targets,
                        {"gama": gama, "familia": familia, "subfamilia": subfamilia},
                    )

        return targets

    async def _queue_combo_targets(
        self,
        page: Page,
        targets: dict[str, dict[str, str]],
        combo: dict[str, dict[str, str]],
    ) -> None:
        if self._check_time_budget("Time budget exceeded. Skipping remaining combos."):
            return
        if not await self._apply_combo(page, combo):
            return

        self._filter_combinations += 1
        await self._click_action(page, ("BUSCAR",))
        self._listing_pages_visited += 1
        await self._expand_all_products(page)

        category = self._combo_category(combo)
        sub_category = self._combo_sub_category(combo)
        customer_code = await self._read_customer_code(page)
        combo_links = await self._collect_listing_product_links(page)

        for product_url in combo_links:
            self._register_product_target(
                targets,
                product_url,
                {
                    "category": category,
                    "sub_category": sub_category,
                    "customer_code": customer_code,
                },
            )
            if len(targets) >= self.max_pages:
                break

        combo_debug_entry = {
            "category": category,
            "sub_category": sub_category,
            "catalog_url": page.url,
            "customer_code": customer_code,
            "links_found": len(combo_links),
            "sample_links": combo_links[:5],
        }
        self._combo_debug.append(combo_debug_entry)
        _logger.info(
            "Eldisser combo fetched category=%s sub_category=%s customer_code=%s links_found=%s queued_links=%s sample_links=%s",
            category,
            sub_category,
            customer_code,
            len(combo_links),
            len(targets),
            combo_links[:3],
        )
        self._emit_progress(
            note="Scanning category listings.",
            current_category=category,
            current_sub_category=sub_category,
            queued_product_links=len(targets),
        )
        self._drain_stream_futures(block=False)

    async def _read_customer_code(self, page: Page) -> str:
        customer_code = await page.evaluate(
            """() => {
                const normalizeDigits = (value) => (value || "").toString().replace(/\\D+/g, "");
                const candidates = [
                    document.querySelector("input[name='customerno']")?.value || "",
                    document.querySelector("input[id='customerno']")?.value || "",
                    document.querySelector("input[name='codClienteDetalle']")?.value || "",
                    document.querySelector("input[id='codClienteDetalle']")?.value || "",
                    document.querySelector("[data-customerno]")?.getAttribute("data-customerno") || "",
                    window.customerno || "",
                ];
                for (const candidate of candidates) {
                    const digits = normalizeDigits(candidate);
                    if (digits) return digits;
                }
                return "";
            }"""
        )
        resolved = self._clean_text(str(customer_code or "")) or self._customer_code
        if resolved and resolved != self._customer_code:
            self._customer_code = resolved
        if not resolved:
            _logger.warning("Eldisser customer code could not be resolved from the listing page url=%s", page.url)
        return resolved

    async def _goto_with_retry(
        self,
        page: Page,
        url: str,
        *,
        wait_until: str = "domcontentloaded",
        timeout_ms: int | None = None,
        retries: int | None = None,
        label: str = "",
    ) -> bool:
        resolved_timeout = int(timeout_ms or (self._pg_login_timeout_seconds * 1000))
        resolved_retries = max(0, int(self._pg_login_retry_count if retries is None else retries))
        for attempt in range(resolved_retries + 1):
            try:
                await page.goto(url, wait_until=wait_until, timeout=resolved_timeout)
                await self._fetcher.prepare_page(page)
                return True
            except Exception as exc:
                _logger.warning(
                    "Eldisser page.goto failed label=%s attempt=%s/%s url=%s error=%s",
                    label or "unknown",
                    attempt + 1,
                    resolved_retries + 1,
                    url,
                    exc,
                )
                await page.wait_for_timeout(1000)
        return False

    async def _open_catalog(self, page: Page) -> None:
        catalog_url = self._catalog_url()
        if not await self._goto_with_retry(page, catalog_url, label="catalog"):
            raise RuntimeError("Eldisser catalog page could not be opened.")
        await self._ensure_logged_in(page, catalog_url)
        await self._fetcher.prepare_page(page)
        if self.force_tienda_view:
            await self._ensure_tienda_view(page)
            await self._fetcher.prepare_page(page)

    async def _apply_combo(self, page: Page, combo: dict[str, dict[str, str]]) -> bool:
        await self._open_catalog(page)
        if gama := combo.get("gama"):
            previous_familia_options = await self._read_select_options(page, ("FAMILIA",))
            if not await self._set_select_option(page, ("GAMA",), gama["value"]):
                return False
            await self._after_filter_change(
                page,
                dependent_labels=("FAMILIA",),
                previous_options=previous_familia_options,
            )
        if familia := combo.get("familia"):
            previous_subfamilia_options = await self._read_select_options(page, ("SUBFAMILIA",))
            if not await self._set_select_option(page, ("FAMILIA",), familia["value"]):
                return False
            await self._after_filter_change(
                page,
                dependent_labels=("SUBFAMILIA",),
                previous_options=previous_subfamilia_options,
            )
        if subfamilia := combo.get("subfamilia"):
            if not await self._set_select_option(page, ("SUBFAMILIA",), subfamilia["value"]):
                return False
            await self._after_filter_change(page)
        return True

    async def _after_filter_change(
        self,
        page: Page,
        dependent_labels: tuple[str, ...] | None = None,
        previous_options: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        await page.wait_for_timeout(500 if self._pg_fast_listing else 900)
        await self._fetcher.prepare_page(page)
        if dependent_labels:
            return await self._wait_for_select_options(page, dependent_labels, previous_options=previous_options)
        return []

    async def _wait_for_select_options(
        self,
        page: Page,
        labels: tuple[str, ...],
        *,
        rounds: int = 10,
        previous_options: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        latest: list[dict[str, str]] = []
        previous_signature = self._option_signature(previous_options or [])
        for _round in range(rounds):
            latest = await self._read_select_options(page, labels)
            if latest:
                if not previous_signature or self._option_signature(latest) != previous_signature:
                    return latest
            await page.wait_for_timeout(350 if self._pg_fast_listing else 500)
            await self._fetcher.prepare_page(page)
        return latest

    def _option_signature(self, options: list[dict[str, str]]) -> tuple[tuple[str, str], ...]:
        return tuple(
            (
                self._normalize_label_text(str(option.get("value") or "")),
                self._normalize_label_text(str(option.get("text") or "")),
            )
            for option in options
        )

    async def _ensure_logged_in(self, page: Page, url: str) -> None:
        if not await self._needs_login(page):
            return
        if not (self.login_username and self.login_password):
            raise RuntimeError("Eldisser B2B login required but login_username/login_password were not provided.")
        if self.login_url and page.url != self.login_url:
            if not await self._goto_with_retry(page, self.login_url, label="login"):
                raise RuntimeError("Eldisser login page could not be opened.")
        form = page.locator("form").filter(has=page.locator("input[type='password']")).first
        username_candidates = (
            "input[type='email']",
            "input[name*='user' i]",
            "input[id*='user' i]",
            "input[name*='login' i]",
            "input[id*='login' i]",
            "input[placeholder*='usuario' i]",
            "input[placeholder*='email' i]",
            "input[type='text']",
        )
        password_locator = page.locator("input[type='password']").first
        username_locator = None
        for selector in username_candidates:
            candidate = form.locator(selector).first if await form.count() else page.locator(selector).first
            if await candidate.count():
                username_locator = candidate
                break
        if not username_locator or not await password_locator.count():
            raise RuntimeError("Eldisser B2B login form fields were not found.")
        await username_locator.fill(self.login_username)
        await password_locator.fill(self.login_password)
        if not await self._click_action(page, ("ENTRAR", "ACCEDER", "INICIAR", "LOGIN")):
            await password_locator.press("Enter")
        await page.wait_for_timeout(1200)
        await self._fetcher.prepare_page(page)
        if await self._needs_login(page):
            raise RuntimeError("Eldisser B2B login failed or session was not established.")
        if page.url != url:
            if not await self._goto_with_retry(page, url, label="return"):
                raise RuntimeError("Eldisser catalog page could not be re-opened after login.")

    async def _needs_login(self, page: Page) -> bool:
        if "login" in page.url.lower() or "acesso" in page.url.lower():
            return True
        password_fields = page.locator("input[type='password']")
        if await password_fields.count():
            return True
        body_text = self._normalize_label_text(await page.text_content("body") or "")
        login_markers = ("INICIAR SESION", "INICIAR SESS", "ACCEDER", "LOGIN")
        return any(marker in body_text for marker in login_markers) and "B2B" in body_text

    async def _ensure_tienda_view(self, page: Page) -> None:
        body_text = self._normalize_label_text(await page.text_content("body") or "")
        if "VISTA" not in body_text:
            return
        require_detail_markers = any(
            marker in body_text
            for marker in (
                "CARACTERISTICAS PRINCIPALES",
                "ESPECIFICACIONES",
                "DISP:",
            )
        )
        if await self._is_tienda_view_ready(page, body_text=body_text, require_detail_markers=require_detail_markers):
            return
        for _attempt in range(3):
            if not await self._click_action(page, ("TIENDA",), include_generic=True):
                break
            body_text = self._normalize_label_text(await page.text_content("body") or "")
            if await self._is_tienda_view_ready(
                page,
                body_text=body_text,
                require_detail_markers=require_detail_markers,
            ):
                return
        _logger.warning(
            "Eldisser could not confirm TIENDA view on url=%s require_detail_markers=%s",
            page.url,
            require_detail_markers,
        )

    async def _is_tienda_view_ready(
        self,
        page: Page,
        *,
        body_text: str | None = None,
        require_detail_markers: bool = False,
    ) -> bool:
        normalized = body_text or self._normalize_label_text(await page.text_content("body") or "")
        if "VISTA" not in normalized:
            return True
        if "PRECIO" not in normalized or "PVD" not in normalized:
            return False
        if require_detail_markers:
            return any(marker in normalized for marker in ("DISP:", "CARACTERISTICAS PRINCIPALES", "ESPECIFICACIONES"))
        return True

    async def _click_action(self, page: Page, labels: tuple[str, ...], *, include_generic: bool = False) -> bool:
        clicked = await page.evaluate(
            """([labels, includeGeneric]) => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .replace(/\\s+/g, " ")
                    .trim()
                    .toUpperCase();
                const normalizedLabels = labels.map(normalize);
                const isVisible = (element) => {
                    if (!element) return false;
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
                };
                const selectors = includeGeneric
                    ? "button, a, input[type='submit'], input[type='button'], label, span, div"
                    : "button, a, input[type='submit'], input[type='button']";
                for (const element of document.querySelectorAll(selectors)) {
                    if (!isVisible(element)) continue;
                    const text = normalize(element.value || element.innerText || element.textContent);
                    if (!text) continue;
                    if (!normalizedLabels.some((label) => text.includes(label))) continue;
                    element.click();
                    return true;
                }
                return false;
            }""",
            [list(labels), include_generic],
        )
        if clicked:
            await page.wait_for_timeout(400 if self._pg_fast_listing else 900)
            await self._fetcher.prepare_page(page)
        return bool(clicked)

    async def _click_load_more(self, page: Page) -> dict[str, Any]:
        click_scan_started_at = time.perf_counter()
        result = await page.evaluate(
            """() => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .replace(/\\s+/g, " ")
                    .trim()
                    .toUpperCase();
                const isVisible = (element) => {
                    if (!element) return false;
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
                };
                const actionableSelector = "button, a, [role='button'], input[type='submit'], input[type='button'], label, span, div";
                const fastSelector = "a.linkSiguiente.btnPequeno, button.linkSiguiente.btnPequeno";
                const viewportHeight = window.innerHeight || document.documentElement?.clientHeight || 0;
                const candidates = [];
                const pushCandidate = (element, rectOverride = null) => {
                    if (!isVisible(element)) return;
                    const text = normalize(element.value || element.innerText || element.textContent);
                    if (!text || (!text.includes("VER MAS") && !text.includes("VER MAS PRODUCTOS"))) return;
                    const rect = rectOverride || element.getBoundingClientRect();
                    if (rect.bottom < -200 || rect.top > (viewportHeight + 400)) return;
                    candidates.push({
                        element,
                        text,
                        top: rect.top,
                        left: rect.left,
                        tag: (element.tagName || "").toLowerCase(),
                        classes: (element.className || "").toString().slice(0, 160),
                    });
                };
                const fastNode = document.querySelector(fastSelector);
                if (fastNode) {
                    pushCandidate(fastNode);
                }
                if (!candidates.length) {
                    const nodes = document.querySelectorAll(actionableSelector);
                    for (let index = 0; index < nodes.length; index += 1) {
                        if (index >= 5000) break;
                        const element = nodes[index];
                        if (!isVisible(element)) continue;
                        const rect = element.getBoundingClientRect();
                        if (rect.bottom < -200 || rect.top > (viewportHeight + 400)) continue;
                        pushCandidate(element, rect);
                        if (candidates.length >= 12) break;
                    }
                }
                candidates.sort((left, right) => {
                    if (right.top !== left.top) return right.top - left.top;
                    return left.left - right.left;
                });
                const dispatchClick = (element) => {
                    const clickable = element.closest("button, a, [role='button'], input[type='submit'], input[type='button']") || element;
                    clickable.scrollIntoView({ block: "center", inline: "nearest" });
                    for (const type of ["pointerdown", "mousedown", "mouseup", "click"]) {
                        clickable.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
                    }
                    if (typeof clickable.click === "function") {
                        clickable.click();
                    }
                    return clickable;
                };
                const candidate = candidates[0];
                if (!candidate) {
                    return { clicked: false, candidate_count: 0, fast_mode: Boolean(fastNode) };
                }
                const clicked = dispatchClick(candidate.element);
                return {
                    clicked: true,
                    candidate_count: candidates.length,
                    text: candidate.text,
                    tag: (clicked.tagName || candidate.tag || "").toLowerCase(),
                    classes: (clicked.className || candidate.classes || "").toString().slice(0, 160),
                    fast_mode: Boolean(fastNode),
                    candidate_samples: candidates.slice(0, 8).map((item) => ({
                        text: item.text,
                        tag: item.tag,
                        classes: item.classes,
                        top: item.top,
                        left: item.left,
                    })),
                };
            }"""
        )
        click_scan_elapsed = time.perf_counter() - click_scan_started_at
        if click_scan_elapsed >= 2.0 or int(result.get("candidate_count") or 0) >= 10:
            _logger.info(
                "Eldisser VER MAS scan elapsed=%.2fs candidate_count=%s clicked=%s fast_mode=%s tag=%s classes=%s url=%s",
                click_scan_elapsed,
                int(result.get("candidate_count") or 0),
                bool(result.get("clicked")),
                bool(result.get("fast_mode")),
                result.get("tag") or "",
                result.get("classes") or "",
                page.url,
            )
        if result.get("clicked"):
            await page.wait_for_timeout(400 if self._pg_fast_listing else 900)
        return result

    async def _expand_all_products(self, page: Page) -> None:
        initial_state = await self._read_listing_state(page)
        known_item_ids = set(str(value) for value in (initial_state.get("ids") or []) if str(value))
        previous_card_count = len(known_item_ids)
        no_growth_clicks = 0

        for _index in range(120):
            if self._check_time_budget("Time budget exceeded. Stopping listing expansion."):
                break
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(250 if self._pg_fast_listing else 400)
            current_state = await self._read_listing_state(page)
            for item_id in current_state.get("ids") or []:
                if item_id:
                    known_item_ids.add(str(item_id))
            current_card_count = len(known_item_ids)
            _logger.info(
                "Eldisser expand iteration=%s current_card_count=%s previous_card_count=%s visible_id_count=%s visible_card_count=%s load_more_candidate_count=%s url=%s",
                _index + 1,
                current_card_count,
                previous_card_count,
                int(current_state.get("visibleIdCount") or 0),
                int(current_state.get("visibleCardCount") or 0),
                int(current_state.get("loadMoreCandidateCount") or 0),
                page.url,
            )
            load_more_result = await self._click_load_more(page)
            if not load_more_result.get("clicked"):
                _logger.info(
                    "Eldisser expand finished because VER MAS was no longer clickable current_card_count=%s previous_card_count=%s",
                    current_card_count,
                    previous_card_count,
                )
                break

            self._emit_progress(
                note="Clicked Eldisser VER MAS.",
                force=True,
                current_listing_count=current_card_count,
                current_listing_round=_index + 1,
            )
            new_card_count = await self._wait_for_listing_card_growth(page, current_card_count, known_item_ids)
            if new_card_count <= current_card_count:
                no_growth_clicks += 1
                _logger.info(
                    "Eldisser VER MAS click produced no new cards current_card_count=%s new_card_count=%s no_growth_clicks=%s clicked_tag=%s clicked_text=%s candidate_count=%s clicked_classes=%s",
                    current_card_count,
                    new_card_count,
                    no_growth_clicks,
                    load_more_result.get("tag") or "",
                    load_more_result.get("text") or "",
                    load_more_result.get("candidate_count") or 0,
                    load_more_result.get("classes") or "",
                )
            else:
                no_growth_clicks = 0
                _logger.info(
                    "Eldisser VER MAS click increased cards current_card_count=%s new_card_count=%s clicked_tag=%s clicked_text=%s candidate_count=%s clicked_classes=%s",
                    current_card_count,
                    new_card_count,
                    load_more_result.get("tag") or "",
                    load_more_result.get("text") or "",
                    load_more_result.get("candidate_count") or 0,
                    load_more_result.get("classes") or "",
                )
            if int(load_more_result.get("candidate_count") or 0) >= 10:
                _logger.info(
                    "Eldisser VER MAS candidate diagnostics iteration=%s samples=%s url=%s",
                    _index + 1,
                    load_more_result.get("candidate_samples") or [],
                    page.url,
                )
            previous_card_count = new_card_count
            if no_growth_clicks >= 6:
                _logger.info(
                    "Eldisser expand stopped after repeated no-growth VER MAS clicks final_card_count=%s",
                    new_card_count,
                )
                break

    async def _read_listing_probe(self, page: Page) -> dict[str, Any]:
        probe = await page.evaluate(
            """() => {
                const normalize = (value) => (value || "")
                    .replace(/\\s+/g, " ")
                    .trim();
                const upper = (value) => normalize(value).toUpperCase();
                const isVisible = (element) => {
                    if (!element) return false;
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
                };
                const viewportHeight = window.innerHeight || document.documentElement?.clientHeight || 0;
                const scrollHeight = document.documentElement?.scrollHeight || document.body?.scrollHeight || 0;
                const cardSelector = ".bloque-producto-tienda, .contenido-producto";
                let allCards = [];
                let skippedCardScan = false;
                if (scrollHeight <= 200000) {
                    allCards = Array.from(document.querySelectorAll(cardSelector));
                } else {
                    skippedCardScan = true;
                }
                let skippedVisibilityCheck = false;
                let visibleCards = [];
                if (!skippedCardScan && allCards.length <= 4000) {
                    visibleCards = allCards.filter((element) => isVisible(element));
                } else {
                    skippedVisibilityCheck = true;
                }
                const loadMoreCandidates = [];
                const fastSelector = "a.linkSiguiente.btnPequeno, button.linkSiguiente.btnPequeno";
                for (const element of document.querySelectorAll(fastSelector)) {
                    if (!isVisible(element)) continue;
                    const rect = element.getBoundingClientRect();
                    if (rect.bottom < -200 || rect.top > (viewportHeight + 400)) continue;
                    loadMoreCandidates.push({
                        text: upper(element.value || element.innerText || element.textContent),
                        className: normalize(element.className || "").slice(0, 120),
                        top: rect.top,
                        left: rect.left,
                    });
                    if (loadMoreCandidates.length >= 12) break;
                }
                if (!loadMoreCandidates.length) {
                    for (const element of document.querySelectorAll("button, a, [role='button'], input[type='submit'], input[type='button'], label, span, div")) {
                        if (!isVisible(element)) continue;
                        const rect = element.getBoundingClientRect();
                        if (rect.bottom < -200 || rect.top > (viewportHeight + 400)) continue;
                        const text = upper(element.value || element.innerText || element.textContent);
                        if (!text || (!text.includes("VER MAS") && !text.includes("VER MAS PRODUCTOS"))) continue;
                        loadMoreCandidates.push({
                            text,
                            className: normalize(element.className || "").slice(0, 120),
                            top: rect.top,
                            left: rect.left,
                        });
                        if (loadMoreCandidates.length >= 12) break;
                    }
                }
                const bodyRect = (document.body || document.documentElement || { getBoundingClientRect: () => ({ top: 0, bottom: 0 }) }).getBoundingClientRect();
                return {
                    rawSelectorCount: skippedCardScan ? -1 : allCards.length,
                    visibleSelectorCount: skippedVisibilityCheck ? (skippedCardScan ? -1 : allCards.length) : visibleCards.length,
                    visibleCardCount: skippedVisibilityCheck ? (skippedCardScan ? -1 : allCards.length) : visibleCards.length,
                    skippedCardScan,
                    skippedVisibilityCheck,
                    loadMoreCandidateCount: loadMoreCandidates.length,
                    loadMoreCandidates,
                    scrollHeight,
                    viewportHeight,
                    readyState: document.readyState || "",
                    title: document.title || "",
                    url: window.location.href,
                    bodyTop: bodyRect.top || 0,
                    bodyBottom: bodyRect.bottom || 0,
                };
            }"""
        )
        return dict(probe or {})

    async def _read_listing_ids(self, page: Page) -> dict[str, Any]:
        state = await page.evaluate(
            """() => {
                const normalize = (value) => (value || "")
                    .replace(/\\s+/g, " ")
                    .trim();
                const isVisible = (element) => {
                    if (!element) return false;
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
                };
                const cardSelector = ".bloque-producto-tienda, .contenido-producto";
                const actionSelector = "[onclick*='DetalleItem'], a[href*='id='], [data-href*='id='], [data-url*='id='], [data-link*='id=']";
                const viewportHeight = window.innerHeight || document.documentElement?.clientHeight || 0;
                const visibleActionNodes = Array.from(document.querySelectorAll(actionSelector)).filter((element) => {
                    if (!element) return false;
                    const ownerCard = element.closest(cardSelector);
                    const probe = ownerCard || element;
                    if (!isVisible(probe)) return false;
                    const rect = probe.getBoundingClientRect();
                    return rect.bottom >= -200 && rect.top <= (viewportHeight + 400);
                });
                const idCounts = new Map();
                const sampleIds = [];
                for (const element of visibleActionNodes) {
                    const candidates = [
                        element.getAttribute?.("onclick") || "",
                        element.getAttribute?.("href") || "",
                        element.getAttribute?.("data-href") || "",
                        element.getAttribute?.("data-url") || "",
                        element.getAttribute?.("data-link") || "",
                    ];
                    let matchedId = "";
                    for (const candidate of candidates) {
                        if (!candidate) continue;
                        const match = candidate.match(/DetalleItem\\(\\s*['"]?(\\d{4,10})['"]?\\s*\\)|[?&]id=(\\d{4,10})/i);
                        const value = match ? (match[1] || match[2] || "") : "";
                        if (value) {
                            matchedId = value;
                            break;
                        }
                    }
                    if (!matchedId) continue;
                    idCounts.set(matchedId, (idCounts.get(matchedId) || 0) + 1);
                }
                const sampleIdFrequencies = Array.from(idCounts.entries())
                    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
                    .slice(0, 5)
                    .map(([itemId, frequency]) => ({ itemId, frequency }));
                for (const [itemId] of idCounts.entries()) {
                    if (sampleIds.length >= 5) break;
                    sampleIds.push(itemId);
                }

                return {
                    count: idCounts.size,
                    ids: Array.from(idCounts.keys()),
                    topLevelCount: 0,
                    actionNodeCount: visibleActionNodes.length,
                    visibleIdCount: idCounts.size,
                    idSignatureCount: idCounts.size,
                    duplicateActionCount: Math.max(visibleActionNodes.length - idCounts.size, 0),
                    maxIdFrequency: sampleIdFrequencies.length ? sampleIdFrequencies[0].frequency : 0,
                    sampleTitles: Array.from(document.querySelectorAll(".titulo-producto, .title-product, .item-title, h2, h3, strong"))
                        .map((element) => normalize(element.textContent || ""))
                        .filter((text) => text.length >= 8)
                        .slice(0, 5),
                    sampleSignatures: sampleIds.map((value) => `id:${value}`),
                    topLevelSummaries: [],
                    sampleIdFrequencies,
                };
            }"""
        )
        return dict(state or {})

    async def _read_listing_state(self, page: Page) -> dict[str, Any]:
        probe: dict[str, Any] = {}
        probe_elapsed = 0.0
        if not self._pg_fast_listing:
            probe_started_at = time.perf_counter()
            probe = await self._read_listing_probe(page)
            probe_elapsed = time.perf_counter() - probe_started_at
            if probe_elapsed >= 2.0:
                _logger.info(
                    "Eldisser listing probe was slow elapsed=%.2fs raw_selector_count=%s visible_selector_count=%s visible_card_count=%s skipped_card_scan=%s skipped_visibility_check=%s load_more_candidate_count=%s viewport_height=%s scroll_height=%s ready_state=%s body_top=%s body_bottom=%s url=%s",
                    probe_elapsed,
                    int(probe.get("rawSelectorCount") or 0),
                    int(probe.get("visibleSelectorCount") or 0),
                    int(probe.get("visibleCardCount") or 0),
                    bool(probe.get("skippedCardScan")),
                    bool(probe.get("skippedVisibilityCheck")),
                    int(probe.get("loadMoreCandidateCount") or 0),
                    int(probe.get("viewportHeight") or 0),
                    int(probe.get("scrollHeight") or 0),
                    probe.get("readyState") or "",
                    probe.get("bodyTop") or 0,
                    probe.get("bodyBottom") or 0,
                    page.url,
                )

        ids_started_at = time.perf_counter()
        ids_state = await self._read_listing_ids(page)
        ids_elapsed = time.perf_counter() - ids_started_at
        if (
            ids_elapsed >= 2.0
            or int(ids_state.get("duplicateActionCount") or 0) >= max(int(ids_state.get("idSignatureCount") or 0), 1) * 2
        ):
            _logger.info(
                "Eldisser listing id extraction elapsed=%.2fs action_node_count=%s visible_id_count=%s duplicate_action_count=%s max_id_frequency=%s sample_id_frequencies=%s url=%s",
                ids_elapsed,
                int(ids_state.get("actionNodeCount") or 0),
                int(ids_state.get("visibleIdCount") or 0),
                int(ids_state.get("duplicateActionCount") or 0),
                int(ids_state.get("maxIdFrequency") or 0),
                ids_state.get("sampleIdFrequencies") or [],
                page.url,
            )

        merged_state = {
            **probe,
            **ids_state,
            "probeElapsedMs": round(probe_elapsed * 1000, 1),
            "idExtractionElapsedMs": round(ids_elapsed * 1000, 1),
            "stateElapsedMs": round((probe_elapsed + ids_elapsed) * 1000, 1),
        }
        return merged_state

    async def _count_listing_cards(self, page: Page) -> int:
        state = await self._read_listing_state(page)
        return int(state.get("count") or 0)

    async def _wait_for_listing_card_growth(
        self,
        page: Page,
        baseline_count: int,
        known_item_ids: set[str],
        *,
        rounds: int = 12,
        stable_rounds: int = 3,
    ) -> int:
        latest_count = baseline_count
        best_count = baseline_count
        settled_rounds = 0

        for _round in range(rounds):
            self._emit_progress(
                note="Expanding Eldisser listing.",
                force=True,
                current_listing_count=best_count,
                current_listing_round=_round + 1,
            )
            _logger.info(
                "Eldisser listing growth round start round=%s baseline_count=%s best_count=%s known_item_ids=%s url=%s",
                _round + 1,
                baseline_count,
                best_count,
                len(known_item_ids),
                page.url,
            )
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(300 if self._pg_fast_listing else 500)
            count_started_at = time.perf_counter()
            state = await self._read_listing_state(page)
            round_ids = {str(value) for value in (state.get("ids") or []) if str(value)}
            previous_known_count = len(known_item_ids)
            known_item_ids.update(round_ids)
            latest_count = len(known_item_ids)
            round_new_ids = latest_count - previous_known_count
            count_elapsed = time.perf_counter() - count_started_at
            _logger.info(
                "Eldisser listing growth round=%s baseline_count=%s latest_count=%s round_new_ids=%s best_count=%s raw_selector_count=%s visible_selector_count=%s visible_card_count=%s action_node_count=%s id_signature_count=%s duplicate_action_count=%s max_id_frequency=%s load_more_candidate_count=%s viewport_height=%s scroll_height=%s probe_elapsed_ms=%s id_extraction_elapsed_ms=%s state_elapsed_ms=%s elapsed=%.2fs url=%s",
                _round + 1,
                baseline_count,
                latest_count,
                round_new_ids,
                best_count,
                int(state.get("rawSelectorCount") or 0),
                int(state.get("visibleSelectorCount") or 0),
                int(state.get("visibleCardCount") or 0),
                int(state.get("actionNodeCount") or 0),
                int(state.get("idSignatureCount") or 0),
                int(state.get("duplicateActionCount") or 0),
                int(state.get("maxIdFrequency") or 0),
                int(state.get("loadMoreCandidateCount") or 0),
                int(state.get("viewportHeight") or 0),
                int(state.get("scrollHeight") or 0),
                state.get("probeElapsedMs") or 0,
                state.get("idExtractionElapsedMs") or 0,
                state.get("stateElapsedMs") or 0,
                count_elapsed,
                page.url,
            )
            if (
                count_elapsed >= 3.0
                or int(state.get("duplicateActionCount") or 0) >= max(int(state.get("visibleIdCount") or 0), 1) * 2
                or int(state.get("loadMoreCandidateCount") or 0) >= 10
            ):
                _logger.info(
                    "Eldisser listing growth diagnostics round=%s baseline_count=%s latest_count=%s round_new_ids=%s sample_titles=%s sample_signatures=%s sample_id_frequencies=%s load_more_candidates=%s ready_state=%s page_title=%s url=%s",
                    _round + 1,
                    baseline_count,
                    latest_count,
                    round_new_ids,
                    state.get("sampleTitles") or [],
                    state.get("sampleSignatures") or [],
                    state.get("sampleIdFrequencies") or [],
                    state.get("loadMoreCandidates") or [],
                    state.get("readyState") or "",
                    state.get("title") or "",
                    page.url,
                )
            if round_new_ids > 0:
                best_count = latest_count
                settled_rounds = 0
                self._emit_progress(
                    note="Expanded Eldisser listing.",
                    force=True,
                    current_listing_count=best_count,
                    current_listing_round=_round + 1,
                )
                continue
            if best_count > baseline_count and round_new_ids == 0:
                settled_rounds += 1
                if settled_rounds >= stable_rounds:
                    return best_count
        return max(latest_count, best_count)

    async def _collect_listing_product_links(self, page: Page) -> list[str]:
        _logger.info("Eldisser collecting listing product links after expansion url=%s", page.url)
        html_started_at = time.perf_counter()
        html = await page.content()
        html_elapsed = time.perf_counter() - html_started_at
        soup = BeautifulSoup(html, "html.parser")
        current_card_count = self._count_listing_cards_in_soup(soup, page.url)
        _logger.info(
            "Eldisser collected listing HTML current_card_count=%s elapsed=%.2fs html_length=%s url=%s",
            current_card_count,
            html_elapsed,
            len(html),
            page.url,
        )
        links = self._extract_listing_product_links(soup, page.url)
        if links:
            return links

        card_targets_started_at = time.perf_counter()
        try:
            card_targets = await asyncio.wait_for(
                page.evaluate(
                    """() => {
                const selector = ".bloque-producto-tienda, .contenido-producto";
                const cards = Array.from(document.querySelectorAll(selector))
                    .filter((card) => !(card.parentElement && card.parentElement.closest(selector)));
                const getText = (node) => (node?.innerText || node?.textContent || "").replace(/\\s+/g, " ").trim();
                const extractAction = (element) => {
                    if (!element) return { href: "", action: "" };
                    for (const attr of ["href", "data-href", "data-url", "data-link"]) {
                        const value = element.getAttribute?.(attr) || "";
                        if (value) return { href: value, action: "" };
                    }
                    const onclick = element.getAttribute?.("onclick") || "";
                    if (onclick) return { href: "", action: onclick };
                    return { href: "", action: "" };
                };
                const pushAction = (actions, href, action, text) => {
                    const key = `${href || ""}|||${action || ""}`;
                    if (!key.trim() || actions.some((candidate) => `${candidate.href || ""}|||${candidate.action || ""}` === key)) {
                        return;
                    }
                    actions.push({
                        href: href || "",
                        action: action || "",
                        text: text || "",
                    });
                };
                return cards.slice(0, 300).map((card) => {
                    const titleNode = card.querySelector(".titulo-producto, .title-product, .item-title, h2, h3, strong");
                    const actionNodes = [
                        card,
                        titleNode,
                        titleNode?.closest("a"),
                        ...(titleNode ? Array.from(titleNode.querySelectorAll("a, [onclick], [data-href], [data-url], [data-link]")) : []),
                        ...Array.from(card.querySelectorAll("a, button, [onclick], [data-href], [data-url], [data-link], .titulo-producto, .title-product, .item-title")).slice(0, 40),
                    ].filter(Boolean);
                    const actions = [];
                    for (const node of actionNodes) {
                        const extracted = extractAction(node);
                        pushAction(actions, extracted.href, extracted.action, getText(node));
                    }
                    for (const match of (card.outerHTML || "").matchAll(/DetalleItem\\(\\s*['"]?(\\d{4,10})['"]?\\s*\\)/gi)) {
                        const itemId = match[1] || "";
                        if (!itemId) continue;
                        pushAction(actions, "", `DetalleItem('${itemId}')`, getText(titleNode));
                    }
                    return {
                        title: getText(titleNode),
                        cardText: getText(card).slice(0, 800),
                        actions,
                    };
                });
            }"""
                ),
                timeout=20.0,
            )
        except asyncio.TimeoutError:
            _logger.warning(
                "Eldisser card target evaluation timed out current_card_count=%s url=%s",
                current_card_count,
                page.url,
            )
            return links
        card_targets_elapsed = time.perf_counter() - card_targets_started_at
        _logger.info(
            "Eldisser evaluated card targets current_card_count=%s card_targets=%s elapsed=%.2fs url=%s",
            current_card_count,
            len(card_targets),
            card_targets_elapsed,
            page.url,
        )
        fallback_links: list[str] = []
        seen = set()
        samples: list[dict[str, str]] = []
        for card in card_targets:
            card_text = str(card.get("cardText") or "")
            title = str(card.get("title") or "")
            for action in card.get("actions") or []:
                candidate = self._listing_target_from_action(
                    href=str(action.get("href") or ""),
                    raw_action=str(action.get("action") or ""),
                    current_url=page.url,
                )
                if not candidate:
                    continue
                if not self._should_visit(candidate):
                    continue
                if candidate in seen:
                    continue
                if not self._looks_like_product_card_text(f"{title} {card_text}"):
                    continue
                seen.add(candidate)
                fallback_links.append(candidate)
                samples.append(
                    {
                        "title": title[:120],
                        "candidate": candidate,
                        "action_text": str(action.get("text") or "")[:120],
                    }
                )
                break
        if fallback_links:
            _logger.info("Eldisser fallback card link extraction found %s links sample=%s", len(fallback_links), samples[:3])
            return fallback_links
        if card_targets:
            _logger.info(
                "Eldisser found %s product cards but no navigable detail links sample_cards=%s",
                len(card_targets),
                [
                    {
                        "title": str(card.get("title") or "")[:120],
                        "actions": [
                            {
                                "href": str(action.get("href") or "")[:120],
                                "action": str(action.get("action") or "")[:160],
                            }
                            for action in (card.get("actions") or [])[:3]
                        ],
                    }
                    for card in card_targets[:3]
                ],
            )
        return []

    def _count_listing_cards_in_soup(self, soup: BeautifulSoup, current_url: str) -> int:
        cards = self._top_level_listing_cards_in_soup(soup)
        signatures: set[str] = set()
        for card in cards:
            signature = self._listing_card_signature_from_soup(card, current_url)
            if signature:
                signatures.add(signature)
        return len(signatures) or len(cards)

    def _top_level_listing_cards_in_soup(self, soup: BeautifulSoup) -> list[Any]:
        cards: list[Any] = []
        for card in soup.select(".bloque-producto-tienda, .contenido-producto"):
            if any(self._is_listing_card_tag(parent) for parent in getattr(card, "parents", []) if getattr(parent, "attrs", None) is not None):
                continue
            cards.append(card)
        return cards

    def _is_listing_card_tag(self, node: Any) -> bool:
        classes = node.get("class") if getattr(node, "get", None) else None
        if not classes:
            return False
        class_set = {str(value).strip().lower() for value in classes if str(value).strip()}
        return "bloque-producto-tienda" in class_set or "contenido-producto" in class_set

    def _listing_card_signature_from_soup(self, card: Any, current_url: str) -> str:
        for element in card.select("[onclick], a[href], [data-href], [data-url], [data-link]"):
            candidate = self._listing_target_from_action(
                href=str(element.get("href") or element.get("data-href") or element.get("data-url") or element.get("data-link") or ""),
                raw_action=str(element.get("onclick") or ""),
                current_url=current_url,
            )
            if candidate:
                return f"url:{candidate}"
        title_node = card.select_one(".titulo-producto, .title-product, .item-title, h2, h3, strong")
        title = self._normalize_label_text(self._clean_text(self._first_text(title_node)))
        if title:
            return f"title:{title[:180]}"
        text = self._normalize_label_text(self._clean_text(card.get_text(" ", strip=True)))
        if text:
            return f"text:{text[:180]}"
        return ""

    async def _read_select_options(self, page: Page, labels: tuple[str, ...]) -> list[dict[str, str]]:
        selector_hints = self._select_hints_for_labels(labels)
        options = await page.evaluate(
            """([labels, selectorHints]) => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .replace(/\\s+/g, " ")
                    .trim()
                    .toUpperCase();
                const normalizedLabels = labels.map(normalize);
                const findSelectByHints = () => {
                    for (const selector of selectorHints || []) {
                        const candidate = document.querySelector(selector);
                        if (candidate && candidate.tagName === "SELECT") {
                            return candidate;
                        }
                    }
                    return null;
                };
                const scoreSelect = (select) => {
                    let score = 0;
                    let node = select;
                    for (let depth = 0; depth < 3 && node; depth += 1, node = node.parentElement) {
                        const text = normalize(node.innerText || "");
                        for (const label of normalizedLabels) {
                            if (text.includes(label)) {
                                score = Math.max(score, label.length + (3 - depth));
                            }
                        }
                    }
                    for (const value of [select.name, select.id, select.getAttribute("aria-label"), select.getAttribute("data-label")]) {
                        const text = normalize(value || "");
                        for (const label of normalizedLabels) {
                            if (text.includes(label)) {
                                score = Math.max(score, label.length + 4);
                            }
                        }
                    }
                    return score;
                };
                let bestSelect = findSelectByHints();
                let bestScore = 0;
                if (!bestSelect) {
                    for (const select of document.querySelectorAll("select")) {
                        const score = scoreSelect(select);
                        if (score > bestScore) {
                            bestSelect = select;
                            bestScore = score;
                        }
                    }
                }
                if (!bestSelect || (!selectorHints?.length && bestScore <= 0)) {
                    return [];
                }
                if (bestSelect.selectize) {
                    const selectize = bestSelect.selectize;
                    return Object.values(selectize.options || {}).map((option) => ({
                        value: option.value || "",
                        text: option.text || option.label || option.value || "",
                        disabled: Boolean(option.disabled),
                    }));
                }
                return Array.from(bestSelect.options).map((option) => ({
                    value: option.value || "",
                    text: option.textContent || "",
                    disabled: Boolean(option.disabled),
                }));
            }""",
            [list(labels), selector_hints],
        )
        cleaned: list[dict[str, str]] = []
        seen = set()
        for option in options:
            text = self._clean_text(str(option.get("text") or ""))
            value = self._clean_text(str(option.get("value") or ""))
            normalized = self._normalize_label_text(text)
            normalized_value = self._normalize_label_text(value)
            if option.get("disabled"):
                continue
            if not text or normalized in {"SELECCIONAR", "TODOS", "TODAS", "BORRAR FILTRO", "BORRAR FILTROS"}:
                continue
            if normalized_value == "___BLANK___":
                continue
            if not value and "SELECCIONAR" in normalized:
                continue
            key = (value, normalized)
            if key in seen:
                continue
            seen.add(key)
            cleaned.append({"value": value or text, "text": text})
        return cleaned

    async def _set_select_option(self, page: Page, labels: tuple[str, ...], selected_value: str) -> bool:
        selector_hints = self._select_hints_for_labels(labels)
        selected = await page.evaluate(
            """([labels, selectedValue, selectorHints]) => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .replace(/\\s+/g, " ")
                    .trim()
                    .toUpperCase();
                const normalizedLabels = labels.map(normalize);
                const normalizedSelected = normalize(selectedValue);
                const callSupplierHooks = () => {
                    if (normalizedLabels.includes("FAMILIA") && typeof window.familiaGama === "function") {
                        window.familiaGama();
                    }
                    if (normalizedLabels.includes("SUBFAMILIA")) {
                        const gama = document.getElementById("_x003C_Cod_gama_x003E__Text_eq_Filter")?.value || "";
                        const familia = document.getElementById("Product_Group_Code_Text_eq_Filter")?.value || "";
                        if (typeof window.MarcaGamaFamiliaSubfamilia === "function") {
                            window.MarcaGamaFamiliaSubfamilia(gama, familia);
                        }
                    }
                };
                const findSelectByHints = () => {
                    for (const selector of selectorHints || []) {
                        const candidate = document.querySelector(selector);
                        if (candidate && candidate.tagName === "SELECT") {
                            return candidate;
                        }
                    }
                    return null;
                };
                const scoreSelect = (select) => {
                    let score = 0;
                    let node = select;
                    for (let depth = 0; depth < 3 && node; depth += 1, node = node.parentElement) {
                        const text = normalize(node.innerText || "");
                        for (const label of normalizedLabels) {
                            if (text.includes(label)) {
                                score = Math.max(score, label.length + (3 - depth));
                            }
                        }
                    }
                    for (const value of [select.name, select.id, select.getAttribute("aria-label"), select.getAttribute("data-label")]) {
                        const text = normalize(value || "");
                        for (const label of normalizedLabels) {
                            if (text.includes(label)) {
                                score = Math.max(score, label.length + 4);
                            }
                        }
                    }
                    return score;
                };
                let bestSelect = findSelectByHints();
                let bestScore = 0;
                if (!bestSelect) {
                    for (const select of document.querySelectorAll("select")) {
                        const score = scoreSelect(select);
                        if (score > bestScore) {
                            bestSelect = select;
                            bestScore = score;
                        }
                    }
                }
                if (!bestSelect || (!selectorHints?.length && bestScore <= 0)) {
                    return false;
                }
                if (bestSelect.selectize) {
                    const selectize = bestSelect.selectize;
                    const option = Object.values(selectize.options || {}).find((candidate) => {
                        return normalize(candidate.value || "") === normalizedSelected
                            || normalize(candidate.text || candidate.label || "") === normalizedSelected;
                    });
                    if (!option) {
                        return false;
                    }
                    selectize.setValue(option.value, false);
                    selectize.refreshOptions(false);
                    if (window.jQuery) {
                        window.jQuery(bestSelect).trigger("input");
                        window.jQuery(bestSelect).trigger("change");
                    }
                    if (typeof bestSelect.onchange === "function") {
                        bestSelect.onchange();
                    }
                    callSupplierHooks();
                    bestSelect.dispatchEvent(new Event("input", { bubbles: true }));
                    bestSelect.dispatchEvent(new Event("change", { bubbles: true }));
                    return true;
                }
                const option = Array.from(bestSelect.options).find((candidate) => {
                    return normalize(candidate.value || "") === normalizedSelected
                        || normalize(candidate.textContent || "") === normalizedSelected;
                });
                if (!option) {
                    return false;
                }
                bestSelect.value = option.value;
                option.selected = true;
                if (window.jQuery) {
                    window.jQuery(bestSelect).trigger("input");
                    window.jQuery(bestSelect).trigger("change");
                }
                if (typeof bestSelect.onchange === "function") {
                    bestSelect.onchange();
                }
                callSupplierHooks();
                bestSelect.dispatchEvent(new Event("input", { bubbles: true }));
                bestSelect.dispatchEvent(new Event("change", { bubbles: true }));
                return true;
            }""",
            [list(labels), selected_value, selector_hints],
        )
        return bool(selected)

    def _select_hints_for_labels(self, labels: tuple[str, ...]) -> list[str]:
        normalized = {self._normalize_label_text(label) for label in labels}
        if "GAMA" in normalized:
            return [
                "select#_x003C_Cod_gama_x003E__Text_eq_Filter",
                "select[name='_x003C_Cod_gama_x003E__Text_eq_Filter']",
                "select[data-search-name_gama]",
            ]
        if "FAMILIA" in normalized:
            return [
                "select#Product_Group_Code_Text_eq_Filter",
                "select[name='Product_Group_Code_Text_eq_Filter']",
            ]
        if "SUBFAMILIA" in normalized:
            return [
                "select#Subfamilia_Text_eq_Filter",
                "select[name='Subfamilia_Text_eq_Filter']",
            ]
        return []

    def _listing_target_from_action(self, *, href: str, raw_action: str, current_url: str) -> str:
        direct = (href or "").strip()
        if direct and not direct.lower().startswith("javascript:"):
            return self._normalize_url(urljoin(current_url, direct))

        raw = raw_action or ""
        if not raw:
            return ""
        detalle_match = re.search(r"""DetalleItem\(\s*['"]?(\d{4,10})['"]?\s*\)""", raw, re.IGNORECASE)
        if detalle_match:
            item_id = detalle_match.group(1)
            return self._normalize_url(urljoin(current_url, f"/Item/DetalleItem?id={item_id}"))
        patterns = (
            r"""['"]((?:https?:)?//[^'"]+)['"]""",
            r"""['"]((?:/|\.{1,2}/)[^'"]+)['"]""",
        )
        for pattern in patterns:
            for match in re.finditer(pattern, raw, re.IGNORECASE):
                candidate = self._normalize_url(urljoin(current_url, match.group(1)))
                if candidate and self._is_probable_product_target_url(candidate):
                    return candidate
        return ""

    def _is_probable_product_target_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        if "oferta=" in query or "utm_source=homebutton" in query:
            return False
        if any(token in path for token in ("/producto", "/product", "/articulo", "/itemdetail")):
            return True
        if "/item" in path and query:
            return True
        return False

    def _looks_like_product_card_text(self, text: str) -> bool:
        normalized = self._normalize_label_text(text or "")
        if not normalized:
            return False
        has_code = bool(PG_ELDISSER_CODE_RE.search(normalized))
        has_price = any(marker in normalized for marker in ("PVP", "PRECIO", "PVD"))
        return has_code and has_price

    def _cache_card_data(self, element: Any, url: str) -> None:
        def get_attr(name: str) -> str:
            val = str(element.get(name) or "").strip()
            if not val:
                parent = element.find_parent(attrs={name: True})
                val = str(parent.get(name) or "").strip() if parent else ""
            return val

        ean = self._clean_text(get_attr("data-ean-ean"))
        img = self._clean_text(get_attr("data-ean-img"))
        name = self._clean_text(get_attr("data-ean-descripcion"))
        marca_cod = self._clean_text(get_attr("data-marca-cod"))

        if not any([ean, img, name]):
            return

        image_url = self._normalize_url(urljoin(self.source_url, img)) if img else ""
        marca_parts = marca_cod.split("\t", 1)
        brand = self._clean_text(marca_parts[1]) if len(marca_parts) > 1 else self._clean_text(marca_cod)

        self._listing_card_cache[url] = {
            "ean13": ean,
            "image_url": image_url,
            "name": name,
            "brand": brand,
        }

    def _extract_eldisser_card_links(self, soup: BeautifulSoup) -> list[str]:
        detail_base = self._detail_view_url()
        links: list[str] = []
        seen: set[str] = set()
        # Primary: anchors carry data-ean-no directly
        for anchor in soup.select("a[data-ean-no]"):
            ref = str(anchor.get("data-ean-no") or "").strip()
            if ref and re.fullmatch(r"\d{4,10}", ref):
                url = f"{detail_base}?id={ref}"
                if url not in seen:
                    seen.add(url)
                    links.append(url)
                    self._cache_card_data(anchor, url)
        if links:
            return links
        # Secondary: card root element carries data-no-tr
        for card in soup.select("[data-no-tr]"):
            ref = str(card.get("data-no-tr") or "").strip()
            if ref and re.fullmatch(r"\d{4,10}", ref):
                url = f"{detail_base}?id={ref}"
                if url not in seen:
                    seen.add(url)
                    links.append(url)
                    self._cache_card_data(card, url)
        if links:
            return links
        # Tertiary: onclick DetalleItem pattern
        for anchor in soup.select("a[onclick]"):
            ref = self._extract_detail_item_id(str(anchor.get("onclick") or ""))
            if ref:
                url = f"{detail_base}?id={ref}"
                if url not in seen:
                    seen.add(url)
                    links.append(url)
        return links

    def _extract_listing_product_links(self, soup: BeautifulSoup, current_url: str) -> list[str]:
        # Eldisser cards have no href — extract from data attributes first
        card_links = self._extract_eldisser_card_links(soup)
        if card_links:
            return card_links
        candidates: list[tuple[int, str]] = []
        current_normalized = self._normalize_url(current_url)
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href:
                continue
            candidate = self._normalize_url(urljoin(current_url, href))
            if not candidate or not self._should_visit(candidate):
                continue
            if candidate == current_normalized:
                continue
            if not self._is_listing_product_anchor(anchor, candidate):
                continue
            rank = self._link_priority(
                candidate,
                anchor_text=self._first_text(anchor),
                anchor=anchor,
                current_url=current_url,
            )
            if rank > 20:
                continue
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
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        current_parsed = urlparse(current_url)
        current_path = current_parsed.path.lower()
        current_query = current_parsed.query.lower()
        if path == current_path and query == current_query:
            return 100
        if "oferta=" in query:
            return 100
        if "/item" in path and ("utm_source=homebutton" in query or not query):
            return 100
        if "/item" in path and query:
            return 0
        if any(token in path for token in ("/producto", "/product", "/articulo", "/itemdetail")):
            return 10
        text = self._normalize_label_text(anchor_text or "")
        if PG_ELDISSER_CODE_RE.search(text):
            return 20
        return 100

    def _extract_product_name(self, soup: BeautifulSoup) -> str:
        selectors = (
            "h1",
            ".product-title",
            ".item-title",
            ".detail-title",
            ".title-product",
        )
        for selector in selectors:
            value = self._first_text(soup.select_one(selector))
            normalized = self._normalize_label_text(value)
            if value and normalized not in {"CARACTERISTICAS PRINCIPALES", "PRODUCTOS", "PRODUTOS"}:
                return value
        for heading in soup.select("h2, h3, strong"):
            value = self._clean_text(self._first_text(heading))
            if not value:
                continue
            if self._normalize_label_text(value) in {"CARACTERISTICAS PRINCIPALES", "ESPECIFICACIONES", "PRODUCTOS", "PRODUTOS"}:
                continue
            if len(value) >= 10 and not value.isdigit():
                return value
        return ""

    def _extract_reference(self, soup: BeautifulSoup) -> str:
        badge_selectors = (
            ".product-code",
            ".item-code",
            ".reference",
            ".codigo",
        )
        for selector in badge_selectors:
            value = self._clean_text(self._first_text(soup.select_one(selector)))
            if value and PG_ELDISSER_CODE_RE.fullmatch(value):
                return value
        text = soup.get_text(" ", strip=True)
        match = PG_ELDISSER_CODE_RE.search(text)
        return match.group(0) if match else ""

    def _extract_ean(self, soup: BeautifulSoup, features: dict | None = None) -> str:
        if features is None:
            features = self._extract_specifications(soup)
        for section in features.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if self._normalize_label_text(str(key)) == "EAN":
                        match = PG_ELDISSER_EAN_RE.search(str(value))
                        if match:
                            return match.group(0)
        text = soup.get_text(" ", strip=True)
        for match in PG_ELDISSER_EAN_RE.finditer(text):
            value = match.group(0)
            if len(value) >= 8:
                return value
        return ""

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        selectors = (
            ".brand",
            ".product-brand",
            ".item-brand",
            "h2",
        )
        for selector in selectors:
            value = self._clean_text(self._first_text(soup.select_one(selector)))
            if value and len(value) <= 40 and value.isupper():
                return value
        features = self._extract_specifications(soup)
        for section in features.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if self._normalize_label_text(str(key)) == "MARCA":
                        return self._clean_text(str(value))
        return ""

    def _extract_category_fields(self, soup: BeautifulSoup) -> tuple[str, str]:
        breadcrumbs = self._extract_breadcrumbs(soup)
        cleaned = [self._clean_text(item) for item in breadcrumbs if self._clean_text(item)]
        if len(cleaned) >= 2:
            return cleaned[-2], cleaned[-1]
        if cleaned:
            return cleaned[-1], ""
        return "", ""

    def _extract_named_price(self, text: str, label: str) -> float:
        match = re.search(rf"{label}\s*([0-9]+(?:[.,][0-9]{{1,2}})?)", text, re.IGNORECASE)
        if not match:
            return 0.0
        return float(match.group(1).replace(".", "").replace(",", "."))

    def _extract_stock_text(self, text: str) -> str:
        match = PG_ELDISSER_STOCK_RE.search(text)
        return match.group(0) if match else ""

    def _extract_stock_info(self, text: str) -> dict[str, Any]:
        match = PG_ELDISSER_STOCK_RE.search(text or "")
        if not match:
            return {
                "text": "",
                "immediate_quantity": 0,
                "total_quantity": 0,
                "lead_time_note": "",
            }
        immediate_quantity = int(match.group(1) or 0)
        total_quantity = int(match.group(2) or match.group(1) or 0)
        lead_time_note = ""
        if match.group(2):
            if immediate_quantity > 0:
                lead_time_note = f"{immediate_quantity} unidade(s) entregues em 2 dias; stock total {total_quantity}."
            elif total_quantity > 0:
                lead_time_note = f"Sem entrega imediata; stock total {total_quantity} com entrega estimada em 7 dias."
        elif total_quantity > 0:
            lead_time_note = f"Stock disponível: {total_quantity}."
        return {
            "text": match.group(0),
            "immediate_quantity": immediate_quantity,
            "total_quantity": total_quantity,
            "lead_time_note": lead_time_note,
        }

    def _extract_stock_quantity(self, stock_text: str) -> int:
        return int(self._extract_stock_info(stock_text or "").get("total_quantity") or 0)

    def _add_stock_features(self, features: dict[str, dict[str, str]], stock_info: dict[str, Any]) -> None:
        if not stock_info.get("text"):
            return
        section = features.setdefault("Disponibilidade", {})
        immediate_quantity = int(stock_info.get("immediate_quantity") or 0)
        total_quantity = int(stock_info.get("total_quantity") or 0)
        section["Disponibilidade fornecedor"] = str(stock_info.get("text") or "")
        section["Stock total fornecedor"] = str(total_quantity)
        section["Entrega rapida (2 dias)"] = str(immediate_quantity)
        if stock_info.get("lead_time_note"):
            section["Observacao de entrega"] = str(stock_info["lead_time_note"])

    def _extract_product_images(self, soup: BeautifulSoup) -> list[str]:
        images: list[str] = []
        for selector in (
            ".product-image img[src]",
            ".item-image img[src]",
            ".gallery img[src]",
            ".thumbnails img[src]",
            "img[src]",
        ):
            for image in soup.select(selector):
                src = (image.get("data-src") or image.get("src") or "").strip()
                if not src:
                    continue
                full_url = self._normalize_url(urljoin(self.source_url, src))
                if full_url and self._is_likely_product_image(full_url):
                    images.append(full_url)
        deduped: list[str] = []
        seen = set()
        for image in images:
            if image in seen:
                continue
            seen.add(image)
            deduped.append(image)
        return deduped

    def _extract_caracteristicas_principales(self, soup: BeautifulSoup) -> dict[str, str]:
        return self._extract_table_after_heading(soup, ("CARACTERISTICAS PRINCIPALES",))

    def _extract_specifications(self, soup: BeautifulSoup) -> dict[str, dict[str, str]]:
        sections: dict[str, dict[str, str]] = {}
        current_section = ""
        spec_root = self._find_section_root(soup, ("ESPECIFICACIONES",))
        if spec_root:
            for node in spec_root.find_all(["h2", "h3", "h4", "tr"], recursive=True):
                if node.name in {"h2", "h3", "h4"}:
                    current_section = self._clean_text(node.get_text(" ", strip=True))
                    if current_section and current_section not in sections:
                        sections[current_section] = {}
                    continue
                cells = node.find_all(["th", "td"], recursive=False)
                if len(cells) >= 2:
                    key = self._clean_text(cells[0].get_text(" ", strip=True))
                    value = self._clean_text(cells[-1].get_text(" ", strip=True))
                    if key and value:
                        sections.setdefault(current_section or "Especificaciones", {})[key] = value
        return sections

    def _extract_table_after_heading(self, soup: BeautifulSoup, headings: tuple[str, ...]) -> dict[str, str]:
        root = self._find_section_root(soup, headings)
        if not root:
            return {}
        values: dict[str, str] = {}
        for row in root.find_all("tr"):
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) < 2:
                continue
            key = self._clean_text(cells[0].get_text(" ", strip=True))
            value = self._clean_text(cells[-1].get_text(" ", strip=True))
            if key and value:
                values[key] = value
        return values

    def _find_section_root(self, soup: BeautifulSoup, headings: tuple[str, ...]):
        heading_set = {self._normalize_label_text(item) for item in headings}
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "strong", "span", "div"]):
            text = self._normalize_label_text(heading.get_text(" ", strip=True))
            if text not in heading_set:
                continue
            current = heading.parent
            for _index in range(4):
                if not current:
                    break
                if current.find("table"):
                    return current
                current = current.parent
            return heading.parent
        return None

    def _principales_to_text(self, principales: dict[str, str]) -> str:
        if not principales:
            return ""
        return "\n".join(f"{key}: {value}" for key, value in principales.items())

    def _specs_to_text(self, features: dict[str, dict[str, str]]) -> str:
        parts: list[str] = []
        for section, values in features.items():
            if section:
                parts.append(section)
            for key, value in values.items():
                parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def _catalog_url(self) -> str:
        parsed = urlparse(self.source_url)
        if parsed.path in {"", "/"}:
            return self._normalize_url(urljoin(self.source_url, "/Item?utm_source=homebutton"))
        return self.source_url

    def _combo_category(self, combo: dict[str, dict[str, str]]) -> str:
        gama = combo.get("gama") or {}
        familia = combo.get("familia") or {}
        return gama.get("text") or familia.get("text") or ""

    def _combo_sub_category(self, combo: dict[str, dict[str, str]]) -> str:
        parts = []
        familia = combo.get("familia") or {}
        subfamilia = combo.get("subfamilia") or {}
        if familia.get("text"):
            parts.append(familia["text"])
        if subfamilia.get("text"):
            parts.append(subfamilia["text"])
        return " / ".join(parts)

    def _normalize_label_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFD", value or "")
        normalized = "".join(character for character in normalized if not unicodedata.combining(character))
        return re.sub(r"\s+", " ", normalized).strip().upper()

    def _is_catalog_listing_page(self, url: str, normalized_text: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        if "/item" not in path:
            return False
        if "oferta=" in query:
            return True
        if any(marker in normalized_text for marker in ("CARACTERISTICAS PRINCIPALES", "ESPECIFICACIONES", "DISP:")):
            return False
        if "BUSCAR" in normalized_text and "GAMA" in normalized_text and "FAMILIA" in normalized_text:
            return True
        if "VER MAS PRODUCTOS" in normalized_text:
            return True
        if "UTM_SOURCE=HOMEBUTTON" in query:
            return True
        return False

    def _is_listing_product_anchor(self, anchor: Any, candidate_url: str) -> bool:
        parsed = urlparse(candidate_url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        if "oferta=" in query or "utm_source=homebutton" in query:
            return False
        if "/item" not in path and not any(token in path for token in ("/producto", "/product", "/articulo", "/itemdetail")):
            return False
        combined_parts: list[str] = []
        node = anchor
        for _index in range(5):
            if not node:
                break
            text = self._normalize_label_text(node.get_text(" ", strip=True))
            if text:
                combined_parts.append(text)
            node = getattr(node, "parent", None)
        combined_text = " ".join(combined_parts)
        has_code = bool(PG_ELDISSER_CODE_RE.search(combined_text))
        has_price = any(marker in combined_text for marker in ("PVP", "PRECIO", "PVD"))
        has_image = bool(anchor.select_one("img"))
        if not has_image:
            node = anchor
            for _index in range(4):
                node = getattr(node, "parent", None)
                if not node:
                    break
                if getattr(node, "select_one", None) and node.select_one("img"):
                    has_image = True
                    break
        return has_code and (has_price or has_image)

    async def _debug_filter_controls(self, page: Page) -> dict[str, Any]:
        return await page.evaluate(
            """() => {
                const normalize = (value) => (value || "")
                    .normalize("NFD")
                    .replace(/[\\u0300-\\u036f]/g, "")
                    .replace(/\\s+/g, " ")
                    .trim();
                const selects = Array.from(document.querySelectorAll("select")).slice(0, 12).map((select) => ({
                    name: normalize(select.name || ""),
                    id: normalize(select.id || ""),
                    aria: normalize(select.getAttribute("aria-label") || ""),
                    dataLabel: normalize(select.getAttribute("data-label") || ""),
                    optionCount: select.options.length,
                    selectizeOptionCount: select.selectize ? Object.keys(select.selectize.options || {}).length : 0,
                    sampleOptions: Array.from(select.options).slice(0, 5).map((option) => normalize(option.textContent || "")),
                    sampleSelectizeOptions: select.selectize
                        ? Object.values(select.selectize.options || {}).slice(0, 5).map((option) => normalize(option.text || option.label || option.value || ""))
                        : [],
                }));
                const visibleTexts = Array.from(document.querySelectorAll("label, span, div, button"))
                    .map((node) => normalize(node.textContent || ""))
                    .filter((text) => text && (text.includes("GAMA") || text.includes("FAMILIA") || text.includes("SUBFAMILIA") || text.includes("BUSCAR")))
                    .slice(0, 20);
                return {
                    url: window.location.href,
                    title: document.title || "",
                    selectCount: document.querySelectorAll("select").length,
                    selects,
                    visibleTexts,
                };
            }"""
        )

    def _record_product_debug(self, entry: dict[str, Any]) -> None:
        status = str(entry.get("status") or "")
        if len(self._product_debug) < self._pg_product_debug_max_entries:
            self._product_debug.append(entry)
        if status == "accepted_product":
            self._accepted_product_debug_count += 1
            if self._accepted_product_debug_count % self._pg_product_debug_log_every == 0:
                _logger.info(
                    "Eldisser accepted products=%s visited=%s last_entry=%s",
                    self._accepted_product_debug_count,
                    self._progress_visited_pages(),
                    entry,
                )
            return
        _logger.info("Eldisser product debug: %s", entry)
