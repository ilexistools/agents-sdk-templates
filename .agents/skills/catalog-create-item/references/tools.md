# Writing a tool

A tool is deterministic Python exposed through the catalog. Same input, same
output; no LLM.

## Shape

```python
"""Date extractor (tool).

Adapts the pure function ``extract_dates`` to the catalog contract.
"""

from datetime import date

from pydantic import BaseModel, Field


class Input(BaseModel):
    text: str = Field(min_length=1, max_length=20_000, description="Text that may contain dates.")
    day_first: bool = Field(True, description="Read 03/04/2026 as 3 April (true) or March 4 (false).")


class Output(BaseModel):
    dates: list[date] = Field(description="Dates found, in order of appearance, without duplicates.")


def extract_dates(text: str, day_first: bool = True) -> list[date]:
    ...  # pure logic: no I/O, no globals, easy to test


async def run(request: Input) -> Output:
    return Output(dates=extract_dates(request.text, request.day_first))
```

## Rules

- **Logic in pure functions**, the handler only adapts. Put the function in the
  same `handler.py` for small tools, or in a module next to it
  (`app/tools/<id>/logic.py`) when it grows. Import with the full path
  (`from app.tools.<id>.logic import ...`).
- **Constrain inputs** with Pydantic (`min_length`, `max_length`, `ge`, `le`,
  `Literal[...]`, `pattern`). Always cap text and list sizes so a call cannot
  exhaust memory or time.
- **Output types are precise**: `int`, `float`, `date`, `list[...]`, nested
  models. Avoid a single `result: str` when the result has structure.
- **Field names** in snake_case English; field descriptions say units, formats and
  edge-case behavior ("empty list when nothing is found").
- **Errors.** Invalid input is Pydantic's job. For other expected failures (not
  found, upstream refused), raise `ItemError("City not found.")` from
  `app.catalog`: every channel shows that message (API 422, MCP error, CLI).
  Any other exception is reported only as a generic failure. Never put secrets
  or stack traces in messages.
- **Blocking work** (CPU-heavy loops, blocking I/O) runs in a thread:
  `return await asyncio.to_thread(work, ...)`.

## Tools that call an external service

- Declare every setting the tool needs in `item.toml`:
  `requires = ["WEATHER_API_KEY"]`. It then appears in the dashboard's Settings
  (group "Agents and tools"), runs are blocked while it is missing, and the
  dashboard warns.
- Read it at run time, not at import time:

  ```python
  from app.settings import configured_value

  async def run(request: Input) -> Output:
      key = configured_value("WEATHER_API_KEY")
  ```

- Use the standard library (`urllib.request`) or a declared dependency; add new
  dependencies to `pyproject.toml` with `uv add <package>` and mention them in the
  README. Always set a timeout (≤ 30 s) and run blocking calls with
  `asyncio.to_thread`.
- Validate and limit what you send (no arbitrary URLs from input unless that is
  the purpose; if it is, allow only `http`/`https`).
- Examples with `output` must not depend on the network: use an offline example
  in `item.toml` only if the result is stable; otherwise omit `output` for that
  example and cover the behavior with a mocked test (see testing.md).

## Manifest checklist

- `category` reused when possible; `tags` include `offline` or `network`.
- At least two examples, one showing an edge case (empty input, unusual format).
- `channels`: drop `mcp` if the tool should not be callable by external agents.
