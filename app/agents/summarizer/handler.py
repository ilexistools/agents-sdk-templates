"""Summarizer (agent).

The model behavior lives in ``app/assets/agents/summarizer.md``.
This handler only validates the input, calls the agent and returns the structured output.
``create_agent`` picks the provider and model (see docs/catalog-standards.md).
"""

from pydantic import BaseModel, Field

from app.orchestration.providers import create_agent


class Input(BaseModel):
    text: str = Field(min_length=1, description="Text to summarize, in any language.")


class Output(BaseModel):
    summary: str = Field(description="Faithful, concise summary in the same language as the input text.")


async def run(request: Input) -> Output:
    agent = create_agent("summarizer", output_type=Output)
    return await agent.run(request.text)
