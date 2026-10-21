import logging
import uuid
from hmac import compare_digest

from odoo import _, fields, models
from odoo.exceptions import UserError

try:
    import requests
except ImportError:
    requests = None


_logger = logging.getLogger(__name__)


class PrestashopInstance(models.Model):
    _name = "prestashop.instance"
    _description = "Prestashop CloudSync Instance"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    client_id = fields.Char(required=True)
    client_secret = fields.Char(required=True)
    oauth_url = fields.Char(
        required=True,
        default="https://oauth.prestashop.com/oauth2/token",
    )
    oauth_audience = fields.Char(
        required=True,
        default="https://api.cloudsync.prestashop.com",
        help="OAuth audience sent when requesting access token.",
    )
    oauth_scope = fields.Char(
        help="Optional OAuth scopes, space-separated.",
    )

    raw_base_url = fields.Char(
        required=True,
        default="https://api.cloudsync.prestashop.com/raw/v1",
    )
    shop_id = fields.Char(required=True, help="CloudSync shop UUID.")
    customer_page_size = fields.Integer(default=100, required=True)
    webhook_enabled = fields.Boolean(default=True)
    webhook_key = fields.Char(
        default=lambda self: uuid.uuid4().hex,
        copy=False,
        readonly=True,
    )
    webhook_secret = fields.Char(
        copy=False,
        help="Secret expected in header X-Prestashop-Webhook-Secret or Basic Auth password.",
    )
    webhook_url = fields.Char(
        compute="_compute_webhook_url",
        readonly=True,
    )

    last_customer_sync_at = fields.Datetime(readonly=True, copy=False)
    last_sync_status = fields.Selection(
        [
            ("never", "Never"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="never",
        readonly=True,
        copy=False,
    )
    last_sync_message = fields.Text(readonly=True, copy=False)

    def _compute_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "").rstrip("/")
        for record in self:
            if base_url and record.webhook_key:
                record.webhook_url = "%s/prestashop/webhook/%s" % (base_url, record.webhook_key)
            else:
                record.webhook_url = False

    def action_regenerate_webhook_key(self):
        for record in self:
            record.webhook_key = uuid.uuid4().hex

    def _check_webhook_secret(self, provided_secret):
        self.ensure_one()
        if not self.webhook_secret:
            return True
        if not provided_secret:
            return False
        return compare_digest(self.webhook_secret, provided_secret)

    def _ensure_requests(self):
        if requests is None:
            raise UserError(
                _(
                    "Python package 'requests' is required on the Odoo server "
                    "to use the Prestashop connector."
                )
            )

    def _get_access_token(self):
        self.ensure_one()
        self._ensure_requests()

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "audience": self.oauth_audience,
        }
        if self.oauth_scope:
            payload["scope"] = self.oauth_scope

        try:
            response = requests.post(
                self.oauth_url,
                data=payload,
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=45,
            )
        except requests.RequestException as exc:
            raise UserError(_("Could not reach Prestashop OAuth server: %s") % exc) from exc

        if response.status_code >= 400:
            raise UserError(
                _("Prestashop OAuth error (%s): %s")
                % (response.status_code, response.text[:600])
            )

        token = (response.json() or {}).get("access_token")
        if not token:
            raise UserError(_("Prestashop OAuth response does not contain access_token."))
        return token

    def _raw_get(self, path, token, params=None):
        self.ensure_one()
        self._ensure_requests()

        url = "%s/%s" % (self.raw_base_url.rstrip("/"), path.lstrip("/"))
        try:
            response = requests.get(
                url,
                params=params or {},
                headers={
                    "Authorization": "Bearer %s" % token,
                    "Accept": "application/json",
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            raise UserError(_("Could not reach Prestashop Raw API: %s") % exc) from exc

        if response.status_code >= 400:
            raise UserError(
                _("Prestashop Raw API error (%s): %s")
                % (response.status_code, response.text[:600])
            )
        try:
            return response.json() or {}
        except ValueError as exc:
            raise UserError(_("Prestashop Raw API returned a non-JSON response.")) from exc

    def _raw_healthcheck(self, token):
        self.ensure_one()
        self._ensure_requests()

        url = "%s/healthcheck" % self.raw_base_url.rstrip("/")
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": "Bearer %s" % token,
                    "Accept": "application/json",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            raise UserError(_("Could not reach Prestashop Raw API healthcheck: %s") % exc) from exc

        if response.status_code >= 400:
            raise UserError(
                _("Prestashop Raw API healthcheck failed (%s): %s")
                % (response.status_code, response.text[:600])
            )

    def _sync_customer_by_content_id(self, token, content_id):
        self.ensure_one()
        data = self._raw_get(
            path="%s/customers/%s" % (self.shop_id, content_id),
            token=token,
            params={},
        )
        customer = data.get("item") or {}
        if not customer:
            return 0, 0
        return self._upsert_customer(customer)

    @staticmethod
    def _first_non_empty(data, keys):
        for key in keys:
            value = data.get(key)
            if value not in (None, False, ""):
                return value
        return False

    def _prepare_partner_vals(self, customer):
        first_name = self._first_non_empty(customer, ["firstname", "firstName", "first_name"])
        last_name = self._first_non_empty(customer, ["lastname", "lastName", "last_name"])
        company_name = self._first_non_empty(customer, ["company", "companyName"])
        email = self._first_non_empty(customer, ["email", "mail"])
        phone = self._first_non_empty(customer, ["phone", "phoneNumber"])
        mobile = self._first_non_empty(customer, ["mobile", "mobilePhone"])
        vat = self._first_non_empty(customer, ["vat", "vatNumber", "taxId", "dni"])

        full_name = " ".join(part for part in [first_name, last_name] if part).strip()
        if not full_name:
            full_name = company_name or email or _("Prestashop Customer")

        vals = {
            "name": full_name,
            "email": email or False,
            "phone": phone or False,
            "mobile": mobile or False,
            "vat": vat or False,
            "is_company": bool(company_name and not (first_name or last_name)),
            "customer_rank": 1,
        }

        country_code = self._first_non_empty(
            customer,
            ["countryCode", "country_code", "countryIso", "countryISO", "country"],
        )
        if country_code:
            country = self.env["res.country"].search(
                [("code", "=", str(country_code).upper())],
                limit=1,
            )
            if country:
                vals["country_id"] = country.id

        return vals

    def _upsert_customer(self, customer):
        self.ensure_one()
        Partner = self.env["res.partner"].sudo()

        customer_id = str(
            self._first_non_empty(
                customer,
                [
                    "idCustomer",
                    "customerId",
                    "id_customer",
                    "id",
                ],
            )
            or ""
        ).strip()
        content_id = str(customer.get("id") or "").strip()

        if not customer_id:
            _logger.warning(
                "Skipping Prestashop customer without idCustomer (shop=%s, payload=%s)",
                self.shop_id,
                customer,
            )
            return 0, 0

        domain = [
            ("prestashop_shop_id", "=", self.shop_id),
            ("prestashop_customer_id", "=", customer_id),
        ]
        partner = Partner.search(domain, limit=1)

        if not partner:
            email = self._first_non_empty(customer, ["email", "mail"])
            if email:
                partner = Partner.search([("email", "=", email)], limit=1)

        vals = self._prepare_partner_vals(customer)
        vals.update(
            {
                "prestashop_shop_id": self.shop_id,
                "prestashop_customer_id": customer_id,
                "prestashop_content_id": content_id or False,
            }
        )

        if partner:
            partner.write(vals)
            return 0, 1

        vals["company_id"] = self.company_id.id
        Partner.create(vals)
        return 1, 0

    def _sync_customers(self, token=None):
        self.ensure_one()

        token = token or self._get_access_token()
        offset = 0
        page_size = max(1, self.customer_page_size)
        created = 0
        updated = 0
        processed = 0

        while True:
            data = self._raw_get(
                path="%s/customers" % self.shop_id,
                token=token,
                params={"offset": offset, "limit": page_size},
            )
            items = data.get("items") or []
            if not items:
                break

            for customer in items:
                c_count, u_count = self._upsert_customer(customer)
                created += c_count
                updated += u_count
                processed += 1

            if len(items) < page_size:
                break
            offset += page_size

        message = _("Processed %(processed)s customers. Created: %(created)s, Updated: %(updated)s.") % {
            "processed": processed,
            "created": created,
            "updated": updated,
        }

        self.write(
            {
                "last_customer_sync_at": fields.Datetime.now(),
                "last_sync_status": "success",
                "last_sync_message": message,
            }
        )
        return message

    def _payload_to_events(self, payload):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            if isinstance(payload.get("events"), list):
                return payload.get("events")
            return [payload]
        return []

    def _event_targets_customers(self, event):
        if not isinstance(event, dict):
            return False

        candidates = []
        for key in ("kind", "resource", "entity", "table", "topic", "eventType", "type"):
            value = event.get(key)
            if value:
                candidates.append(str(value).lower())

        if any("customer" in candidate for candidate in candidates):
            return True
        if self._first_non_empty(event, ["idCustomer", "id_customer", "customerId"]):
            return True
        return False

    def process_webhook_payload(self, payload):
        self.ensure_one()

        if not self.webhook_enabled:
            return _("Webhook disabled.")

        events = self._payload_to_events(payload)
        if not events:
            return _("No events found in webhook payload.")

        token = self._get_access_token()
        synced = 0
        created = 0
        updated = 0
        fallback_full_sync = False
        has_customer_event = False

        for event in events:
            if not self._event_targets_customers(event):
                continue
            has_customer_event = True

            event_shop_id = self._first_non_empty(event, ["shopId", "shop_id"])
            if event_shop_id and str(event_shop_id) != str(self.shop_id):
                continue

            shop_content_id = self._first_non_empty(event, ["shopContentId", "shop_content_id", "contentId"])
            if shop_content_id:
                c_count, u_count = self._sync_customer_by_content_id(token=token, content_id=shop_content_id)
                created += c_count
                updated += u_count
                synced += 1
            else:
                fallback_full_sync = True

        if fallback_full_sync:
            message = self._sync_customers(token=token)
            return _("Webhook processed. %s") % message

        if not has_customer_event:
            return _("Webhook ignored (no customer event).")

        message = _("Webhook processed. Targeted customers synced: %(synced)s. Created: %(created)s, Updated: %(updated)s.") % {
            "synced": synced,
            "created": created,
            "updated": updated,
        }
        self.write(
            {
                "last_customer_sync_at": fields.Datetime.now(),
                "last_sync_status": "success",
                "last_sync_message": message,
            }
        )
        return message

    def action_test_connection(self):
        for instance in self:
            token = instance._get_access_token()
            instance._raw_healthcheck(token=token)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Prestashop"),
                "message": _("Connection successful."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_sync_customers(self):
        messages = []
        for instance in self:
            try:
                sync_message = instance._sync_customers()
                messages.append("%s: %s" % (instance.name, sync_message))
            except Exception as exc:
                error_message = str(exc)
                instance.write(
                    {
                        "last_sync_status": "failed",
                        "last_sync_message": error_message,
                    }
                )
                raise UserError(
                    _("Customer sync failed for '%(instance)s': %(error)s")
                    % {"instance": instance.name, "error": error_message}
                ) from exc

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Prestashop Clients"),
                "message": "\n".join(messages),
                "type": "success",
                "sticky": False,
            },
        }
