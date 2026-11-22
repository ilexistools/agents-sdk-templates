# __TITLE__

> Agent `__ID__`. Summarize here, in one sentence, what it does.

## When to use

- A situation the agent solves.
- A situation where it should **not** be used (and what to use instead).

## How it works

1. `handler.py` validates the input (`Input`).
2. `GPTAgent` loads the prompt from `app/assets/agents/__ID__.md`.
3. The model answers in the `Output` format, which is validated before being returned.

Explain the prompt decisions that are not obvious.

## Input and output

The fields are documented in `handler.py` and shown in the catalog dashboard.

## Example

```powershell
uv run --locked python -m app.catalog_cli run __ID__ --example 1
```

## Requirements and limitations

- Requires `OPENAI_API_KEY` (set it in the dashboard's **Settings**).
- LLM answers vary between runs; do not use it for exact calculations.
