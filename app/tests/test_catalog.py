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

    def test_agent_handlers_use_create_agent_with_their_own_id(self):
        from unittest.mock import AsyncMock

        for item in discover().values():
            if item.type != "agent":
                continue
            handler = item.implementation()
            with self.subTest(item=item.id):
                sentinel = handler.Output.model_construct()
                fake = AsyncMock()
                fake.run.return_value = sentinel
                with patch.object(handler, "create_agent", return_value=fake) as factory:
                    result = asyncio.run(handler.run(handler.Input.model_validate(item.examples[0].input)))
                args, kwargs = factory.call_args
                self.assertEqual(args[0] if args else kwargs.get("agent_id"), item.id)
                self.assertIs(kwargs.get("output_type"), handler.Output)
                fake.run.assert_awaited_once()
                self.assertIs(result, sentinel)

    def test_item_errors_reach_the_caller(self):
        from app.catalog import ItemError
        from app.main import app
        from app.tools.word_count import handler

        client = TestClient(app)

        async def not_found(request):
            raise ItemError("Nothing to count.")

        async def crash(request):
            raise KeyError("internal detail")

        with patch.object(handler, "run", not_found):
            response = client.post("/api/catalog/word_count/run", json={"text": "x"})
        self.assertEqual((response.status_code, response.json()["detail"]), (422, "Nothing to count."))
        with patch.object(handler, "run", crash):
            response = client.post("/api/catalog/word_count/run", json={"text": "x"})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("internal detail", response.text)

    def test_settings_required_by_items_appear_in_settings(self):
        from app import catalog, catalog_api
        from app.main import app

        items = discover()
        items["word_count"] = items["word_count"].model_copy(update={"requires": ["WEATHER_API_KEY", "WEATHER_BASE_URL"]})
        client = TestClient(app)
        with patch.object(catalog, "discover", return_value=items), \
                patch.object(catalog_api, "discover", return_value=items):
            fields = {f["key"]: f for f in client.get("/api/settings").json()["fields"]}
            self.assertTrue(fields["WEATHER_API_KEY"]["secret"])
            self.assertFalse(fields["WEATHER_BASE_URL"]["secret"])
            self.assertEqual(fields["WEATHER_API_KEY"]["group"], "Agents and tools")
            self.assertIn("Word counter", fields["WEATHER_API_KEY"]["help"])
            self.assertEqual(items["word_count"].missing_requirements(), ["WEATHER_API_KEY", "WEATHER_BASE_URL"])
            blocked = client.post("/api/catalog/word_count/run", json={"text": "x"})
            self.assertEqual(blocked.status_code, 409)
            self.assertEqual(client.put("/api/settings", json={"WEATHER_API_KEY": "abc123456789"}).status_code, 200)
            self.assertEqual(items["word_count"].missing_requirements(), ["WEATHER_BASE_URL"])

    def test_check_rejects_provider_keys_in_agent_requires(self):
        item = discover()["summarizer"].model_copy(update={"requires": ["OPENAI_API_KEY"]})
        self.assertTrue(any("OPENAI_API_KEY" in problem for problem in check(item)))
        with self.assertRaises(Exception):
            Item.model_validate({**discover()["word_count"].model_dump(), "requires": ["lowercase"]})

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

    def test_bulk_actions(self):
        from app.main import app

        client = TestClient(app)
        state = lambda: {i["id"]: (i["active"], tuple(i["channels"])) for i in client.get("/api/catalog").json()}
        self.assertEqual(client.patch("/api/catalog", json={"active": False}).status_code, 200)
        self.assertFalse(any(active for active, _ in state().values()))
        response = client.patch("/api/catalog", json={"ids": ["word_count"], "active": True, "disable_channels": ["mcp"]})
        self.assertEqual(response.json(), [{"id": "word_count", "active": True, "channels": ["api", "cli"]}])
        self.assertEqual(state()["summarizer"], (False, ("api", "cli", "mcp")))
        client.patch("/api/catalog", json={"enable_channels": ["mcp"]})
        self.assertEqual(state()["word_count"][1], ("api", "cli", "mcp"))
        for body, code in (({}, 422), ({"ids": ["nope"], "active": True}, 404),
                           ({"enable_channels": ["mcp"], "disable_channels": ["mcp"]}, 422),
                           ({"enable_channels": ["email"]}, 422)):
            with self.subTest(body=body):
                self.assertEqual(client.patch("/api/catalog", json=body).status_code, code)

    def test_cli_bulk_commands(self):
        import io
        import json as jsonlib
        import sys
        from contextlib import redirect_stdout

        from app import catalog_cli

        def cli(*args):
            output = io.StringIO()
            with patch.object(sys, "argv", ["catalog", *args]), redirect_stdout(output):
                catalog_cli.main()
            return jsonlib.loads(output.getvalue())

        # Works with whatever items the project has, not only the bundled examples.
        items = discover()
        self.assertEqual({r["id"] for r in cli("disable", "--all")}, set(items))
        self.assertEqual(cli("enable", "word_count")["active"], True)
        tools = {r["id"]: r for r in cli("disable", "--type", "tool", "--channel", "mcp")}
        self.assertEqual(set(tools), {item_id for item_id, item in items.items() if item.type == "tool"})
        self.assertEqual(tools["word_count"], {"id": "word_count", "active": True, "channels": ["api", "cli"]})
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()), patch.object(sys, "stderr", io.StringIO()):
                cli("enable")

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
            fields = {field["key"]: field for field in client.get("/api/settings").json()["fields"]}
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
        for changes in (
            {"UNKNOWN": "x"},
            {"LOCAL_BASE_URL": "ftp://host"},
            {"OLLAMA_BASE_URL": "not a url"},
            {"OPENAI_MODEL_NAME": "a\nb"},
            {"DEFAULT_MODEL": "unknown:model"},
            {"DEFAULT_MODEL": "gpt-4.1"},
        ):
            with self.subTest(changes=changes):
                self.assertEqual(client.put("/api/settings", json=changes).status_code, 422)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "CATALOG_DB": str(Path(self.tmp.name) / "catalog.sqlite3"),
            "CATALOG_ENV_FILE": str(Path(self.tmp.name) / ".env"),
        })
        self.env.start()
        for key in ("DEFAULT_MODEL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OLLAMA_BASE_URL"):
            os.environ.pop(key, None)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_model_references(self):
        from app.orchestration.providers import parse

        cases = {
            "openai:gpt-4.1": ("openai", "gpt-4.1"),
            "ollama:llama3.2:3b": ("ollama", "llama3.2:3b"),
            "openrouter:anthropic/claude-sonnet-5-5": ("openrouter", "anthropic/claude-sonnet-5-5"),
            "gpt-4.1-mini": ("openai", "gpt-4.1-mini"),
        }
        for ref, expected in cases.items():
            with self.subTest(ref=ref):
                resolved = parse(ref)
                self.assertEqual((resolved.provider.id, resolved.model), expected)
        os.environ["DEFAULT_MODEL"] = "ollama:llama3.2"
        self.assertEqual(parse(None).ref, "ollama:llama3.2")
        self.assertEqual(parse("qwen2.5").ref, "ollama:qwen2.5")
        os.environ["OLLAMA_BASE_URL"] = "http://gpu-box:11434/v1"
        self.assertEqual(parse("ollama:x").base_url, "http://gpu-box:11434/v1")
        self.assertIsNone(parse("ollama:x").missing_key)
        self.assertEqual(parse("anthropic:claude-sonnet-5-5").missing_key, "ANTHROPIC_API_KEY")

    def test_create_agent_uses_the_right_backend(self):
        from app.orchestration.gpt_agent import GPTAgent
        from app.orchestration.gpt_agent_local import GPTLocalAgent
        from app.orchestration.providers import create_agent

        os.environ["OPENAI_API_KEY"] = "sk-test-placeholder"
        openai_agent = create_agent("summarizer", model="openai:gpt-4.1")
        self.assertIsInstance(openai_agent, GPTAgent)
        self.assertEqual(openai_agent.model, "gpt-4.1")

        local_agent = create_agent("summarizer", model="ollama:llama3.2:3b")
        self.assertIsInstance(local_agent, GPTLocalAgent)
        self.assertEqual(local_agent.model.model, "llama3.2:3b")
        self.assertEqual(str(local_agent.model._client.base_url), "http://localhost:11434/v1/")

        with self.assertRaisesRegex(RuntimeError, "ANTHROPIC_API_KEY"):
            create_agent("summarizer", model="anthropic:claude-sonnet-5-5")

    def test_dashboard_model_choice_reaches_the_handler(self):
        from app.main import app
        from app.agents.summarizer import handler
        from app.orchestration.providers import agent_model_ref

        client = TestClient(app)
        self.assertEqual(client.get("/api/catalog/summarizer").json()["model"]["source"], "default")
        self.assertEqual(client.patch("/api/catalog/summarizer/model", json={"model": "nope:x"}).status_code, 422)
        self.assertEqual(client.patch("/api/catalog/word_count/model", json={"model": "ollama:x"}).status_code, 422)

        response = client.patch("/api/catalog/summarizer/model", json={"model": "ollama:llama3.2"})
        self.assertEqual(response.json()["model"]["ref"], "ollama:llama3.2")
        detail = client.get("/api/catalog/summarizer").json()
        self.assertEqual((detail["model"]["source"], detail["missing_requirements"]), ("item", []))

        seen = []

        async def fake_run(request):
            seen.append(agent_model_ref("summarizer"))
            return handler.Output(summary="ok")

        with patch.object(handler, "run", fake_run):
            self.assertEqual(client.post("/api/catalog/summarizer/run", json={"text": "hi"}).json(), {"summary": "ok"})
        self.assertEqual(seen, [("ollama:llama3.2", "item")])

        client.patch("/api/catalog/summarizer/model", json={"model": None})
        self.assertEqual(client.get("/api/catalog/summarizer").json()["model"]["source"], "default")

    def test_provider_endpoints(self):
        from app.main import app

        client = TestClient(app)
        providers = {provider["id"]: provider for provider in client.get("/api/providers").json()}
        self.assertTrue({"openai", "anthropic", "gemini", "ollama", "local"} <= set(providers))
        self.assertTrue(providers["ollama"]["ready"])
        self.assertFalse(providers["anthropic"]["ready"])
        self.assertEqual(client.post("/api/providers/unknown/models").status_code, 404)
        missing = client.post("/api/providers/anthropic/models")
        self.assertEqual(missing.status_code, 502)
        self.assertIn("ANTHROPIC_API_KEY", missing.json()["detail"])

        class FakeModels:
            def list(self):
                return [type("M", (), {"id": "llama3.2"})(), type("M", (), {"id": "qwen2.5"})()]

        with patch("openai.OpenAI") as client_class:
            client_class.return_value.models = FakeModels()
            listed = client.post("/api/providers/ollama/models").json()
        self.assertEqual(listed["models"], ["ollama:llama3.2", "ollama:qwen2.5"])

if __name__ == "__main__":
    unittest.main()
