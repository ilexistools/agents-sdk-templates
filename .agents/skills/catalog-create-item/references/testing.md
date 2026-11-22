# Testing items

Everything must pass offline: no network, no provider key.

## What is already automatic

`app/tests/test_catalog.py` runs for every item, with no code from you:

- `check` passes (README, prompt, documented fields, async `run`, valid examples);
- every tool example with `output` returns exactly that output;
- every agent handler calls `create_agent` with its own id and `output_type=Output`,
  and returns the agent's result.

So a simple tool with good examples needs no extra test file.

## When to add a test file

Add `app/tests/test_<id>.py` when the item has edge cases worth pinning, calls an
external service, or contains logic beyond what examples show. Name tests after
behavior. Import the handler module directly.

### Tool with pure logic

```python
import asyncio
import unittest

from app.tools.date_extractor import handler


class DateExtractorTests(unittest.TestCase):
    def test_ignores_invalid_dates(self):
        self.assertEqual(handler.extract_dates("31/02/2026"), [])

    def test_handler_contract(self):
        result = asyncio.run(handler.run(handler.Input(text="on 03/04/2026")))
        self.assertEqual([d.isoformat() for d in result.dates], ["2026-04-03"])


if __name__ == "__main__":
    unittest.main()
```

### Tool that calls a service: mock the boundary

```python
import asyncio
import os
import unittest
from unittest.mock import patch

from app.tools.weather import handler


class WeatherTests(unittest.TestCase):
    def test_uses_key_and_parses_response(self):
        with patch.dict(os.environ, {"WEATHER_API_KEY": "test-key"}), \
             patch.object(handler, "fetch_json", return_value={"temp_c": 21.5}) as fetch:
            result = asyncio.run(handler.run(handler.Input(city="Lisbon")))
        self.assertEqual(result.temperature_c, 21.5)
        self.assertIn("test-key", str(fetch.call_args))
```

Keep the network call in one small function (`fetch_json`) so it is the only
thing to mock.

### Agent: mock `create_agent`

```python
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.agents.invoice_reviewer import handler


class InvoiceReviewerTests(unittest.TestCase):
    def test_sends_the_invoice_text_and_returns_the_output(self):
        expected = handler.Output(verdict="ok", issues=[])
        fake = AsyncMock()
        fake.run.return_value = expected
        with patch.object(handler, "create_agent", return_value=fake) as factory:
            result = asyncio.run(handler.run(handler.Input(text="Invoice 42 ...")))
        factory.assert_called_once_with("invoice_reviewer", output_type=handler.Output)
        fake.run.assert_awaited_once()
        self.assertIn("Invoice 42", fake.run.await_args.args[0])
        self.assertEqual(result, expected)
```

Test the prompt *structure* offline with the loader if useful:
`load_agent_markdown("<id>")["sections"]` must contain the four sections.

## Live checks

`python -m app catalog run <id> --example N` runs against the configured provider
and may cost money. Run it once before finishing an agent, report what you saw,
and never commit keys or recorded responses containing personal data.
