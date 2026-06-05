# OpenAI Agents SDK Orchestration Template

A didactic Python template for experimenting with OpenAI orchestration patterns.

The project shows three complementary ways to call OpenAI models:

- `GPT`: a lightweight wrapper over the OpenAI Responses API with typed parsing.
- `GPTAgent`: a wrapper over `openai-agents` using `Agent` and `Runner.run(...)`.
- `GPTSandboxAgent`: a sandbox-capable wrapper using `SandboxAgent`, local skills, optional MCP, and a sandbox runtime.

It also exposes a small FastAPI endpoint that writes and evaluates haiku.

## What This Project Demonstrates

- Agent orchestration structure in Python.
- Typed outputs with Pydantic (`BaseModel`).
- Agent instructions loaded from Markdown files.
- Sync and async execution patterns.
- Handoffs between agents.
- Optional MCP server integration for `GPTAgent` and `GPTSandboxAgent`.
- Local sandbox skills loaded from `app/assets/skills`.
- HTTP API exposure with FastAPI.

## Project Structure

```text
.
|-- app/
|   |-- main.py
|   |-- test_gpt.py
|   |-- test_gpt_agents.py
|   |-- test_gpt_sandbox_agent.py
|   |-- assets/
|   |   |-- instructions/
|   |   |   |-- writer.md
|   |   |   |-- evaluator.md
|   |   |   `-- translator.md
|   |   `-- skills/
|   |       `-- haiku_quality/
|   |           `-- SKILL.md
|   `-- orchestration/
|       |-- config.py
|       |-- gpt.py
|       |-- gpt_agent.py
|       |-- gpt_sandbox_agent.py
|       `-- util.py
|-- env-example
|-- requirements.txt
`-- LICENSE
```

## Prerequisites

- Python 3.10+
- OpenAI API key (`OPENAI_API_KEY`)

Project dependencies:

- `openai`
- `python-dotenv`
- `openai-agents`
- `fastapi`
- `uvicorn`

## Setup

### 1. Create A Virtual Environment

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Use `env-example` as a base and create a `.env` file in the project root:

```env
OPENAI_MODEL_NAME="gpt-4.1-mini"
OPENAI_SANDBOX_MODEL_NAME="gpt-5-mini"
OPENAI_API_KEY="your-api-key"
```

`OPENAI_MODEL_NAME` is the default model for the regular `GPT` and `GPTAgent` examples. If omitted, the project defaults to `gpt-4.1-mini`.

`OPENAI_SANDBOX_MODEL_NAME` is intended for sandbox experiments. Sandbox agents use model-facing tools that rely on custom tool support, so a GPT-5-family model such as `gpt-5-mini` is a safer default than `gpt-4.1-mini`.

## Configuration Helpers

Shared environment/model logic lives in `app/orchestration/config.py`.

```python
from app.orchestration.config import default_model, sandbox_model

regular_model = default_model()
sandbox_default = sandbox_model()
```

`default_model()` reads `OPENAI_MODEL_NAME`.

`sandbox_model()` reads `OPENAI_SANDBOX_MODEL_NAME` and falls back to `gpt-5-mini`.

Instruction files are loaded with `instruction_loader(...)` from `app/orchestration/util.py`.

```python
from app.orchestration.util import instruction_loader

instructions = instruction_loader("writer")
```

By default, `instruction_loader("writer")` reads:

```text
app/assets/instructions/writer.md
```

This keeps prompts outside Python source code and makes them easy to edit independently.

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
python -m app.test_gpt
python -m app.test_gpt_agents
python -m app.test_gpt_sandbox_agent
```

### `app/test_gpt.py`

Demonstrates the lightweight `GPT` wrapper.

Use this when you want a simple Responses API call with typed parsing and do not need agent handoffs, MCP, or sandbox capabilities.

### `app/test_gpt_agents.py`

Demonstrates `GPTAgent` with a writer/evaluator flow.

The writer agent creates the haiku. The evaluator agent is passed as a handoff-capable agent. The final output is parsed into a Pydantic model:

```python
class HaikuResponse(BaseModel):
    subject: str
    haiku: str
    score: int
```

### `app/test_gpt_sandbox_agent.py`

Demonstrates `GPTSandboxAgent` with local sandbox skills.

This is a real integration example: it calls the model and uses the sandbox-capable agent. Because it makes an external OpenAI API call, it requires a valid `OPENAI_API_KEY`.

## `GPTAgent` With MCP

`GPTAgent` can run with or without an MCP server.

Without MCP:

```python
agent = GPTAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions=instruction_loader("writer"),
    output_type=HaikuResponse,
)

result = agent.run_sync("Write a haiku about the changing seasons.")
```

With MCP:

```python
agent = GPTAgent(
    name="MCP Agent",
    role="You are a helpful assistant with access to MCP tools.",
    instructions="Use available tools when they help answer the user.",
    output_type=GPTAgentResponse,
    mcp_url="http://localhost:8001/mcp",
    mcp_headers={"Authorization": "Bearer token-if-needed"},
    mcp_timeout=30,
)

result = agent.run_sync("Use the available tools to answer this request.")
```

When `mcp_url` is omitted, `GPTAgent` behaves like the original implementation and simply calls:

```python
Runner.run(agent, prompt)
```

When `mcp_url` is provided, `GPTAgent` opens an `MCPServerStreamableHttp` connection for the run and assigns it to `self.mcp_servers`.

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

That skill gives the agent review criteria for haiku:

- three lines;
- approximate 5-7-5 syllable target;
- concrete imagery;
- restrained explanation;
- strict integer scoring.

Example:

```python
from app.orchestration.config import sandbox_model

writer = GPTSandboxAgent(
    name="Haiku Agent",
    role="You are a helpful assistant that writes haikus.",
    instructions=instruction_loader("writer"),
    output_type=HaikuResponse,
    model=sandbox_model(),
    skills_dir="app/assets/skills",
)

result = writer.run_sync("Write a haiku about the changing seasons.")
```

You can also pass:

```python
skills_dir="assets/skills"
```

The wrapper resolves that project-relative path to `app/assets/skills` when possible.

## How To Know A Skill Is Being Used

Loading a skill directory makes the skill available to the sandbox agent. It does not automatically prove that the model used the skill in a particular response.

For stronger evidence during testing, use one or more of these strategies:

- Mention the skill explicitly in the prompt, for example: `Use the Haiku Quality skill.`
- Add an artificial test-only rule to a skill, such as `always return score=6`, then assert that value.
- Inspect traces or intermediate run steps if you enable tracing for the Agents SDK.

For normal product behavior, the skill should contain useful domain guidance. For tests, a deliberately obvious rule is often better because it turns skill usage into something you can assert.

## Sync Versus Async

Every wrapper exposes an async method:

```python
result = await agent.run(prompt)
```

The wrappers also expose a sync convenience method:

```python
result = agent.run_sync(prompt)
```

Do not call `run_sync(...)` inside an already-running event loop. In async contexts such as FastAPI endpoints, use:

```python
result = await agent.run(prompt)
```

The wrappers raise a clear `RuntimeError` if `run_sync(...)` is called from inside an active event loop.

## Customization

- Edit instructions in `app/assets/instructions/*.md`.
- Edit or add skills under `app/assets/skills/<skill_name>/SKILL.md`.
- Change the regular model with `OPENAI_MODEL_NAME` in `.env`.
- Change the sandbox model with `OPENAI_SANDBOX_MODEL_NAME` in `.env`, or pass `model=...` directly.
- Add handoffs by passing `handoffs=[other_agent]`.
- Add MCP by passing `mcp_url`, `mcp_headers`, and `mcp_timeout`.
- Reuse `instruction_loader(...)` to keep prompts outside source code.

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

or pass it directly:

```python
model="gpt-5-mini"
```

### The Skill Exists, But The Output Does Not Prove It Was Used

That is expected. A skill can be available without being obviously reflected in the final answer. For verifiable tests, add a test-only rule to the skill and assert the result.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
