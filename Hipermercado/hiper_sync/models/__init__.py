"""Modelos Odoo do Hiper Sync Core.

* ``vendor``               -- ``hiper.sync.vendor``: ficha do fornecedor.
* ``sync_run``             -- ``hiper.sync.run``: execucao de sincronizacao.
* ``sync_run_line``        -- ``hiper.sync.run.line``: detalhe linha-a-linha.
* ``category_map``         -- ``hiper.sync.category.map``: mapeamento de
  categoria fornecedor -> categoria interna/publica + regras de margem.
* ``feature_line``         -- ``hiper.product.feature.line``: features
  tecnicas importadas (chave/valor) por produto.
* ``pg_product_image``     -- herda ``product.image`` para guardar a URL
  origem de cada imagem secundaria importada.
* ``product_template``     -- herda ``product.template`` para campos de sync,
  locks granulares e fila assincrona de imagens.
* ``res_config_settings``  -- ecra de definicoes (chaves API, parametros
  globais).
"""

from . import category_map
from . import feature_line
from . import pg_product_image
from . import product_template
from . import res_config_settings
from . import sync_run
from . import sync_run_line
from . import vendor
