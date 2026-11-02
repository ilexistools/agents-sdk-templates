"""Thin sync/async wrapper around the OpenAI Decisions API."""

from collections.abc import Iterable
from functools import cached_property
from typing import Any

from openai import AsyncOpenAI, OpenAI
from openai.types.decision import Decision
from openai.types.decision_create_params import InputUnionMember1, Question

from app.orchestration.config import decision_model, load_environment


DecisionInput = str | Iterable[InputUnionMember1]


class GPTDecision:
    """Return the SDK Decision, preserving answers, refusals, model and usage.

    Clients are injectable and created lazily. Questions must have unique names.
    Extra run options are forwarded to decisions.create (e.g. timeout or caching).
    """

    def __init__(
        self,
        *,
        model: str | None = None,
        client: OpenAI | None = None,
        async_client: AsyncOpenAI | None = None,
    ):
        load_environment()
        self.model = model if model is not None else decision_model()
        if not self.model.strip():
            raise ValueError("A Decisions model must be configured.")
        self._client = client
        self._async_client = async_client

    @cached_property
    def client(self) -> OpenAI:
        return self._client if self._client is not None else OpenAI()

    @cached_property
    def async_client(self) -> AsyncOpenAI:
        return self._async_client if self._async_client is not None else AsyncOpenAI()

    @staticmethod
    def _questions(questions: Iterable[Question]) -> list[Question]:
        items = list(questions)
        if not 1 <= len(items) <= 400:
            raise ValueError("Provide between 1 and 400 questions.")
        names = set()
        for question in items:
            if question.get("type") not in {"predicate", "choice", "score"}:
                raise ValueError("Question type must be predicate, choice or score.")
            name = question.get("name")
            if not isinstance(name, str) or not name.strip() or name in names:
                raise ValueError("Each question must have a non-empty, unique name.")
            names.add(name)
        return items

    async def run(
        self, input: DecisionInput, *, questions: Iterable[Question], **request_options: Any
    ) -> Decision:
        items = self._questions(questions)
        return await self.async_client.decisions.create(
            model=self.model, input=input, questions=items, **request_options
        )

    def run_sync(
        self, input: DecisionInput, *, questions: Iterable[Question], **request_options: Any
    ) -> Decision:
        items = self._questions(questions)
        return self.client.decisions.create(
            model=self.model, input=input, questions=items, **request_options
        )
