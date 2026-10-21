# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_cancel(self):
        """Ao cancelar uma linha de extracto bancário, prefixar 'CANCELADO-'
        no `unique_import_id` da bank.statement.line associada.

        Razão: a chave única `unique_import_id` impede reimportar a mesma
        transação. Quando o user cancela um movimento errado (ex.: importado
        para o journal errado) e quer reimportar correctamente, a colisão
        bloqueia. Com o prefixo, o ID deixa de colidir e o reimport passa.

        Se já existir outra linha com o mesmo prefixo 'CANCELADO-' (re-cancelar
        a mesma transação várias vezes), incrementa-se um contador para evitar
        colisão na chave única.
        """
        result = super().button_cancel()
        StatementLine = self.env['account.bank.statement.line']
        for move in self:
            line = move.statement_line_id
            if (line
                    and line.unique_import_id
                    and not line.unique_import_id.startswith('CANCELADO-')):
                new_val = 'CANCELADO-' + line.unique_import_id
                counter = 1
                while StatementLine.search_count([
                    ('unique_import_id', '=', new_val),
                    ('id', '!=', line.id),
                ]):
                    counter += 1
                    new_val = f'CANCELADO-{counter}-' + line.unique_import_id
                line.unique_import_id = new_val
        return result
