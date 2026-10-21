# Hipermercado

Addons e servicos de integracao do projeto Hipermercado.

## Modulos Odoo (19.0)

| Modulo | Descricao |
|---|---|
| `hiper_sync` | Core de sincronizacao de catalogo e stock de fornecedores. |
| `pg_stock_route_hierarchy` | Hierarquia de routes de stock e calculo de quantidade vendavel no website. |
| `pg_hipermercado_website` | Ajustes de website (performance do mega menu). |
| `emipro_theme_base` | Base do tema (Emipro, licenca OPL-1). |
| `theme_clarico_vega` | Tema eCommerce Clarico Vega (Emipro, licenca OPL-1). |

## Modulos PrestaShop

Em `Prestashop/`, integracoes de catalogo e stock por fornecedor: `fusion`, `intauferma`,
`intdepau`, `intdmi`, `inteldisser`, `intexperteletro`, `intmacorlux`, `intociostock`,
`intorima`, `intsorefoz`.

## Servicos de crawling

| Componente | Descricao |
|---|---|
| `pg_crawler_bot` | Servico de crawling com adaptadores por fornecedor. |
| `pg_mielectro_crawler_bot` | Crawler dedicado ao fornecedor Mielectro. |
| `remote_crawler_service_example` | Exemplo de servico de crawler remoto. |
| `pg_wheelhouse` | Wheels Python para instalacao offline dos crawlers. |

Dependencias Python em `requirements.txt`.

## Referencia local do source Odoo

O source do Odoo nao e versionado. Colocar ou ligar em `vendor/` (ignorado por git) a versao
19.0 correspondente quando for necessario para analise.
