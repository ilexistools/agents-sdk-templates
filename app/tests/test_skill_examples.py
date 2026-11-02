"""Offline checks for executable assets bundled with development skills."""

import asyncio
import json
import runpy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from agents.tool_context import ToolContext


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents/skills"


def asset(skill, name):
    return runpy.run_path(str(SKILLS / skill / "assets" / name))


class SkillExamplesTests(unittest.TestCase):
    def test_agent_validator_uses_loader_and_rejects_invalid_contracts(self):
        skill = SKILLS / "agents-template-criar-agente"
        validator = runpy.run_path(str(skill / "scripts/validar_agente.py"))["validate"]
        sample = skill / "assets/relatorio_revisor.md"
        self.assertEqual(validator(sample, ROOT), [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / sample.name
            text = sample.read_text(encoding="utf-8")
            for invalid in (
                text.replace("max_tokens: 2048", "max_tokens:"),
                text.replace("id: relatorio_revisor", "id: outro"),
                text.split("# KNOWLEDGE")[0],
                "---\n[broken\n---\n",
            ):
                with self.subTest(invalid=invalid[:60]):
                    path.write_text(invalid, encoding="utf-8")
                    self.assertTrue(validator(path, ROOT))

    def test_fastapi_example_serializes_output_and_validates_input(self):
        example = asset("agents-template-criar-aplicacao", "classificacao_api.py")
        expected = example["ClassificacaoResponse"](
            categoria="dúvida", justificativa="Solicita informação.",
        )
        with patch.object(example["classificador"], "run", new=AsyncMock(return_value=expected)) as run:
            with TestClient(example["app"]) as client:
                response = client.post("/classificar", json={"texto": "Como acessar?"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), expected.model_dump())
                self.assertEqual(client.post("/classificar", json={"texto": ""}).status_code, 422)
            run.assert_awaited_once_with("Como acessar?")

    def test_pipeline_passes_validated_extraction_to_reviewer(self):
        example = asset("agents-template-orquestrar-agentes", "fluxo_sequencial.py")
        extracted = example["ExtracaoResponse"](fatos=["Prazo de cinco dias."])
        expected = example["RevisaoResponse"](resumo="Prazo registrado.", pendencias=[])
        calls = []

        async def extract(prompt):
            calls.append("extract")
            self.assertEqual(prompt, "relatório")
            return extracted

        async def review(prompt):
            calls.append("review")
            self.assertEqual(json.loads(prompt), extracted.model_dump())
            return expected

        result = asyncio.run(example["processar"](
            "relatório", SimpleNamespace(run=extract), SimpleNamespace(run=review),
        ))
        self.assertEqual(result, expected)
        self.assertEqual(calls, ["extract", "review"])

    def test_pipeline_stops_on_extraction_failure(self):
        example = asset("agents-template-orquestrar-agentes", "fluxo_sequencial.py")
        reviewer = SimpleNamespace(run=AsyncMock())
        for extraction in (AsyncMock(side_effect=RuntimeError("offline failure")),
                           AsyncMock(return_value={"invalid": True})):
            with self.subTest(extraction=extraction):
                with self.assertRaises((RuntimeError, ValueError)):
                    asyncio.run(example["processar"](
                        "relatório", SimpleNamespace(run=extraction), reviewer,
                    ))
                reviewer.run.assert_not_awaited()

    def test_python_tool_schema_and_adapter(self):
        example = asset("agents-template-integrar-ferramentas", "ferramenta_texto.py")
        self.assertEqual(example["contar_palavras"]("uma  frase\ncurta"), 3)
        tool = example["contar_palavras_tool"]
        self.assertEqual(tool.params_json_schema["required"], ["texto"])
        arguments = json.dumps({"texto": "duas palavras"})
        context = ToolContext(
            context=None,
            tool_name=tool.name,
            tool_call_id="offline-test",
            tool_arguments=arguments,
        )
        result = asyncio.run(tool.on_invoke_tool(context, arguments))
        self.assertEqual(str(result), "2")
        self.assertIn(tool, example["criar_agente"]().tools)


if __name__ == "__main__":
    unittest.main()
