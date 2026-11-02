"""Decisions examples: grouped questions and explicit specialist routing.

No API calls happen on import. Run as `python -m app.examples.decisions --help`.
"""

import argparse
import asyncio
from collections.abc import Mapping
from typing import Literal, Protocol

from openai.types.decision import Decision
from openai.types.decision_create_params import Question
from pydantic import BaseModel

from app.orchestration.gpt_agent import GPTAgent, GPTAgentResponse
from app.orchestration.gpt_decision import GPTDecision


DEPARTMENT_QUESTION: Question = {
    "type": "choice",
    "name": "department",
    "instructions": "Which department should handle this request?",
    "choices": [
        {"value": "billing", "description": "Charges, invoices and payment questions."},
        {"value": "technical", "description": "Access errors and software malfunctions."},
        {"value": "other", "description": "Requests outside the listed departments."},
    ],
}

EXAMPLE_QUESTIONS: list[Question] = [
    {
        "type": "predicate",
        "name": "refund_requested",
        "instructions": "Does the person explicitly ask for a refund?",
    },
    DEPARTMENT_QUESTION,
    {
        "type": "score",
        "name": "impact",
        "instructions": "Rate the operational impact described, using only stated facts.",
        "levels": [
            {"label": "No blockage", "description": "No task is described as blocked."},
            {"label": "Partial blockage", "description": "A task is blocked but has a workaround."},
            {"label": "Full blockage", "description": "A required task is blocked with no workaround."},
        ],
    },
]


class Specialist(Protocol):
    async def run(self, prompt: str) -> GPTAgentResponse: ...


class RoutingResult(BaseModel):
    status: Literal["completed", "review_required"]
    reason: Literal[
        "refusal", "low_confidence", "unmapped_choice", "missing_answer", "unexpected_answer_type"
    ] | None = None
    route: str | None = None
    decision: Decision
    output: GPTAgentResponse | None = None


async def route_request(
    text: str,
    *,
    decider: GPTDecision,
    specialists: Mapping[str, Specialist],
    min_confidence: float,
) -> RoutingResult:
    """Execute only an explicitly mapped route above a caller-selected threshold.

    Refusal, uncertain or unhandled answers require review without running an agent.
    Provider and specialist failures propagate to the caller.
    """
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1.")
    decision = await decider.run(text, questions=[DEPARTMENT_QUESTION])
    answers = [answer for answer in decision.answers if answer.name == "department"]
    if len(answers) != 1:
        return RoutingResult(status="review_required", reason="missing_answer", decision=decision)
    answer = answers[0]
    if answer.type == "refusal":
        return RoutingResult(status="review_required", reason="refusal", decision=decision)
    if answer.type != "choice":
        return RoutingResult(status="review_required", reason="unexpected_answer_type", decision=decision)
    if not min_confidence <= answer.confidence <= 1:
        return RoutingResult(status="review_required", reason="low_confidence", decision=decision)
    if not isinstance(answer.choice, str) or answer.choice not in specialists:
        return RoutingResult(status="review_required", reason="unmapped_choice", decision=decision)
    output = await specialists[answer.choice].run(text)
    return RoutingResult(
        status="completed", route=answer.choice, decision=decision, output=output
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["evaluate", "route"], default="evaluate")
    parser.add_argument("--text", default="I was charged twice. Please refund the duplicate charge.")
    parser.add_argument("--min-confidence", type=float)
    args = parser.parse_args()
    if args.mode == "route" and (
        args.min_confidence is None or not 0 <= args.min_confidence <= 1
    ):
        parser.error("route requires --min-confidence between 0 and 1; calibrate it with labeled examples")

    decider = GPTDecision()
    async with decider.async_client:
        if args.mode == "evaluate":
            result = await decider.run(args.text, questions=EXAMPLE_QUESTIONS)
        else:
            specialists = {
                "billing": GPTAgent(
                    name="Billing specialist",
                    instructions="Explain next steps for the billing request; do not claim to perform transactions.",
                ),
                "technical": GPTAgent(
                    name="Technical specialist",
                    instructions="Suggest troubleshooting steps based on the reported issue.",
                ),
            }
            result = await route_request(
                args.text, decider=decider, specialists=specialists,
                min_confidence=args.min_confidence,
            )
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
