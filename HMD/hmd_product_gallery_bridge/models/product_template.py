# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    hmd_studio_gallery_attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Studio Gallery Attachments",
        compute="_compute_hmd_studio_gallery_attachment_ids",
        store=False,
    )

    def _get_hmd_studio_gallery_attachments(self):
        """Return the gallery attachments that should be exposed on the website."""
        self.ensure_one()

        attachments = self.hmd_studio_gallery_attachment_ids
        if attachments:
            return attachments.sudo()

        gallery_records = getattr(self, "x_studio_product_images", False)
        if not gallery_records:
            return self.env["ir.attachment"].browse()

        return self._map_hmd_gallery_records_to_attachments(gallery_records.sudo())

    def _map_hmd_gallery_records_to_attachments(self, gallery_records):
        Attachment = self.env["ir.attachment"].sudo()
        attachments = Attachment.browse()

        if not gallery_records:
            return attachments

        if gallery_records._name == "ir.attachment":
            return gallery_records

        if hasattr(gallery_records, "_ensure_hmd_attachment_bridge"):
            return gallery_records._ensure_hmd_attachment_bridge()

        collected = Attachment.browse()
        if "hmd_attachment_id" in gallery_records._fields:
            collected |= gallery_records.mapped("hmd_attachment_id")
        if "attachment_id" in gallery_records._fields:
            collected |= gallery_records.mapped("attachment_id")

        return collected.filtered(lambda att: att)

    def _extract_hmd_gallery_image_data(self, record):
        data_fields = [
            "image_1920",
            "image_1024",
            "image_512",
            "image_256",
            "image_128",
            "image",
        ]

        for field in data_fields:
            if field in record._fields:
                value = getattr(record, field)
                if value:
                    if isinstance(value, bytes):
                        value = value.decode()
                    mimetype = False
                    if "mimetype" in record._fields and record.mimetype:
                        mimetype = record.mimetype
                    return value, mimetype

        if "attachment_id" in record._fields and record.attachment_id and record.attachment_id.datas:
            datas = record.attachment_id.datas
            if isinstance(datas, bytes):
                datas = datas.decode()
            mimetype = record.attachment_id.mimetype or False
            return datas, mimetype

        return False, False

    def _prepare_hmd_gallery_item_from_attachment(self, attachment, original, website, alt):
        attachment = attachment.sudo()
        original = (original or attachment).sudo()

        def _get_dimensions(record):
            width = getattr(record, "image_width", False) or getattr(record, "width", False)
            height = getattr(record, "image_height", False) or getattr(record, "height", False)
            return width or False, height or False

        mimetype = attachment.mimetype or original.mimetype or "image/png"
        original_mimetype = original.mimetype or mimetype
        width, height = _get_dimensions(attachment)
        original_width, original_height = _get_dimensions(original)

        title = attachment.name or alt

        def _image_url(record):
            url = False
            if website:
                url = website.image_url(record, "datas")
            if not url:
                url = record.website_url or False
            if not url:
                url = "/web/image/%s/%s/%s" % (record._name, record.id, "datas")
            return url

        attachment_src = _image_url(attachment)
        original_src = _image_url(original) or attachment_src

        return {
            "attachment": attachment,
            "original_attachment": original,
            "src": attachment_src,
            "original_src": original_src,
            "alt": title,
            "title": title,
            "mimetype": mimetype,
            "mimetype_before_conversion": original_mimetype,
            "width": width,
            "height": height,
            "original_width": original_width,
            "original_height": original_height,
        }

    def _get_hmd_studio_gallery_items(self):
        self.ensure_one()

        website = self.env["website"].sudo().get_current_website()
        attachments = self._get_hmd_studio_gallery_attachments().sudo()
        items = []

        if attachments:
            for attachment in attachments:
                if not attachment:
                    continue
                original = attachment.original_id or attachment
                items.append(
                    self._prepare_hmd_gallery_item_from_attachment(
                        attachment,
                        original,
                        website,
                        self.display_name,
                    )
                )
            return items

        gallery_records = getattr(self, "x_studio_product_images", False)
        if not gallery_records:
            return items

        gallery_records = gallery_records.sudo()
        for record in gallery_records:
            attachment = False
            original = False
            src = False
            alt = getattr(record, "name", False) or self.display_name

            if record._name == "ir.attachment":
                attachment = record
            elif "hmd_attachment_id" in record._fields and record.hmd_attachment_id:
                attachment = record.hmd_attachment_id
            elif "attachment_id" in record._fields and record.attachment_id:
                attachment = record.attachment_id

            if attachment:
                attachment = attachment.sudo()
                original = attachment.original_id or attachment
                items.append(
                    self._prepare_hmd_gallery_item_from_attachment(
                        attachment,
                        original,
                        website,
                        alt,
                    )
                )
                continue

            datas, mimetype = self._extract_hmd_gallery_image_data(record)
            if not datas:
                continue

            mimetype = mimetype or "image/png"
            src = "data:%s;base64,%s" % (mimetype, datas)
            items.append(
                {
                    "attachment": False,
                    "original_attachment": False,
                    "src": src,
                    "original_src": src,
                    "alt": alt,
                    "title": alt,
                    "mimetype": mimetype,
                    "mimetype_before_conversion": mimetype,
                    "width": getattr(record, "image_width", False) or False,
                    "height": getattr(record, "image_height", False) or False,
                    "original_width": getattr(record, "image_width", False) or False,
                    "original_height": getattr(record, "image_height", False) or False,
                }
            )

        return items

    @api.depends(
        "x_studio_product_images",
        "x_studio_product_images.image_1920",
        "x_studio_product_images.hmd_attachment_id",
    )
    def _compute_hmd_studio_gallery_attachment_ids(self):
        IrAttachment = self.env["ir.attachment"]
        for template in self:
            gallery_records = getattr(template, "x_studio_product_images", False)
            attachments = IrAttachment.browse()

            if gallery_records:
                model_name = gallery_records._name
                if model_name == "product.image":
                    attachments = gallery_records._ensure_hmd_attachment_bridge()
                elif model_name == "ir.attachment":
                    attachments = gallery_records

            attachments = attachments.filtered(lambda att: att)

            if attachments:
                dangling = attachments.filtered(
                    lambda att: att.res_model != "product.template" or att.res_id != template.id
                )
                if dangling:
                    dangling.sudo().write({"res_model": "product.template", "res_id": template.id})

            template.hmd_studio_gallery_attachment_ids = attachments

