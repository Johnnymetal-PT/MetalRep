# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Normaliza os registos que já existiam à data da instalação.

    A lógica vive em `mrp.workorder.pg_normalise_shopfloor_states`, que é pública e pode
    ser chamada outra vez a qualquer momento — ver o método para o detalhe.
    """
    env["mrp.workorder"].pg_normalise_shopfloor_states()
