# OpenAI Agents SDK Template - Haiku Orchestration

A didactic example project showing how to orchestrate AI agents with the `openai-agents` SDK in Python.

This template creates two agents:
- `Haiku Writer`: writes a haiku for a given subject.
- `Haiku Evaluator`: evaluates the haiku quality using basic haiku conventions.

The project is intentionally small, so it is easy to study and extend.

## What This Project Demonstrates

- How to structure a simple multi-agent orchestration in Python
- How to define typed outputs with Pydantic (`BaseModel`)
- How to include external knowledge from a local Markdown file
- How to execute an async agent workflow and expose a sync entrypoint

## Project Structure

```text
.
|-- app/
|   |-- main.py
|   `-- orchestration/
|       |-- haiku_agents.py
|       `-- knowledge/
|           `-- haiku_writer.md
|-- env-example
|-- requirements.txt
`-- LICENSE
```

## Requirements

- Python 3.10+
- OpenAI API key

Dependencies (from `requirements.txt`):
- `openai-agents`
- `python-dotenv`

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Create your `.env` file from `env-example`.

### 1) Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

Create `.env` in the project root with:

```env
OPENAI_MODEL_NAME="gpt-4.1-mini"
OPENAI_API_KEY="your-api-key"
```

## Run the Project

From the project root:

```bash
python -m app.main
```

Expected behavior:
- The script asks the writer agent for a haiku about `recursion in programming`.
- The final typed response is printed with:
  - `Subject`
  - `Haiku`
  - `Score`

## How It Works

### 1) Output model (`HaikuResponse`)

In `app/orchestration/haiku_agents.py`, the response is typed with Pydantic:
- `subject: str`
- `haiku: str`
- `score: int`

This ensures consistent output shape from the agent workflow.

### 2) Knowledge loading

The method `__get_knowledge()` loads `app/orchestration/knowledge/haiku_writer.md`.

That text is appended to the writer agent instructions, giving the model local guidance on haiku style.

### 3) Agent creation

`__create_agents()` defines:
- **Haiku Evaluator**: strict reviewer instructions
- **Haiku Writer**: writes the poem and can hand off to evaluator

Both currently use `gpt-4.1-mini` as a fixed model in code.

### 4) Execution

- `run(subject)` executes asynchronously with `Runner.run(...)`
- `run_sync(subject)` wraps it with `asyncio.run(...)`
- `app/main.py` uses `run_sync(...)` for a simple CLI-style run

## Customize

You can extend this template by:
- Changing the subject in `app/main.py`
- Editing `haiku_writer.md` to alter writing style
- Adjusting evaluator strictness in agent instructions
- Adding more agents and handoff paths

## Notes

- A `.env` file is loaded with `python-dotenv`.
- Keep your `OPENAI_API_KEY` private and never commit it.
- The model value from `.env` is present, but the current code sets model names directly in `haiku_agents.py`.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
