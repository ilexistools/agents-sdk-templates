"""Catalog contract: every item must follow docs/catalog-standards.md.

Run with: uv run --locked python -m unittest app.tests.test_catalog -v
"""

import asyncio
import os
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from app.catalog import Item, check, discover
from app.catalog_cli import scaffold


class CatalogStandardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "CATALOG_DB": str(Path(self.tmp.name) / "catalog.sqlite3"),
            "CATALOG_ENV_FILE": str(Path(self.tmp.name) / ".env"),
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_every_item_follows_the_standard(self):
        items = discover()
        self.assertTrue(items)
        for item in items.values():
            with self.subTest(item=item.id):
                self.assertEqual(check(item), [])

    def test_tool_examples_produce_expected_output(self):
        for item in discover().values():
            if item.type != "tool":
                continue
            handler = item.implementation()
            for example in item.examples:
                with self.subTest(item=item.id, example=example.title):
                    self.assertIsNotNone(example.output, "Tools must declare output in their examples.")
                    result = asyncio.run(handler.run(handler.Input.model_validate(example.input)))
                    self.assertEqual(result.model_dump(mode="json"), example.output)

    def test_api_exposes_contract_and_runs_examples(self):
        from app.main import app

        client = TestClient(app)
        listing = {item["id"]: item for item in client.get("/api/catalog").json()}
        self.assertEqual(listing["word_count"]["category"], "Text")
        detail = client.get("/api/catalog/word_count").json()
        self.assertEqual([field["name"] for field in detail["input"]], ["text"])
        self.assertTrue(all(field["description"] for field in detail["output"]))
        example = listing["word_count"]["examples"][0]
        response = client.post("/api/catalog/word_count/run", json=example["input"])
        self.assertEqual(response.json(), example["output"])

    def test_disabled_channel_is_hidden_from_mcp(self):
        from app import catalog_mcp
        from app.catalog import set_channels

        item = discover()["word_count"]
        set_channels(item, {"api"})
        tools = asyncio.run(catalog_mcp.list_tools(None, None)).tools
        self.assertNotIn("word_count", [tool.name for tool in tools])

    def test_scaffold_creates_valid_items(self):
        root = Path(self.tmp.name)
        for kind in ("tool", "agent"):
            with self.subTest(kind=kind):
                created = scaffold(kind, f"new_{kind}", "New item", root=root, prompts=root / "prompts")
                manifest = tomllib.loads((root / f"{kind}s" / f"new_{kind}" / "item.toml").read_text(encoding="utf-8"))
                item = Item.model_validate(manifest)
                self.assertEqual((item.id, item.type), (f"new_{kind}", kind))
                self.assertTrue(all(path.exists() for path in created))
                for path in created:
                    self.assertNotIn("__ID__", path.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            scaffold("tool", "new_tool", "Duplicate", root=root)
        with self.assertRaises(ValueError):
            scaffold("tool", "Invalid-Name", "X", root=root)


    def test_settings_store_keys_without_returning_them(self):
        from app.main import app

        client = TestClient(app)
        secret = "sk-test-0000000000abcd"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENAI_API_KEY", None)
            response = client.put("/api/settings", json={"OPENAI_API_KEY": secret, "OPENAI_MODEL_NAME": "gpt-test"})
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(secret, response.text)
            fields = {field["key"]: field for field in client.get("/api/settings").json()}
            self.assertEqual(fields["OPENAI_API_KEY"]["hint"], "••••abcd")
            self.assertNotIn("value", fields["OPENAI_API_KEY"])
            self.assertEqual(fields["OPENAI_MODEL_NAME"]["value"], "gpt-test")
            self.assertIn(secret, (Path(self.tmp.name) / ".env").read_text(encoding="utf-8"))
            self.assertEqual(discover()["summarizer"].missing_requirements(), [])

            client.put("/api/settings", json={"OPENAI_API_KEY": None})
            self.assertNotIn(secret, (Path(self.tmp.name) / ".env").read_text(encoding="utf-8"))
            self.assertEqual(discover()["summarizer"].missing_requirements(), ["OPENAI_API_KEY"])
            run = client.post("/api/catalog/summarizer/run", json={"text": "hello"})
            self.assertEqual(run.status_code, 409)

    def test_settings_reject_invalid_values(self):
        from app.main import app

        client = TestClient(app)
        for changes in ({"UNKNOWN": "x"}, {"LOCAL_BASE_URL": "ftp://host"}, {"OPENAI_MODEL_NAME": "a\nb"}):
            with self.subTest(changes=changes):
                self.assertEqual(client.put("/api/settings", json=changes).status_code, 422)

if __name__ == "__main__":
    unittest.main()
