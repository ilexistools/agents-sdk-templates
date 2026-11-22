# Changelog

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
