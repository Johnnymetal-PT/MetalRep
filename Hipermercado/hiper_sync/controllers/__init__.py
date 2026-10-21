"""Controllers HTTP do Hiper Sync Core.

* ``pg_remote_crawler`` -- endpoint ``POST /hiper_sync/crawler/upload`` usado
  pelo crawler externo para entregar o CSV gerado de volta ao Odoo
  (autenticacao por Bearer token configurado em
  ``hiper_sync.remote_crawler_upload_token``).
"""

from . import pg_remote_crawler
