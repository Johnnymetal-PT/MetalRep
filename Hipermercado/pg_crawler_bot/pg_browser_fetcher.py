from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

_logger = logging.getLogger(__name__)


@dataclass
class PgBrowserResponse:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]


class PgBrowserFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.5,
        stability_delay_ms: int = 750,
        fast_mode: bool = False,
        blocked_resource_types: list[str] | None = None,
        user_agent: str | None = None,
        proxy_server: str | None = None,
        proxy_username: str | None = None,
        proxy_password: str | None = None,
        browser_channel: str | None = None,
        storage_state_path: str | None = None,
        restart_after_pages: int | None = None,
        restart_after_minutes: int | None = None,
    ) -> None:
        self.timeout_ms = timeout_seconds * 1000
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.fast_mode = bool(fast_mode)
        self.blocked_resource_types = [value for value in (blocked_resource_types or []) if value]
        self.stability_delay_ms = stability_delay_ms
        if self.fast_mode:
            self.stability_delay_ms = min(self.stability_delay_ms, 250)
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
        self.proxy_server = (proxy_server or "").strip() or None
        self.proxy_username = (proxy_username or "").strip() or None
        self.proxy_password = proxy_password or None
        self.browser_channel = (browser_channel or "").strip() or None
        self.storage_state_path = Path(storage_state_path).resolve() if storage_state_path else None
        self.restart_after_pages = max(0, int(restart_after_pages or 0))
        self.restart_after_minutes = max(0, int(restart_after_minutes or 0))

        self._loop: asyncio.AbstractEventLoop | None = None
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._pages_since_restart = 0
        self._restart_started_at: float | None = None

    def fetch(self, url: str, page_action=None) -> PgBrowserResponse:
        return self._run(self._fetch_with_retries(url, page_action))

    def submit_form(
        self,
        *,
        origin_url: str,
        submit_url: str,
        form_body: str,
        page_action=None,
        headers: dict[str, str] | None = None,
        referrer: str | None = None,
    ) -> PgBrowserResponse:
        return self._run(
            self._submit_form_with_retries(
                origin_url=origin_url,
                submit_url=submit_url,
                form_body=form_body,
                page_action=page_action,
                headers=headers,
                referrer=referrer,
            )
        )

    def run_page_task(self, task):
        return self._run(self._run_page_task_with_retries(task))

    def export_storage_state(self) -> dict[str, Any]:
        try:
            return dict(self._run(self._export_storage_state()) or {})
        except Exception:
            return {}

    def close(self) -> None:
        try:
            self._run(self._aclose())
        except Exception:
            pass

    def _run(self, coro):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop.run_until_complete(coro)

    async def _ensure_browser(self) -> None:
        if self._browser and self._context:
            return

        self._playwright = await async_playwright().start()

        launch_kwargs: dict[str, Any] = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--no-first-run",
                "--password-store=basic",
                "--use-mock-keychain",
                "--window-size=1440,900",
            ],
        }
        if self.browser_channel:
            launch_kwargs["channel"] = self.browser_channel
        if self.proxy_server:
            proxy: dict[str, str] = {"server": self.proxy_server}
            if self.proxy_username:
                proxy["username"] = self.proxy_username
            if self.proxy_password:
                proxy["password"] = self.proxy_password
            launch_kwargs["proxy"] = proxy

        self._browser = await self._playwright.chromium.launch(**launch_kwargs)
        context_kwargs: dict[str, Any] = {
            "user_agent": self.user_agent,
            "viewport": {"width": 1440, "height": 900},
            "screen": {"width": 1440, "height": 900},
            "device_scale_factor": 1.0,
            "locale": "es-ES",
            "timezone_id": "Europe/Madrid",
            "color_scheme": "light",
            "reduced_motion": "no-preference",
            "java_script_enabled": True,
            "has_touch": False,
            "is_mobile": False,
        }
        if self.storage_state_path and self.storage_state_path.exists():
            context_kwargs["storage_state"] = str(self.storage_state_path)
        self._context = await self._browser.new_context(**context_kwargs)
        if self.blocked_resource_types:
            blocked = set(self.blocked_resource_types)

            async def _route_handler(route, request):
                if request.resource_type in blocked:
                    await route.abort()
                else:
                    await route.continue_()

            await self._context.route("**/*", _route_handler)
        self._pages_since_restart = 0
        self._restart_started_at = time.monotonic()
        await self._context.set_extra_http_headers(
            {
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "DNT": "1",
            }
        )

    async def _fetch_with_retries(self, url: str, page_action=None) -> PgBrowserResponse:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self._fetch_once(url, page_action)
            except Exception as exc:
                last_exc = exc
                if self._is_browser_crash(exc):
                    await self._restart_browser("fetch crash")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay_seconds)
        raise RuntimeError(str(last_exc) if last_exc else f"Browser fetch failed for {url}")

    async def _submit_form_with_retries(
        self,
        *,
        origin_url: str,
        submit_url: str,
        form_body: str,
        page_action=None,
        headers: dict[str, str] | None = None,
        referrer: str | None = None,
    ) -> PgBrowserResponse:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self._submit_form_once(
                    origin_url=origin_url,
                    submit_url=submit_url,
                    form_body=form_body,
                    page_action=page_action,
                    headers=headers,
                    referrer=referrer,
                )
            except Exception as exc:
                last_exc = exc
                if self._is_browser_crash(exc):
                    await self._restart_browser("submit crash")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay_seconds)
        raise RuntimeError(str(last_exc) if last_exc else f"Browser form submit failed for {submit_url}")

    async def _fetch_once(self, url: str, page_action=None) -> PgBrowserResponse:
        await self._ensure_browser()
        assert self._context is not None
        await self._restart_if_needed("pre-fetch guard")

        page: Page = await self._context.new_page()
        page.set_default_timeout(self.timeout_ms)
        page.set_default_navigation_timeout(self.timeout_ms)

        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await self.prepare_page(page)
            if page_action:
                await page_action(page, url)
                await self.prepare_page(page)

            html_started_at = time.perf_counter()
            html = await page.content()
            html_elapsed = time.perf_counter() - html_started_at
            if html_elapsed >= 5.0:
                _logger.info(
                    "Browser fetch page.content was slow url=%s elapsed=%.2fs html_length=%s",
                    page.url,
                    html_elapsed,
                    len(html),
                )
            final_url = page.url
            status_code = response.status if response else 0
            headers = await response.all_headers() if response else {}

            if self._is_interstitial(html):
                raise RuntimeError(f"Challenge/interstitial returned for {url}")
            if self._is_incomplete_dom(html):
                raise RuntimeError(f"Incomplete DOM returned for {url}")

            return PgBrowserResponse(
                url=final_url,
                status_code=status_code,
                text=html,
                headers=headers,
            )
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"Timed out loading {url}") from exc
        finally:
            await self._persist_storage_state()
            await page.close()
            await self._mark_page_used()

    async def _submit_form_once(
        self,
        *,
        origin_url: str,
        submit_url: str,
        form_body: str,
        page_action=None,
        headers: dict[str, str] | None = None,
        referrer: str | None = None,
    ) -> PgBrowserResponse:
        await self._ensure_browser()
        assert self._context is not None
        await self._restart_if_needed("pre-submit guard")

        page: Page = await self._context.new_page()
        page.set_default_timeout(self.timeout_ms)
        page.set_default_navigation_timeout(self.timeout_ms)

        try:
            await page.goto(origin_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await self.prepare_page(page)
            if page_action:
                await page_action(page, origin_url)
                await self.prepare_page(page)

            submit_started_at = time.perf_counter()
            result = await asyncio.wait_for(
                page.evaluate(
                    """async ({ submitUrl, formBody, headers, referrer }) => {
                        const requestHeaders = {
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            ...(headers || {}),
                        };
                        const response = await fetch(submitUrl, {
                            method: "POST",
                            headers: requestHeaders,
                            body: formBody,
                            credentials: "include",
                            referrer: referrer || undefined,
                        });
                        const text = await response.text();
                        return {
                            url: response.url || submitUrl,
                            status: response.status || 0,
                            headers: Object.fromEntries(response.headers.entries()),
                            text,
                        };
                    }""",
                    {
                        "submitUrl": submit_url,
                        "formBody": form_body,
                        "headers": headers or {},
                        "referrer": referrer or "",
                    },
                ),
                timeout=(self.timeout_ms / 1000.0) + 5.0,
            )
            submit_elapsed = time.perf_counter() - submit_started_at
            if submit_elapsed >= 5.0:
                _logger.info(
                    "Browser form submit was slow origin_url=%s submit_url=%s elapsed=%.2fs html_length=%s",
                    origin_url,
                    submit_url,
                    submit_elapsed,
                    len(result.get("text") or ""),
                )

            return PgBrowserResponse(
                url=str(result.get("url") or submit_url),
                status_code=int(result.get("status") or 0),
                text=str(result.get("text") or ""),
                headers={str(key): str(value) for key, value in dict(result.get("headers") or {}).items()},
            )
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Timed out submitting form to {submit_url}") from exc
        finally:
            await self._persist_storage_state()
            await page.close()
            await self._mark_page_used()

    async def _run_page_task_with_retries(self, task):
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await self._run_page_task(task)
            except Exception as exc:
                last_exc = exc
                if self._is_browser_crash(exc):
                    await self._restart_browser("task crash")
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay_seconds)
        raise RuntimeError(str(last_exc) if last_exc else "Browser task failed.")

    async def _run_page_task(self, task):
        await self._ensure_browser()
        assert self._context is not None
        await self._restart_if_needed("pre-task guard")

        page: Page = await self._context.new_page()
        page.set_default_timeout(self.timeout_ms)
        page.set_default_navigation_timeout(self.timeout_ms)
        try:
            return await task(page)
        finally:
            await self._persist_storage_state()
            await page.close()
            await self._mark_page_used()

    async def prepare_page(self, page: Page) -> None:
        started_at = time.perf_counter()
        await self._wait_for_page_ready(page)
        ready_elapsed = time.perf_counter() - started_at
        stable_started_at = time.perf_counter()
        await self._wait_for_stable_dom(page)
        stable_elapsed = time.perf_counter() - stable_started_at
        total_elapsed = time.perf_counter() - started_at
        if total_elapsed >= 5.0:
            _logger.info(
                "Browser prepare_page was slow url=%s total=%.2fs ready=%.2fs stable=%.2fs",
                page.url,
                total_elapsed,
                ready_elapsed,
                stable_elapsed,
            )

    async def _wait_for_page_ready(self, page: Page) -> None:
        if not self.fast_mode:
            try:
                await page.wait_for_load_state("networkidle", timeout=self.timeout_ms)
            except PlaywrightTimeoutError:
                pass

        try:
            await page.wait_for_function(
                "() => document.readyState === 'complete' || document.readyState === 'interactive'",
                timeout=self.timeout_ms,
            )
        except PlaywrightTimeoutError:
            pass

        await page.wait_for_timeout(self.stability_delay_ms)

    async def _wait_for_stable_dom(self, page: Page) -> None:
        if self.fast_mode:
            await page.wait_for_timeout(min(self.stability_delay_ms, 150))
            return
        previous = None
        stable_rounds = 0

        for _ in range(4):
            snapshot = await page.evaluate(
                """() => {
                    const body = document.body;
                    return {
                        length: body ? body.innerText.length : 0,
                        childCount: body ? body.querySelectorAll('*').length : 0,
                        title: document.title || '',
                        state: document.readyState || '',
                    };
                }"""
            )
            if snapshot == previous:
                stable_rounds += 1
                if stable_rounds >= 1:
                    break
            else:
                stable_rounds = 0
            previous = snapshot
            await page.wait_for_timeout(self.stability_delay_ms)

    def _is_interstitial(self, html: str) -> bool:
        lowered = html.lower()
        markers = (
            "just a moment...",
            "cf-chl",
            "/cdn-cgi/challenge-platform/",
            "attention required!",
            "verify you are human",
            "checking your browser",
            "enable javascript and cookies to continue",
        )
        return any(marker in lowered for marker in markers)

    def _is_incomplete_dom(self, html: str) -> bool:
        lowered = html.lower()
        if "<body" not in lowered:
            return True
        if len(html.strip()) < 1200:
            return True
        return False

    async def _persist_storage_state(self) -> None:
        if self.storage_state_path and self._context:
            self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(self.storage_state_path))

    async def _export_storage_state(self) -> dict[str, Any]:
        await self._ensure_browser()
        if not self._context:
            return {}
        state = await self._context.storage_state()
        if self.storage_state_path:
            self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
            await self._context.storage_state(path=str(self.storage_state_path))
        return dict(state or {})

    def _is_browser_crash(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "target crashed" in message or "browser has disconnected" in message or "page crashed" in message

    async def _restart_if_needed(self, reason: str) -> None:
        if not self._context:
            return
        if self.restart_after_pages and self._pages_since_restart >= self.restart_after_pages:
            await self._restart_browser(f"{reason} page_limit={self.restart_after_pages}")
            return
        if self.restart_after_minutes and self._restart_started_at:
            elapsed = time.monotonic() - self._restart_started_at
            if elapsed >= (self.restart_after_minutes * 60):
                await self._restart_browser(f"{reason} age_limit={self.restart_after_minutes}m")

    async def _mark_page_used(self) -> None:
        if not self._context:
            return
        self._pages_since_restart += 1

    async def _restart_browser(self, reason: str) -> None:
        _logger.warning("Restarting browser context: %s", reason)
        await self._aclose()
        await self._ensure_browser()

    async def _aclose(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
