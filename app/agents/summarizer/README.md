# Summarizer

> Agent `summarizer`. Summarizes a text in its original language, keeping facts,
> conclusions and caveats. It is the reference example for LLM-based agents.

## When to use

- Condensing meeting notes, emails, articles or reports for quick reading.
- **Do not** use it to translate (see the `translator` agent in `app/assets/agents/`)
  or when every number in the text must be reproduced exactly.

## How it works

A catalog agent has two parts:

| Part | File | Responsibility |
|---|---|---|
| Contract | `app/agents/summarizer/handler.py` | Defines `Input` and `Output` and calls the agent |
| Behavior | `app/assets/agents/summarizer.md` | Role, goal and model instructions |

Flow of a run:

1. A channel (API, CLI or MCP) receives `{"text": "..."}` and the catalog checks
   that the item is enabled on that channel.
2. `handler.py` validates the input with `Input` (the text cannot be empty).
3. `GPTAgent(agent_id="summarizer")` reads `summarizer.md`: the front matter sets `role`,
   `goal` and `max_tokens`, and every section (`# INPUT`, `# OUTPUT`, `# INSTRUCTIONS`,
   `# KNOWLEDGE`) is appended to the instructions sent to the model.
4. The model answers with `output_type=Output`, that is, JSON with `summary`.
5. The catalog validates the answer with `Output` before returning it to the channel.

To change **what** the agent does, edit the `.md` file. To change the **shape** of
the input or output, edit `handler.py`, the `# OUTPUT` section of the `.md` file,
the examples in `item.toml`, and bump `version`.

## Example

```powershell
uv run --locked python -m app.catalog_cli run summarizer --example 1
```

Output (varies between runs): `{"summary": "The 2027 budget was approved with 8% more for research; the travel cut was postponed to March."}`

## Requirements and limitations

- Requires `OPENAI_API_KEY` (set it in the dashboard's **Settings**); the model can be changed there too (`OPENAI_MODEL_NAME`).
- `max_tokens: 768` limits the summary length.
- Very long texts may exceed the model's context window; split them first.
