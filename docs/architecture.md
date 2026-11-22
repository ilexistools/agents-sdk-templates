# Architecture

How the template fits together, for developers and AI coding assistants. Read
this before changing anything outside `app/agents/` and `app/tools/`. The rules
for writing items are in [catalog-standards.md](catalog-standards.md).

## Layers

```
            ┌───────────── channels ─────────────┐
 dashboard  │ catalog.html → catalog_api.py (REST)│   python -m app serve
 CLI        │ catalog_cli.py                      │   python -m app catalog …
 MCP        │ catalog_mcp.py                      │   python -m app mcp
            └──────────────────┬──────────────────┘
                               ▼
 catalog core      app/catalog.py   discover · check · state · execute
                               ▼
 items (yours)     app/tools/<id>/   app/agents/<id>/   item.toml + handler.py + README.md
                               ▼ (agents only)
 model layer       app/orchestration/providers.py → create_agent()
                   gpt_agent.py (OpenAI) · gpt_agent_local.py (any compatible provider)
                   util.py loads app/assets/agents/<id>.md
                               ▼
 configuration     app/settings.py (.env, Settings dialog) · app/security.py (token, read-only)
```

| Layer | Owner | Change it when |
|---|---|---|
| Items (`app/agents`, `app/tools`, `app/assets/agents/<id>.md`) | Project developers | Always: this is where features go |
| Catalog core, channels, dashboard | Template | The standard itself must change (propose it first) |
| Model layer | Template | Adding a provider (`PROVIDERS`) or a wrapper capability |
| Configuration and security | Template | Adding a platform-wide setting; never to weaken protection |

Keeping project code inside the items layer is what lets a project merge later
template updates without conflicts.

## Lifecycle of an item

1. **Discovery.** `catalog.discover()` reads every `app/{agents,tools}/*/item.toml`
   into an `Item` (Pydantic). The folder name must equal `id`, the parent folder
   must match `type`. There is no registry and no cache: every request rediscovers.
2. **Validation.** `catalog.check(item)` enforces the standard (README, prompt,
   documented `Input`/`Output` fields, `async run`, valid examples, `create_agent`
   in agent handlers). `python -m app catalog check` runs it for all items;
   `app/tests/test_catalog.py` runs it in the test suite.
3. **Description.** `catalog.describe(item)` turns the handler's Pydantic models
   into field lists (name, type, required, description), adds missing settings and,
   for agents, the resolved model. The dashboard and `GET /api/catalog/{id}` use it.
4. **Execution.** Every channel calls `catalog.execute(item, channel, payload)`:
   - refuses if the item is disabled or the channel is off (`Unavailable`);
   - validates `payload` with `handler.Input`;
   - sets the per-item model override (context variable `providers.model_override`);
   - awaits `handler.run(request)` and validates the result with `handler.Output`.

   Missing settings (from `requires` or the agent's provider) raise `Unavailable`
   before the handler runs. Channels translate errors: validation → 422,
   `ItemError` → its message (422 in the API), `Unavailable` → 409, anything else →
   a generic failure without internal details (502 in the API).

## State and configuration

| What | Where | Written by |
|---|---|---|
| Enabled flag, enabled channels, per-agent model | SQLite `.catalog.sqlite3` (`CATALOG_DB`) | Dashboard, API, CLI `enable`/`disable` |
| Provider keys, server addresses, default model, keys in `requires` | `.env` (`CATALOG_ENV_FILE`) | Settings dialog / `PUT /api/settings`, or by hand |
| Access token, read-only flag, host, port | Environment or `.env` | Operator only (never the dashboard) |

- `load_environment()` loads `.env` without overriding variables already set, so
  real environment variables (Docker, hosting secrets) win.
- Secrets are write-only: `GET /api/settings` returns a masked hint, never a value.
- A setting listed in an item's `requires` appears in Settings automatically
  (group "Agents and tools"); names containing KEY, TOKEN, SECRET or PASSWORD are
  treated as secrets.

## Model selection

`create_agent(agent_id, model=None, **kwargs)` resolves a `provider:model`
reference in this order: explicit `model` argument or dashboard choice → `model:`
in the prompt front matter → `DEFAULT_MODEL` → `openai:<OPENAI_MODEL_NAME>`.
`openai:` builds a `GPTAgent` (Responses API, native structured output); every
other provider builds a `GPTLocalAgent` against its OpenAI-compatible endpoint,
with the output schema in the instructions and local validation. Missing keys
raise `RuntimeError("Missing setting: …")` before any network call.

## Security model

- Without `CATALOG_TOKEN` the app has no authentication; `python -m app serve`
  therefore refuses non-loopback hosts unless a token is set.
- With `CATALOG_TOKEN`, `app/security.py` requires it on every route except
  `GET /health` (Bearer, or Basic with the token as password).
- `CATALOG_SETTINGS_READONLY=true` blocks `PUT /api/settings`.
- The MCP HTTP transports (`/mcp`, `/sse`) use the same token middleware, and
  `python -m app mcp` also refuses non-loopback hosts without `CATALOG_TOKEN`.
  The stdio transport needs no token: it only talks to the process that started it.
- Item code runs with the server's permissions. Items must not read secrets other
  than those in `requires`, write outside their folder, or execute untrusted input.

## Extension points

| Goal | Do this | Do not |
|---|---|---|
| New capability | `python -m app catalog new tool <id>` (or `new agent <id>`) and fill the files | Add routes in `catalog_api.py` or `main.py` |
| Tool needs an API key or URL | Add it to `requires` (appears in Settings) and read it with `os.environ` / `configured_value` at run time | Hard-code it, or add it to `settings.FIELDS` |
| Agent needs a specific model | `model: provider:model` in its prompt, or choose it in the dashboard | Import `GPTAgent`/`GPTLocalAgent` in the handler |
| Agent uses a tool | Pass `tools=[...]` to `create_agent` (Agents SDK `function_tool`); keep the tool's logic in a pure function | Call another item's handler module directly from the dashboard path |
| New provider | One `Provider(...)` entry in `PROVIDERS` + key in `env-example` | Provider-specific branches in handlers |
| Platform-wide setting | `settings.FIELDS` + `env-example` + docs | Items reading undeclared settings |

## Tests

| Suite | Guarantees |
|---|---|
| `test_catalog` | Every item passes `check`; tool examples return their expected output; agent handlers call `create_agent` with their own id and `Output`; API, MCP filtering, generator, settings, providers |
| `test_deploy` | Entry point, token, read-only settings |
| `test_skill_examples`, `test_mcp_server`, `test_gpt_decision` | Template examples and wrappers |

All run offline: `uv run --locked python -m unittest discover -s app/tests -v`.
