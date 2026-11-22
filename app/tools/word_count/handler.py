"""Word counter (tool).

Adapts the pure function ``count_words`` to the catalog contract.
"""

from pydantic import BaseModel, Field

from app.mcp_tools.tools import count_words


class Input(BaseModel):
    text: str = Field(description="Text to analyze. Words are separated by any whitespace.")


class Output(BaseModel):
    word_count: int = Field(description="Number of words.")
    character_count: int = Field(description="Number of characters, excluding spaces and line breaks.")


async def run(request: Input) -> Output:
    return Output(**count_words(request.text))
