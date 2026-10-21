# Copyright 2024 HMD
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
import logging

from markupsafe import Markup

from odoo import fields, models
from odoo.http import request
from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    website_gallery_html = fields.Html(
        string="Website Gallery HTML",
        sanitize=False,
        translate=html_translate,
        help=(
            "Custom gallery content rendered on the website product page. "
            "Leave empty to display images from the product gallery field."
        ),
    )

    def write(self, vals):
        """Allow website editors to persist gallery changes without product rights."""
        if self.env.context.get("skip_gallery_html"):
            _logger.debug(
                "Skipping gallery write for templates %s via context flag", self.ids
            )
            return super().write(vals)
        vals = dict(vals or {})
        gallery_present = "website_gallery_html" in vals
        gallery_value = vals.pop("website_gallery_html") if gallery_present else None
        _logger.info(
            "Product gallery write invoked",
            extra={
                "template_ids": self.ids,
                "gallery_present": gallery_present,
                "current_user": self.env.user.id,
                "context": dict(self.env.context),
            },
        )
        target = self
        if (
            gallery_present
            and self.env.user.has_group("website.group_website_publisher")
            and not self.env.user.has_group("product.group_product_manager")
        ):
            _logger.info("Elevating gallery write with sudo for templates %s", self.ids)
            target = self.sudo()
        res = True
        if vals:
            _logger.debug(
                "Writing non-gallery values %s on product templates %s", vals, target.ids
            )
            res = super(ProductTemplate, target).write(vals)
        if gallery_present:
            _logger.info(
                "Persisting website_gallery_html for templates %s (length=%s)",
                target.ids,
                len(gallery_value or ""),
            )
            super(ProductTemplate, target.with_context(skip_gallery_html=True)).write(
                {"website_gallery_html": gallery_value}
            )
        _logger.debug(
            "Product gallery write finished for templates %s with result %s",
            target.ids,
            res,
        )
        return res

    # ---------- Gallery helpers ----------
    def _get_gallery_images_for_template(self):
        """Return metadata for gallery images for the current template(s)."""
        binary_fields_priority = (
            "image_1920",
            "image_1024",
            "image_512",
            "image_256",
            "image_128",
            "image",
            "datas",
        )
        attachment_model = self.env["ir.attachment"]
        gallery_data_per_template = {}
        for template in self.sudo():
            gallery_records = getattr(
                template, "x_studio_product_images", attachment_model.browse()
            )
            if not gallery_records:
                gallery_data_per_template[template.id] = []
                continue
            product_gallery = []
            for record in gallery_records.sudo():
                field_name = next(
                    (f for f in binary_fields_priority if f in record._fields),
                    False,
                )
                if not field_name:
                    continue
                try:
                    binary_value = record[field_name]
                except KeyError:
                    continue
                if not binary_value:
                    continue
                product_gallery.append(
                    {
                        "product_id": template.id,
                        "src": "/web/image/%s/%s/%s"
                        % (record._name, record.id, field_name),
                        "alt": record.name or "",
                        "mimetype": getattr(record, "mimetype", False) or False,
                    }
                )
            gallery_data_per_template[template.id] = product_gallery
        return gallery_data_per_template

    def _get_all_gallery_images_for_website(self):
        """Return metadata for every gallery image grouped by product template."""
        images_map = self.env["product.template"]._get_gallery_images_for_template()
        all_gallery = []
        for product_id, images in images_map.items():
            for image in images:
                image_copy = dict(image)
                image_copy.setdefault("product_id", product_id)
                all_gallery.append(image_copy)
        return all_gallery

    def _get_default_gallery_markup(self):
        """Very plain 4-column grid; archaic & Studio friendly."""
        return Markup("""
            <div class="col-6 col-lg-3"><p class="mb-0"><img class="img img-fluid rounded" src="/web/image/website.s_key_images_default_image_1" loading="lazy"/></p></div>
            <div class="col-6 col-lg-3"><p class="mb-0"><img class="img img-fluid rounded" src="/web/image/website.s_key_images_default_image_2" loading="lazy"/></p></div>
            <div class="col-6 col-lg-3"><p class="mb-0"><img class="img img-fluid rounded" src="/web/image/website.s_key_images_default_image_3" loading="lazy"/></p></div>
            <div class="col-6 col-lg-3"><p class="mb-0"><img class="img img-fluid rounded" src="/web/image/website.s_key_images_default_image_4" loading="lazy"/></p></div>
        """)

    def ensure_gallery_html_populated(self):
        """Populate the HTML once for website publishers if empty."""
        for tmpl in self:
            if tmpl.website_gallery_html:
                continue
            try:
                if self.env.user.has_group("website.group_website_publisher"):
                    default_html = str(self._get_default_gallery_markup())
                    tmpl.sudo().write({"website_gallery_html": default_html})
                    _logger.info("Auto-populated website_gallery_html for template %s", tmpl.id)
            except Exception:
                _logger.debug("Skipping gallery autopopulate for %s", tmpl.id)

    def _get_gallery_html_for_website(self):
        """Return the gallery HTML; auto-populate field on first edit session."""
        self.ensure_one()
        html = self.website_gallery_html
        if html:
            _logger.debug(
                "Using stored gallery HTML for template %s (length=%s)",
                self.id,
                len(html),
            )
            return Markup(html)
        _logger.info(
            "Gallery HTML missing for template %s, generating default markup",
            self.id,
        )
        default_markup = self._get_default_gallery_markup()
        if not default_markup:
            _logger.debug(
                "No default gallery markup generated for template %s", self.id
            )
            return Markup("")
        default_str = str(default_markup)
        # Only persist on first time if editor is open and user can edit
        should_persist = False
        try:
            website = getattr(request, "website", None)
            editor_active = False
            if website:
                # Odoo 18 has website.is_editor()
                is_editor_attr = getattr(website, "is_editor", None)
                editor_active = bool(is_editor_attr()) if callable(is_editor_attr) else bool(is_editor_attr)
            if not editor_active:
                # Fallback checks
                req_flag = getattr(request, "is_frontend_editor", None)
                editor_active = bool(req_flag()) if callable(req_flag) else bool(req_flag)
            if editor_active:
                should_persist = request.env.user.has_group(
                    "website.group_website_publisher"
                )
        except Exception:
            should_persist = False
        if should_persist:
            _logger.info(
                "Auto-populating gallery HTML for template %s (length=%s)",
                self.id,
                len(default_str),
            )
            self.with_context(skip_gallery_html=True).sudo().write(
                {"website_gallery_html": default_str}
            )
        else:
            _logger.debug(
                "Returning default markup for template %s without persisting", self.id
            )
        return Markup(default_str)
