# -*- coding: utf-8 -*-
"""Vista focada das linhas para editar campos Intrastat em faturas publicadas.

Na view base, `invoice_line_ids` é `readonly="state != 'draft'"`, o que
bloqueia TODOS os campos da linha quando a fatura está publicada. Para
permitir editar apenas os campos Intrastat (Intrastat, País do Produto e
Código HS) numa fatura confirmada — sem desbloquear preço/conta/quantidade
— expomos um One2many dedicado (mesmo modelo e mesmo inverse `move_id`),
cuja lista só contém esses campos como editáveis.

A nível de modelo, gravar estes campos numa move publicada é permitido pelo
standard (`account.move.line.write`): só impostos é que estão vedados e os
campos fiscais validam a data de bloqueio.
"""

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    pg_intrastat_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="move_id",
        string="Linhas (Intrastat)",
        domain=[("display_type", "=", "product")],
        help="Vista focada das linhas de produto para rever/corrigir os "
             "campos Intrastat, País do Produto e Código HS, inclusive em "
             "faturas já confirmadas. Não permite criar nem apagar linhas.",
    )
