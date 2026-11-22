"""Running and deploying: entry point, access token and read-only settings.

Run with: uv run --locked python -m unittest app.tests.test_deploy -v
"""

import base64
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "CATALOG_DB": str(Path(self.tmp.name) / "catalog.sqlite3"),
            "CATALOG_ENV_FILE": str(Path(self.tmp.name) / ".env"),
        })
        self.env.start()
        for key in ("CATALOG_TOKEN", "CATALOG_SETTINGS_READONLY"):
            os.environ.pop(key, None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def client(self):
        from app.main import app

        return TestClient(app)

    def test_open_without_token(self):
        self.assertEqual(self.client().get("/api/catalog").status_code, 200)

    def test_preferences_are_stored_in_sqlite(self):
        import sqlite3

        client = self.client()
        self.assertEqual(client.get("/api/preferences").json(), {})
        saved = client.put("/api/preferences", json={
            "theme": "dark", "filters_panel": "collapsed", "bulk_channel": "mcp",
            "view": {"q": "count", "type": "tool", "item": "word_count", "status": ""},
        }).json()
        self.assertEqual(saved["view"], {"q": "count", "type": "tool", "item": "word_count"})
        self.assertEqual(client.put("/api/preferences", json={"theme": "light"}).json()["filters_panel"], "collapsed")
        from contextlib import closing

        with closing(sqlite3.connect(os.environ["CATALOG_DB"])) as db:
            stored = dict(db.execute("SELECT key, value FROM preferences"))
        self.assertEqual(stored["theme"], '"light"')
        self.assertNotIn("theme", client.put("/api/preferences", json={"theme": None}).json())

    def test_preference_migration_never_overwrites_server_values(self):
        client = self.client()
        client.put("/api/preferences", json={"theme": "system"})
        migrated = client.put("/api/preferences?only_missing=true",
                              json={"theme": "dark", "filters_panel": "collapsed"}).json()
        self.assertEqual((migrated["theme"], migrated["filters_panel"]), ("system", "collapsed"))
        self.assertEqual(client.put("/api/preferences", json={"theme": "dark"}).json()["theme"], "dark")

    def test_preferences_are_validated_and_allowed_when_settings_are_read_only(self):
        client = self.client()
        for body in ({"theme": "pink"}, {"filters_panel": "open"}, {"bulk_channel": "email"},
                     {"view": {"unknown": "x"}}, {"view": {"q": "x" * 201}}, {"view": "q=x"}, {"colour": "red"},
                     {"theme": ["dark"]}, {"filters_panel": {"a": 1}}, {"view": {"q": 5}}):
            with self.subTest(body=body):
                self.assertEqual(client.put("/api/preferences", json=body).status_code, 422)
        os.environ["CATALOG_SETTINGS_READONLY"] = "true"
        self.assertEqual(client.put("/api/preferences", json={"theme": "dark"}).status_code, 200)
        os.environ["CATALOG_TOKEN"] = "pref-token"
        self.assertEqual(client.get("/api/preferences").status_code, 401)

    def test_dashboard_is_never_served_stale(self):
        self.assertEqual(self.client().get("/").headers["cache-control"], "no-cache")

    def test_favicon_is_served(self):
        response = self.client().get("/favicon.ico")
        self.assertEqual((response.status_code, response.headers["content-type"]), (200, "image/svg+xml"))

    def test_token_protects_everything_but_health(self):
        os.environ["CATALOG_TOKEN"] = "s3cret-token"
        client = self.client()
        self.assertEqual(client.get("/health").status_code, 200)
        for path in ("/", "/api/catalog", "/api/settings", "/docs"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 401)
                self.assertIn("Basic", response.headers["www-authenticate"])
        wrong = {"Authorization": "Bearer nope"}
        self.assertEqual(client.get("/api/catalog", headers=wrong).status_code, 401)
        bearer = {"Authorization": "Bearer s3cret-token"}
        self.assertEqual(client.get("/api/catalog", headers=bearer).status_code, 200)
        basic = {"Authorization": "Basic " + base64.b64encode(b"anyone:s3cret-token").decode()}
        self.assertEqual(client.get("/", headers=basic).status_code, 200)
        self.assertEqual(client.get("/", headers={"Authorization": "Basic !!!"}).status_code, 401)

    def test_read_only_settings(self):
        client = self.client()
        self.assertFalse(client.get("/api/settings").json()["readonly"])
        os.environ["CATALOG_SETTINGS_READONLY"] = "true"
        body = client.get("/api/settings").json()
        self.assertTrue(body["readonly"])
        self.assertTrue(body["fields"])
        response = client.put("/api/settings", json={"DEFAULT_MODEL": "ollama:llama3.2"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse((Path(self.tmp.name) / ".env").exists())

    def test_default_ports_match_everywhere(self):
        from app.__main__ import DEFAULT_PORT

        self.assertEqual(DEFAULT_PORT, "8787")
        source = (ROOT / "app" / "catalog_mcp.py").read_text(encoding="utf-8")
        self.assertIn('os.getenv("MCP_PORT", "8888")', source)
        compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn('PORT: "8787"', compose)
        self.assertIn("EXPOSE 8787", (ROOT / "Dockerfile").read_text(encoding="utf-8"))

    def test_loopback_detection(self):
        from app.__main__ import is_loopback

        for host, expected in (("127.0.0.1", True), ("localhost", True), ("::1", True),
                               ("0.0.0.0", False), ("192.168.0.10", False), ("example.com", False)):
            with self.subTest(host=host):
                self.assertEqual(is_loopback(host), expected)

    def test_serve_refuses_public_host_without_token(self):
        env = {key: value for key, value in os.environ.items() if key != "CATALOG_TOKEN"}
        result = subprocess.run(
            [sys.executable, "-m", "app", "serve", "--host", "0.0.0.0", "--port", "8765"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("CATALOG_TOKEN", result.stderr)

    def test_token_in_env_file_is_honored(self):
        Path(os.environ["CATALOG_ENV_FILE"]).write_text('CATALOG_TOKEN="from-file"\n', encoding="utf-8")
        code = (
            "import os, app.__main__ as m\n"
            "from app.orchestration.config import load_environment\n"
            "load_environment()\n"
            "from app.security import token_configured\n"
            "print(token_configured())\n"
        )
        env = {key: value for key, value in os.environ.items() if key != "CATALOG_TOKEN"}
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.stdout.strip(), "True")


class CatalogMcpHttpTests(unittest.TestCase):
    """The catalog MCP server over HTTP (it previously failed to start)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "CATALOG_DB": str(Path(self.tmp.name) / "catalog.sqlite3"),
            "CATALOG_ENV_FILE": str(Path(self.tmp.name) / ".env"),
        })
        self.env.start()
        os.environ.pop("CATALOG_TOKEN", None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def rpc(self, client, method, params, headers=None):
        return client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream", **(headers or {})},
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )

    def test_streamable_http_lists_and_calls_catalog_items(self):
        from app.catalog_mcp import streamable_http_app

        with TestClient(streamable_http_app(), base_url="http://127.0.0.1:8888") as client:
            init = {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}
            self.assertEqual(self.rpc(client, "initialize", init).status_code, 200)
            tools = self.rpc(client, "tools/list", {}).json()["result"]["tools"]
            self.assertIn("word_count", {tool["name"] for tool in tools})
            result = self.rpc(client, "tools/call", {"name": "word_count", "arguments": {"text": "one two three"}})
            self.assertEqual(result.json()["result"]["structuredContent"], {"word_count": 3, "character_count": 11})

    def test_token_protects_mcp_http(self):
        from app.catalog_mcp import sse_app, streamable_http_app

        os.environ["CATALOG_TOKEN"] = "mcp-token"
        with TestClient(streamable_http_app(), base_url="http://127.0.0.1:8888") as client:
            self.assertEqual(self.rpc(client, "tools/list", {}).status_code, 401)
            ok = self.rpc(client, "tools/list", {}, {"Authorization": "Bearer mcp-token"})
            self.assertEqual(ok.status_code, 200)
        with TestClient(sse_app(), base_url="http://127.0.0.1:8888") as client:
            self.assertEqual(client.get("/sse").status_code, 401)

    def test_mcp_reads_transport_and_host_from_settings(self):
        Path(os.environ["CATALOG_ENV_FILE"]).write_text(
            'MCP_TRANSPORT="streamable-http"\nMCP_HOST="0.0.0.0"\nMCP_PORT="8899"\n', encoding="utf-8")
        env = {key: value for key, value in os.environ.items()
               if key not in ("CATALOG_TOKEN", "MCP_TRANSPORT", "MCP_HOST", "MCP_PORT")}
        result = subprocess.run([sys.executable, "-m", "app", "mcp"], cwd=ROOT, env=env, input="",
                                capture_output=True, text=True, timeout=60)
        # It chose HTTP on 0.0.0.0 from .env, so it refuses to start without a token.
        self.assertEqual(result.returncode, 2)
        self.assertIn("0.0.0.0", result.stderr)

    def test_mcp_settings_are_validated(self):
        from app.main import app

        client = TestClient(app)
        for changes in ({"MCP_TRANSPORT": "websocket"}, {"MCP_PORT": "99999"}, {"MCP_PORT": "abc"},
                        {"MCP_HOST": "http://example.com"}, {"MCP_HOST": "two words"}):
            with self.subTest(changes=changes):
                self.assertEqual(client.put("/api/settings", json=changes).status_code, 422)
        ok = client.put("/api/settings", json={"MCP_TRANSPORT": "sse", "MCP_HOST": "0.0.0.0", "MCP_PORT": "9000"})
        self.assertEqual(ok.status_code, 200)
        fields = {field["key"]: field for field in ok.json()["fields"]}
        self.assertEqual((fields["MCP_TRANSPORT"]["value"], fields["MCP_PORT"]["value"]), ("sse", "9000"))
        self.assertEqual(fields["MCP_TRANSPORT"]["group"], "MCP server")
        for key in ("MCP_TRANSPORT", "MCP_HOST", "MCP_PORT"):
            os.environ.pop(key, None)

    def test_mcp_refuses_public_host_without_token(self):
        env = {key: value for key, value in os.environ.items() if key != "CATALOG_TOKEN"}
        result = subprocess.run(
            [sys.executable, "-m", "app", "mcp", "--transport", "streamable-http", "--host", "0.0.0.0"],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("CATALOG_TOKEN", result.stderr)


if __name__ == "__main__":
    unittest.main()
