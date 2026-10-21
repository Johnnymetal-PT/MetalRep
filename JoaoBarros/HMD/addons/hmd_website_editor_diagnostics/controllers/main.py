import base64
import json
import os

from odoo import http
from odoo.http import request


STANDARD_VIEW_MODULE_PREFIXES = (
    "base",
    "web",
    "web_editor",
    "portal",
    "mail",
    "website",
    "website_sale",
    "theme_",
)

SUSPICIOUS_ARCH_PATTERNS = (
    "<script",
    "<style",
    "display:none",
    "visibility:hidden",
    "o_main_navbar",
    "o_frontend_to_backend_nav",
    "o_we_",
    "html/css",
    "editor",
)

SUSPICIOUS_TEXT_PATTERNS = (
    "display:none",
    "display: none",
    "visibility:hidden",
    "visibility: hidden",
    "o_main_navbar",
    "o_frontend_to_backend_nav",
    "o_we_",
    "edit",
    "editor",
    "html/css",
    "pointer-events:none",
    "pointer-events: none",
    ".o_edit_website_container",
    ".o_frontend_to_backend_nav",
)


class HmdWebsiteEditorDiagnosticsController(http.Controller):
    def _safe_has_group(self, xmlid):
        try:
            return request.env.user.has_group(xmlid)
        except Exception:
            return None

    def _normalize_path(self, raw_path):
        path = (raw_path or "/").strip()
        if not path:
            return "/"
        if not path.startswith("/"):
            path = "/" + path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        return path or "/"

    def _path_variants(self, path):
        if path == "/":
            return ["/"]
        return [path, path + "/"]

    def _get_xmlid(self, record):
        xmlid_map = record.get_external_id()
        return xmlid_map.get(record.id) or False

    def _preview_text(self, value, limit=220):
        text = (value or "").strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."

    def _find_hits(self, text, patterns):
        text_lower = (text or "").lower()
        return [pattern for pattern in patterns if pattern in text_lower]

    def _looks_textual(self, mimetype=None, name=None, path=None):
        raw = " ".join(filter(None, [mimetype or "", name or "", path or ""])).lower()
        return any(
            marker in raw
            for marker in (
                "text/",
                "javascript",
                "ecmascript",
                "json",
                "css",
                "scss",
                ".js",
                ".css",
                ".scss",
                ".xml",
                ".html",
            )
        )

    def _decode_attachment_preview(self, attachment):
        if attachment.type == "url":
            return {
                "full_content": attachment.url or "",
                "preview": attachment.url or "",
                "hits": self._find_hits(attachment.url or "", SUSPICIOUS_TEXT_PATTERNS),
            }

        preview = ""
        if "raw" in attachment._fields and attachment.raw:
            raw_value = attachment.raw
            if isinstance(raw_value, bytes):
                preview = raw_value.decode("utf-8", errors="replace")
            else:
                preview = str(raw_value)
        elif "datas" in attachment._fields and attachment.datas:
            try:
                preview = base64.b64decode(attachment.datas).decode("utf-8", errors="replace")
            except Exception:
                preview = ""

        return {
            "full_content": preview,
            "preview": self._preview_text(preview, limit=400),
            "hits": self._find_hits(preview, SUSPICIOUS_TEXT_PATTERNS),
        }

    def _classify_view_source(self, view, xmlid):
        if not view.arch_fs:
            return "db_only"
        module_name = (xmlid or "").split(".", 1)[0]
        if module_name.startswith(STANDARD_VIEW_MODULE_PREFIXES):
            return "standard"
        return "custom_module"

    def _view_payload(self, view):
        xmlid = self._get_xmlid(view)
        arch_text = ""
        for field_name in ("arch_db", "arch"):
            if field_name in view._fields:
                arch_text = view[field_name] or ""
                if arch_text:
                    break
        arch_text_lower = arch_text.lower()
        return {
            "id": view.id,
            "name": view.name,
            "xml_id": xmlid,
            "key": view.key,
            "active": bool(view.active),
            "priority": view.priority,
            "mode": view.mode,
            "type": view.type,
            "website_id": view.website_id.id if "website_id" in view._fields and view.website_id else False,
            "website_name": view.website_id.name if "website_id" in view._fields and view.website_id else False,
            "arch_fs": view.arch_fs or False,
            "source": self._classify_view_source(view, xmlid),
            "inherit_id": view.inherit_id.id if view.inherit_id else False,
            "inherit_name": view.inherit_id.name if view.inherit_id else False,
            "inherit_key": view.inherit_id.key if view.inherit_id else False,
            "suspicious_hits": [
                pattern for pattern in SUSPICIOUS_ARCH_PATTERNS if pattern in arch_text_lower
            ],
            "arch_preview": self._preview_text(arch_text),
        }

    def _page_payload(self, page):
        view_xmlid = self._get_xmlid(page.view_id) if "view_id" in page._fields and page.view_id else False
        payload = {
            "id": page.id,
            "name": page.name,
            "url": page.url,
            "website_id": page.website_id.id if "website_id" in page._fields and page.website_id else False,
            "website_name": page.website_id.name if "website_id" in page._fields and page.website_id else False,
            "view_id": page.view_id.id if "view_id" in page._fields and page.view_id else False,
            "view_name": page.view_id.name if "view_id" in page._fields and page.view_id else False,
            "view_key": page.view_id.key if "view_id" in page._fields and page.view_id else False,
            "view_active": bool(page.view_id.active) if "view_id" in page._fields and page.view_id else False,
            "view_xml_id": view_xmlid,
            "view_arch_fs": page.view_id.arch_fs if "view_id" in page._fields and page.view_id else False,
            "view_source": self._classify_view_source(page.view_id, view_xmlid) if "view_id" in page._fields and page.view_id else False,
            "published": "-",
        }
        for field_name in ("is_published", "website_published"):
            if field_name in page._fields:
                payload[field_name] = bool(page[field_name])
                payload["published"] = bool(page[field_name])
        return payload

    def _find_page_candidates(self, website, target_path):
        Page = request.env["website.page"].sudo()
        domain = [("url", "in", self._path_variants(target_path))]
        pages = Page.search(domain, order="website_id, id")
        if "website_id" in Page._fields:
            pages = pages.filtered(lambda p: not p.website_id or p.website_id == website)
        return pages

    def _find_extension_views(self, root_view, website):
        View = request.env["ir.ui.view"].sudo()
        domain = [
            ("inherit_id", "=", root_view.id),
            ("mode", "=", "extension"),
            ("active", "=", True),
        ]
        if "website_id" in View._fields:
            domain.append(("website_id", "in", [False, website.id]))
        views = View.search(domain, order="priority, id")
        return [self._view_payload(view) for view in views]

    def _find_layout_views(self, website):
        layout_view = request.env.ref("website.layout", raise_if_not_found=False)
        if not layout_view:
            return []
        return self._find_extension_views(layout_view, website)

    def _find_website_groups(self, user):
        Group = request.env["res.groups"].sudo()
        groups = Group.search([("category_id.name", "=", "Website")], order="name, id")
        payload = []
        for group in groups:
            xmlid = self._get_xmlid(group)
            payload.append(
                {
                    "id": group.id,
                    "name": group.name,
                    "full_name": group.full_name if "full_name" in group._fields else group.display_name,
                    "xml_id": xmlid,
                    "user_member": user in group.users,
                }
            )
        return payload

    def _find_custom_code_fields(self, record, field_names):
        payload = []
        for field_name in field_names:
            if field_name not in record._fields:
                continue
            value = record[field_name]
            if not value:
                continue
            text_value = value if isinstance(value, str) else str(value)
            payload.append(
                {
                    "field": field_name,
                    "length": len(text_value),
                    "preview": self._preview_text(text_value),
                }
            )
        return payload

    def _find_website_custom_code(self, website):
        return self._find_custom_code_fields(
            website,
            (
                "custom_code_head",
                "custom_code_footer",
                "custom_code",
                "custom_code_css",
                "custom_code_scss",
                "custom_code_js",
                "custom_javascript",
                "custom_css",
            ),
        )

    def _find_suspicious_db_views(self, website, active_page_view):
        View = request.env["ir.ui.view"].sudo()
        domain = [
            ("active", "=", True),
            ("type", "=", "qweb"),
            ("arch_fs", "=", False),
        ]
        if "website_id" in View._fields:
            domain.append(("website_id", "in", [False, website.id]))
        views = View.search(domain, order="priority, id")
        payload = []
        root_ids = []
        if active_page_view:
            root_ids.append(active_page_view.id)
        layout_view = request.env.ref("website.layout", raise_if_not_found=False)
        if layout_view:
            root_ids.append(layout_view.id)

        for view in views:
            view_payload = self._view_payload(view)
            if not view_payload["suspicious_hits"]:
                continue
            if root_ids and view.inherit_id and view.inherit_id.id in root_ids:
                view_payload["scope"] = "matched_root"
            elif (view.key or "").startswith("website."):
                view_payload["scope"] = "website_key"
            else:
                view_payload["scope"] = "other"
            payload.append(view_payload)
        return payload

    def _find_ir_assets(self, website):
        if "ir.asset" not in request.env:
            return []
        Asset = request.env["ir.asset"].sudo()
        domain = [("active", "=", True)]
        if "website_id" in Asset._fields:
            domain.append(("website_id", "in", [False, website.id]))
        assets = Asset.search(domain, order="bundle, sequence, id")
        payload = []
        for asset in assets:
            row = {
                "id": asset.id,
                "name": asset.name if "name" in asset._fields else False,
                "bundle": asset.bundle if "bundle" in asset._fields else False,
                "directive": asset.directive if "directive" in asset._fields else False,
                "path": asset.path if "path" in asset._fields else False,
                "target": asset.target if "target" in asset._fields else False,
                "website_id": asset.website_id.id if "website_id" in asset._fields and asset.website_id else False,
                "website_name": asset.website_id.name if "website_id" in asset._fields and asset.website_id else False,
            }
            path_terms = []
            for value in (row["path"], row["target"]):
                if value:
                    path_terms.append(value)
                    path_terms.append(os.path.basename(value))

            attachment_payloads = []
            if path_terms:
                Attachment = request.env["ir.attachment"].sudo()
                attachment_matches = Attachment.browse()
                search_fields = ("url", "name", "store_fname")
                for field_name in search_fields:
                    if field_name not in Attachment._fields:
                        continue
                    for term in {term for term in path_terms if term}:
                        attachment_matches |= Attachment.search([(field_name, "=", term)])

                seen = set()
                for attachment in attachment_matches:
                    if attachment.id in seen:
                        continue
                    seen.add(attachment.id)
                    preview_info = {"preview": "", "hits": []}
                    if self._looks_textual(
                        mimetype=getattr(attachment, "mimetype", False),
                        name=attachment.name,
                        path=getattr(attachment, "url", False),
                    ):
                        preview_info = self._decode_attachment_preview(attachment)

                    attachment_payloads.append(
                        {
                            "id": attachment.id,
                            "name": attachment.name,
                            "type": attachment.type,
                            "mimetype": getattr(attachment, "mimetype", False) or False,
                            "url": getattr(attachment, "url", False) or False,
                            "full_content": preview_info["full_content"],
                            "preview": preview_info["preview"],
                            "hits": preview_info["hits"],
                        }
                    )

            row["attachments"] = attachment_payloads
            row["attachment_count"] = len(attachment_payloads)
            row["content_hits"] = sorted(
                {
                    hit
                    for attachment_payload in attachment_payloads
                    for hit in attachment_payload["hits"]
                }
            )
            row["content_preview"] = next(
                (
                    attachment_payload["preview"]
                    for attachment_payload in attachment_payloads
                    if attachment_payload["preview"]
                ),
                "",
            )
            if not row["path"] or row["directive"] in ("replace", "remove"):
                payload.append(row)
        return payload

    def _find_custom_modules(self):
        Module = request.env["ir.module.module"].sudo()
        modules = Module.search(
            [
                ("state", "=", "installed"),
                "|",
                ("name", "=like", "hmd_%"),
                ("name", "=like", "pg_%"),
            ],
            order="name",
        )
        payload = []
        for module in modules:
            dependency_names = sorted(module.dependencies_id.mapped("name"))
            if not any(name in ("website", "website_sale", "website_sale_stock", "web_editor") for name in dependency_names):
                continue
            payload.append(
                {
                    "name": module.name,
                    "display_name": module.shortdesc or module.name,
                    "state": module.state,
                    "dependencies": dependency_names,
                    "dependency_text": ", ".join(dependency_names),
                }
            )
        return payload

    def _diagnose(self, target_path):
        website = request.website.sudo().get_current_website()
        user = request.env.user
        normalized_path = self._normalize_path(target_path)
        page_candidates = self._find_page_candidates(website, normalized_path)
        active_page = page_candidates[:1]
        active_page_view = active_page.view_id if active_page and active_page.view_id else False
        layout_views = self._find_layout_views(website)
        page_views = self._find_extension_views(active_page_view, website) if active_page_view else []
        website_groups = self._find_website_groups(user)
        website_custom_code = self._find_website_custom_code(website)
        suspicious_db_views = self._find_suspicious_db_views(website, active_page_view)
        ir_assets = self._find_ir_assets(website)

        groups = {
            "base.group_system": self._safe_has_group("base.group_system"),
            "base.group_user": self._safe_has_group("base.group_user"),
            "base.group_portal": self._safe_has_group("base.group_portal"),
            "website.group_website_designer": self._safe_has_group("website.group_website_designer"),
            "website.group_website_publisher": self._safe_has_group("website.group_website_publisher"),
        }

        issues = []
        if not any(group["user_member"] for group in website_groups):
            issues.append("Current user does not belong to any Website application group.")
        if not page_candidates:
            issues.append(
                "No website.page was found for this URL. That usually means the URL is served by a controller route or the page only exists as a database customization elsewhere."
            )
        if active_page and active_page_view and not active_page_view.active:
            issues.append("The matched page view exists but is inactive.")
        if active_page and active_page_view and not active_page_view.arch_fs:
            issues.append("The matched page view is database-backed instead of file-backed.")
        if any(view["source"] == "db_only" for view in layout_views):
            issues.append("There are active database-only inherits on website.layout.")
        if any(view["source"] == "db_only" for view in page_views):
            issues.append("There are active database-only inherits on the matched page view.")
        if website_custom_code:
            issues.append("This website has non-empty custom code fields stored in the database.")
        if suspicious_db_views:
            issues.append("Suspicious database-only qWeb views with script/style/editor-related code were found.")
        if ir_assets:
            issues.append("Custom ir.asset records were found that may affect frontend JS/CSS bundles.")
        if any(asset["content_hits"] for asset in ir_assets):
            issues.append("Custom asset content includes editor/topbar-related suspicious patterns.")
        if not issues:
            issues.append("No obvious server-side blocker was detected from the current metadata.")

        return {
            "target_path": normalized_path,
            "website": {
                "id": website.id,
                "name": website.name,
                "domain": website.domain or False,
            },
            "user": {
                "id": user.id,
                "name": user.name,
                "login": user.login,
                "groups": groups,
                "group_rows": [{"name": name, "state": state} for name, state in groups.items()],
            },
            "website_groups": website_groups,
            "website_custom_code": website_custom_code,
            "page_candidates": [self._page_payload(page) for page in page_candidates],
            "layout_extension_views": layout_views,
            "page_extension_views": page_views,
            "suspicious_db_views": suspicious_db_views,
            "ir_assets": ir_assets,
            "has_asset_attachments": any(asset["attachments"] for asset in ir_assets),
            "installed_custom_website_modules": self._find_custom_modules(),
            "issues": issues,
        }

    @http.route(
        "/hmd/website/editor_diagnostics",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def website_editor_diagnostics(self, path="/", **kwargs):
        diagnostic = self._diagnose(path)
        return request.render(
            "hmd_website_editor_diagnostics.report",
            {
                "diagnostic": diagnostic,
                "json_url": "/hmd/website/editor_diagnostics/json?path=%s" % diagnostic["target_path"],
            },
        )

    @http.route(
        "/hmd/website/editor_diagnostics/json",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def website_editor_diagnostics_json(self, path="/", **kwargs):
        diagnostic = self._diagnose(path)
        return request.make_response(
            json.dumps(diagnostic, indent=2, sort_keys=True),
            headers=[("Content-Type", "application/json")],
        )
