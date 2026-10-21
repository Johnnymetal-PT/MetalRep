from __future__ import annotations

from .pg_adapters import PgEldisserB2BCrawler, PgGenericCrawler, PgMielectroCrawler


PG_ADAPTERS = {
    PgEldisserB2BCrawler.adapter_key: PgEldisserB2BCrawler,
    PgMielectroCrawler.adapter_key: PgMielectroCrawler,
    PgGenericCrawler.adapter_key: PgGenericCrawler,
}


def pg_get_crawler_class(source_url: str, adapter_key: str | None = None):
    if adapter_key:
        crawler_class = PG_ADAPTERS.get(adapter_key)
        if not crawler_class:
            raise ValueError(f"Unknown crawler adapter: {adapter_key}")
        return crawler_class
    for crawler_class in PG_ADAPTERS.values():
        if crawler_class is PgGenericCrawler:
            continue
        if crawler_class.supports_url(source_url):
            return crawler_class
    return PgGenericCrawler
