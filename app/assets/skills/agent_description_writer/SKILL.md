# Agent Description Writer

Use this skill when writing or improving an agent definition for this project from a user request.

The output must follow the project agent template used in `app/assets/agents/*.md`.

## Goal

Transform a user's request for an agent into a complete Markdown agent definition that can be saved as:

```text
app/assets/agents/<agent_id>.md
```

## Required Format

Return the agent definition in this exact structure:

```markdown
---
id: <agent_id>
role: <short role name>
goal: <one-sentence objective>
backstory: <concise background that shapes behavior>
max_tokens: <integer>
model: <model name>
---

# INPUT
<what the agent expects to receive>

# OUTPUT
<what the agent must return>

# INSTRUCTIONS
<specific behavioral rules>

# KNOWLEDGE
<domain knowledge, standards, terminology, constraints, or examples the agent should rely on>
```

## Writing Rules

- Infer reasonable defaults from the user's request when details are missing.
- Ask a clarifying question only when the missing detail would change the agent's purpose or output contract.
- Use a stable lowercase `id` suitable for a filename, preferably short words joined by underscores.
- Make `role` specific and human-readable, such as `Contract Clause Reviewer` or `Lesson Plan Designer`.
- Write `goal` as a single operational sentence.
- Write `backstory` as behavior-shaping context, not biography for its own sake.
- Set `max_tokens` according to expected output size:
  - `512` for short classification, extraction, or rewriting tasks.
  - `2048` for normal writing, review, planning, or structured responses.
  - `4096` or more only for long documents or complex analysis.
- Use `gpt-4.1-mini` as the default `model` unless the request requires stronger reasoning, tool use, sandbox behavior, or the user names another model.
- Keep the agent definition self-contained; do not assume external files unless the user explicitly requests them.
- Prefer precise, testable instructions over vague style guidance.
- Include constraints about formatting, language, tone, citations, refusal behavior, or validation when they matter.
- Do not include explanations outside the agent definition unless the user asks for implementation notes.

## Section Guidance

### INPUT

Describe accepted inputs as bullets when there are multiple input types. Include optional context, files, parameters, target audience, language, or output format when relevant.

### OUTPUT

Specify the exact final response shape. Use plain language for flexible text outputs, or include a Pydantic-style schema when the surrounding code will parse structured output.

Example:

```python
class AgentResponse(BaseModel):
    summary: str
    findings: list[str]
    next_steps: list[str]
```

### INSTRUCTIONS

Write operational rules in imperative bullets. Cover:

- How to interpret the input.
- What sequence of reasoning or work to perform.
- What to preserve, transform, omit, or validate.
- How to handle ambiguity or missing information.
- What the final answer must and must not contain.

### KNOWLEDGE

Add compact domain knowledge the model should use during the task, such as terminology, evaluation criteria, style standards, business rules, or examples. Avoid generic AI advice.

## Quality Checklist

Before returning the definition, verify that:

- The YAML frontmatter is complete and parseable.
- The `id` matches the intended filename.
- The role, goal, and instructions point to the same job.
- The output contract is clear enough to test.
- The agent can work from only the user input plus this definition.
- The Markdown contains all four required sections.
