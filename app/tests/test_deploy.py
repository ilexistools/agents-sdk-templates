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
