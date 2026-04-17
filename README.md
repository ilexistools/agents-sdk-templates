# OpenAI Agents SDK Orchestration Template

A didactic Python example showing how to create agents, chain handoffs, and expose everything through a FastAPI API.

The project includes two main flows:
- `GPT`: a lightweight wrapper over OpenAI `responses.parse`.
- `GPTAgent`: a wrapper based on `openai-agents` and `Runner.run(...)`.

## What this project demonstrates

- Agent orchestration structure in Python.
- Typed outputs with Pydantic (`BaseModel`).
- Agent instructions loaded from local Markdown files.
- Sync and async execution patterns.
- HTTP API exposure with FastAPI.

## Project structure

```text
.
|-- app/
|   |-- main.py
|   |-- test_gpt.py
|   |-- test_gpt_agents.py
|   |-- assets/
|   |   `-- instructions/
|   |       |-- writer.md
|   |       |-- evaluator.md
|   |       `-- translator.md
|   `-- orchestration/
|       |-- gpt.py
|       |-- gpt_agent.py
|       `-- util.py
|-- env-example
|-- requirements.txt
`-- LICENSE
```

## Prerequisites

- Python 3.10+
- OpenAI API key (`OPENAI_API_KEY`)

Project dependencies:
- `python-dotenv`
- `openai-agents`
- `fastapi`
- `uvicorn`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Create a `.env` file with your key.

### 1) Virtual environment

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Environment variables

Use `env-example` as a base and create `.env` in the project root:

```env
OPENAI_MODEL_NAME="gpt-4.1-mini"
OPENAI_API_KEY="your-api-key"
```

Note: the model is currently hardcoded in the code (`gpt-4.1-mini`), so `OPENAI_MODEL_NAME` is not yet used by the main modules.

## Running the API

From the project root:

```bash
python -m app.main
```

Or with auto-reload:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

## Endpoints

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

## Local examples (without FastAPI)

- `app/test_gpt.py`: simple translation using the `GPT` wrapper.
- `app/test_gpt_agents.py`: `writer` + `evaluator` flow using `GPTAgent`.

Run them with:

```bash
python -m app.test_gpt
python -m app.test_gpt_agents
```

## Customization

- Edit instructions in `app/assets/instructions/*.md`.
- Change the model in `app/main.py`, `app/test_gpt.py`, and `app/test_gpt_agents.py`.
- Create new agents in `app/orchestration/gpt_agent.py` and add new handoffs.
- Reuse `instruction_loader(...)` to keep prompts outside source code.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
