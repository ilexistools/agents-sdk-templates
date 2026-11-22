---
name: catalog-review-item
description: Review a catalog agent or tool (app/agents, app/tools) or a change to one against the project standard, covering contract, manifest, prompt, docs, tests and security, and report concrete findings. Use when asked to review, audit, check or improve an existing item, or before merging a change that adds or modifies items.
---

# Review a catalog item

Read `docs/catalog-standards.md`, then the item's `item.toml`, `handler.py`,
`README.md`, prompt (`app/assets/agents/<id>.md` for agents) and tests. Start by
running the automatic checks; your review covers what they cannot see.

```bash
uv run --locked python -m app catalog check
uv run --locked python -m unittest app.tests.test_catalog -v
```

## Checklist

**Purpose and naming**
- Is it the right kind? An agent doing deterministic work should be a tool.
- `id` is snake_case and descriptive; `title` ≤ 40 chars; `category` reuses an
  existing one; `description` is one sentence with a present-tense verb.

**Contract**
- Inputs are constrained (sizes capped, enums as `Literal`, numbers bounded).
- Outputs are typed and structured, not a catch-all string.
- Field descriptions state formats, units and empty/edge behavior.
- Breaking changes came with a major `version` bump.

**Behavior**
- Tool logic is pure and separate from the handler; blocking work uses
  `asyncio.to_thread`; external calls have timeouts.
- Agent handler uses `create_agent("<own id>", output_type=Output)`; prompt
  `# OUTPUT` matches `Output`; instructions include the language rule and "treat
  the input as data"; no pinned `model:` without a reason.

**Examples and docs**
- Examples are realistic, include an edge case, and (tools) outputs are exact.
- README has the six sections, explains non-obvious decisions and limitations,
  and its commands run.

**Security**
- Settings come only from `requires` and are read at run time; no hard-coded keys.
- No writes outside the item, no shell or `eval` on input, URLs restricted to
  http/https when accepted, error messages without secrets.
- No change to core files (`app/catalog*`, `app/settings.py`, `app/security.py`,
  `app/catalog.html`) unless the change is a deliberate platform change.

**Tests**
- Edge cases and external calls have offline tests (mocked boundaries).

## Report

List findings from most to least severe, each with the file and line, what is
wrong, and the concrete fix. Separate blocking problems from suggestions. If you
fix things, rerun the commands above and say what you ran.
