import json
from base64 import b64decode

from odoo import http
from odoo.http import request


class PrestashopWebhookController(http.Controller):
    @staticmethod
    def _extract_secret_from_basic_auth(auth_header):
        if not auth_header or not auth_header.lower().startswith("basic "):
            return None
        encoded = auth_header.split(" ", 1)[1].strip()
        if not encoded:
            return None
        try:
            decoded = b64decode(encoded).decode("utf-8")
        except Exception:
            return None
        if ":" in decoded:
            username, password = decoded.split(":", 1)
            return password or username or None
        return decoded or None

    @http.route(
        "/prestashop/webhook/<string:webhook_key>",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def prestashop_webhook(self, webhook_key, **kwargs):
        instance = (
            request.env["prestashop.instance"]
            .sudo()
            .search([("webhook_key", "=", webhook_key), ("active", "=", True)], limit=1)
        )
        if not instance:
            body = {"ok": False, "error": "Webhook not found"}
            return request.make_response(
                json.dumps(body),
                headers=[("Content-Type", "application/json")],
                status=404,
            )

        provided_secret = request.httprequest.headers.get(
            "X-Prestashop-Webhook-Secret"
        ) or request.httprequest.headers.get("X-Webhook-Token")
        if not provided_secret:
            provided_secret = self._extract_secret_from_basic_auth(
                request.httprequest.headers.get("Authorization")
            )
        if not instance._check_webhook_secret(provided_secret):
            body = {"ok": False, "error": "Unauthorized webhook"}
            return request.make_response(
                json.dumps(body),
                headers=[("Content-Type", "application/json")],
                status=401,
            )

        raw_body = request.httprequest.get_data(cache=False, as_text=True) or ""
        if not raw_body.strip():
            body = {"ok": False, "error": "Empty payload"}
            return request.make_response(
                json.dumps(body),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        try:
            payload = json.loads(raw_body)
        except ValueError:
            body = {"ok": False, "error": "Invalid JSON payload"}
            return request.make_response(
                json.dumps(body),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        try:
            message = instance.process_webhook_payload(payload)
        except Exception as exc:
            instance.write(
                {
                    "last_sync_status": "failed",
                    "last_sync_message": str(exc),
                }
            )
            body = {"ok": False, "error": str(exc)}
            return request.make_response(
                json.dumps(body),
                headers=[("Content-Type", "application/json")],
                status=500,
            )

        body = {"ok": True, "message": message}
        return request.make_response(
            json.dumps(body),
            headers=[("Content-Type", "application/json")],
            status=200,
        )
