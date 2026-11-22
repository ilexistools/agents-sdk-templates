# Changelog

## Unreleased

- Add bulk actions: an **Actions** section in the Filters sidebar enables or
  disables all items shown, or turns a channel on or off for them, with Undo;
  `PATCH /api/catalog` applies the same changes to several items (or all), and the
  CLI's `enable`/`disable` accept several ids, `--all`, `--type` and `--channel`.
- `catalog check` prints `FAIL` instead of the leftover Portuguese `FALHA`.
- Move search and filters into a left **Filters** sidebar: docked by default,
  collapsible to an icon rail with an active-filter badge (the choice is
  remembered), a drawer on small screens, a "Clear filters" button and `/` to
  search. The Category filter is always shown, listing every category with its count.
- Add an **MCP server** section to Settings: transport (stdio, streamable-http,
  sse), host and port, with the exact command or URL clients should use. The
  catalog MCP server now loads `.env`, so these settings apply to
  `python -m app mcp` without flags. `env-example` no longer sets
  `MCP_TRANSPORT`; MCP clients that start the server should pass `--transport stdio`.
- Serve the dashboard with `Cache-Control: no-cache`, so browsers never show a stale
  copy after an update.
- Fix the catalog MCP server over HTTP: `--transport streamable-http` and `sse`
  failed at startup (`Server.run()` has no `transport` argument in MCP SDK 2).
  Both now run under uvicorn, use `CATALOG_TOKEN` like the dashboard and refuse a
  non-local host without it; the compose `mcp` profile passes the token.
- Move the default ports away from the usual 8000/8001 so they do not clash with other
  development servers: the dashboard/API now uses **8787** (was 8000) and the
  catalog MCP server over HTTP **8888** (was 8001), including the Docker image and
  compose file. Override them with `--port`, `PORT` or `MCP_PORT`.
- Add `python -m app serve | mcp | catalog`, a single entry point that reads
  `HOST`/`PORT` and refuses to listen on a non-local address without a token.
- Add optional access protection: `CATALOG_TOKEN` requires a Bearer token or
  Basic auth on every request except `GET /health`; `CATALOG_SETTINGS_READONLY`
  makes Settings read-only. `.env` is loaded at startup so both can live there.
- Add a `Dockerfile`, `.dockerignore` and `docker-compose.yml` (with an optional
  MCP-over-HTTP profile) and a "Run and deploy" guide in the README.
- `GET /api/settings` now returns `{"readonly": ..., "fields": [...]}`.
- Add knowledge for AI coding assistants: `docs/architecture.md`, a rewritten
  `AGENTS.md` (project map, commands, rules, skill index), the
  `catalog-create-item` skill with tool, agent and testing references, and the new
  `catalog-review-item` and `catalog-extend-platform` skills.
- Make every skill visible to Claude Code through generated `.claude/skills/`
  pointers (`scripts/sync_skills.py`), checked by `app.tests.test_project_knowledge`.
- Settings listed in an item's `requires` now appear in Settings automatically;
  `requires` names must be `UPPER_SNAKE_CASE`, and `check` rejects provider keys there.
- Add `ItemError` for expected item failures, shown by every channel; missing
  settings are now checked in `execute`, so the CLI and MCP report them too.
- `test_catalog` checks that every agent handler calls `create_agent` with its own id.

## 0.8.0 — 2026-11-22

- Add a catalog of agents and tools: items in `app/agents/<id>/` and
  `app/tools/<id>/` are discovered automatically and published through a local
  dashboard (`GET /`), a REST API (`/api/catalog/...`), a CLI (`app.catalog_cli`)
  and an MCP server (`app.catalog_mcp`), with per-item enabled state and channels.
- Define the catalog standard in `docs/catalog-standards.md`: `item.toml`
  manifest (category, version, tags, requirements, runnable examples),
  `handler.py` contract with documented fields, and a per-item README. Add
  `catalog_cli new` (templates) and `catalog_cli check` (validation), plus the
  `word_count` tool and `summarizer` agent as reference items.
- Add provider-independent agents: `app/orchestration/providers.py` with presets
  for OpenAI, Anthropic, Gemini, DeepSeek, Mistral, Groq, OpenRouter, Ollama,
  LM Studio and any OpenAI-compatible server; `provider:model` references;
  `create_agent()`; and the `DEFAULT_MODEL` setting. Agents can pick a model per
  item in the dashboard.
- Add dashboard Settings to edit provider keys, local server addresses and the
  default model in `.env`; keys are write-only. Add a connection test that lists
  a provider's models (`POST /api/providers/{id}/models`).
- Add `AGENTS.md`, `CLAUDE.md` and the `catalog-create-item` skill so AI coding
  assistants follow the catalog standard. The catalog is in English.
- `GPTAgent` and `GPTLocalAgent` now let a constructor `model` argument replace
  the model of a Markdown definition loaded with `agent_id`.
- `load_environment()` honors `CATALOG_ENV_FILE`.

Behavior change: code that relied on `GPTAgent(agent_id=..., model=...)` ignoring
`model` now gets the passed model. Live calls were validated with OpenAI only;
other providers are covered by offline tests with mocked connections.

## 0.7.0 — 2026-11-02

- Add `GPTDecision` with synchronous/asynchronous calls, injectable lazy clients,
  named-question validation and complete SDK responses, including refusals and usage.
- Add grouped predicate/choice/score examples and explicit specialist routing with
  caller-selected confidence thresholds and review outcomes.
- Add offline Decisions transport/routing tests and document the API, configuration
  and examples; update the application and orchestration development skills.

## 0.6.0 — 2026-11-02

- Update OpenAI to 3.42.1, Agents SDK to 0.24.0 and the remaining dependencies;
  refresh the lockfile and align its project version with `pyproject.toml`.
- Migrate the sample server to MCP SDK 2.3.0 and its `MCPServer` API, preserving
  streamable HTTP, SSE and stdio transport options.
- Document DeepSeek configuration through the existing Chat Completions wrappers
  and add commented environment settings.
- Add four repository skills for creating agents, building applications,
  orchestrating workflows and integrating tools, with examples and a validator.
- Add a development-skills guide and offline tests for MCP integration and the
  executable skill examples.

Dependency compatibility: this version requires OpenAI SDK 3 and MCP SDK 2.
Custom code using MCP 1's `FastMCP` needs migration. Live DeepSeek calls and
sandbox backend execution were not part of the offline validation.
