"""Offline Decisions API transport, validation and routing checks."""

import asyncio
import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx2
from openai import AsyncOpenAI, OpenAI
from openai.types.decision import Decision

from app.examples.decisions import EXAMPLE_QUESTIONS, route_request
from app.orchestration import config
from app.orchestration.gpt_agent import GPTAgentResponse
from app.orchestration.gpt_decision import GPTDecision


def decision_payload(answers=None):
    return {
        "model": "gpt-6-luna",
        "answers": answers if answers is not None else [
            {"type": "predicate", "name": "refund_requested", "probability": 0.9},
            {
                "type": "choice", "name": "department", "choice": "billing",
                "confidence": 0.95,
                "probabilities": [{"value": "billing", "probability": 0.95},
                                  {"value": "technical", "probability": 0.03},
                                  {"value": "other", "probability": 0.02}],
            },
            {
                "type": "score", "name": "impact", "score": 0.2, "confidence": 0.8,
                "probabilities": [
                    {"value": 0, "label": "No blockage", "probability": 0.8},
                    {"value": 1, "label": "Partial blockage", "probability": 0.2},
                    {"value": 2, "label": "Full blockage", "probability": 0.0},
                ],
            },
            {"type": "refusal", "name": "unanswerable"},
        ],
        "usage": {
            "input_tokens": 40,
            "input_tokens_details": {"cache_write_tokens": 0, "cached_tokens": 0},
            "output_tokens": 4,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 44,
        },
    }


class GPTDecisionTests(unittest.TestCase):
    def test_sync_sdk_transport_preserves_all_answer_types_and_usage(self):
        requests = []

        def respond(request):
            requests.append(request)
            return httpx2.Response(200, json=decision_payload())

        with OpenAI(
            api_key="offline-test", base_url="https://api.openai.com/v1",
            http_client=httpx2.Client(transport=httpx2.MockTransport(respond)),
        ) as client:
            wrapper = GPTDecision(client=client, model="gpt-6-luna")
            result = wrapper.run_sync(
                "Refund the duplicate charge", questions=iter(EXAMPLE_QUESTIONS),
                prompt_cache_key="offline-example", extra_headers={"X-Test": "decisions"},
            )
        body = json.loads(requests[0].content)
        self.assertEqual(str(requests[0].url), "https://api.openai.com/v1/decisions")
        self.assertEqual(requests[0].method, "POST")
        self.assertEqual(body["questions"], EXAMPLE_QUESTIONS)
        self.assertEqual(body["input"], "Refund the duplicate charge")
        self.assertEqual(body["model"], "gpt-6-luna")
        self.assertEqual(body["prompt_cache_key"], "offline-example")
        self.assertEqual(requests[0].headers["X-Test"], "decisions")
        self.assertIsInstance(result, Decision)
        self.assertEqual([answer.type for answer in result.answers], ["predicate", "choice", "score", "refusal"])
        self.assertEqual(result.answers[0].probability, 0.9)
        self.assertEqual(result.answers[1].confidence, 0.95)
        self.assertEqual(result.answers[2].score, 0.2)
        self.assertEqual(result.usage.total_tokens, 44)

    def test_question_validation_happens_before_client_creation(self):
        wrapper = GPTDecision()
        question = EXAMPLE_QUESTIONS[0]
        invalid = [[], [question] * 401, [question, question],
                   [{"type": "predicate", "instructions": "Check"}],
                   [{"type": "unknown", "name": "test", "instructions": "Check"}]]
        with patch("app.orchestration.gpt_decision.OpenAI") as client:
            for questions in invalid:
                with self.subTest(questions=questions[:2]):
                    with self.assertRaises(ValueError):
                        wrapper.run_sync("text", questions=questions)
            client.assert_not_called()

    def test_model_configuration_is_independent_of_regular_model(self):
        with patch.object(config, "load_environment"), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.decision_model(), "gpt-6-luna")
            os.environ["OPENAI_MODEL_NAME"] = "regular-model"
            self.assertEqual(config.decision_model(), "gpt-6-luna")
            os.environ["OPENAI_DECISION_MODEL_NAME"] = "configured-model"
            with patch("app.orchestration.gpt_decision.load_environment"):
                self.assertEqual(GPTDecision().model, "configured-model")
                self.assertEqual(GPTDecision(model="explicit-model").model, "explicit-model")
                with self.assertRaises(ValueError):
                    GPTDecision(model="")

    def test_sync_provider_error_propagates(self):
        client = SimpleNamespace(decisions=SimpleNamespace(create=Mock(side_effect=RuntimeError("provider failed"))))
        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            GPTDecision(client=client).run_sync("text", questions=EXAMPLE_QUESTIONS)


class AsyncGPTDecisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_sdk_accepts_structured_input_and_keeps_boolean_choices(self):
        evidence = [{"role": "user", "content": [
            {"type": "input_json", "data": {"charges": [49, 49]}},
        ]}]
        questions = [{
            "type": "choice", "name": "duplicate", "instructions": "Duplicate charge?",
            "choices": [{"value": True}, {"value": False}],
        }]
        answer = {
            "type": "choice", "name": "duplicate", "choice": False, "confidence": 0.6,
            "probabilities": [{"value": True, "probability": 0.4},
                              {"value": False, "probability": 0.6}],
        }
        requests = []

        def respond(request):
            requests.append(request)
            return httpx2.Response(200, json=decision_payload([answer]))

        async with AsyncOpenAI(
            api_key="offline-test", base_url="https://api.openai.com/v1",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(respond)),
        ) as client:
            wrapper = GPTDecision(async_client=client, model="gpt-6-luna")
            with patch("app.orchestration.gpt_decision.OpenAI") as sync_client:
                result = await wrapper.run(evidence, questions=questions)
                sync_client.assert_not_called()
        self.assertEqual(json.loads(requests[0].content)["input"], evidence)
        self.assertIs(result.answers[0].choice, False)

    async def test_async_validation_and_error_propagation(self):
        call = AsyncMock(side_effect=RuntimeError("provider failed"))
        wrapper = GPTDecision(async_client=SimpleNamespace(decisions=SimpleNamespace(create=call)))
        with self.assertRaises(ValueError):
            await wrapper.run("text", questions=[])
        call.assert_not_awaited()
        with self.assertRaisesRegex(RuntimeError, "provider failed"):
            await wrapper.run("text", questions=EXAMPLE_QUESTIONS)


class DecisionRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_selected_specialist_receives_original_request(self):
        decision = Decision.model_validate(decision_payload())
        decider = SimpleNamespace(run=AsyncMock(return_value=decision))
        expected = GPTAgentResponse(final_output="Next steps")
        billing = SimpleNamespace(run=AsyncMock(return_value=expected))
        technical = SimpleNamespace(run=AsyncMock())
        result = await route_request(
            "duplicate charge", decider=decider,
            specialists={"billing": billing, "technical": technical}, min_confidence=0.8,
        )
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.route, "billing")
        self.assertEqual(result.output, expected)
        self.assertIs(result.decision, decision)
        billing.run.assert_awaited_once_with("duplicate charge")
        technical.run.assert_not_awaited()

    async def test_review_paths_do_not_execute_specialists(self):
        choice = decision_payload()["answers"][1]
        cases = [
            ([{"type": "refusal", "name": "department"}], "refusal"),
            ([dict(choice, confidence=0.5)], "low_confidence"),
            ([dict(choice, choice="other")], "unmapped_choice"),
            ([], "missing_answer"),
            ([dict(choice, name="wrong_name")], "missing_answer"),
            ([choice, choice], "missing_answer"),
            ([{"type": "predicate", "name": "department", "probability": 0.9}], "unexpected_answer_type"),
        ]
        for answers, reason in cases:
            with self.subTest(reason=reason, answers=answers):
                specialist = SimpleNamespace(run=AsyncMock())
                decision = Decision.model_validate(decision_payload(answers))
                result = await route_request(
                    "request", decider=SimpleNamespace(run=AsyncMock(return_value=decision)),
                    specialists={"billing": specialist}, min_confidence=0.8,
                )
                self.assertEqual(result.status, "review_required")
                self.assertEqual(result.reason, reason)
                self.assertIsNone(result.output)
                self.assertIsNone(result.route)
                specialist.run.assert_not_awaited()

    async def test_threshold_validation_and_specialist_failure(self):
        decider = SimpleNamespace(run=AsyncMock(return_value=Decision.model_validate(decision_payload())))
        for threshold in (-1, 2, float("nan")):
            with self.assertRaises(ValueError):
                await route_request("request", decider=decider, specialists={}, min_confidence=threshold)
        decider.run.assert_not_awaited()
        with self.assertRaisesRegex(RuntimeError, "specialist failed"):
            await route_request(
                "request", decider=decider,
                specialists={"billing": SimpleNamespace(run=AsyncMock(side_effect=RuntimeError("specialist failed")))},
                min_confidence=0.8,
            )


if __name__ == "__main__":
    unittest.main()
