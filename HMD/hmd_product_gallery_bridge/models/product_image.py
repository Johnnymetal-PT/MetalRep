# -*- coding: utf-8 -*-
"""Espelho de `product.image` em `ir.attachment` ligado ao template.

A galeria Studio do produto vive em `product.image` (via Studio One2many
`x_studio_product_images`). Para o site reutilizar os helpers standard
de imagens, precisamos de attachments com res_model='product.template'.

Este modulo mantem em cada `product.image` um `hmd_attachment_id` que
e criado/atualizado/apagado em sincronia (create/write/unlink). A flag
de contexto `hmd_gallery_bridge_skip=True` evita recursao.

Ver `__manifest__.py` para o guia completo.
"""

import mimetypes

from odoo import api, fields, models


class ProductImage(models.Model):
    _inherit = "product.image"

    hmd_attachment_id = fields.Many2one(
        "ir.attachment",
        string="HMD Gallery Attachment",
        copy=False,
        readonly=True,
    )

    def _ensure_hmd_attachment_bridge(self):
        """Garante que existe attachment espelho e devolve-os.

        Usado pelo compute em `product.template` para nao depender de
        ser chamado via write/create.
        """
        self.sudo()._sync_hmd_attachment()
        return self.mapped("hmd_attachment_id").filtered(lambda att: att)

    def _sync_hmd_attachment(self):
        images = self.sudo()
        Attachment = self.env["ir.attachment"].sudo()
        attachments_by_template = {}
        templates_by_id = {}

        for image in images:
            attachment = image.hmd_attachment_id
            datas, mimetype = image._get_hmd_attachment_payload()
            template = image.product_tmpl_id or image.product_variant_id.product_tmpl_id

            if not template or not datas:
                if attachment:
                    attachment.sudo().unlink()
                    image.with_context(hmd_gallery_bridge_skip=True).sudo().write({"hmd_attachment_id": False})
                continue

            templates_by_id.setdefault(template.id, template)
            vals = image._prepare_hmd_attachment_vals(template, datas, mimetype)

            if attachment:
                update_vals = {
                    key: value
                    for key, value in vals.items()
                    if attachment[key] != value
                }
                if update_vals:
                    attachment.sudo().write(update_vals)
            else:
                attachment = Attachment.create(vals)
                image.with_context(hmd_gallery_bridge_skip=True).sudo().write({"hmd_attachment_id": attachment.id})

            if attachment:
                attachments_by_template.setdefault(template.id, Attachment.browse())
                attachments_by_template[template.id] |= attachment

        for template_id, attachments in attachments_by_template.items():
            template = templates_by_id.get(template_id)
            if not template or not template.company_id or not attachments:
                continue
            attachments.filtered(lambda att: att.company_id != template.company_id).sudo().write(
                {"company_id": template.company_id.id}
            )

    def _get_hmd_attachment_payload(self):
        self.ensure_one()

        candidate_fields = [
            "image_1920",
            "image_1024",
            "image_512",
            "image_256",
            "image_128",
            "image",
        ]

        datas = False
        for field in candidate_fields:
            if field in self._fields:
                value = getattr(self, field)
                if value:
                    datas = value.decode() if isinstance(value, bytes) else value
                    break

        if not datas and "attachment_id" in self._fields and self.attachment_id:
            datas = self.attachment_id.datas
            if isinstance(datas, bytes):
                datas = datas.decode()

        mimetype = False
        if "mimetype" in self._fields and self.mimetype:
            mimetype = self.mimetype
        elif "attachment_id" in self._fields and self.attachment_id and self.attachment_id.mimetype:
            mimetype = self.attachment_id.mimetype

        return datas, mimetype

    def _prepare_hmd_attachment_vals(self, template, datas, mimetype=False):
        name = (self.name or template.name or "Product Image").strip()
        if not name:
            name = template.display_name or "Product Image"

        mimetype = mimetype or mimetypes.guess_type(name, strict=False)[0] or "image/png"

        vals = {
            "name": name,
            "datas_fname": name,
            "datas": datas,
            "mimetype": mimetype,
            "res_model": "product.template",
            "res_id": template.id,
            "type": "binary",
            "public": True,
        }

        if template.company_id:
            vals["company_id"] = template.company_id.id

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        images = super().create(vals_list)
        images._sync_hmd_attachment()
        return images

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("hmd_gallery_bridge_skip"):
            self._sync_hmd_attachment()
        return res

    def unlink(self):
        attachments = self.mapped("hmd_attachment_id")
        res = super().unlink()
        attachments.sudo().unlink()
        return res
