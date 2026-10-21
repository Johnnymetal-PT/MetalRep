"""Modelos do PG Stock Route Hierarchy (todos por heranca; sem modelos novos).

* ``pg_res_company``         -- 4 campos de armazem + helpers de hierarquia
  + ``_pg_apply_stock_hierarchy`` (configura rules e resupply).
* ``pg_res_config_settings`` -- expoe a configuracao em Definicoes.
* ``pg_sale_order``          -- forca primario nas SOs do website e usa
  somatorio da hierarquia em ``_get_free_qty``.
* ``pg_sale_order_line``     -- ajusta ``_read_qties`` e injecta routes
  custom em ``_prepare_procurement_values``.
* ``pg_website``             -- ``_get_product_available_qty`` usa
  hierarquia + virtual supplier.
"""

from . import pg_res_company
from . import pg_res_config_settings
from . import pg_sale_order
from . import pg_sale_order_line
from . import pg_website
