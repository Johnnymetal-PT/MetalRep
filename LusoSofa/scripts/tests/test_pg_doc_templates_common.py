import unittest
import unicodedata
from types import SimpleNamespace
from unittest.mock import patch

from scripts import pg_doc_templates_common as mod


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


# Resultados partilhados pelos dois transportes. O que difere e o envelope: em JSON-2 o corpo
# da resposta E o resultado; em JSON-RPC vem dentro de {"result": ...}.
RESULTADOS = {
    ("ir.model.data", "search_read"): [{"res_id": 321}],
    ("knowledge.article", "fields_get"): {"body": {"type": "html"}, "pg_template_body_md": {"type": "text"}},
    ("knowledge.article", "search_read"): [
        {
            "id": 10,
            "pg_template_code": "TPL_A",
            "pg_template_version": "1.2.3",
            "pg_template_state": "published",
            "pg_template_body_md": "",
            "body": "<h1>Titulo</h1><p>Texto</p>",
            "write_uid": [1, "Admin"],
            "write_date": "2026-05-26 10:00:00",
        },
        {
            "id": 11,
            "pg_template_code": "TPL_B",
            "pg_template_version": "1.0.0",
            "pg_template_state": "draft",
            "pg_template_body_md": "draft",
            "body": "<p>draft</p>",
            "write_uid": [1, "Admin"],
            "write_date": "2026-05-26 10:00:01",
        },
    ],
    ("ir.attachment", "search_read"): [
        {
            "id": 99,
            "name": "asset.png",
            "datas": "Zm9v",
            "mimetype": "image/png",
            "checksum": "abc",
            "write_date": "2026-05-26 11:00:00",
        }
    ],
}


def _resultado_por_url(url):
    for (model, metodo), valor in RESULTADOS.items():
        if f"/{model}/{metodo}" in url:
            return valor
    raise AssertionError(f"URL inesperado: {url}")


class FakeSession:
    """Fake do transporte JSON-2 (a via principal).

    Aceita `headers` de proposito: sem esse parametro, a chamada de _call_json2 rebentava
    com TypeError, o call_kw engolia a excepcao e todos estes testes acabavam a exercitar
    o fallback JSON-RPC sem que nada o dissesse. A assercao de URL abaixo garante que uma
    queda silenciosa para o fallback volta a falhar o teste em vez de passar disfarcada.
    """

    def __init__(self):
        self.headers = {}
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        if "/json/2/" not in url:
            raise AssertionError(f"O transporte JSON-2 nao devia chamar {url}")
        return FakeResponse(_resultado_por_url(url))


class PgDocTemplatesCommonTests(unittest.TestCase):
    @patch("scripts.pg_doc_templates_common.requests", new=SimpleNamespace(Session=lambda: FakeSession()))
    def test_fetch_published_articles_uses_native_body_with_fallback(self):
        rows = mod.fetch_published_articles(
            base_url="https://odoo.example.com",
            database="db",
            login="user@example.com",
            api_key="token",
            workspace_xmlid="pg_doc_templates.workspace_doc_templates",
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["pg_template_code"], "TPL_A")
        self.assertEqual(rows[0]["pg_template_state"], "published")
        self.assertIn("# Titulo", rows[0]["pg_template_body_md"])
        self.assertEqual(rows[0]["pg_template_body_source"], "knowledge.article.body")

    @patch("scripts.pg_doc_templates_common.requests", new=SimpleNamespace(Session=lambda: FakeSession()))
    def test_fetch_attachments_for_article(self):
        mod.fetch_published_articles(
            base_url="https://odoo.example.com",
            database="db",
            login="user@example.com",
            api_key="token",
            workspace_xmlid="pg_doc_templates.workspace_doc_templates",
        )

        attachments = mod.fetch_attachments(10)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0]["name"], "asset.png")



    def test_normalize_native_body_uses_nfc(self):
        decomposed = "Cafe\u0301"
        normalized = mod._normalize_native_body(decomposed)
        self.assertEqual(normalized, unicodedata.normalize("NFC", decomposed))
        self.assertEqual(normalized, "Café")


class FakeJsonRpcSession:
    """Fake do transporte JSON-RPC: despacha por service/method do payload."""

    def __init__(self):
        self.headers = {}
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json})
        if url.endswith("/web/session/authenticate"):
            raise AssertionError("O login de sessao web nao aceita chaves de API; ver _authenticate.")
        if not url.endswith("/jsonrpc"):
            raise AssertionError(f"URL inesperado no transporte JSON-RPC: {url}")

        params = json["params"]
        if params["service"] == "common" and params["method"] == "authenticate":
            return FakeResponse({"result": 7})
        if params["service"] == "object" and params["method"] == "execute_kw":
            _db, uid, _key, model, metodo = params["args"][:5]
            if uid != 7:
                raise AssertionError(f"uid da autenticacao nao foi reutilizado: {uid}")
            return FakeResponse({"result": RESULTADOS[(model, metodo)]})
        raise AssertionError(f"Chamada inesperada: {params}")


class TransporteJsonRpcTests(unittest.TestCase):
    """O fallback JSON-RPC autenticava em /web/session/authenticate, que rejeita chaves de
    API com AccessDenied: nunca funcionou, e por isso qualquer falha transitoria da via
    JSON-2 derrubava o pull inteiro. Estes testes travam a regressao."""

    def setUp(self):
        self.session = FakeJsonRpcSession()
        patcher = patch("scripts.pg_doc_templates_common.requests", new=SimpleNamespace(Session=lambda: self.session))
        patcher.start()
        self.addCleanup(patcher.stop)

    def _pull(self):
        return mod.fetch_published_articles(
            base_url="https://odoo.example.com",
            database="db",
            login="user@example.com",
            api_key="token",
            workspace_xmlid="pg_doc_templates.workspace_doc_templates",
            transport="jsonrpc",
        )

    def test_devolve_articles_pelo_transporte_jsonrpc(self):
        rows = self._pull()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["pg_template_code"], "TPL_A")

    def test_autentica_no_servico_common_e_nao_na_sessao_web(self):
        self._pull()
        primeira = self.session.calls[0]
        self.assertTrue(primeira["url"].endswith("/jsonrpc"))
        self.assertEqual(primeira["json"]["params"]["service"], "common")
        self.assertEqual(primeira["json"]["params"]["method"], "authenticate")

    def test_reutiliza_o_uid_em_vez_de_autenticar_a_cada_chamada(self):
        self._pull()
        mod.fetch_attachments(10)
        autenticacoes = [c for c in self.session.calls if c["json"]["params"]["method"] == "authenticate"]
        self.assertEqual(len(autenticacoes), 1)


if __name__ == "__main__":
    unittest.main()
