# Changelog

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
