"""Hiper Sync Core -- ponto de entrada do modulo.

Modulo de sincronizacao de feeds de fornecedores do Hipermercado. Consultar o
``__manifest__.py`` para o guia de utilizacao completo (objetivo de negocio,
pre-requisitos, passo a passo, FAQ).

Estrutura:
    * ``models``      -- entidades Odoo (vendor, sync_run, category_map, ...).
    * ``services``    -- logica pura (adapters, merger, publisher, traducao).
    * ``controllers`` -- endpoints HTTP (upload do crawler remoto).
"""

from . import models
from . import services
from . import controllers
