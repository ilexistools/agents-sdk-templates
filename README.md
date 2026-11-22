# OpenAI agents SDK templates

A Python starter project for building typed model integrations, agent workflows and decision-based routing. Run agents on OpenAI, Anthropic, Gemini, DeepSeek, Mistral, Groq, OpenRouter, Ollama, LM Studio or any OpenAI-compatible server; publish them through a local dashboard, REST API, CLI and MCP server; add tools through MCP; or experiment with sandbox execution and reusable skills.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Latest tag](https://img.shields.io/github/v/tag/ilexistools/agents-sdk-templates?label=version)](https://github.com/ilexistools/agents-sdk-templates/tags)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

The template keeps orchestration visible in ordinary Python: wrappers handle model calls, Pydantic models describe outputs, Markdown files define agents, and application code controls execution. It is intended for learning, prototyping and adapting these patterns to your own application.

[Getting started](#getting-started) · [Catalog](#catalog-of-agents-and-tools) · [Providers and models](#providers-and-models) · [Run and deploy](#run-and-deploy) · [Wrapper reference](#wrapper-reference) · [Decisions](#decisions-and-routing) · [Development skills](#skills-for-coding-agents) · [Changelog](CHANGELOG.md)

## What you can build

- **A catalog of agents and tools:** drop a folder into `app/agents/` or `app/tools/` and it appears in a local dashboard, the REST API, a CLI and an MCP server, with generated documentation and runnable examples.
- **Typed model integrations:** extract or generate data with explicit Pydantic output contracts.
- **Specialist workflows:** run mandatory processing stages, configure handoffs, or expose an agent as a tool.
- **Decision-based triage:** classify requests, evaluate conditions and score inputs before selecting a specialist.
- **Provider-independent agents:** choose a model as `provider:model` (for example `anthropic:claude-sonnet-5-5` or `ollama:llama3.2`) without changing code.
- **Tool-enabled agents:** connect Python functions and MCP servers to the Agents SDK wrappers.
- **Sandbox experiments:** make task-specific skills available to an agent with a configured execution backend.
- **HTTP integrations:** adapt the included FastAPI application and runnable endpoint examples.

The repository includes executable examples, offline regression tests, seven skills for coding agents and focused guides for the [architecture](docs/architecture.md), [catalog standards](docs/catalog-standards.md), [Decisions](docs/decisions.md) and [development skills](docs/development-skills.md).

## Contents

- [Getting started](#getting-started)
- [Catalog of agents and tools](#catalog-of-agents-and-tools)
- [Providers and models](#providers-and-models)
- [Run and deploy](#run-and-deploy)
- [Wrapper reference](#wrapper-reference)
- [Configuration](#configuration)
- [Typed outputs and execution](#typed-outputs-and-execution)
- [Markdown agent definitions](#markdown-agent-definitions)
- [Local models and compatible providers](#local-models-and-compatible-providers)
- [DeepSeek API](#deepseek-api)
- [Agent orchestration](#agent-orchestration)
- [Decisions and routing](#decisions-and-routing)
- [Python tools and MCP](#python-tools-and-mcp)
- [Sandbox execution and runtime skills](#sandbox-execution-and-runtime-skills)
- [FastAPI application](#fastapi-application)
- [Skills for coding agents](#skills-for-coding-agents)
- [Examples and tests](#examples-and-tests)
- [Project structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Scope and compatibility](#scope-and-compatibility)
- [Contributing](#contributing)
- [License](#license)

## Getting started

### 1. Set up the project

You need Python 3.12 or later and [uv](https://docs.astral.sh/uv/). Python 3.12 is the version selected by the repository's `.python-version` file.

```bash
git clone https://github.com/ilexistools/agents-sdk-templates.git
cd agents-sdk-templates
uv sync --locked
```

`uv sync --locked` creates `.venv` and installs the versions recorded in `uv.lock`. The commands below use `uv run --locked`, so you do not need to activate the environment manually. Run them from the repository root.

### 2. Check the installation without a provider key

Run the offline tests:

```bash
uv run --locked python -m unittest discover -s app/tests -v
```

Or start the application:

```bash
uv run --locked python -m app serve
```

Open [the catalog dashboard](http://localhost:8000/), [the health endpoint](http://localhost:8000/health) or [the interactive API documentation](http://localhost:8000/docs). The `word_count` tool runs offline from the dashboard; agents need a provider (next step).

### 3. Configure your provider

**From the dashboard (simplest).** Click the gear icon to open **Settings**, paste the key of the provider you use (or the address of a local server such as Ollama), click **Test connection**, and set **Default model** as `provider:model`, for example `openai:gpt-4.1-mini` or `ollama:llama3.2`. Settings writes the values to `.env`.

**By editing `.env`.** Copy the environment template:

**macOS / Linux**

```bash
cp env-example .env
```

**Windows PowerShell**

```powershell
Copy-Item env-example .env
```

Set `DEFAULT_MODEL` and the key of your provider (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, ...); see [Providers and models](#providers-and-models). `.env` is ignored by Git.

A real OpenAI key is needed for the OpenAI-only wrappers (`GPT`, Decisions and the sandbox examples). Catalog agents run on whichever provider you choose; local servers need no key. The offline tests and the dashboard's offline tool do not require a provider key.

### 4. Make your first typed model call

Save this as `app/examples/quickstart.py`:

```python
from pydantic import BaseModel
from app.orchestration.gpt import GPT

class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str]

model = GPT(
    instructions="Summarize the supplied text clearly and identify its key points.",
    output_type=SummaryResponse,
)
result = model.run_sync(
    "The team completed the prototype. User testing starts next week. "
    "The remaining task is to document the integration."
)
print(result.model_dump_json(indent=2))
```

Run it with your OpenAI key configured:

```bash
uv run --locked python -m app.examples.quickstart
```

This makes a real API call. The generated output follows your Python contract; its contents depend on the model.

To run the same kind of task on any provider, use `create_agent` with a model reference:

```python
import asyncio
from pydantic import BaseModel
from app.orchestration.providers import create_agent

class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str]

agent = create_agent(
    model="anthropic:claude-sonnet-5-5",   # or "ollama:llama3.2", "gemini:gemini-2.5-flash", ...
    name="Summarizer",
    instructions="Summarize the supplied text clearly and identify its key points.",
    output_type=SummaryResponse,
)
print(asyncio.run(agent.run("The team completed the prototype. User testing starts next week.")))
```

## Catalog of agents and tools

The application includes a catalog: every folder in `app/agents/` or `app/tools/` that follows the [catalog standards](docs/catalog-standards.md) is discovered automatically and published, with no registration code, in:

| Channel | How to use it |
|---|---|
| Dashboard | http://127.0.0.1:8000: filter by type, category, channel and status; open an item to see its contract, choose its model, run its examples and enable or disable it |
| REST API | `GET /api/catalog`, `GET /api/catalog/{id}`, `POST /api/catalog/{id}/run`, `PATCH /api/catalog/{id}` (`{"active": false}`), `PATCH /api/catalog/{id}/channels`, `PATCH /api/catalog/{id}/model` |
| CLI | `uv run --locked python -m app.catalog_cli list \| check \| new \| run \| enable \| disable` |
| MCP | `uv run --locked python -m app.catalog_mcp` (stdio by default; see below) |

The dashboard is an admin tool: without `CATALOG_TOKEN` it has no authentication, so it only listens on `127.0.0.1`. See [Run and deploy](#run-and-deploy) to protect it with a token and run it elsewhere.

```powershell
uv run --locked python -m app.catalog_cli list
uv run --locked python -m app.catalog_cli run word_count --example 1
'{"text":"one two"}' | uv run --locked python -m app.catalog_cli run word_count --input -
uv run --locked python -m app.catalog_cli disable word_count
uv run --locked python -m app.catalog_cli enable word_count
```

**Reference items.** `word_count` is a deterministic tool that works offline. `summarizer` is an agent that takes `{"text": "..."}` and runs on the configured model. Each has a README explaining how it works: [word_count](app/tools/word_count/README.md), [summarizer](app/agents/summarizer/README.md).

**Adding an item.** Use the generator, which creates the manifest, contract, README and (for agents) the prompt, then validate:

```powershell
uv run --locked python -m app.catalog_cli new tool date_extractor --title "Date extractor"
uv run --locked python -m app.catalog_cli new agent reviewer --title "Text reviewer"
uv run --locked python -m app.catalog_cli check
uv run --locked python -m unittest app.tests.test_catalog -v
```

**State.** Items start enabled. Enabled state, channels and per-agent model choices are stored in `.catalog.sqlite3` in the repository root (not versioned); point every process to another file with `CATALOG_DB`. Settings are stored in `.env`; use `CATALOG_ENV_FILE` to point to another file.

**MCP server.** Configure the client to start `uv run --locked python -m app.catalog_mcp` over stdio, with the repository root as the working directory. The server lists only items that are enabled with the MCP channel on; the client may need to refresh its tool list after a change. Three transports are available, selected by argument or by `MCP_TRANSPORT`:

```powershell
uv run --locked python -m app.catalog_mcp --transport stdio
uv run --locked python -m app.catalog_mcp --transport streamable-http --host 127.0.0.1 --port 8001
uv run --locked python -m app.catalog_mcp --transport sse --host 127.0.0.1 --port 8001
```

Streamable HTTP is served at `http://127.0.0.1:8001/mcp` and SSE at `http://127.0.0.1:8001/sse`. Configure Codex or Claude Code with stdio for a local subprocess, or with the HTTP MCP URL when the client and server can reach each other over the network. Restart the MCP server after changing Settings so it picks up new values.

AI coding assistants (Codex, Claude Code and others) get the same rules from [AGENTS.md](AGENTS.md)/[CLAUDE.md](CLAUDE.md), the [architecture guide](docs/architecture.md) and the `catalog-*` skills; see [Skills for coding agents](#skills-for-coding-agents).

## Providers and models

Agents built with `create_agent` (all catalog agents) are provider-independent. A **model reference** names the provider and the model:

| Provider | Reference prefix | Setting | Example |
|---|---|---|---|
| OpenAI | `openai:` | `OPENAI_API_KEY` | `openai:gpt-4.1-mini` |
| Anthropic | `anthropic:` | `ANTHROPIC_API_KEY` | `anthropic:claude-sonnet-5-5` |
| Google Gemini | `gemini:` | `GEMINI_API_KEY` | `gemini:gemini-2.5-flash` |
| DeepSeek | `deepseek:` | `DEEPSEEK_API_KEY` | `deepseek:deepseek-flash` |
| Mistral | `mistral:` | `MISTRAL_API_KEY` | `mistral:mistral-large-latest` |
| Groq | `groq:` | `GROQ_API_KEY` | `groq:llama-3.3-70b-versatile` |
| OpenRouter | `openrouter:` | `OPENROUTER_API_KEY` | `openrouter:openai/gpt-4.1-mini` |
| Ollama | `ollama:` | `OLLAMA_BASE_URL` (no key) | `ollama:llama3.2:3b` |
| LM Studio | `lmstudio:` | `LMSTUDIO_BASE_URL` (no key) | `lmstudio:local-model` |
| Any OpenAI-compatible server | `local:` | `LOCAL_BASE_URL`, `LOCAL_API_KEY` | `local:my-model` |

Everything after the first `:` is the model name. A reference without a known prefix uses the default provider. Model names in the table are examples: use **Test connection** in Settings (or `POST /api/providers/{id}/models`) to list the models your account actually has.

**Which model an agent uses** (first match wins): the model passed to `create_agent(model=...)` or chosen for the agent in the dashboard; then `model:` in the agent's Markdown front matter; then `DEFAULT_MODEL` (which falls back to `openai:<OPENAI_MODEL_NAME>`).

**How it works.** [app/orchestration/providers.py](app/orchestration/providers.py) holds the provider presets. `create_agent` returns a `GPTAgent` (OpenAI Responses API, native structured output) for `openai:` and a `GPTLocalAgent` (Chat Completions, JSON schema in the instructions, validated locally) for every other provider. It raises `RuntimeError("Missing setting: ...")` when the provider's key is not configured. To add a provider with an OpenAI-compatible endpoint, add one `Provider(...)` entry to `PROVIDERS` and its key to `env-example`; Settings lists it automatically.

Provider compatibility still varies: tools, handoffs, reasoning and JSON compliance depend on the model. Prefer capable models for structured output, and validate the combination you plan to use.

## Run and deploy

Once you have built your agents and tools, anyone with a copy of the project can run it in one of three ways.

### On a computer, with uv

```bash
uv sync --locked
uv run --locked python -m app serve                 # dashboard + API: http://127.0.0.1:8000
uv run --locked python -m app mcp                   # MCP server for a local client (stdio)
uv run --locked python -m app catalog list          # catalog CLI
```

`serve` accepts `--host`, `--port` and `--reload`, or the `HOST` and `PORT` environment variables.

### With Docker

The repository includes a [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) (Docker Compose 2.24 or later).

1. Create `.env` from `env-example` with your provider keys, and add an access token:

   ```dotenv
   CATALOG_TOKEN="a-long-random-string"
   ```

2. Start it:

   ```bash
   docker compose up -d --build
   ```

3. Open http://127.0.0.1:8000. The browser asks for a user name and password: use any user name and the token as the password.

| Command | Effect |
|---|---|
| `docker compose up -d --build` | Build and start the dashboard + API |
| `docker compose --profile mcp up -d --build` | Also start the MCP server over HTTP on `http://127.0.0.1:8001/mcp` |
| `docker compose logs -f app` | Follow the logs |
| `docker compose down` | Stop (catalog state and settings stay in the `data` volume) |

Without Compose: `docker build -t my-agents .` then `docker run -p 127.0.0.1:8000:8000 -e CATALOG_TOKEN=... --env-file .env -v agents-data:/data my-agents`.

The ports are published on `127.0.0.1` only. To reach the server from other machines, change the mapping to `"8000:8000"` and put it behind a reverse proxy with HTTPS. The MCP HTTP endpoint has no token, so keep it local or behind an authenticating proxy.

### On a hosting platform

Any service that runs a Dockerfile (Render, Railway, Fly.io, Google Cloud Run, Azure Container Apps, ...) works: the image listens on `$PORT`, exposes `GET /health` for health checks and keeps its state in `/data`. Set `CATALOG_TOKEN` and your provider keys as the platform's secrets, set `CATALOG_SETTINGS_READONLY=true` so keys are managed only there, and attach a persistent volume at `/data` if you want dashboard changes (enabled items, channels, models) to survive restarts.

### Security and run settings

| Variable | Default | Purpose |
|---|---|---|
| `CATALOG_TOKEN` | Not set | When set, every request except `GET /health` needs it, as `Authorization: Bearer <token>` or Basic auth (any user, token as password) |
| `CATALOG_SETTINGS_READONLY` | `false` | `true` blocks changes to Settings from the dashboard and API; keys come from the environment |
| `HOST`, `PORT` | `127.0.0.1`, `8000` | Address used by `python -m app serve` (the image uses `0.0.0.0`) |
| `CATALOG_DB`, `CATALOG_ENV_FILE` | Repository root | Catalog state and the settings file (`/data/...` in the image) |

`python -m app serve` refuses to listen on a non-local address without `CATALOG_TOKEN`, because the dashboard can read and change API keys (pass `--insecure` only on isolated, trusted networks). Calling the API with a token:

```bash
curl -H "Authorization: Bearer $CATALOG_TOKEN" http://127.0.0.1:8000/api/catalog
```

In Docker, values from `.env` are passed as environment variables and take precedence over keys later edited in Settings (which are saved to `/data/.env`). Use one or the other for each key.

## Wrapper reference

Import wrappers from their modules under `app.orchestration`.

| Wrapper | Import module | Use it for | Return value |
|---|---|---|---|
| `GPT` | `gpt` | Direct OpenAI Responses API calls with typed parsing | Parsed output object |
| `GPTAgent` | `gpt_agent` | Agents SDK execution, Python tools, handoffs and MCP | Final agent output |
| `GPTSandboxAgent` | `gpt_sandbox_agent` | Agent execution with a sandbox backend and runtime skills | Final agent output |
| `GPTLocal` | `gpt_local` | Direct Chat Completions calls to a compatible local or remote server | Parsed output, with a text-response fallback |
| `GPTLocalAgent` | `gpt_agent_local` | Agents SDK workflows using a compatible Chat Completions provider | Final output parsed by the wrapper |
| `GPTDecision` | `gpt_decision` | Predicates, fixed-choice classification and rubric scoring | Complete SDK `Decision` object |
| `create_agent(...)` | `providers` | Factory: an agent for any provider from a `provider:model` reference (returns `GPTAgent` or `GPTLocalAgent`) | The agent instance |

Prefer `create_agent` for new agents, so the provider stays a configuration choice. Use a specific wrapper when you need its provider-specific features (Decisions, the sandbox or direct calls).

All wrappers expose `run_sync(...)` and async `run(...)`. `GPTDecision` additionally requires `questions=...` and uses a different response contract.

`GPTAgent`, `GPTLocalAgent` and `GPTSandboxAgent` support tools, handoffs and MCP. `GPT` and `GPTLocal` are direct-call wrappers. The existing constructors do not expose every SDK option: several accept `**kwargs` without forwarding unknown fields. Check the relevant module before using an advanced option.

## Configuration

Use [env-example](env-example) as the source for a complete configuration. These values are the repository's defaults, not recommendations for every workload.

Every variable below except `MCP_*`, `CATALOG_*` and the optional `OPENAI_*` model names can be edited in the dashboard's **Settings**.

| Variable | Default | Purpose |
|---|---|---|
| `DEFAULT_MODEL` | `openai:<OPENAI_MODEL_NAME>` | `provider:model` used by `create_agent` and catalog agents that do not choose one |
| `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `MISTRAL_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY` | Not set | Keys for the corresponding `provider:` prefixes |
| `OLLAMA_BASE_URL`, `LMSTUDIO_BASE_URL` | `http://localhost:11434/v1`, `http://localhost:1234/v1` | Addresses of local servers for `ollama:` and `lmstudio:` |
| `OPENAI_API_KEY` | No usable key supplied | Authentication for OpenAI API calls |
| `OPENAI_MODEL_NAME` | `gpt-4.1-mini` | Fallback model for `GPT` and `GPTAgent` |
| `OPENAI_SANDBOX_MODEL_NAME` | `gpt-5-mini` | Fallback model for `GPTSandboxAgent` |
| `OPENAI_DECISION_MODEL_NAME` | `gpt-6-luna` | Independent model setting for `GPTDecision` |
| `LOCAL_BASE_URL` | `http://localhost:1234/v1` | Compatible Chat Completions endpoint |
| `LOCAL_MODEL_NAME` | `local-model` | Model identifier accepted by that server |
| `LOCAL_API_KEY` | `lm-studio` | Local placeholder or the remote provider's real key |
| `LOCAL_DISABLE_TRACING` | `true` | Disable Agents SDK tracing when constructing `GPTLocalAgent` (all non-OpenAI providers) |
| `MCP_TRANSPORT` | `streamable-http` | Default transport for the sample MCP server (the catalog MCP server defaults to `stdio`) |
| `CATALOG_DB` | `.catalog.sqlite3` | Catalog state: enabled items, channels and per-agent models |
| `CATALOG_ENV_FILE` | `.env` | File read and written by Settings and loaded by the wrappers |

Configuration helpers live in [app/orchestration/config.py](app/orchestration/config.py):

```python
from app.orchestration.config import default_model, sandbox_model, decision_model

regular_model = default_model()
sandbox_default = sandbox_model()
decisions_default = decision_model()
```

Model availability depends on the provider and account. If a configured model is unavailable, select an available model with the capabilities your workflow requires.

### Configuration precedence

For `GPT`, `GPTAgent`, `GPTSandboxAgent`, `GPTLocal` and `GPTLocalAgent`:

- **Without `agent_id`:** constructor settings such as `model` and `max_tokens` are used; omitted models fall back to the corresponding environment setting.
- **With `agent_id`:** the Markdown definition supplies the name, role, instructions, model and token limit. For `GPTAgent` and `GPTLocalAgent`, a constructor `model` argument replaces the Markdown model (this is how `create_agent` applies a provider choice); `max_tokens` is always taken from the Markdown. For `GPT`, `GPTLocal` and `GPTSandboxAgent`, constructor `model` and `max_tokens` do not replace those fields.
- **Markdown model omitted or empty:** the wrapper uses its provider-specific fallback. This is useful when sharing a definition across environments.
- **Markdown model with a provider prefix** (`model: ollama:llama3.2`): only `create_agent` understands the prefix. Instantiating `GPTAgent(agent_id=...)` directly with such a definition would send the whole string to OpenAI.

`output_type`, `tools`, `handoffs` and MCP settings can still be supplied where the selected wrapper supports them. `GPTDecision` does not load Markdown definitions: its constructor `model` overrides `OPENAI_DECISION_MODEL_NAME`, and questions are passed directly.

## Typed outputs and execution

Define a Pydantic `BaseModel` and pass it as `output_type`. A schema described only in a prompt or Markdown section does not create the corresponding Python model.

The default agent response contains `final_output: str`. When you supply a custom model, use that model's fields. The agent wrappers return the final content directly, rather than the Agents SDK's `RunResult`.

### Asynchronous applications

Inside FastAPI endpoints or another active event loop, use `await`:

```python
from app.orchestration.gpt_agent import GPTAgent

agent = GPTAgent(instructions="Answer clearly and concisely.")

async def answer_question(question: str) -> str:
    result = await agent.run(question)
    return result.final_output
```

The agent wrappers reject `run_sync()` inside an active event loop. Direct-call wrappers use blocking synchronous clients, so async applications should use their async methods as well.

### Structured output with compatible providers

`GPTLocal` and `GPTLocalAgent` put the output schema into instructions and validate the returned text with Pydantic. They do not guarantee server-enforced JSON Schema output.

For a custom output model, invalid JSON can raise a validation error in `GPTLocalAgent`. `GPTLocal` can fall back to `GPTLocalResponse`; applications requiring a specific custom type should check the returned type before using its fields. Both wrappers handle common Markdown code fences in model output.

## Markdown agent definitions

Application agents live in [app/assets/agents](app/assets/agents). Each definition contains YAML frontmatter and four conventional sections: `INPUT`, `OUTPUT`, `INSTRUCTIONS` and `KNOWLEDGE`.

For example, save this as `app/assets/agents/document_reviewer.md`:

```markdown
---
id: document_reviewer
role: Document reviewer
goal: Identify clarity and consistency issues in the supplied document.
backstory: Use only the supplied text and distinguish missing evidence from facts.
max_tokens: 2048
---

# INPUT
The document text and optional context about its intended audience.

# OUTPUT
A JSON object with summary (string) and issues (list of strings).

# INSTRUCTIONS
- Summarize the document in English.
- Identify internal contradictions, ambiguous wording and missing information.
- Do not introduce external facts.
- Return only the requested JSON object.

# KNOWLEDGE
Each issue should identify a concrete passage or information gap.
```

The definition omits `model`, allowing the wrapper to use its configured fallback. Load it with a matching Python output contract:

```python
from pydantic import BaseModel
from app.orchestration.gpt_agent import GPTAgent

class ReviewResponse(BaseModel):
    summary: str
    issues: list[str]

reviewer = GPTAgent(agent_id="document_reviewer", output_type=ReviewResponse)
result = reviewer.run_sync("The launch is scheduled for Monday. The date is still undecided.")
print(result.model_dump())
```

### Definition fields and loader behavior

| Field | Meaning |
|---|---|
| `id` | Keep it equal to the filename without `.md`; file lookup uses the filename |
| `name` | Optional display name; defaults to the requested `agent_id` |
| `role` | Prepended to the assembled instructions by the wrapper |
| `goal` | Objective included in the assembled instructions |
| `backstory` | Optional behavior-shaping context included in the instructions |
| `model` | Model override; omit it to use the wrapper's fallback |
| `max_tokens` | Output budget; defaults to 2048 when omitted |

Do not leave `max_tokens:` blank: the loader converts the field with `int(...)`. Avoid additional level-one Markdown headings inside the four sections, because the loader treats them as section boundaries.

For lower-level access, use `load_agent_config(agent_id, fallback_model=...)` or `load_agent_markdown(agent_id)` from [app/orchestration/util.py](app/orchestration/util.py). The latter exposes raw `metadata` and `sections`.

The coding-agent skill includes an offline definition validator:

```bash
uv run --locked python .agents/skills/agents-template-criar-agente/scripts/validar_agente.py app/assets/agents/document_reviewer.md
```

The validator checks authoring conventions and actual loading. It does not evaluate the quality of model responses.

## Local models and compatible providers

For agents, the simplest path is `create_agent(model="ollama:<model>")` or `"lmstudio:<model>"`, described in [Providers and models](#providers-and-models). This section covers the underlying `Local` wrappers, which you can also use directly.

The `Local` wrappers accept a compatible hosted endpoint as well as a local server. Support depends on the provider's implementation of Chat Completions, output formatting and tools.

| Server or provider | Base URL | Key |
|---|---|---|
| LM Studio | `http://localhost:1234/v1` | Placeholder if authentication is disabled |
| Ollama | `http://localhost:11434/v1` | Placeholder if authentication is disabled |
| DeepSeek | `https://api.deepseek.com` | Real DeepSeek API key |
| Another compatible server | Its documented API base URL | As required by that server |

Configure `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME` and `LOCAL_API_KEY` in `.env`, then use:

```python
from app.orchestration.gpt_local import GPTLocal

model = GPTLocal(instructions="Answer in Brazilian Portuguese.")
result = model.run_sync("Explain machine learning in two sentences.")
print(result.final_output)
```

Connection parameters can also be passed directly:

```python
from app.orchestration.gpt_local import GPTLocal

model = GPTLocal(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="your-installed-model",
)
```

Replace the model identifier with one actually installed on your server. These examples omit `agent_id` so the local model setting is used. Bundled definitions such as `writer.md` currently specify OpenAI models; edit or omit their `model` field before using them with another provider.

For Agents SDK workflows, import `GPTLocalAgent` from `app.orchestration.gpt_agent_local`. Its tracing switch affects the global Agents SDK tracing configuration; account for that when mixing providers in one process.

## DeepSeek API

With `create_agent`, set `DEEPSEEK_API_KEY` (or paste it in Settings) and use a reference such as `deepseek:deepseek-flash`; nothing else is needed.

The direct Chat Completions wrappers can also use a DeepSeek key without an additional library. Configure the same `LOCAL_*` variables:

```dotenv
LOCAL_BASE_URL="https://api.deepseek.com"
LOCAL_MODEL_NAME="deepseek-flash"
LOCAL_API_KEY="your-deepseek-api-key"
LOCAL_DISABLE_TRACING="true"
```

The model identifier above is an example; consult the [DeepSeek documentation](https://api-docs.deepseek.com/guides/harness) for available models and provider-specific behavior.

For a direct call, use `GPTLocal` as in the preceding section. For an agent:

```python
from app.orchestration.gpt_agent_local import GPTLocalAgent

agent = GPTLocalAgent(
    name="DeepSeek assistant",
    instructions="Answer clearly in Portuguese.",
)
result = agent.run_sync("Explain machine learning.")
print(result.final_output)
```

With tracing disabled, these paths do not need an OpenAI key. The direct wrappers read `LOCAL_API_KEY`; only `create_agent` with the `deepseek:` prefix reads `DEEPSEEK_API_KEY`.

Tool calls, MCP, handoffs and reasoning behavior must be checked with the selected DeepSeek model. In particular, tool conversations in thinking mode may require provider-specific handling of reasoning content. The project documents the compatible connection path; live DeepSeek behavior has not been validated by the offline tests. This configuration does not imply DeepSeek support for OpenAI Decisions or the sandbox runtime.


## Agent orchestration

### Mandatory processing stages

When every stage must execute in a known order, orchestrate the calls in Python and validate each intermediate result. Serialize Pydantic output with `model_dump_json()` before passing it to the next agent.

The [sequential workflow example](.agents/skills/agents-template-orquestrar-agentes/assets/fluxo_sequencial.py) demonstrates extraction followed by review, with injectable agents for testing and explicit failure propagation.

### Model-selected handoffs

A handoff allows an agent to transfer control to a specialist:

```python
from app.orchestration.gpt_agent import GPTAgent

reviewer = GPTAgent(
    name="Reviewer",
    instructions="Review the supplied text and identify clarity issues.",
)
coordinator = GPTAgent(
    name="Coordinator",
    instructions="Delegate document-review requests to Reviewer.",
    handoffs=[reviewer],
)
result = coordinator.run_sync("Review this sentence: the date is final but still undecided.")
print(result.final_output)
```

This makes a handoff available to the model; it does not guarantee that every request passes through the reviewer. Use a mandatory Python sequence when review is required on every execution.

For consultation where the coordinator should retain control, an `Agent`-based specialist can be exposed with `specialist.as_tool(...)`. See the [orchestration patterns](.agents/skills/agents-template-orquestrar-agentes/references/padroes.md) for examples and contract considerations.

Do not share a wrapper instance across concurrent executions that open connections through `mcp_url`: that path mutates `self.mcp_servers`. Use separate instances or manage connection ownership explicitly.

## Decisions and routing

`GPTDecision` uses a separate API contract for decisions with fixed answer types:

| Question type | Result | Example use |
|---|---|---|
| `predicate` | Estimated probability of a condition | Detect an explicit refund request |
| `choice` | One supplied category, with probabilities and confidence | Choose the responsible department |
| `score` | A score over ordered rubric levels | Assess the operational impact of a request |

The wrapper returns the full SDK `Decision`, including `answers`, `model` and `usage`. A question can return a refusal. Questions need unique, non-empty names, and a request accepts 1–400 questions.

Evaluate the bundled questions:

```bash
uv run --locked python -m app.examples.decisions --mode evaluate --text "I was charged twice. Please refund the duplicate charge."
```

Route a request to a configured specialist:

```bash
uv run --locked python -m app.examples.decisions --mode route --min-confidence 0.8 --text "The login page fails with an error."
```

The threshold `0.8` is illustrative. Calibrate your own value with representative labeled examples. The routing example requires an explicit threshold and returns `review_required` for a refusal, insufficient confidence, an unhandled category or an unusable answer. Only a mapped qualifying choice executes a specialist.

These commands make real OpenAI calls. See [Decisions and specialist routing](docs/decisions.md) for sync/async usage, injected clients, structured evidence, request options, result contracts and offline tests. Check [the official API guide](https://developers.openai.com/api/docs/guides/decisions) for current provider capabilities.

## Python tools and MCP

### Expose a Python function

Use the Agents SDK's `function_tool` decorator and pass the resulting tool to an agent wrapper:

```python
from agents import function_tool
from app.orchestration.gpt_agent import GPTAgent

@function_tool
def count_words(text: str) -> int:
    """Count whitespace-separated words in the supplied text."""
    return len(text.split())

agent = GPTAgent(
    instructions="Use the tool when asked to count words.",
    tools=[count_words],
)
result = agent.run_sync("How many words are in: a short example sentence?")
print(result.final_output)
```

Parameter annotations and docstrings describe the tool's contract. Keep business logic independently testable when the tool has more than a trivial implementation. The [Python tool example](.agents/skills/agents-template-integrar-ferramentas/assets/ferramenta_texto.py) demonstrates a pure function and its SDK adapter.

### Start the sample MCP server

The server uses MCP SDK 2's `MCPServer` and exposes two tools:

| Tool | Behavior |
|---|---|
| `count_text_words` | Counts whitespace-separated words and the sum of their character lengths |
| `clean_text_spacing` | Collapses repeated whitespace into single spaces |

Start it from the repository root:

```bash
uv run --locked python -m app.mcp_tools.server --transport streamable-http
```

The streamable HTTP endpoint is `http://localhost:8000/mcp`. Other transport options are:

```bash
uv run --locked python -m app.mcp_tools.server --transport sse
uv run --locked python -m app.mcp_tools.server --transport stdio
```

The SSE endpoint is `/sse`; stdio communicates through the process streams. The HTTP transports bind to `0.0.0.0:8000` in the example code. The default FastAPI server also uses port 8000, so change one port before running both HTTP services together.

You can use the `MCP_TRANSPORT` process environment variable instead of the flag. Unlike the wrappers, this server does not load `.env` itself. To load it explicitly with uv:

```bash
uv run --locked --env-file .env python -m app.mcp_tools.server
```

### Connect an agent

With the MCP server running in a separate terminal:

```python
from app.orchestration.gpt_agent import GPTAgent

agent = GPTAgent(
    name="Text assistant",
    instructions="Use the available tools for counting words and cleaning spacing.",
    mcp_url="http://localhost:8000/mcp",
    mcp_timeout=30,
)
result = agent.run_sync("Count the words in: a short example sentence.")
print(result.final_output)
```

`mcp_headers` accepts authentication headers when required; obtain credential values from the application environment. `run()` opens a `MCPServerStreamableHttp` connection for the execution and closes it afterward.

For multiple servers, SSE or stdio clients, manage their connection contexts in your application and pass connected objects through `mcp_servers=[...]`. Do not also set `mcp_url` expecting the lists to be combined: that path replaces `self.mcp_servers` with its own connection. Keep the contexts open until the agent finishes.

A browser GET without MCP-compatible headers can return `406 Not Acceptable`; validate the service with an MCP client and a tool call. Additional details are in the [MCP integration reference](.agents/skills/agents-template-integrar-ferramentas/references/mcp.md).

## Sandbox execution and runtime skills

`GPTSandboxAgent` adds the SDK's sandbox capabilities and makes the skills in [app/assets/skills](app/assets/skills) available during execution.

```python
from app.orchestration.gpt_sandbox_agent import GPTSandboxAgent

agent = GPTSandboxAgent(
    name="Haiku reviewer",
    instructions="Use the haiku_quality skill to review the supplied haiku.",
    skills_dir="app/assets/skills",
)
# Requires a configured backend and a model that supports its tools.
result = agent.run_sync("Review this haiku: An old silent pond / A frog jumps into the pond / Splash! Silence again.")
print(result.final_output)
```

| Platform | Default backend selection | Additional requirement |
|---|---|---|
| macOS / Linux | `UnixLocalSandboxClient` | A runtime environment compatible with the local backend |
| Windows | `DockerSandboxClient` | The SDK's optional Docker dependencies and an accessible Docker daemon |

The default dependency installation does not include the optional Docker backend dependencies. Configure them in the environment used for sandbox runs. A backend can also be provided explicitly through `sandbox_client`.

Use a model supporting the sandbox's tools. If you use `agent_id`, remember that the Markdown `model` overrides `OPENAI_SANDBOX_MODEL_NAME`; simply changing the environment does not replace a model fixed in a bundled definition.

### Included runtime skills

| Skill | Purpose |
|---|---|
| `haiku_quality` | Review haiku structure, imagery and scoring criteria |
| `agent_description_writer` | Draft agent definitions in the project's Markdown format |

The wrapper combines default capabilities with lazy skill loading from the selected directory. Supplying `capabilities` explicitly replaces that default composition; include the skill capability if you still need it.

Runtime skills appear at `.agents` inside the sandbox workspace. This is separate from the repository's `.agents/skills/` directory used by coding agents. Making a skill available does not prove that the model read or followed it: verify task-specific behavior or inspect traces when available.

See the [sandbox reference](.agents/skills/agents-template-integrar-ferramentas/references/sandbox.md) for backend selection, paths and validation limits. Construction-only checks do not prove that a sandbox backend can execute.

## FastAPI application

The default [app/main.py](app/main.py) is a minimal HTTP integration scaffold that also mounts the [catalog](#catalog-of-agents-and-tools) dashboard and API ([app/catalog_api.py](app/catalog_api.py)). Start it with:

```bash
uv run --locked python -m app serve --reload
```

`python -m app serve` wraps uvicorn (`app.main:app`); you can still run uvicorn directly.

| Endpoint | Purpose | Model call |
|---|---|---|
| `GET /` | Catalog dashboard | No |
| `GET /health` | Returns `{"status":"ok"}` | No |
| `POST /example` | Accepts a `data` object and returns a fixed sample message | No |
| `/api/catalog/...` | Catalog listing, item contracts, state, channels, models and runs | Only `POST .../run` on an agent |
| `GET`/`PUT /api/settings` | Read (keys masked) and update provider settings in `.env` | No |
| `GET /api/providers`, `POST /api/providers/{id}/models` | Provider status; connection test listing the provider's models | Lists models, no generation |
| `GET /docs` | Interactive OpenAPI documentation | No |

Example request from a POSIX shell:

```bash
curl -X POST http://localhost:8000/example \
  -H "Content-Type: application/json" \
  -d '{"data":{"message":"hello"}}'
```

Windows PowerShell equivalent:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/example -Method Post -ContentType 'application/json' -Body '{"data":{"message":"hello"}}'
```

Response:

```json
{
  "data": {
    "message": "This is an example response"
  }
}
```

To try the separate haiku endpoint backed by agents, configure OpenAI and run:

```bash
uv run --locked uvicorn app.tests.test_main:app --port 8001
```

That example exposes `POST /haiku` with input `{"subject":"the changing seasons"}` and returns `subject`, `haiku` and `score`. Its requests make real model calls. A separate [classification endpoint example](.agents/skills/agents-template-criar-aplicacao/assets/classificacao_api.py) and its startup command are documented in the [development skills guide](docs/development-skills.md).

The examples are starting points for your own endpoints. Define your application's error mapping, access controls and persistence according to its requirements before deploying it.

## Skills for coding agents

The repository includes seven development skills under `.agents/skills/`. They help a coding agent follow the project's conventions, use the actual wrappers and validate its work. Coding agents also read the project rules in [AGENTS.md](AGENTS.md) (Codex and others) and [CLAUDE.md](CLAUDE.md) (Claude Code, which imports AGENTS.md), and the [architecture guide](docs/architecture.md).

| Harness | Finds skills in | Notes |
|---|---|---|
| Codex and agents that read `.agents/skills/` | `.agents/skills/<name>/` | The source of truth |
| Claude Code | `.claude/skills/<name>/SKILL.md` | Generated pointers to `.agents/skills/`; refresh with `uv run --locked python scripts/sync_skills.py` |
| Any other agent | Ask it to read `AGENTS.md` and the relevant `SKILL.md` | |

| Skill | Main task |
|---|---|
| [`catalog-create-item`](.agents/skills/catalog-create-item/SKILL.md) | Create or change a catalog agent or tool: contract, manifest, prompt, README and offline tests |
| [`catalog-review-item`](.agents/skills/catalog-review-item/SKILL.md) | Review an item or a change against the standard, including security |
| [`catalog-extend-platform`](.agents/skills/catalog-extend-platform/SKILL.md) | Add providers, platform settings, manifest fields, endpoints or dashboard features safely |
| [`agents-template-criar-agente`](.agents/skills/agents-template-criar-agente/SKILL.md) | Create or review Markdown definitions, output contracts and loading code |
| [`agents-template-criar-aplicacao`](.agents/skills/agents-template-criar-aplicacao/SKILL.md) | Implement Python features and FastAPI endpoints, including Decisions integration |
| [`agents-template-orquestrar-agentes`](.agents/skills/agents-template-orquestrar-agentes/SKILL.md) | Build sequential flows, Decisions-based routing, handoffs and specialist tools |
| [`agents-template-integrar-ferramentas`](.agents/skills/agents-template-integrar-ferramentas/SKILL.md) | Integrate Python tools, MCP 2 connections and sandbox capabilities |

Example request:

```text
Use $catalog-create-item to add a tool that converts currencies using an exchange-rate API.
```

In Claude Code, describe the task ("add a tool that ...") or type `/catalog-create-item`.

The four `agents-template-*` skills are written in Portuguese; the three `catalog-*` skills are in English, like the catalog. All are versioned with the project. Discovery depends on your coding agent's support for repository skills; in a session that has not discovered them, reload the project or start a new chat. Another agent can also be asked to read the relevant `SKILL.md` directly.

| Location | Used by | Content |
|---|---|---|
| `.agents/skills/` | Coding agents working on the project | Development instructions, references and reusable examples |
| `app/assets/skills/` | Sandbox agents during a task | Runtime skill instructions |
| `app/assets/agents/` | Agent-definition loaders | Markdown definitions of application agents |
| `app/agents/`, `app/tools/` | The catalog | Published catalog items (manifest, contract, README) |

The [complete development skills guide](docs/development-skills.md) covers invocation, assets, validators, discovery and maintenance. No global skill installation is required to keep the skills in this repository.

## Examples and tests

### Offline regression tests

Run all discoverable tests:

```bash
uv run --locked python -m unittest discover -s app/tests -v
```

Or run a focused module:

```bash
uv run --locked python -m unittest app.tests.test_catalog -v
uv run --locked python -m unittest app.tests.test_gpt_decision -v
uv run --locked python -m unittest app.tests.test_mcp_server -v
uv run --locked python -m unittest app.tests.test_skill_examples -v
```

| Test module | Coverage |
|---|---|
| `test_project_knowledge` | Skills have valid front matter and Codex metadata, Claude Code mirrors are in sync, AGENTS.md indexes every skill, and links and documented commands resolve |
| `test_deploy` | `python -m app` entry point, refusal to listen publicly without a token, token authentication (Bearer and Basic) and read-only Settings |
| `test_catalog` | Every item follows the standard, tool examples produce their expected output, catalog API and MCP channel filtering, the `new` generator, Settings (keys never returned, validation), model references, `create_agent` backends, per-agent model choice and provider endpoints |
| `test_gpt_decision` | Sync/async SDK requests over mock HTTP transports, typed answers, usage, validation and routing outcomes |
| `test_mcp_server` | Transport configuration, HTTP tool calls and Agents SDK stdio integration |
| `test_skill_examples` | Agent definition validation, endpoint contracts, sequential data flow, failure handling and a tool adapter |

These tests do not call paid models or require a Docker backend. They do not establish live provider access, model accuracy, threshold calibration or sandbox execution capability.

Check dependency consistency with:

```bash
uv pip check
```

### Runnable demonstrations

Several files under `app/tests/` are demonstrations rather than unittest cases. Running them as modules can make real provider calls:

| Command after `uv run --locked python -m` | Demonstrates | Prerequisites |
|---|---|---|
| `app.tests.test_gpt` | Typed translation using `GPT` and a Markdown definition | OpenAI key and model access |
| `app.tests.test_gpt_agents` | Writer/evaluator handoff using `GPTAgent` | OpenAI key and model access |
| `app.tests.test_gpt_sandbox_agent` | Sandbox execution with runtime skills | OpenAI key, suitable model and backend |
| `app.tests.test_gpt_local` | Direct compatible Chat Completions call | Configured server and compatible agent model |
| `app.tests.test_gpt_agent_local` | Compatible-provider writer/evaluator agents | Configured server, compatible agent models and tool support |
| `app.examples.decisions` | Grouped decisions or explicit specialist routing | OpenAI key and Decisions model access |
| `app.catalog_cli run summarizer --example 1` | A catalog agent on the configured provider | A configured provider and model |

For local demonstrations, review the Markdown models before execution. Always run from the project root as a module, rather than invoking a file path such as `python app/tests/test_gpt_agents.py`.

## Project structure

```text
.
|-- .agents/skills/               # Seven skills for coding agents (source of truth)
|-- .claude/skills/               # Generated Claude Code pointers to .agents/skills
|-- app/
|   |-- main.py                   # FastAPI application (mounts the catalog)
|   |-- catalog.py                # Catalog discovery, validation, state and execution
|   |-- catalog.html              # Catalog dashboard
|   |-- catalog_api.py            # Dashboard, catalog, settings and provider endpoints
|   |-- catalog_cli.py            # Catalog CLI (list, check, new, run, enable, disable)
|   |-- __main__.py               # `python -m app serve | mcp | catalog`
|   |-- catalog_mcp.py            # Catalog MCP server
|   |-- security.py               # CATALOG_TOKEN and read-only Settings
|   |-- settings.py               # Settings stored in .env (keys write-only)
|   |-- agents/<id>/              # Catalog agents: item.toml, handler.py, README.md
|   |-- tools/<id>/               # Catalog tools: item.toml, handler.py, README.md
|   |-- templates/catalog/        # Templates used by `catalog_cli new`
|   |-- assets/
|   |   |-- agents/               # Markdown application-agent definitions
|   |   `-- skills/               # Runtime sandbox skills
|   |-- examples/
|   |   `-- decisions.py          # Evaluation and specialist-routing CLI
|   |-- mcp_tools/
|   |   |-- server.py             # MCP 2 server and transport selection
|   |   `-- tools.py              # Text-processing functions
|   |-- orchestration/
|   |   |-- config.py             # Environment and model defaults
|   |   |-- gpt.py                # OpenAI Responses wrapper
|   |   |-- gpt_agent.py          # Agents SDK wrapper
|   |   |-- gpt_agent_local.py    # Compatible Chat Completions agents
|   |   |-- gpt_decision.py       # OpenAI Decisions wrapper
|   |   |-- gpt_local.py          # Direct compatible Chat Completions calls
|   |   |-- gpt_sandbox_agent.py  # Sandbox-capable agent
|   |   |-- providers.py          # Provider presets, model references, create_agent
|   |   `-- util.py               # Markdown agent loaders
|   `-- tests/                    # Offline tests and live demonstrations
|-- docs/
|   |-- architecture.md           # How the layers, state, providers and security fit
|   |-- catalog-standards.md      # How to build catalog agents and tools
|   |-- decisions.md              # Decisions API and routing guide
|   `-- development-skills.md     # Coding-agent skills guide
|-- .python-version               # Preferred development interpreter
|-- AGENTS.md, CLAUDE.md          # Rules for AI coding assistants
|-- Dockerfile, docker-compose.yml # Container image and local deployment
|-- scripts/sync_skills.py        # Regenerates .claude/skills from .agents/skills
|-- CHANGELOG.md
|-- env-example
|-- LICENSE
|-- pyproject.toml                # Project metadata and dependency constraints
`-- uv.lock                       # Reproducible dependency resolution
```

## Troubleshooting

| Symptom | What to check |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Run from the repository root using `uv run --locked python -m ...` |
| Authentication error | Replace placeholders with the correct provider's key; verify which wrapper and environment variable you are using |
| Model unavailable or wrong provider model | Inspect both environment settings and the Markdown `model`; frontmatter takes precedence with `agent_id` |
| Local connection refused | Start the server and verify its port, base URL and loaded model identifier |
| JSON parsing or Pydantic error | Check the actual response and output contract; compatible-provider structured output depends on model compliance |
| `Cannot combine structured output constraints with lazy grammar` | Use the current `GPTLocalAgent`, which avoids combining server `response_format` with tool grammar and validates the final text locally |
| `run_sync()` fails in an active event loop | Use `await agent.run(...)` inside async functions |
| MCP browser request returns `406` | Use a protocol-aware client with the appropriate headers and make a tool call |
| MCP transport in `.env` is ignored | Pass `--transport`, export `MCP_TRANSPORT`, or load `.env` with `uv run --env-file .env` |
| Address already in use | The sample API and MCP HTTP server both default to port 8000; change one port |
| Sandbox rejects a `custom` tool | Check model capability and the resolved Markdown model, not just the sandbox fallback environment variable |
| Unix-local sandbox error on Windows | Use the Docker backend or provide a supported client; verify optional dependencies and daemon availability |
| Skill available but behavior does not show its use | Check a task-specific observable outcome or traces; loading is not proof of use |
| Decisions returns `review_required` | Inspect `reason`, the named answer, confidence and the configured specialist mapping |
| Dashboard shows "Missing setting" or a run returns `409` | Add the key of the agent's provider in Settings, or choose another model in the agent's side panel |
| **Test connection** fails | For local servers, start the server and check its address; for hosted providers, check the key (HTTP 401/403 means it was rejected) |
| Agent ignores the model chosen in Settings | A per-agent choice or the prompt's `model:` takes precedence over `DEFAULT_MODEL`; the side panel shows which one is in use |
| Settings change not seen by the MCP server | Restart `app.catalog_mcp`; it runs in its own process |
| `Refusing to listen on 0.0.0.0 without CATALOG_TOKEN` | Set `CATALOG_TOKEN` (in `.env` or the environment), or run on `127.0.0.1` |
| Browser keeps asking for a password, or the API returns `401` | Use any user name and `CATALOG_TOKEN` as the password; API clients send `Authorization: Bearer <token>` |
| `docker compose` says `Set CATALOG_TOKEN` | Add `CATALOG_TOKEN` to `.env` next to `docker-compose.yml` |
| Settings shows "Read-only" | The server runs with `CATALOG_SETTINGS_READONLY=true`; change keys in its environment and restart |
| `catalog_cli check` reports a problem | Follow the message; the rules are in [docs/catalog-standards.md](docs/catalog-standards.md) |

## Scope and compatibility

This is an instructional template with small wrappers and examples. The default API has no application-specific business logic, authentication layer, database or background-job system. Add those capabilities as your application requires them.

- **Provider compatibility:** an OpenAI-compatible endpoint does not guarantee support for every parameter, model feature, tool or handoff pattern.
- **Model selection:** defaults illustrate the current project configuration. Choose available models suitable for the task and validate them in your target environment.
- **Decisions:** the implementation targets OpenAI and preserves its SDK response types; it is separate from compatible Chat Completions calls.
- **Sandbox execution:** backend selection and optional dependencies are environment-specific; offline tests do not execute a live sandbox.
- **Dependencies:** `pyproject.toml` defines allowed versions and `uv.lock` records the resolved environment. OpenAI SDK 3 and MCP SDK 2 are used by the current release; see [compatibility notes](CHANGELOG.md).

## Contributing

Changes should include a concrete example or test appropriate to the behavior being changed, plus the relevant documentation update. Before submitting a change:

```bash
uv sync --locked
uv run --locked python -m unittest discover -s app/tests -v
uv run --locked python -m app.catalog_cli check
uv pip check
git diff --check
```

Catalog items must follow the [catalog standards](docs/catalog-standards.md).

When modifying a wrapper or the Markdown loader, review its development skill, examples and provider assumptions. Keep actual credentials out of committed files. In a bug report or pull request, include the command, platform, relevant versions and expected versus observed behavior, with sensitive values removed.

## License

Distributed under the [MIT license](LICENSE).
