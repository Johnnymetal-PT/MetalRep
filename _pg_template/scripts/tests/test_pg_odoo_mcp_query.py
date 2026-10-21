import json
import unittest
from unittest.mock import MagicMock, patch

from scripts import pg_odoo_mcp_query as mcp_mod


class TestPgOdooMcpQuery(unittest.TestCase):
    def test_normalize_mcp_url(self):
        self.assertEqual(
            mcp_mod.normalize_mcp_url("https://example.odoo.com"),
            "https://example.odoo.com/mcp",
        )
        self.assertEqual(
            mcp_mod.normalize_mcp_url("https://example.odoo.com/"),
            "https://example.odoo.com/mcp",
        )
        self.assertEqual(
            mcp_mod.normalize_mcp_url("https://example.odoo.com/odoo"),
            "https://example.odoo.com/mcp",
        )
        self.assertEqual(
            mcp_mod.normalize_mcp_url("https://example.odoo.com/mcp"),
            "https://example.odoo.com/mcp",
        )

    def test_parse_list_arg(self):
        self.assertIsNone(mcp_mod.parse_list_arg(None))
        self.assertEqual(mcp_mod.parse_list_arg("a,b,c"), ["a", "b", "c"])
        self.assertEqual(mcp_mod.parse_list_arg('["x", "y"]'), ["x", "y"])
        self.assertEqual(mcp_mod.parse_list_arg(" name , stage_id "), ["name", "stage_id"])

    @patch("urllib.request.urlopen")
    def test_mcp_initialize(self, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Odoo", "version": "1.0.0"},
            },
        }).encode("utf-8")
        fake_resp.__enter__.return_value = fake_resp
        mock_urlopen.return_value = fake_resp

        client = mcp_mod.OdooMcpClient("https://test.odoo.com", "fake_key")
        init_data = client.initialize()

        self.assertEqual(init_data["protocolVersion"], "2024-11-05")
        self.assertEqual(init_data["serverInfo"]["name"], "Odoo")

    @patch("urllib.request.urlopen")
    def test_mcp_search(self, mock_urlopen):
        fake_leads = [
            {"id": 1, "name": "Lead Test", "stage_id": [1, "New"]},
            {"id": 2, "name": "Lead 2", "stage_id": [2, "Qualified"]},
        ]
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": json.dumps(fake_leads)}],
                "isError": False,
            },
        }).encode("utf-8")
        fake_resp.__enter__.return_value = fake_resp
        mock_urlopen.return_value = fake_resp

        client = mcp_mod.OdooMcpClient("https://test.odoo.com", "fake_key")
        leads = client.search("crm.lead", domain='[["stage_id","=",1]]', fields=["name", "stage_id"])

        self.assertEqual(len(leads), 2)
        self.assertEqual(leads[0]["name"], "Lead Test")

    @patch("urllib.request.urlopen")
    def test_mcp_call_tool_error(self, mock_urlopen):
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [{"type": "text", "text": "Access Denied to model crm.lead"}],
                "isError": True,
            },
        }).encode("utf-8")
        fake_resp.__enter__.return_value = fake_resp
        mock_urlopen.return_value = fake_resp

        client = mcp_mod.OdooMcpClient("https://test.odoo.com", "fake_key")
        with self.assertRaises(RuntimeError) as ctx:
            client.search("crm.lead")

        self.assertIn("Access Denied", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
