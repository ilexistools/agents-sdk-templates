# Decisions and specialist routing

`GPTDecision` adds OpenAI Decisions to the template. It evaluates fixed questions
and returns the SDK's `Decision` object. A separate example uses the answer to
select a specialist through an explicit application-level mapping.

The current supported Decisions model is `gpt-6-luna`. Question types are
`predicate` (a condition probability), `choice` (a category), and `score` (an
ordered-rubric result). For scores, the value can fall between level indices.
Decisions returns answers; the application executes selected actions. See the
[official Decisions guide](https://developers.openai.com/api/docs/guides/decisions)
for provider capabilities and current model availability.

## Configuration

Use the existing locked environment; no dependency change is needed:

```bash
uv sync --locked
```

Set in your environment or `.env`:

```dotenv
OPENAI_API_KEY="your-openai-api-key"
OPENAI_DECISION_MODEL_NAME="gpt-6-luna"
```

The Decisions model is independent of `OPENAI_MODEL_NAME`, which configures
the specialists. The constructor's `model` argument takes precedence over
`OPENAI_DECISION_MODEL_NAME`; otherwise the default is `gpt-6-luna`.
This integration targets OpenAI; it does not assume a Decisions endpoint on
DeepSeek or local Chat Completions servers.

## Direct calls

```python
from app.orchestration.gpt_decision import GPTDecision

decider = GPTDecision()
with decider.client:
    result = decider.run_sync(
        "Please refund the duplicate charge.",
        questions=[{
            "type": "predicate",
            "name": "refund_requested",
            "instructions": "Does the person explicitly ask for a refund?",
        }],
    )
for answer in result.answers:
    # Any question can return type='refusal'; preserve it for the caller.
    print(answer.model_dump())
print(result.model, result.usage.model_dump())
```

Async equivalent, within an async function:

```python
from app.examples.decisions import EXAMPLE_QUESTIONS
from app.orchestration.gpt_decision import GPTDecision

async def evaluate(text: str):
    decider = GPTDecision()
    async with decider.async_client:
        return await decider.run(text, questions=EXAMPLE_QUESTIONS)
```

`EXAMPLE_QUESTIONS` includes one question of each type. Independent questions
share the same input; decisions dependent on an earlier answer require separate
calls. Keep categories and rubric levels distinct and observable.

## Wrapper contract

| Surface | Behavior |
|---|---|
| `GPTDecision(model=None, client=None, async_client=None)` | Loads environment configuration; accepts existing SDK clients |
| `run_sync(input, *, questions, **request_options)` | Uses the synchronous SDK client |
| `await run(input, *, questions, **request_options)` | Uses the asynchronous SDK client |
| Return value | Complete SDK `Decision`: `answers`, `model`, `usage` |
| Input | Text or the SDK's iterable of input items, including structured evidence |
| Request options | Forwarded to `decisions.create`, e.g. `timeout`, `prompt_cache_key`, `safety_identifier` |

Clients are created lazily, so constructing a wrapper or rejecting invalid
questions needs no API key. Only the client used by a call is created. Manage
its lifetime with a context manager as above, or inject an SDK client managed
by the surrounding application. Construct a new wrapper/client after closing it.

The wrapper accepts 1–400 questions and requires each question to have a
non-empty, unique `name` and one of the three supported types. Naming is a
wrapper convention stricter than the SDK's optional names. Detailed question
schemas remain the SDK/API contract; this is not a complete local schema validator.

`model` is a constructor setting. `agent_id`, `output_type`, `max_tokens`,
`tools` and `handoffs` are not Decisions options. The return is not a
`GPTAgentResponse` or a `RunResult`, and it has no `final_output` field.
The wrapper preserves per-answer refusals and propagates SDK errors without
converting them into successful answers.

## Runnable examples

From the repository root, evaluate all three question types:

```bash
uv run --locked python -m app.examples.decisions --mode evaluate --text "I was charged twice. Please refund the duplicate charge."
```

To run the classifier and then a selected specialist:

```bash
uv run --locked python -m app.examples.decisions --mode route --min-confidence 0.8 --text "The login page fails with an error."
```

`0.8` is an illustrative threshold, not a recommended universal setting. Select
it using labeled examples and the costs of wrong routing. No threshold is
silently applied: route mode requires an explicit value between 0 and 1.
Confidence is not a guarantee of correctness.

Both commands make real OpenAI calls and may incur charges. Evaluate mode makes
one Decisions request. Route mode makes one Decisions request and, only for a
mapped confident answer, runs an agent (which can involve model calls).

## Routing behavior

`app/examples/decisions.py` exposes `route_request(text, *, decider, specialists,
min_confidence)`. Pass already configured specialists mapping `billing` and
`technical` to objects with an async `run` returning `GPTAgentResponse`.
The CLI constructs two `GPTAgent` instances using the regular model setting.

The function asks only the `department` question and passes the original text
to the selected specialist. It never imports or executes a callable named by
the model. The returned `RoutingResult` retains the whole `Decision`:

| Situation | Status | Reason | Specialist executed |
|---|---|---|---|
| Mapped choice meeting the threshold | `completed` | `null` | Only the selected one |
| Question refused | `review_required` | `refusal` | No |
| Confidence below threshold or invalid | `review_required` | `low_confidence` | No |
| No configured destination, including `other` | `review_required` | `unmapped_choice` | No |
| Missing or non-unique named answer | `review_required` | `missing_answer` | No |
| Named answer has a different type | `review_required` | `unexpected_answer_type` | No |

`completed` results include `route` and `output`. Review results leave them null.
The example signals that review is required; it does not create a review queue
or send notifications. Provider and specialist exceptions propagate to the
calling application rather than being treated as a category or refusal.

## Validation and limits

```bash
uv run --locked python -m unittest app.tests.test_gpt_decision -v
```

The offline tests exercise the actual synchronous and asynchronous SDK with
mock HTTP transports, verify request serialization and typed responses, and
test route execution, review cases and error propagation. They preserve boolean
choice values, fractional scores, refusals and usage information.

These checks do not establish live account access, latency, confidence
calibration or classification accuracy. Use representative data before setting
application thresholds. For generated explanations, extracted objects or tool
calls, continue using the corresponding Responses/Agents wrappers.
