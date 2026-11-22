"""__TITLE__ (agent).

Catalog contract: Input, Output and async run. The model behavior lives in
app/assets/agents/__ID__.md; this file only adapts the input, calls the agent
and returns the structured output. create_agent picks the provider and model
(dashboard choice, prompt front matter or the default model), so do not
instantiate a specific wrapper here. Document every field with description:
the text is shown in the dashboard, the API docs and the MCP schema.
"""

from pydantic import BaseModel, Field

from app.orchestration.providers import create_agent


class Input(BaseModel):
    text: str = Field(min_length=1, description="Text the agent should process.")


class Output(BaseModel):
    result: str = Field(description="Answer produced by the agent.")


async def run(request: Input) -> Output:
    agent = create_agent("__ID__", output_type=Output)
    return await agent.run(request.text)
