# OpenAI agents SDK templates

A Python starter project for building typed model integrations, agent workflows and decision-based routing. Use OpenAI directly, connect an OpenAI-compatible local or hosted model, add tools through MCP, or experiment with sandbox execution and reusable skills.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Latest tag](https://img.shields.io/github/v/tag/ilexistools/agents-sdk-templates?label=version)](https://github.com/ilexistools/agents-sdk-templates/tags)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

The template keeps orchestration visible in ordinary Python: wrappers handle model calls, Pydantic models describe outputs, Markdown files define agents, and application code controls execution. It is intended for learning, prototyping and adapting these patterns to your own application.

[Getting started](#getting-started) · [Wrapper reference](#wrapper-reference) · [Decisions](#decisions-and-routing) · [Development skills](#skills-for-coding-agents) · [Changelog](CHANGELOG.md)

## What you can build

- **Typed model integrations:** extract or generate data with explicit Pydantic output contracts.
- **Specialist workflows:** run mandatory processing stages, configure handoffs, or expose an agent as a tool.
- **Decision-based triage:** classify requests, evaluate conditions and score inputs before selecting a specialist.
- **Provider-compatible applications:** use OpenAI, local servers such as LM Studio and Ollama, or the DeepSeek hosted API.
- **Tool-enabled agents:** connect Python functions and MCP servers to the Agents SDK wrappers.
- **Sandbox experiments:** make task-specific skills available to an agent with a configured execution backend.
- **HTTP integrations:** adapt the included FastAPI application and runnable endpoint examples.

The repository includes executable examples, offline regression tests, four skills for coding agents and focused guides for [Decisions](docs/decisions.md) and [development skills](docs/development-skills.md).

## Contents

- [Getting started](#getting-started)
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

Or start the sample HTTP application:

```bash
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [the health endpoint](http://localhost:8000/health) or [the interactive API documentation](http://localhost:8000/docs). The default application returns sample data and does not call a model.

### 3. Configure your provider

Copy the environment template:

**macOS / Linux**

```bash
cp env-example .env
```

**Windows PowerShell**

```powershell
Copy-Item env-example .env
```

For OpenAI, replace `OPENAI_API_KEY` in `.env` with your own key. For a local server or DeepSeek, configure the `LOCAL_*` settings described below. `.env` is ignored by Git.

A real OpenAI key is needed for OpenAI model calls, Decisions and the OpenAI sandbox examples. Local servers may accept placeholder keys; DeepSeek requires its own key. The offline tests and default FastAPI application do not require a provider key.

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

All wrappers expose `run_sync(...)` and async `run(...)`. `GPTDecision` additionally requires `questions=...` and uses a different response contract.

`GPTAgent`, `GPTLocalAgent` and `GPTSandboxAgent` support tools, handoffs and MCP. `GPT` and `GPTLocal` are direct-call wrappers. The existing constructors do not expose every SDK option: several accept `**kwargs` without forwarding unknown fields. Check the relevant module before using an advanced option.

## Configuration

Use [env-example](env-example) as the source for a complete configuration. These values are the repository's defaults, not recommendations for every workload.

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | No usable key supplied | Authentication for OpenAI API calls |
| `OPENAI_MODEL_NAME` | `gpt-4.1-mini` | Fallback model for `GPT` and `GPTAgent` |
| `OPENAI_SANDBOX_MODEL_NAME` | `gpt-5-mini` | Fallback model for `GPTSandboxAgent` |
| `OPENAI_DECISION_MODEL_NAME` | `gpt-6-luna` | Independent model setting for `GPTDecision` |
| `LOCAL_BASE_URL` | `http://localhost:1234/v1` | Compatible Chat Completions endpoint |
| `LOCAL_MODEL_NAME` | `local-model` | Model identifier accepted by that server |
| `LOCAL_API_KEY` | `lm-studio` | Local placeholder or the remote provider's real key |
| `LOCAL_DISABLE_TRACING` | `true` | Disable Agents SDK tracing when constructing `GPTLocalAgent` |
| `MCP_TRANSPORT` | `streamable-http` | Default transport for the sample MCP server |

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
- **With `agent_id`:** the Markdown definition supplies the name, role, instructions, model and token limit. Constructor `model` and `max_tokens` arguments do not replace those fields.
- **Markdown model omitted or empty:** the wrapper uses its provider-specific fallback. This is useful when sharing a definition across environments.

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

The existing Chat Completions wrappers can use a DeepSeek key without an additional library. Configure the same `LOCAL_*` variables:

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

With tracing disabled, these paths do not need an OpenAI key. The wrappers read `LOCAL_API_KEY`; they do not automatically read `DEEPSEEK_API_KEY`.

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

The default [app/main.py](app/main.py) is a minimal HTTP integration scaffold. Start it with:

```bash
uv run --locked uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| Endpoint | Purpose | Model call |
|---|---|---|
| `GET /health` | Returns `{"status":"ok"}` | No |
| `POST /example` | Accepts a `data` object and returns a fixed sample message | No |
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

The repository includes four development skills under `.agents/skills/`. They help a coding agent use the actual wrappers, generate compatible definitions and validate its implementation.

| Skill | Main task |
|---|---|
| [`agents-template-criar-agente`](.agents/skills/agents-template-criar-agente/SKILL.md) | Create or review Markdown definitions, output contracts and loading code |
| [`agents-template-criar-aplicacao`](.agents/skills/agents-template-criar-aplicacao/SKILL.md) | Implement Python features and FastAPI endpoints, including Decisions integration |
| [`agents-template-orquestrar-agentes`](.agents/skills/agents-template-orquestrar-agentes/SKILL.md) | Build sequential flows, Decisions-based routing, handoffs and specialist tools |
| [`agents-template-integrar-ferramentas`](.agents/skills/agents-template-integrar-ferramentas/SKILL.md) | Integrate Python tools, MCP 2 connections and sandbox capabilities |

Example request:

```text
Use $agents-template-orquestrar-agentes to classify requests with GPTDecision and route them to configured specialists.
```

Skills are written in Portuguese and versioned with the project. Discovery depends on your coding agent's support for repository skills; in a session that has not discovered them, reload the project or start a new chat. Another agent can also be asked to read the relevant `SKILL.md` directly.

| Location | Used by | Content |
|---|---|---|
| `.agents/skills/` | Coding agents working on the project | Development instructions, references and reusable examples |
| `app/assets/skills/` | Sandbox agents during a task | Runtime skill instructions |
| `app/assets/agents/` | Agent-definition loaders | Markdown definitions of application agents |

The [complete development skills guide](docs/development-skills.md) covers invocation, assets, validators, discovery and maintenance. No global skill installation is required to keep the skills in this repository.

## Examples and tests

### Offline regression tests

Run all discoverable tests:

```bash
uv run --locked python -m unittest discover -s app/tests -v
```

Or run a focused module:

```bash
uv run --locked python -m unittest app.tests.test_gpt_decision -v
uv run --locked python -m unittest app.tests.test_mcp_server -v
uv run --locked python -m unittest app.tests.test_skill_examples -v
```

| Test module | Coverage |
|---|---|
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

For local demonstrations, review the Markdown models before execution. Always run from the project root as a module, rather than invoking a file path such as `python app/tests/test_gpt_agents.py`.

## Project structure

```text
.
|-- .agents/skills/               # Four skills for coding agents
|-- app/
|   |-- main.py                   # Minimal FastAPI application
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
|   |   `-- util.py               # Markdown agent loaders
|   `-- tests/                    # Offline tests and live demonstrations
|-- docs/
|   |-- decisions.md              # Decisions API and routing guide
|   `-- development-skills.md     # Coding-agent skills guide
|-- .python-version               # Preferred development interpreter
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
uv pip check
git diff --check
```

When modifying a wrapper or the Markdown loader, review its development skill, examples and provider assumptions. Keep actual credentials out of committed files. In a bug report or pull request, include the command, platform, relevant versions and expected versus observed behavior, with sensitive values removed.

## License

Distributed under the [MIT license](LICENSE).
