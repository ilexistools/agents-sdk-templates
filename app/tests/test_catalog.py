"""Contrato do catálogo: todo item deve seguir docs/padroes-catalogo.md.

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
        self.env = patch.dict(os.environ, {"CATALOG_DB": str(Path(self.tmp.name) / "catalog.sqlite3")})
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
                    self.assertIsNotNone(example.output, "Ferramentas devem declarar output nos exemplos.")
                    result = asyncio.run(handler.run(handler.Input.model_validate(example.input)))
                    self.assertEqual(result.model_dump(mode="json"), example.output)

    def test_api_exposes_contract_and_runs_examples(self):
        from app.main import app

        client = TestClient(app)
        listing = {item["id"]: item for item in client.get("/api/catalog").json()}
        self.assertEqual(listing["word_count"]["category"], "Texto")
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
                created = scaffold(kind, f"novo_{kind}", "Item novo", root=root, prompts=root / "prompts")
                manifest = tomllib.loads((root / f"{kind}s" / f"novo_{kind}" / "item.toml").read_text(encoding="utf-8"))
                item = Item.model_validate(manifest)
                self.assertEqual((item.id, item.type), (f"novo_{kind}", kind))
                self.assertTrue(all(path.exists() for path in created))
                for path in created:
                    self.assertNotIn("__ID__", path.read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            scaffold("tool", "novo_tool", "Duplicado", root=root)
        with self.assertRaises(ValueError):
            scaffold("tool", "Nome-Invalido", "X", root=root)


if __name__ == "__main__":
    unittest.main()
