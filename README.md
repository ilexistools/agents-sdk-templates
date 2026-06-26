# OpenAI Agents SDK Orchestration Template

A didactic Python template for experimenting with OpenAI orchestration patterns.

The project shows five complementary ways to call models:

- `GPT`: a lightweight wrapper over the OpenAI Responses API with typed parsing.
- `GPTAgent`: a wrapper over `openai-agents` using `Agent` and `Runner.run(...)`.
- `GPTSandboxAgent`: a sandbox-capable wrapper using `SandboxAgent`, local skills, optional MCP, and a sandbox runtime.
- `GPTLocal`: a wrapper that calls any OpenAI-compatible local server (LM Studio, Ollama, etc.) via `chat.completions`.
- `GPTLocalAgent`: same as `GPTAgent` but pointed at a local server via `OpenAIChatCompletionsModel`.

It also exposes a small FastAPI endpoint that writes and evaluates haiku.

## What This Project Demonstrates

- Agent orchestration structure in Python.
- Typed outputs with Pydantic (`BaseModel`).
- Agent definitions loaded from Markdown files via `agent_id`.
- Sync and async execution patterns.
- Handoffs between agents.
- Optional MCP server integration for `GPTAgent` and `GPTSandboxAgent`.
- Local sandbox skills loaded from `app/assets/skills`.
- HTTP API exposure with FastAPI.
- Local open-source model support via any OpenAI-compatible server.

## Project Structure

```text
.
|-- app/
|   |-- main.py
|   |-- test_gpt.py
|   |-- test_gpt_agents.py
|   |-- test_gpt_sandbox_agent.py
|   |-- test_gpt_local.py
|   |-- test_gpt_agent_local.py
|   |-- assets/
|   |   |-- agents/
|   |   |   |-- writer.md
|   |   |   |-- evaluator.md
|   |   |   |-- translator.md
|   |   |   `-- template.md
|   |   `-- skills/
|   |       `-- haiku_quality/
|   |           `-- SKILL.md
|   `-- orchestration/
|       |-- config.py
|       |-- gpt.py
|       |-- gpt_agent.py
|       |-- gpt_sandbox_agent.py
|       |-- gpt_local.py
|       |-- gpt_agent_local.py
|       `-- util.py
|-- pyproject.toml
|-- uv.lock
|-- env-example
`-- LICENSE
```

## Prerequisites

- Python 3.12+
- OpenAI API key (`OPENAI_API_KEY`)

Project dependencies (defined in `pyproject.toml`):

- `openai`
- `openai-agents`
- `python-dotenv`
- `pyyaml`
- `fastapi`
- `uvicorn`

## Setup

### 1. Create A Virtual Environment

With [uv](https://github.com/astral-sh/uv) (recommended):

```bash
uv sync
```

Or with pip:

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e .
```

### 2. Configure Environment Variables

Use `env-example` as a base and create a `.env` file in the project root:

```env
OPENAI_MODEL_NAME="gpt-4.1-mini"
OPENAI_SANDBOX_MODEL_NAME="gpt-5-mini"
OPENAI_API_KEY="your-api-key"

# Local model server (LM Studio, Ollama, etc.)
LOCAL_BASE_URL="http://localhost:1234/v1"
LOCAL_MODEL_NAME="local-model"
LOCAL_API_KEY="lm-studio"
```

`OPENAI_MODEL_NAME` is the default model for `GPT` and `GPTAgent`. If omitted, defaults to `gpt-4.1-mini`.

`OPENAI_SANDBOX_MODEL_NAME` is used by `GPTSandboxAgent`. Sandbox agents rely on custom tool support, so a GPT-5-family model such as `gpt-5-mini` is recommended.

`LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, and `LOCAL_API_KEY` are used by `GPTLocal` and `GPTLocalAgent`. See [Local Models](#local-models-lm-studio-ollama-and-others) for details.

## Agent Definitions

Agents are defined as Markdown files under `app/assets/agents/`. Each file has a YAML frontmatter block followed by named sections.

Example — `app/assets/agents/writer.md`:

```markdown
---
id: writer
role: Haiku Writer
goal: Write short, evocative haiku poems based on a theme provided by the user.
backstory: You are a skilled haiku writer with a deep sensitivity to nature and everyday moments.
max_tokens: 256
model: gpt-4.1-mini
---

# INPUT
A theme, image, or feeling to inspire the haiku.

# OUTPUT
class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int

# INSTRUCTIONS
- Write one haiku based on the user's input.
...

# KNOWLEDGE
How to write haiku...
```

### Frontmatter Fields

| Field | Description |
|---|---|
| `id` | Identifier used as `agent_id` when loading |
| `role` | System role prepended to instructions |
| `goal` | Primary objective of the agent |
| `backstory` | Background context for the agent |
| `model` | Model override (falls back to `OPENAI_MODEL_NAME`) |
| `max_tokens` | Maximum output tokens (default: 2048) |

### Loading An Agent By ID

Pass `agent_id` to any wrapper class to load everything from the markdown file:

```python
from app.orchestration.gpt_agent import GPTAgent

agent = GPTAgent(agent_id="writer", output_type=HaikuResponse)
result = agent.run_sync("Write a haiku about autumn.")
```

The agent name, role, instructions, model, and token limit are all read from the file. You can still override individual fields at the call site — for example, `output_type`, `tools`, `handoffs`, or `mcp_url`.

### Loading Manually (without `agent_id`)

You can still configure agents fully in code by omitting `agent_id`:

```python
agent = GPTAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions="Write one haiku per request.",
    output_type=HaikuResponse,
    model="gpt-4.1-mini",
)
```

## Configuration Helpers

Shared environment and model logic lives in `app/orchestration/config.py`.

```python
from app.orchestration.config import default_model, sandbox_model

regular_model = default_model()   # reads OPENAI_MODEL_NAME
sandbox_default = sandbox_model() # reads OPENAI_SANDBOX_MODEL_NAME
```

The utility `load_agent_config` in `app/orchestration/util.py` is used internally by all three wrapper classes to load and assemble agent configuration from a markdown file:

```python
from app.orchestration.util import load_agent_config

config = load_agent_config("writer", fallback_model=default_model())
# config keys: name, role, instructions, model, max_tokens
```

The lower-level `load_agent_markdown` returns the raw parsed dict with `metadata` and `sections` if you need direct access to the file structure.

## Running The API

From the project root:

```bash
python -m app.main
```

Or with auto-reload:

```bash
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

## API Endpoints

- `GET /health`: health check.
- `POST /haiku`: generates and evaluates a haiku for the given subject.

Request example:

```bash
curl -X POST http://localhost:8000/haiku \
  -H "Content-Type: application/json" \
  -d '{"subject":"the changing seasons"}'
```

Response example:

```json
{
  "subject": "the changing seasons",
  "haiku": "Old leaves on the ground\nFirst light touches waking branches\nSpring breathes through the mist",
  "score": 8
}
```

## Local Examples

Run examples as Python modules from the project root. This keeps absolute imports like `from app...` working correctly.

```bash
# OpenAI
python -m app.test_gpt
python -m app.test_gpt_agents
python -m app.test_gpt_sandbox_agent

# Local model server
python -m app.test_gpt_local
python -m app.test_gpt_agent_local
```

### `app/test_gpt.py`

Demonstrates the lightweight `GPT` wrapper loaded from a markdown agent file.

Use this when you want a simple Responses API call with typed parsing and do not need agent handoffs, MCP, or sandbox capabilities.

### `app/test_gpt_agents.py`

Demonstrates `GPTAgent` with a writer/evaluator flow using `agent_id`.

Both agents are loaded from their respective markdown files. The writer agent creates the haiku; the evaluator is passed as a handoff target. Both receive a custom `output_type` at construction:

```python
evaluator = GPTAgent(agent_id='evaluator', output_type=HaikuResponse)
writer = GPTAgent(agent_id='writer', output_type=HaikuResponse, handoffs=[evaluator])
```

### `app/test_gpt_sandbox_agent.py`

Demonstrates `GPTSandboxAgent` with local sandbox skills loaded from an agent markdown file.

This example makes a real OpenAI API call and requires a valid `OPENAI_API_KEY`.

### `app/test_gpt_local.py`

Demonstrates `GPTLocal` using a locally running model server. Requires `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, and `LOCAL_API_KEY` set in `.env` and the server running before execution.

### `app/test_gpt_agent_local.py`

Demonstrates `GPTLocalAgent` with a writer/evaluator flow using a local model. Same flow as `test_gpt_agents.py` but routed through the local server.

## `GPTAgent` With MCP

`GPTAgent` can run with or without an MCP server.

Without MCP:

```python
agent = GPTAgent(agent_id="writer", output_type=HaikuResponse)
result = agent.run_sync("Write a haiku about the changing seasons.")
```

With MCP:

```python
agent = GPTAgent(
    agent_id="writer",
    output_type=HaikuResponse,
    mcp_url="http://localhost:8001/mcp",
    mcp_headers={"Authorization": "Bearer token-if-needed"},
    mcp_timeout=30,
)

result = agent.run_sync("Write a haiku using the available tools.")
```

When `mcp_url` is omitted, `GPTAgent` calls `Runner.run(agent, prompt)` directly. When provided, it opens an `MCPServerStreamableHttp` connection for the run and assigns it to `self.mcp_servers`.

## `GPTSandboxAgent` And Skills

`GPTSandboxAgent` extends the regular agent pattern with sandbox capabilities and local skills.

The default skills directory is:

```text
app/assets/skills
```

The current sample skill is:

```text
app/assets/skills/haiku_quality/SKILL.md
```

That skill gives the agent review criteria for haiku: three lines, approximate 5-7-5 syllable target, concrete imagery, restrained explanation, and strict integer scoring.

Example:

```python
writer = GPTSandboxAgent(agent_id="writer", output_type=HaikuResponse)
result = writer.run_sync("Write a haiku about the changing seasons.")
```

You can override the skills directory:

```python
writer = GPTSandboxAgent(
    agent_id="writer",
    output_type=HaikuResponse,
    skills_dir="app/assets/skills",
)
```

The wrapper resolves project-relative paths to `app/assets/skills` when possible.

### Sandbox Backend

On macOS/Linux, `GPTSandboxAgent` uses `UnixLocalSandboxClient` by default. On Windows, it falls back to `DockerSandboxClient` (requires Docker Desktop and the `docker` Python package). You can also pass a custom client:

```python
from agents.sandbox.sandboxes.docker import DockerSandboxClient

writer = GPTSandboxAgent(
    agent_id="writer",
    output_type=HaikuResponse,
    sandbox_client=DockerSandboxClient(),
)
```

## How To Know A Skill Is Being Used

Loading a skill directory makes the skill available to the sandbox agent at the `.agents/` path inside the workspace. It does not automatically prove that the model used the skill in a particular response.

For stronger evidence during testing, use one or more of these strategies:

- Mention the skill explicitly in the prompt: `Use the Haiku Quality skill.`
- Add an artificial test-only rule to a skill, such as `always return score=6`, then assert that value.
- Inspect traces or intermediate run steps if you enable tracing for the Agents SDK.

## Local Models (LM Studio, Ollama, and Others)

`GPTLocal` and `GPTLocalAgent` work with any server that exposes an OpenAI-compatible REST API. No real API key is required.

| Server | Default base URL | `LOCAL_API_KEY` |
|---|---|---|
| LM Studio | `http://localhost:1234/v1` | `lm-studio` |
| Ollama | `http://localhost:11434/v1` | `ollama` |
| Other | custom | any non-empty string |

### `GPTLocal`

Uses `chat.completions` directly. When a structured `output_type` is provided, the JSON schema is injected into the system prompt and the response is parsed automatically. Markdown code fences (` ```json ``` `) that some models add are stripped before parsing.

```python
from app.orchestration.gpt_local import GPTLocal, GPTLocalResponse

# Plain text output
agent = GPTLocal(
    agent_id="translator",
    output_type=GPTLocalResponse,
)
result = agent.run_sync("Translate: Hello, world!")
print(result.final_output)

# Structured output
from pydantic import BaseModel

class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int

writer = GPTLocal(agent_id="writer", output_type=HaikuResponse)
result = writer.run_sync("Write a haiku about rain.")
print(result.model_dump())
```

You can override any connection parameter at the call site:

```python
agent = GPTLocal(
    agent_id="writer",
    output_type=HaikuResponse,
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="llama3.2",
)
```

### `GPTLocalAgent`

Uses the Agents SDK with `OpenAIChatCompletionsModel` pointed at the local server. Supports handoffs, tools, and MCP exactly like `GPTAgent`.

```python
from app.orchestration.gpt_agent_local import GPTLocalAgent

evaluator = GPTLocalAgent(agent_id="evaluator", output_type=HaikuResponse)
writer = GPTLocalAgent(
    agent_id="writer",
    output_type=HaikuResponse,
    handoffs=[evaluator],
)
result = writer.run_sync("Write a haiku about the changing seasons.")
print(result.model_dump())
```

### Structured Output Compatibility

`GPTLocal` instructs the model via the system prompt and parses the response with `model_validate_json`. This works with most models but depends on instruction-following quality. For reliable structured output, prefer models fine-tuned for JSON or use tool calling if the server supports it.

`GPTLocalAgent` relies on the Agents SDK runner. Whether structured outputs succeed depends on the model and server capabilities.

## Sync Versus Async

Every wrapper exposes an async method:

```python
result = await agent.run(prompt)
```

And a sync convenience method:

```python
result = agent.run_sync(prompt)
```

Do not call `run_sync(...)` inside an already-running event loop. In async contexts such as FastAPI endpoints, use `await agent.run(prompt)`. The wrappers raise a clear `RuntimeError` if `run_sync(...)` is called from inside an active event loop.

## Customization

- Add or edit agent definitions under `app/assets/agents/<id>.md`.
- Add or edit skills under `app/assets/skills/<skill_name>/SKILL.md`.
- Change the regular model with `OPENAI_MODEL_NAME` in `.env`, or set `model` in the agent markdown frontmatter.
- Change the sandbox model with `OPENAI_SANDBOX_MODEL_NAME` in `.env`.
- Change the local model server with `LOCAL_BASE_URL`, `LOCAL_MODEL_NAME`, and `LOCAL_API_KEY` in `.env`.
- Add handoffs by passing `handoffs=[other_agent]` at construction time.
- Add MCP by passing `mcp_url`, `mcp_headers`, and `mcp_timeout`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Run examples as modules from the project root:

```bash
python -m app.test_gpt_agents
```

Instead of:

```bash
python app/test_gpt_agents.py
```

### `Invalid value: 'custom'`

This can happen when a sandbox run uses a model that does not support the custom tools used by the sandbox runtime.

Use a GPT-5-family model for sandbox examples:

```env
OPENAI_SANDBOX_MODEL_NAME="gpt-5-mini"
```

Or set it in the agent markdown frontmatter:

```yaml
model: gpt-5-mini
```

### `ImportError: UnixLocalSandbox is not supported on Windows`

This error should not occur with the current code, which automatically selects `DockerSandboxClient` on Windows. If you see it, ensure you are running the latest version and that Docker Desktop is running.

### `Connection refused` When Using Local Models

The local server is not running or is listening on a different port. Start LM Studio or Ollama and verify the base URL matches `LOCAL_BASE_URL` in your `.env`.

### Local Model Returns Plain Text Instead Of JSON

The model did not follow the JSON instruction in the system prompt. Try a model with stronger instruction-following capability, or add an explicit reminder in the prompt: `Respond only with valid JSON, no other text.`

### The Skill Exists, But The Output Does Not Prove It Was Used

That is expected. A skill can be available without being obviously reflected in the final answer. For verifiable tests, add a test-only rule to the skill and assert the result.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
