"""Servicos do Hiper Sync Core (logica pura, sem dependencia direta do ORM).

* ``adapter_base``      -- classe base dos adapters: parsing CSV/JSON,
  normalizacao para o esquema interno e validacao de configuracao.
* ``vendor_adapters``   -- factory ``get_adapter(vendor)`` que devolve o
  adapter certo consoante ``source_kind`` ou registado por ``code``.
* ``merger``            -- decide novo produto vs. atualizacao via barcode,
  referencia ou fingerprint.
* ``publisher``         -- aplica regras de publicacao (stock, preco, locks,
  multi-fornecedor) e gera linhas em ``hiper.sync.run.line``.
* ``translate``         -- adapter de traducao (OpenAI / Google) com termos
  protegidos por marca, referencia e EAN.
* ``pg_term_discovery`` -- descoberta automatica de termos protegidos via
  Wikipedia / Wikidata e (opcional) GTIN.
* ``utils``             -- helpers (parsing JSON tolerante, limpeza HTML).
"""

from . import adapter_base
from . import merger
from . import pg_term_discovery
from . import publisher
from . import translate
from . import utils
from . import vendor_adapters
