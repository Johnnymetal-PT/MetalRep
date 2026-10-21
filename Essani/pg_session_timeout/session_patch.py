"""Patch de arranque que sincroniza o max-age do cookie de sessao com o parametro de inatividade."""
import logging

from odoo import http


_logger = logging.getLogger(__name__)


def get_session_max_inactivity(env):
    if not env or not env.cr or env.cr.closed:
        return http.SESSION_LIFETIME
    try:
        icp = env["ir.config_parameter"].sudo()
        value = icp.get_param("sessions.max_inactivity_seconds", http.SESSION_LIFETIME)
        return int(value)
    except (TypeError, ValueError):
        _logger.warning(
            "Invalid value for 'sessions.max_inactivity_seconds', using default value."
        )
        return http.SESSION_LIFETIME


def _patch_http_request():
    if not hasattr(http, "HttpRequest"):
        return

    original = http.HttpRequest._save_session

    def _save_session_patched(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        try:
            session = getattr(self, "session", None)
            response = getattr(self, "future_response", None)
            if session and response:
                response.set_cookie(
                    "session_id",
                    session.sid,
                    max_age=get_session_max_inactivity(self.env),
                    httponly=True,
                )
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "pg_session_timeout: failed to reset session cookie max_age"
            )
        return result

    http.HttpRequest._save_session = _save_session_patched


def _patch_web_authenticate():
    try:
        from odoo.addons.web.controllers import session as session_controller
    except Exception:  # pragma: no cover - module not available
        return

    if not hasattr(session_controller, "Session"):
        return

    original = session_controller.Session.authenticate

    def authenticate_patched(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        try:
            request = http.request
            if request and request.session and request.future_response:
                request.future_response.set_cookie(
                    "session_id",
                    request.session.sid,
                    max_age=get_session_max_inactivity(request.env),
                    httponly=True,
                )
        except Exception:  # pragma: no cover - defensive
            _logger.exception(
                "pg_session_timeout: failed to reset session cookie max_age after login"
            )
        return result

    session_controller.Session.authenticate = authenticate_patched


def post_load():
    # Expose helper on odoo.http for other code paths and parity with upstream
    if not hasattr(http, "get_session_max_inactivity"):
        http.get_session_max_inactivity = get_session_max_inactivity

    _patch_http_request()
    _patch_web_authenticate()
