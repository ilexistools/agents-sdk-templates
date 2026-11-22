"""__TITLE__ (tool).

Catalog contract: Input, Output and async run. Keep the logic deterministic
and testable without network access. Document every field with description:
the text is shown in the dashboard, the API docs and the MCP schema.
"""

from pydantic import BaseModel, Field


class Input(BaseModel):
    text: str = Field(min_length=1, description="Input text.")


class Output(BaseModel):
    result: str = Field(description="Processing result.")


async def run(request: Input) -> Output:
    return Output(result=request.text)
