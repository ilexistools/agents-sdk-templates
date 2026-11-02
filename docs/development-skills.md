# Development skills

The repository bundles four skills for coding agents that create applications
with this template. They are versioned under `.agents/skills/`; their instructions
and UI descriptions are in Portuguese. Application source and README conventions
remain unchanged.

## Discovery and setup

Open this repository as the coding agent's project. In Codex environments that
support repository skills, `.agents/skills/` is the discovery location. If a
running session has not discovered newly added skills, reload the project or
start a new chat and check its available skills list.

No global installation, account connection or runtime dependency is added.
For another coding agent, use its supported skill loader, or explicitly ask it
to read the relevant `SKILL.md`. Do not assume that copying these directories
automatically enables discovery in every agent product. Keep supporting files
with their skill when copying it; run its examples from a checkout of this project.

## Catalog and invocation examples

| Skill | Use it for | Example request |
|---|---|---|
| [agents-template-criar-agente](../.agents/skills/agents-template-criar-agente/SKILL.md) | Markdown definitions, Pydantic output contracts and loading code | `Use $agents-template-criar-agente to create a report reviewer with structured output.` |
| [agents-template-criar-aplicacao](../.agents/skills/agents-template-criar-aplicacao/SKILL.md) | Python features, provider configuration and FastAPI endpoints | `Use $agents-template-criar-aplicacao to create a classification endpoint using DeepSeek.` |
| [agents-template-orquestrar-agentes](../.agents/skills/agents-template-orquestrar-agentes/SKILL.md) | Mandatory stages, handoffs and agents exposed as tools | `Use $agents-template-orquestrar-agentes to extract facts and then review them.` |
| [agents-template-integrar-ferramentas](../.agents/skills/agents-template-integrar-ferramentas/SKILL.md) | Python tools, MCP 2 connections and sandbox capabilities | `Use $agents-template-integrar-ferramentas to connect an agent to the sample MCP server.` |

Automatic selection remains enabled by default; explicit `$skill-name` invocation
makes the intended workflow clear. Several skills can contribute to one request,
but an agent should load only the references relevant to that request.

## Contents and intended outputs

- **Create an agent:** Markdown authoring guidance, a complete report-reviewer
  definition, a matching Pydantic example, and an offline validator using the
  application's real loader. It builds on the writing guidance in the existing
  runtime `agent_description_writer` skill without replacing that skill.
- **Create an application:** wrapper selection, provider configuration, output
  parsing limits, and a runnable FastAPI example with a classification endpoint.
- **Orchestrate agents:** guidance distinguishing mandatory Python stages,
  model-selected handoffs and specialists as tools; an importable two-stage
  extraction/review example with injectable agents and explicit contracts.
- **Integrate tools:** a pure Python function and its `function_tool` adapter,
  MCP 2 server/client lifecycle guidance, and sandbox backend/skill configuration.

The examples are starting points to adapt, not new production endpoints or
automatically registered application agents. In particular, the report-reviewer
definition remains a skill asset until copied to `app/assets/agents/` for a task.

## Development skills versus runtime skills

| Location | Consumer | Purpose |
|---|---|---|
| `.agents/skills/` | The coding agent working on this repository | Create and integrate code and agent definitions |
| `app/assets/skills/` | `GPTSandboxAgent` during application execution | Provide task instructions such as haiku review |
| `app/assets/agents/` | `load_agent_config` and the model wrappers | Define application agents in Markdown |

The sandbox's `skills_path=".agents"` is inside its own workspace. It does not
mean the repository's development skills are loaded by the sandbox. The default
runtime source remains `app/assets/skills/`; this change does not alter it.

## Validation

From the repository root, reproduce the locked environment:

```bash
uv sync --locked
```

Validate the bundled agent example without a model call:

```bash
uv run --locked python .agents/skills/agents-template-criar-agente/scripts/validar_agente.py .agents/skills/agents-template-criar-agente/assets/relatorio_revisor.md
```

Replace the final path with any authored agent file. Multiple files are accepted.
Use `--project-root PATH` when running outside the project root. The validator
checks filename/id agreement, required authoring fields and sections, token/model
types, and successful loading. Its authoring conventions are stricter than the
loader. It does not evaluate response quality or prove a Python output model
matches the prose contract.

Run the offline executable-example checks:

```bash
uv run --locked python -m unittest app.tests.test_skill_examples -v
```

These cover valid and invalid agent definitions, endpoint serialization and
input validation with a mocked model, sequential data flow and failure handling,
and a Python tool's schema and adapter invocation. No provider key, live model
call or Docker backend is required. Existing MCP checks can be run separately:

```bash
uv run --locked python -m unittest app.tests.test_mcp_server -v
```

To try the classification example with a live OpenAI model, configure
`OPENAI_API_KEY` and optionally `OPENAI_MODEL_NAME`, then run:

```bash
uv run --locked uvicorn --app-dir .agents/skills/agents-template-criar-aplicacao/assets classificacao_api:app --port 8001
```

Call `POST /classificar` with `{"texto": "Como acessar o sistema?"}`. It returns
`categoria` and `justificativa`. That request uses the configured provider and
may incur its normal charges; the offline tests replace this call with a mock.

## Maintenance and limits

The current wrappers and loader are the implementation source of truth. When
changing their constructors, model precedence, return types or MCP/sandbox APIs,
review the relevant skill and run its executable checks. Keep provider/model
examples aligned with the provider's official documentation when changing them.

These skills record important current constraints: frontmatter model precedence,
prompt-based JSON parsing for compatible providers, MCP connection lifetime,
mutable MCP state during concurrent calls, and backend requirements on Windows.
Provider-specific tool/reasoning behavior and live sandbox execution still require
validation in the target environment. Offline tests do not establish those claims.

Formal skill manifests can additionally be checked with `quick_validate.py` from
an installed `skill-creator` skill; that tool is authoring infrastructure and is
not a new application dependency.
