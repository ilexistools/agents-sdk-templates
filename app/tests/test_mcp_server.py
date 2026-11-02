"""Offline regression checks for the MCP SDK 2 migration.

Run with: uv run --locked python -m unittest app.tests.test_mcp_server
"""

import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from agents.mcp import MCPServerStdio
from starlette.testclient import TestClient

from app.mcp_tools import server


class MCPServerTests(unittest.TestCase):
    def test_transport_options(self):
        for transport in ("stdio", "sse", "streamable-http"):
            with self.subTest(transport=transport):
                with patch.object(sys, "argv", ["server", "--transport", transport]):
                    with patch.object(server.mcp, "run") as run:
                        server.main()
                options = run.call_args.kwargs
                self.assertEqual(options["transport"], transport)
                if transport == "stdio":
                    self.assertEqual(options, {"transport": "stdio"})
                else:
                    self.assertEqual(options["host"], "0.0.0.0")
                    self.assertEqual(options["port"], 8000)
                if transport == "streamable-http":
                    self.assertEqual(options["streamable_http_path"], "/mcp")
                    self.assertTrue(options["stateless_http"])
                    self.assertTrue(options["json_response"])

    def test_http_tools(self):
        app = server.mcp.streamable_http_app(stateless_http=True, json_response=True)
        with TestClient(app, base_url="http://localhost:8000") as client:
            def request(method, params):
                response = client.post(
                    "/mcp",
                    headers={"Accept": "application/json, text/event-stream"},
                    json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertNotIn("error", payload)
                return payload["result"]

            request("initialize", {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            })
            tools = request("tools/list", {})["tools"]
            self.assertEqual({tool["name"] for tool in tools}, {
                "count_text_words", "clean_text_spacing",
            })
            result = request("tools/call", {
                "name": "count_text_words", "arguments": {"text": "hello world"},
            })
            self.assertFalse(result.get("isError", False))
            self.assertEqual(json.loads(result["content"][0]["text"]), {
                "word_count": 2, "character_count": 10,
            })

    def test_agents_sdk_stdio_tools(self):
        async def check():
            async with MCPServerStdio(params={
                "command": sys.executable,
                "args": ["-m", "app.mcp_tools.server", "--transport", "stdio"],
                "cwd": str(Path(__file__).resolve().parents[2]),
            }) as client:
                tools = await client.list_tools()
                self.assertEqual({tool.name for tool in tools}, {
                    "count_text_words", "clean_text_spacing",
                })
                result = await client.call_tool("clean_text_spacing", {"text": "hello   world"})
                self.assertFalse(result.is_error)
                self.assertEqual(result.content[0].text, "hello world")

        asyncio.run(check())


if __name__ == "__main__":
    unittest.main()
