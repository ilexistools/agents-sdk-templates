# Instructions for AI coding assistants

This repository is a template for building **agents and tools** that are published
automatically through a dashboard, a REST API, a CLI and an MCP server. Most work
happens in `app/agents/` and `app/tools/`; the rest is the platform.

## Read first

| Guide | When |
|---|---|
| [docs/catalog-standards.md](docs/catalog-standards.md) | Before creating or changing any agent or tool |
| [docs/architecture.md](docs/architecture.md) | Before changing anything outside `app/agents/` and `app/tools/` |
| [README.md](README.md) | Setup, providers, running and deployment |

## Skills

Use the matching skill; Codex finds them in `.agents/skills/`, Claude Code in
`.claude/skills/` (generated pointers to the same files).

| Skill | Use for |
|---|---|
| `catalog-create-item` | Creating or changing an agent or tool, with its tests and docs |
| `catalog-review-item` | Reviewing or auditing an item or a change to one |
| `catalog-extend-platform` | Providers, platform settings, manifest fields, API, dashboard, security |
| `agents-template-criar-agente` | Markdown agent definitions for the wrappers (Portuguese) |
| `agents-template-criar-aplicacao` | Python features and FastAPI endpoints using the wrappers (Portuguese) |
| `agents-template-orquestrar-agentes` | Multi-agent flows, handoffs and Decisions routing (Portuguese) |
| `agents-template-integrar-ferramentas` | Python tools, MCP connections and sandbox (Portuguese) |

Edit skills only in `.agents/skills/`, then run
`uv run --locked python scripts/sync_skills.py` to refresh `.claude/skills/`.

## Project map

| Path | What it is |
|---|---|
| `app/tools/<id>/`, `app/agents/<id>/` | Catalog items: `item.toml`, `handler.py`, `README.md` |
| `app/assets/agents/<id>.md` | Agent prompts (front matter + `# INPUT/OUTPUT/INSTRUCTIONS/KNOWLEDGE`) |
| `app/templates/catalog/` | Templates used by `python -m app catalog new` |
| `app/catalog.py` | Discovery, validation (`check`), state, `execute`, `ItemError` |
| `app/catalog_api.py`, `app/catalog.html` | REST API and dashboard |
| `app/catalog_cli.py`, `app/catalog_mcp.py` | CLI and MCP channels |
| `app/orchestration/providers.py` | Providers, `provider:model` references, `create_agent()` |
| `app/settings.py`, `app/security.py` | Settings in `.env`; token and read-only mode |
| `app/tests/` | Offline tests (`test_catalog`, `test_deploy`, `test_project_knowledge`, ...) |

## Commands

```bash
uv run --locked python -m app serve                    # dashboard + API, http://127.0.0.1:8787
uv run --locked python -m app catalog new tool <id> --title "<Title>"
uv run --locked python -m app catalog new agent <id> --title "<Title>"
uv run --locked python -m app catalog check            # validate every item
uv run --locked python -m app catalog run <id> --example 1
uv run --locked python -m app catalog disable <id>... | --all | --type tool [--channel mcp]
uv run --locked python -m unittest discover -s app/tests -v
```

Always run from the repository root with `uv run --locked`.

## Rules

1. **English everywhere**: manifests, field descriptions, prompts, READMEs, messages and UI.
2. Create items with the generator, never by copying folders.
3. `handler.py` exposes only `Input`, `Output` and `async def run(request: Input) -> Output`;
   every field has `Field(description=...)`.
4. Agent handlers call `create_agent("<own id>", output_type=Output)`; never import a
   specific wrapper, so the provider stays a configuration choice.
5. Tools keep logic in pure functions, cap input sizes and raise `ItemError` for
   expected failures. Every setting an item needs goes in `requires` (it appears in
   Settings); never hard-code keys and never list the model provider's key.
6. `item.toml` has realistic `[[examples]]`; tools include the exact `output`.
7. When `Input`/`Output` change, update examples, README and the prompt's `# OUTPUT`,
   and bump `version` (SemVer).
8. Do not change `app/catalog*`, `app/settings.py`, `app/security.py` or
   `app/catalog.html` to accommodate one item. Platform changes follow
   `catalog-extend-platform`. Never weaken the token requirement for non-local hosts.
9. Tests run offline: mock `create_agent` and network boundaries. Before finishing,
   `catalog check` and the full test suite must pass. Say which live checks you ran
   and which you could not.
10. Never commit `.env`, `.catalog.sqlite3` or real keys.
