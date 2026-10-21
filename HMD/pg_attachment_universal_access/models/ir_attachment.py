# -*- coding: utf-8 -*-
"""Override de `ir.attachment` para conceder acesso universal a anexos.

Este ficheiro implementa o comportamento "todos os utilizadores internos
veem todos os anexos" pedido pelo cliente HMD. O standard do Odoo 18 liga
o acesso a um anexo ao acesso do registo-pai (`res_model` + `res_id`):
ver `vendor/odoo_src/community/odoo/addons/base/models/ir_attachment.py`
metodo `check()` e `_search()`. Esse acoplamento e a razao pela qual
qualquer mexida em regras de acesso de outros modelos (produtos, vendas,
projetos, etc.) reabre o erro "Anexo (ir.attachment) - sem acesso".

Solucao aqui: para utilizadores internos (group_user), saltar a
verificacao de acesso ao registo-pai. Mantem-se:
 - bloqueio total para portal/publico (gerido fora deste override),
 - verificacao de `res_field` com `groups=` (campos binarios com
   restricao explicita de grupo continuam protegidos),
 - todos os outros checks standard (criador do anexo orfao, etc.).
"""

from collections import defaultdict

from odoo import api, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def check(self, mode, values=None):
        """Bypass do check ao registo-pai para utilizadores internos.

        Reimplementa o `check()` standard mas, em vez de chamar
        `records.check_access(mode)` sobre o registo-pai, aceita o acesso
        desde que o utilizador seja interno. Continua a aplicar:
          - superuser passa direto;
          - utilizador nao-interno e nao-admin -> AccessError standard;
          - anexos publicos em modo read -> passam direto;
          - anexos orfaos (`res_id` vazio) so para o criador ou system;
          - `res_field` com grupos restritos -> mantido.
        """
        # Superuser e nao-internos seguem comportamento standard.
        if self.env.is_superuser():
            return True
        if not (self.env.is_admin() or self.env.user._is_internal()):
            # Mesma mensagem que o standard para nao mudar UX.
            return super().check(mode, values=values)

        if self:
            self.env["ir.attachment"].flush_model(
                ["res_model", "res_id", "create_uid", "public", "res_field"]
            )
            self._cr.execute(
                "SELECT res_model, res_id, create_uid, public, res_field "
                "FROM ir_attachment WHERE id IN %s",
                [tuple(self.ids)],
            )
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == "read":
                    continue
                if not self.env.is_system():
                    # Anexo orfao so para criador. Mantemos o standard
                    # porque criar/ler anexos sem `res_id` de outros
                    # utilizadores e um vetor de fuga de dados (anexos
                    # ainda nao ligados a registo, ex.: drafts).
                    if not res_id and create_uid != self.env.uid:
                        return super().check(mode, values=values)
                    # Campos binarios com `groups=` definido continuam
                    # protegidos para nao expor campos restritos por
                    # configuracao explicita do programador/Studio.
                    if res_field:
                        field = self.env[res_model]._fields[res_field]
                        if not field.is_accessible(self.env):
                            return super().check(mode, values=values)
        # Nao validamos `records.check_access(mode)` sobre o registo-pai:
        # e este o ponto exato em que o cliente quer abrir o acesso.
        return True

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        """Saltar o filtro por acesso ao registo-pai para utilizadores internos.

        O `_search()` standard pos-filtra o resultset removendo anexos
        cujo registo-pai o utilizador nao consegue ler. Para
        utilizadores internos delegamos a chamada em `super()` mas
        sob `sudo()`: dentro do standard, a verificacao
        `self.env.is_superuser()` passa, ele curto-circuita para o
        `_search` do ORM base e nao corre o pos-filtro.

        A injecao automatica de `res_field=False` continua a aplicar-se
        porque ocorre ANTES do branch `is_superuser` no standard, ou
        seja, binarios de campos com `res_field` continuam excluidos
        por defeito do resultset.
        """
        if self.env.is_superuser():
            return super()._search(domain, offset, limit, order)
        if not (self.env.is_admin() or self.env.user._is_internal()):
            return super()._search(domain, offset, limit, order)
        # Internos: bypass do pos-filtro de registo-pai via sudo().
        return super(IrAttachment, self.sudo())._search(
            domain, offset, limit, order
        )
