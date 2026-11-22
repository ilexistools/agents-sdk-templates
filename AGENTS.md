# Instructions for AI assistants

## Catalog of agents and tools

When creating or changing any item in `app/agents/` or `app/tools/`, follow
[docs/catalog-standards.md](docs/catalog-standards.md). Mandatory summary:

1. **English everywhere**: manifests, field descriptions, prompts, READMEs, messages and UI text.
2. Create new items with the generator, never by copying folders:
   `uv run --locked python -m app.catalog_cli new <agent|tool> <id> --title "<Title>"`.
3. Each item has `item.toml`, `handler.py` and `README.md`; agents also have
   `app/assets/agents/<id>.md`.
4. `handler.py` exposes only `Input`, `Output` and `async def run(request: Input) -> Output`;
   every field has `Field(description=...)`.
5. `item.toml` has at least one `[[examples]]`; tools include the expected `output`.
6. When `Input`/`Output` changes, update the examples, the README, the prompt's
   `# OUTPUT` section (agents) and bump `version` (SemVer).
7. Agent handlers build the agent with `create_agent()` from `app/orchestration/providers.py`,
   never with a specific wrapper, so any provider works. Never hard-code API keys or providers;
   new providers go in `PROVIDERS` and `env-example`.
8. Before finishing, run and keep passing:
   - `uv run --locked python -m app.catalog_cli check`
   - `uv run --locked python -m unittest app.tests.test_catalog -v`

Do not change `app/catalog*.py` or `app/catalog.html` to accommodate a single item:
if the standard does not fit the case, propose a change to the standard.
