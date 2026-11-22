---
name: catalog-create-item
description: Create or change a catalog agent or tool (app/agents, app/tools) following the project standard, with manifest, Pydantic contract, runnable examples and README, all in English. Use when asked to add, publish, document or modify an item shown in the catalog dashboard, API, CLI or MCP server.
---

# Create or change a catalog item

Read `docs/catalog-standards.md` in full before starting. Use
`app/tools/word_count/` (tool) and `app/agents/summarizer/` (agent) as references.
Write everything in English.

## Workflow

1. **Classify.** A tool if the task fits deterministic code; an agent only if it
   needs an LLM. When in doubt, prefer a tool.
2. **Generate the skeleton.**
   `uv run --locked python -m app.catalog_cli new <agent|tool> <id> --title "<Title>"`
3. **Fill in the contract** in `handler.py`: fields with `description`, Pydantic
   constraints, and pure logic (tool) or a `create_agent()` call (agent).
4. **Fill in the manifest** `item.toml`: a description starting with a present-tense
   verb (up to 120 characters), an existing `category` whenever possible, `requires`,
   and realistic examples (with `output` for tools).
5. **Agents:** write `app/assets/agents/<id>.md`; its `# OUTPUT` section reproduces
   `Output`. For prompt-writing techniques, use the `agents-template-criar-agente` skill.
6. **Document** the six standard sections in the item's `README.md`.
7. **Validate** and finish only when everything passes:
   - `uv run --locked python -m app.catalog_cli check`
   - `uv run --locked python -m unittest app.tests.test_catalog -v`
   - `uv run --locked python -m app.catalog_cli run <id> --example 1`
     (agents need a configured provider in the dashboard's Settings; without one,
     report that the example was not run).

## Changing existing items

Did `Input` or `Output` change? Update the examples, README, prompt and `version`
(major when it breaks compatibility). Never rename the `id` of a published item.
