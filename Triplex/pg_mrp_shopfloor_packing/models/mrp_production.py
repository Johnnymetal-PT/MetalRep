# -*- coding: utf-8 -*-
"""Fotografias da embalagem, guardadas na ordem de fabrico.

Ver o __manifest__.py para o contexto de negócio e para a razão de ficarem aqui e não no
produto nem na guia de expedição.
"""
import base64
import binascii

from odoo import _, fields, models
from odoo.exceptions import UserError

# Marca que distingue as fotografias de embalagem dos restantes anexos da ordem. Fica no
# `description` do anexo por ser um campo que já existe e é pesquisável — evita um modelo
# novo só para classificar ficheiros.
MARCADOR_FOTO = "pg_packing_photo"

# Guarda contra um envio acidental de dezenas de ficheiros de uma vez. A reunião falava em
# duas ou três fotografias.
MAX_FOTOS_POR_ENVIO = 10


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    pg_packing_photo_count = fields.Integer(
        string="Fotografias da embalagem",
        compute="_compute_pg_packing_photos",
        help="Quantas fotografias de embalagem estão guardadas nesta ordem de fabrico.",
    )

    pg_packing_photo = fields.Binary(
        string="Última fotografia da embalagem",
        compute="_compute_pg_packing_photos",
        help="A fotografia mais recente, para consulta rápida no formulário. As fotografias "
             "são guardadas como anexos; este campo é apenas uma janela para a última.",
    )

    def _pg_packing_photo_attachments(self):
        """Anexos desta ordem marcados como fotografia de embalagem, do mais recente."""
        self.ensure_one()
        return self.env["ir.attachment"].search([
            ("res_model", "=", "mrp.production"),
            ("res_id", "=", self.id),
            ("description", "=", MARCADOR_FOTO),
        ], order="id desc")

    # Sem `@api.depends` de propósito: o valor vem de uma procura em `ir.attachment`, que não
    # é expressável como dependência de campos. Os anexos não têm relação inversa na ordem de
    # fabrico, e o mixin que traz `message_main_attachment_id` (`mail.thread.main.attachment`)
    # não é herdado por `mrp.production` — declará-lo rebentava o arranque do registry.
    # Como nenhum dos dois campos é armazenado, são recalculados em cada leitura, pelo que a
    # ausência de dependências não perde actualizações entre pedidos.
    def _compute_pg_packing_photos(self):
        for production in self:
            anexos = production._pg_packing_photo_attachments()
            production.pg_packing_photo_count = len(anexos)
            production.pg_packing_photo = anexos[:1].datas or False

    def pg_add_packing_photos(self, fotos):
        """Guarda fotografias de embalagem como anexos desta ordem de fabrico.

        Recebe uma lista de dicionários `{"name": nome, "data": conteudo_base64}`, tal como
        o diálogo do Chão de Fábrica os envia.

        As fotografias ficam na ORDEM DE FABRICO, e não no produto nem na guia:
        - o produto é partilhado por várias ordens (medido: 45 produtos em mais de uma ordem
          aberta), pelo que a fotografia de uma peça apagaria a da outra;
        - a guia de expedição **ainda não existe** no momento em que o operador fecha a
          produção, e quando existe está noutra empresa sem ligação rastreável.

        A ordem de fabrico é o único documento que existe naquele momento, é único por peça e
        nunca é sobreposto.
        """
        self.ensure_one()
        if not fotos:
            return 0
        if len(fotos) > MAX_FOTOS_POR_ENVIO:
            raise UserError(_(
                "Demasiadas fotografias de uma vez (máximo %s).", MAX_FOTOS_POR_ENVIO
            ))

        criados = self.env["ir.attachment"]
        for indice, foto in enumerate(fotos, start=1):
            dados = (foto or {}).get("data")
            if not dados:
                continue
            try:
                base64.b64decode(dados, validate=True)
            except (binascii.Error, ValueError):
                raise UserError(_("Ficheiro de imagem inválido: %s",
                                  (foto or {}).get("name") or indice))
            nome = (foto.get("name") or "").strip() or _("Embalagem %s.jpg", indice)
            criados |= self.env["ir.attachment"].create({
                "name": nome,
                "datas": dados,
                "res_model": "mrp.production",
                "res_id": self.id,
                # Marca que permite distinguir estas fotografias dos restantes anexos.
                "description": MARCADOR_FOTO,
            })
        return len(criados)
