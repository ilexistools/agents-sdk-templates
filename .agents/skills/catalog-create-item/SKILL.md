---
name: catalog-create-item
description: Create or change a catalog agent or tool (app/agents, app/tools) following the project standard, with manifest, Pydantic contract, runnable examples, README and tests, all in English. Use when asked to add, build, publish, document or modify an agent, tool, capability or MCP tool exposed by this project's dashboard, API, CLI or MCP server.
---

# Create or change a catalog item

Work from the repository root. The code is the source of truth; these files
summarize it:

- `docs/catalog-standards.md`: the rules (read it fully the first time).
- `docs/architecture.md`: how discovery, execution, settings and providers fit.
- References: `app/tools/word_count/` (tool) and `app/agents/summarizer/` (agent).

Write everything in English. Never edit `app/catalog*.py`, `app/catalog.html`,
`app/settings.py` or `app/security.py` for a single item; if the standard does
not fit, stop and use the `catalog-extend-platform` skill to propose a change.

## Workflow

1. **Classify.** Tool when the task fits deterministic code (parsing, math,
   lookups, HTTP calls to an API). Agent only when it needs an LLM (language,
   judgment, generation). A task can be a tool that an agent uses.
2. **Name it.** `id` in snake_case, a noun or verb-noun (`date_extractor`,
   `invoice_reviewer`). It becomes the MCP tool name and the API route, so it
   cannot change after publication. Reuse an existing `category`:
   `python -m app catalog list` shows them.
3. **Generate.** `uv run --locked python -m app catalog new <tool|agent> <id> --title "<Title>"`.
4. **Contract.** In `handler.py`, design `Input`/`Output` first; every field gets
   `Field(description=...)` and the right constraints.
   - Tools: read [references/tools.md](references/tools.md).
   - Agents: read [references/agents.md](references/agents.md).
5. **Manifest.** Fill `item.toml`: description = one sentence starting with a
   present-tense verb (≤ 120 chars), `tags`, `requires` for extra settings, and
   2–3 realistic `[[examples]]` (tools: with exact `output`).
6. **Docs.** Fill the six README sections. Explain behavior for someone who has
   never read the code; do not repeat the field list.
7. **Tests.** Follow [references/testing.md](references/testing.md). Tools must
   have their examples verified; add focused tests for edge cases and for any
   external call (mocked).
8. **Validate** and only finish when all pass:

   ```bash
   uv run --locked python -m app catalog check
   uv run --locked python -m unittest discover -s app/tests -v
   uv run --locked python -m app catalog run <id> --example 1
   ```

   Agents need a configured provider; if none is available, say the example was
   not run instead of claiming it works.

## Changing an existing item

- Changed `Input`/`Output`? Update examples, README, the prompt's `# OUTPUT`
  (agents) and bump `version`: major if a field was removed, renamed or made
  required; minor for new optional fields or behavior changes; patch for fixes.
- Never rename `id`. To replace an item, create a new one and disable the old.

## Done means

`check` prints OK, tests pass, examples were run (or you said why not), the
README is accurate, and no file outside the item's folders, its prompt and its
tests changed.
